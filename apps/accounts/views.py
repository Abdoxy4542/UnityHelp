# ===== apps/accounts/views.py =====
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import User, UserProfile, EmailVerification, PasswordReset
from .serializers.serializers import UserSerializer, UserProfileSerializer, LoginSerializer, RegisterSerializer
from .utils import send_verification_email, send_password_reset_email

class RegisterView(generics.CreateAPIView):
    """User registration API endpoint"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    login(request, user)
    
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key
    })

@api_view(['POST'])
def logout_view(request):
    """User logout endpoint"""
    if request.user.is_authenticated:
        Token.objects.filter(user=request.user).delete()
    return Response({'message': 'Successfully logged out'})

class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile API view"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

# Web Template Views
def login_page(request):
    """Login page view"""
    if request.user.is_authenticated:
        return redirect('accounts:home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Find user by email and authenticate with username
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                if not user.is_verified:
                    messages.error(request, 'Please verify your email address before logging in.')
                    return redirect('accounts:verify_email', email=email)
                login(request, user)
                next_url = request.GET.get('next', 'accounts:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'accounts/login.html')

def register_page(request):
    """Registration page view"""
    if request.user.is_authenticated:
        return redirect('accounts:home')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        organization = request.POST.get('organization')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validation
        if not full_name or not email or not organization:
            messages.error(request, "All fields are required")
        elif password != password_confirm:
            messages.error(request, "Passwords don't match")
        elif len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
        else:
            # Split full name into first and last name
            name_parts = full_name.strip().split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            # Generate username from email
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user (not verified yet)
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                organization=organization,
                role='gso',  # Default role
                is_verified=False  # User needs to verify email
            )
            # Create profile
            UserProfile.objects.create(user=user)
            
            # Create email verification
            verification = EmailVerification.objects.create(
                user=user,
                email=email
            )
            
            # Send verification email
            if send_verification_email(user, verification):
                messages.success(request, 'Account created successfully! Please check your email for verification code.')
            else:
                messages.warning(request, 'Account created but email could not be sent. Check console for verification code.')
            
            return redirect('accounts:verify_email', email=email)
    
    return render(request, 'accounts/register.html')

def logout_page(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@login_required
def profile_page(request):
    """User profile page view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.organization = request.POST.get('organization', request.user.organization)
        request.user.phone_number = request.POST.get('phone_number', request.user.phone_number)
        request.user.preferred_language = request.POST.get('preferred_language', request.user.preferred_language)
        request.user.save()
        
        # Update profile info
        profile.bio = request.POST.get('bio', profile.bio)
        profile.emergency_contact = request.POST.get('emergency_contact', profile.emergency_contact)
        profile.email_notifications = bool(request.POST.get('email_notifications'))
        profile.sms_notifications = bool(request.POST.get('sms_notifications'))
        profile.push_notifications = bool(request.POST.get('push_notifications'))
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': profile,
        'role_choices': User.ROLE_CHOICES
    })

@login_required
def home_page(request):
    """Home page view - requires authentication"""
    return render(request, 'dashboard/home.html', {
        'user': request.user
    })

def verify_email(request, email):
    """Email verification page"""
    if request.method == 'POST':
        code = request.POST.get('code')
        
        if not code:
            messages.error(request, 'Please enter the verification code.')
            return render(request, 'accounts/verify_email.html', {'email': email})
        
        try:
            user = User.objects.get(email=email)
            # Find the latest unused verification code
            verification = EmailVerification.objects.filter(
                user=user,
                email=email,
                is_used=False
            ).order_by('-created_at').first()
            
            if not verification:
                messages.error(request, 'No verification code found. Please request a new one.')
                return render(request, 'accounts/verify_email.html', {'email': email})
            
            if verification.code == code and verification.is_valid():
                # Mark verification as used
                verification.is_used = True
                verification.save()
                
                # Mark user as verified
                user.is_verified = True
                user.save()
                
                messages.success(request, 'Email verified successfully! You can now log in.')
                return redirect('accounts:login')
            elif verification.is_expired():
                messages.error(request, 'Verification code has expired. Please request a new one.')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
                
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('accounts:register')
    
    return render(request, 'accounts/verify_email.html', {'email': email})

def resend_verification(request, email):
    """Resend verification code"""
    try:
        user = User.objects.get(email=email)
        
        if user.is_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('accounts:login')
        
        # Create new verification code
        verification = EmailVerification.objects.create(
            user=user,
            email=email
        )
        
        # Send verification email
        if send_verification_email(user, verification):
            messages.success(request, 'Verification code sent to your email.')
        else:
            messages.warning(request, 'Could not send email. Check console for verification code.')
            
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:register')
    
    return redirect('accounts:verify_email', email=email)

def forgot_password(request):
    """Forgot password page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            if not user.is_verified:
                messages.error(request, 'Please verify your email address first.')
                return redirect('accounts:verify_email', email=email)
            
            # Create password reset code
            reset = PasswordReset.objects.create(
                user=user,
                email=email
            )
            
            # Send reset email
            if send_password_reset_email(user, reset):
                messages.success(request, 'Password reset code sent to your email.')
            else:
                messages.warning(request, 'Could not send email. Check console for reset code.')
            
            return redirect('accounts:reset_password', email=email)
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'accounts/forgot_password.html')

def reset_password(request, email):
    """Password reset page"""
    if request.method == 'POST':
        code = request.POST.get('code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not code or not new_password or not confirm_password:
            messages.error(request, 'All fields are required.')
            return render(request, 'accounts/reset_password.html', {'email': email})
        
        if new_password != confirm_password:
            messages.error(request, "Passwords don't match.")
            return render(request, 'accounts/reset_password.html', {'email': email})
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'accounts/reset_password.html', {'email': email})
        
        try:
            user = User.objects.get(email=email)
            # Find the latest unused reset code
            reset = PasswordReset.objects.filter(
                user=user,
                email=email,
                is_used=False
            ).order_by('-created_at').first()
            
            if not reset:
                messages.error(request, 'No reset code found. Please request a new one.')
                return render(request, 'accounts/reset_password.html', {'email': email})
            
            if reset.code == code and reset.is_valid():
                # Mark reset as used
                reset.is_used = True
                reset.save()
                
                # Update user password
                user.set_password(new_password)
                user.save()
                
                messages.success(request, 'Password updated successfully! You can now log in.')
                return redirect('accounts:login')
            elif reset.is_expired():
                messages.error(request, 'Reset code has expired. Please request a new one.')
                return redirect('accounts:forgot_password')
            else:
                messages.error(request, 'Invalid reset code. Please try again.')
                
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('accounts:forgot_password')
    
    return render(request, 'accounts/reset_password.html', {'email': email})

def resend_reset_code(request, email):
    """Resend password reset code"""
    try:
        user = User.objects.get(email=email)
        
        if not user.is_verified:
            messages.error(request, 'Please verify your email address first.')
            return redirect('accounts:verify_email', email=email)
        
        # Create new reset code
        reset = PasswordReset.objects.create(
            user=user,
            email=email
        )
        
        # Send reset email
        if send_password_reset_email(user, reset):
            messages.success(request, 'Reset code sent to your email.')
        else:
            messages.warning(request, 'Could not send email. Check console for reset code.')
            
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:forgot_password')
    
    return redirect('accounts:reset_password', email=email)
