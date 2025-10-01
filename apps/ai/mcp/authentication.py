"""
Authentication utilities for MCP servers
Handles JWT token validation and role-based permissions
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class MCPAuthenticator:
    """Handles authentication for MCP servers"""

    def __init__(self):
        self.secret_key = getattr(settings, 'SECRET_KEY')
        self.algorithm = 'HS256'
        self.token_expiry = getattr(settings, 'MCP_TOKEN_EXPIRY', 3600)  # 1 hour default

    def generate_token(self, user: User) -> str:
        """
        Generate JWT token for user

        Args:
            user: Django User instance

        Returns:
            JWT token string
        """
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiry),
            'iat': datetime.utcnow(),
            'iss': 'unityaid-mcp'
        }

        # Add role information if available
        if hasattr(user, 'role'):
            payload['role'] = user.role

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> Dict:
        """
        Validate JWT token and return payload

        Args:
            token: JWT token string

        Returns:
            Token payload dictionary

        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token has expired
        """
        if token.startswith('Bearer '):
            token = token[7:]

        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        return payload

    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user instance from JWT token

        Args:
            token: JWT token string

        Returns:
            User instance or None if invalid
        """
        try:
            payload = self.validate_token(token)
            user_id = payload.get('user_id')

            if user_id:
                return User.objects.get(id=user_id, is_active=True)

        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, User.DoesNotExist) as e:
            logger.warning(f"Token validation failed: {e}")

        return None


class MCPPermissionChecker:
    """Handles role-based permissions for MCP servers"""

    # Define role hierarchy
    ROLE_HIERARCHY = {
        'public_user': 0,
        'gso': 1,
        'ngo_user': 2,
        'un_user': 3,
        'cluster_lead': 4,
        'admin': 5
    }

    # Define permissions by resource and action
    PERMISSIONS = {
        'sites': {
            'read': ['public_user', 'gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'write': ['gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'admin': ['cluster_lead', 'admin']
        },
        'reports': {
            'read': ['gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'write': ['gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'admin': ['cluster_lead', 'admin']
        },
        'assessments': {
            'read': ['gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'write': ['gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'admin': ['cluster_lead', 'admin']
        },
        'integrations': {
            'read': ['gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'write': ['un_user', 'cluster_lead', 'admin'],
            'admin': ['admin']
        },
        'ai': {
            'read': ['gso', 'ngo_user', 'un_user', 'cluster_lead', 'admin'],
            'write': ['cluster_lead', 'admin'],
            'admin': ['admin']
        }
    }

    def __init__(self):
        pass

    def get_user_role(self, user: User) -> str:
        """
        Get user role string

        Args:
            user: Django User instance

        Returns:
            Role string
        """
        if user.is_superuser:
            return 'admin'
        elif user.is_staff:
            return 'cluster_lead'
        elif hasattr(user, 'role'):
            return user.role
        else:
            return 'public_user'

    def has_permission(self, user: User, resource: str, action: str) -> bool:
        """
        Check if user has permission for specified action on resource

        Args:
            user: Django User instance
            resource: Resource name (sites, reports, assessments, integrations, ai)
            action: Action name (read, write, admin)

        Returns:
            True if user has permission, False otherwise
        """
        if not user or not user.is_active:
            return False

        user_role = self.get_user_role(user)

        # Check if resource exists in permissions
        if resource not in self.PERMISSIONS:
            logger.warning(f"Unknown resource: {resource}")
            return False

        # Check if action exists for resource
        if action not in self.PERMISSIONS[resource]:
            logger.warning(f"Unknown action '{action}' for resource '{resource}'")
            return False

        # Check if user role is allowed for this action
        allowed_roles = self.PERMISSIONS[resource][action]
        return user_role in allowed_roles

    def filter_queryset_by_permissions(self, user: User, queryset, resource: str):
        """
        Filter queryset based on user permissions

        Args:
            user: Django User instance
            queryset: Django QuerySet to filter
            resource: Resource name

        Returns:
            Filtered QuerySet
        """
        if not user or not user.is_active:
            return queryset.none()

        user_role = self.get_user_role(user)

        # Admin and cluster leads can see everything
        if user_role in ['admin', 'cluster_lead']:
            return queryset

        # GSOs can only see data from their assigned sites
        if user_role == 'gso' and hasattr(user, 'assigned_sites'):
            if resource == 'sites':
                return queryset.filter(id__in=user.assigned_sites.all())
            elif resource == 'reports':
                return queryset.filter(site__in=user.assigned_sites.all())
            elif resource == 'assessments':
                return queryset.filter(site__in=user.assigned_sites.all())

        # Default: return full queryset for other roles
        return queryset

    def get_user_accessible_sites(self, user: User):
        """
        Get list of site IDs accessible to user

        Args:
            user: Django User instance

        Returns:
            List of site IDs or None for all sites
        """
        if not user or not user.is_active:
            return []

        user_role = self.get_user_role(user)

        # Admin and cluster leads can access all sites
        if user_role in ['admin', 'cluster_lead', 'un_user']:
            return None  # None means all sites

        # GSOs can only access their assigned sites
        if user_role == 'gso' and hasattr(user, 'assigned_sites'):
            return list(user.assigned_sites.values_list('id', flat=True))

        # NGO users can access sites in their operational areas
        if user_role == 'ngo_user' and hasattr(user, 'operational_areas'):
            # This would need to be implemented based on your site-NGO relationship
            return None

        return []


# Global instances
authenticator = MCPAuthenticator()
permission_checker = MCPPermissionChecker()