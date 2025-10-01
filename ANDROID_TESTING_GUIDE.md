# UnityAid Mobile API Android Testing Guide

## Overview

This guide will help you manually test the UnityAid Mobile API reports feature using Android Studio emulator. You'll be able to submit text, voice, and image reports and verify they appear in the backend database.

## Prerequisites

### Required Software
- **Android Studio** (latest version)
- **UnityAid Django Backend** (running on your machine)
- **API Testing Tool** (Postman, Insomnia, or custom app)

### Backend Setup

1. **Start the Django Server**
   ```bash
   cd C:\Users\Lenovo\Desktop\unityaid_platform

   # Activate virtual environment
   .\venv\Scripts\activate

   # Run migrations
   python manage.py migrate

   # Create test data
   python manage.py create_reports_test_data

   # Start server
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Verify Backend is Running**
   - Open browser to `http://localhost:8000/api/docs/`
   - You should see the API documentation

## Android Studio Emulator Setup

### 1. Create Android Virtual Device (AVD)

1. **Open Android Studio**
2. **Go to Tools → AVD Manager**
3. **Click "Create Virtual Device"**
4. **Select a Device** (e.g., Pixel 4)
5. **Select System Image** (API 30+ recommended)
6. **Configure AVD**:
   - Name: `UnityAid_Test_Device`
   - Enable: Hardware - Keyboard
   - Advanced Settings → Network: Speed: Full, Latency: None
7. **Finish and Start Emulator**

### 2. Configure Network Access

The emulator needs to access your Django server running on localhost.

**Option A: Use 10.0.2.2 (Emulator's localhost)**
- From emulator: `http://10.0.2.2:8000/`
- This maps to your computer's `localhost:8000`

**Option B: Use your computer's IP address**
1. Find your IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Use: `http://YOUR_IP:8000/`

## Testing Options

### Option 1: Using Postman Mobile or HTTP Client Apps

1. **Install HTTP Client** on emulator:
   - HTTP Shortcut
   - Postman (if available)
   - Any REST client app

2. **Test API endpoints** as described in the API Testing section below

### Option 2: Create Simple Android Test App

Create a minimal Android app for testing:

#### Basic Android App Structure

1. **Create New Android Project**
   - Application name: `UnityAid Reporter`
   - Language: Java/Kotlin
   - Minimum SDK: API 24

2. **Add Dependencies** (in `app/build.gradle`):
   ```gradle
   dependencies {
       implementation 'com.squareup.okhttp3:okhttp:4.10.0'
       implementation 'com.squareup.okhttp3:logging-interceptor:4.10.0'
       implementation 'com.google.code.gson:gson:2.10.1'
   }
   ```

3. **Add Permissions** (in `AndroidManifest.xml`):
   ```xml
   <uses-permission android:name="android.permission.INTERNET" />
   <uses-permission android:name="android.permission.RECORD_AUDIO" />
   <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
   <uses-permission android:name="android.permission.CAMERA" />
   ```

4. **Basic MainActivity Layout** (`activity_main.xml`):
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
       android:layout_width="match_parent"
       android:layout_height="match_parent"
       android:orientation="vertical"
       android:padding="16dp">

       <!-- Login Section -->
       <TextView
           android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="UnityAid Mobile Reporter"
           android:textSize="24sp"
           android:textStyle="bold" />

       <EditText
           android:id="@+id/etEmail"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:hint="Email"
           android:text="test_mobile_gso@unityaid.org" />

       <EditText
           android:id="@+id/etPassword"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:hint="Password"
           android:inputType="textPassword"
           android:text="TestPass123!" />

       <Button
           android:id="@+id/btnLogin"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:text="Login" />

       <!-- Report Section -->
       <TextView
           android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="Create Report"
           android:textSize="18sp"
           android:layout_marginTop="32dp" />

       <EditText
           android:id="@+id/etTitle"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:hint="Report Title" />

       <EditText
           android:id="@+id/etContent"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:hint="Report Content"
           android:minLines="3" />

       <Spinner
           android:id="@+id/spinnerType"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:entries="@array/report_types" />

       <Spinner
           android:id="@+id/spinnerPriority"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:entries="@array/priority_levels" />

       <Button
           android:id="@+id/btnSelectImage"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:text="Select Image" />

       <Button
           android:id="@+id/btnRecordVoice"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:text="Record Voice" />

       <Button
           android:id="@+id/btnSubmitReport"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:text="Submit Report" />

       <TextView
           android:id="@+id/tvStatus"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:text="Status: Not logged in"
           android:layout_marginTop="16dp" />

   </LinearLayout>
   ```

5. **Add String Arrays** (`res/values/strings.xml`):
   ```xml
   <resources>
       <string name="app_name">UnityAid Reporter</string>

       <string-array name="report_types">
           <item>text</item>
           <item>voice</item>
           <item>image</item>
           <item>mixed</item>
       </string-array>

       <string-array name="priority_levels">
           <item>low</item>
           <item>medium</item>
           <item>high</item>
           <item>urgent</item>
       </string-array>
   </resources>
   ```

6. **Basic MainActivity.java**:
   ```java
   public class MainActivity extends AppCompatActivity {
       private static final String BASE_URL = "http://10.0.2.2:8000/api/mobile/v1/";
       private String accessToken = "";

       // UI elements
       private EditText etEmail, etPassword, etTitle, etContent;
       private Button btnLogin, btnSubmitReport;
       private TextView tvStatus;
       private Spinner spinnerType, spinnerPriority;

       @Override
       protected void onCreate(Bundle savedInstanceState) {
           super.onCreate(savedInstanceState);
           setContentView(R.layout.activity_main);

           initViews();
           setupListeners();
       }

       private void initViews() {
           etEmail = findViewById(R.id.etEmail);
           etPassword = findViewById(R.id.etPassword);
           etTitle = findViewById(R.id.etTitle);
           etContent = findViewById(R.id.etContent);
           btnLogin = findViewById(R.id.btnLogin);
           btnSubmitReport = findViewById(R.id.btnSubmitReport);
           tvStatus = findViewById(R.id.tvStatus);
           spinnerType = findViewById(R.id.spinnerType);
           spinnerPriority = findViewById(R.id.spinnerPriority);
       }

       private void setupListeners() {
           btnLogin.setOnClickListener(v -> performLogin());
           btnSubmitReport.setOnClickListener(v -> submitReport());
       }

       private void performLogin() {
           // Implement login API call
           // Update tvStatus and accessToken
       }

       private void submitReport() {
           // Implement report submission API call
       }
   }
   ```

## API Testing (Manual with Postman or Similar)

### Step 1: Login

**Endpoint:** `POST http://10.0.2.2:8000/api/mobile/v1/auth/login/`

**Request Body:**
```json
{
    "email": "test_mobile_gso@unityaid.org",
    "password": "TestPass123!",
    "device_id": "android_test_device_001",
    "platform": "android"
}
```

**Expected Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
        "id": 1,
        "email": "test_mobile_gso@unityaid.org",
        "role": "gso",
        "full_name": "Test GSO"
    }
}
```

**Save the `access_token` for subsequent requests.**

### Step 2: Test Text Report Submission

**Endpoint:** `POST http://10.0.2.2:8000/api/mobile/v1/field-reports/`

**Headers:**
```
Authorization: Token YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
    "site": 1,
    "title": "Android Test Text Report",
    "text_content": "This is a test text report submitted from Android emulator via Postman.",
    "report_type": "text",
    "priority": "medium",
    "location_coordinates": {
        "lat": 15.5527,
        "lng": 32.5599
    }
}
```

### Step 3: Test Image Report Submission

**Endpoint:** `POST http://10.0.2.2:8000/api/mobile/v1/field-reports/`

**Headers:**
```
Authorization: Token YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Form Data:**
```
site: 1
title: Android Test Image Report
text_content: This report includes an image attachment.
report_type: image
priority: high
image_file: [Select an image file]
location_coordinates: {"lat": 15.5527, "lng": 32.5599}
```

### Step 4: Test Voice Report Submission

**Endpoint:** `POST http://10.0.2.2:8000/api/mobile/v1/field-reports/`

**Headers:**
```
Authorization: Token YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Form Data:**
```
site: 1
title: Android Test Voice Report
report_type: voice
priority: urgent
voice_file: [Select an audio file - MP3, WAV, OGG, M4A]
location_coordinates: {"lat": 15.5627, "lng": 32.5699}
```

### Step 5: Test Mixed Media Report

**Form Data:**
```
site: 1
title: Android Test Mixed Report
text_content: This is a mixed media report with text, voice, and image.
report_type: mixed
priority: high
voice_file: [Select audio file]
image_file: [Select image file]
location_coordinates: {"lat": 15.5627, "lng": 32.5699}
```

## Verification Steps

### 1. Check API Response
After each submission, verify the response:
```json
{
    "id": 123,
    "title": "Your Report Title",
    "report_type": "text",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    // ... other fields
}
```

### 2. Verify in Django Admin
1. Open `http://localhost:8000/admin/`
2. Login with admin credentials
3. Go to **Reports → Field Reports**
4. Verify your submitted reports appear with correct data

### 3. Check Database Directly
```sql
-- Connect to your database and run:
SELECT id, title, report_type, priority, status, created_at
FROM reports_fieldreport
ORDER BY created_at DESC LIMIT 10;
```

### 4. Verify File Storage
Check that media files are stored correctly:
- **Voice files:** `media/reports/voice/YYYY/MM/`
- **Image files:** `media/reports/images/YYYY/MM/`

### 5. Test API List Endpoint
**Endpoint:** `GET http://10.0.2.2:8000/api/mobile/v1/field-reports/`

**Headers:**
```
Authorization: Token YOUR_ACCESS_TOKEN
```

Should return list of reports you can access based on your role.

## Testing Scenarios

### Scenario 1: GSO User Testing
1. Login as GSO user
2. Submit reports for assigned sites only
3. Verify can view own reports and site reports
4. Test different media types

### Scenario 2: NGO User Testing
1. Login as NGO user
2. Try to submit reports for organization sites
3. Verify limited access to reports

### Scenario 3: Admin User Testing
1. Login as admin
2. Verify can see all reports
3. Test all CRUD operations

### Scenario 4: Error Testing
1. Try submitting without authentication
2. Try submitting voice report without audio file
3. Try submitting to unauthorized site
4. Verify proper error responses

## Troubleshooting

### Common Issues

1. **Network Connection**
   - Emulator can't reach Django server
   - **Solution:** Use `10.0.2.2:8000` instead of `localhost:8000`

2. **Authentication Errors**
   - Token expired or invalid
   - **Solution:** Login again to get new token

3. **File Upload Errors**
   - Files too large or wrong format
   - **Solution:** Check file size limits and supported formats

4. **CORS Errors**
   - Cross-origin requests blocked
   - **Solution:** Verify CORS settings in Django

### Debug Tips

1. **Check Django Logs**
   ```bash
   tail -f logs/django.log
   ```

2. **Enable Django Debug Mode**
   ```python
   # In settings/development.py
   DEBUG = True
   ```

3. **Check API Documentation**
   - Visit `http://localhost:8000/api/docs/`
   - Use interactive API testing

## Expected Results

After successful testing, you should have:
- ✅ Successfully logged in via mobile API
- ✅ Submitted text reports with GPS coordinates
- ✅ Uploaded voice files (MP3, WAV, etc.)
- ✅ Uploaded image files (JPG, PNG, etc.)
- ✅ Created mixed media reports
- ✅ Verified data appears in Django admin
- ✅ Confirmed files stored in correct directories
- ✅ Tested role-based access control

## Next Steps

1. **Extend Android App**: Add full CRUD operations
2. **Add Real-time Features**: WebSocket notifications
3. **Implement Offline Mode**: Local storage and sync
4. **Add GPS Integration**: Automatic location capture
5. **Enhance UI/UX**: Professional mobile interface

## Support

If you encounter issues:
1. Check Django server logs
2. Verify API endpoints in documentation
3. Test with Postman first before mobile app
4. Check database migrations are applied
5. Ensure test data was created successfully

---

**Happy Testing! 🚀**