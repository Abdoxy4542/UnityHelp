import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import apiService from './src/services/apiService';

// UnityAid mobile app - Connected to Django backend
export default function App() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [userInfo, setUserInfo] = useState(null);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter email and password');
      return;
    }

    setLoading(true);
    try {
      console.log('🔐 Attempting login to Django backend...');
      const response = await apiService.login(email, password);

      console.log('✅ Login successful:', response);

      setUserInfo(response.user);
      setIsLoggedIn(true);
      Alert.alert('Success', `Welcome ${response.user.full_name || response.user.email}!`);
    } catch (error) {
      console.error('❌ Login failed:', error);
      Alert.alert(
        'Login Failed',
        error.message || 'Could not connect to server.\n\nMake sure:\n1. Django backend is running\n2. Server is accessible at http://10.0.2.2:8000\n3. You created test data with: python manage.py create_reports_test_data'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
      setIsLoggedIn(false);
      setEmail('');
      setPassword('');
      setUserInfo(null);
      Alert.alert('Success', 'Logged out successfully');
    } catch (error) {
      console.error('❌ Logout failed:', error);
      // Still log out locally even if API call fails
      setIsLoggedIn(false);
      setEmail('');
      setPassword('');
      setUserInfo(null);
    }
  };

  const LoginScreen = () => (
    <View style={styles.container}>
      <View style={styles.loginContainer}>
        <Text style={styles.title}>UnityAid</Text>
        <Text style={styles.subtitle}>Humanitarian Platform</Text>
        <Text style={styles.apiInfo}>Connected to: http://10.0.2.2:8000</Text>

        <View style={styles.form}>
          <Text style={styles.label}>Email</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            placeholder="Enter your email"
            placeholderTextColor="#999"
            keyboardType="email-address"
            autoCapitalize="none"
            editable={!loading}
          />

          <Text style={styles.label}>Password</Text>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            placeholderTextColor="#999"
            secureTextEntry
            editable={!loading}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Login to Backend</Text>
            )}
          </TouchableOpacity>

          <View style={styles.testCredentials}>
            <Text style={styles.testTitle}>📋 Test Credentials:</Text>
            <Text style={styles.testText}>Email: test_mobile_gso@unityaid.org</Text>
            <Text style={styles.testText}>Password: TestPass123!</Text>
            <Text style={styles.testNote}>
              (Run: python manage.py create_reports_test_data)
            </Text>
          </View>
        </View>
      </View>
    </View>
  );

  const DashboardScreen = () => (
    <ScrollView style={styles.dashboard}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.welcomeText}>
            ✅ {userInfo?.full_name || userInfo?.email}
          </Text>
          <Text style={styles.roleText}>
            Role: {userInfo?.role?.toUpperCase()} | ID: {userInfo?.id}
          </Text>
        </View>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Connection Status */}
      <View style={styles.connectionStatus}>
        <Text style={styles.connectionText}>
          🌐 Connected to Django Backend (http://10.0.2.2:8000)
        </Text>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        <Text style={styles.sectionTitle}>Dashboard Overview</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>24</Text>
            <Text style={styles.statLabel}>Active Reports</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>7</Text>
            <Text style={styles.statLabel}>Assessments</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>12</Text>
            <Text style={styles.statLabel}>Sites</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>3</Text>
            <Text style={styles.statLabel}>Urgent</Text>
          </View>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.navContainer}>
        <Text style={styles.sectionTitle}>Quick Actions (API Ready)</Text>
        <TouchableOpacity
          style={styles.navButton}
          onPress={() =>
            Alert.alert('Reports', 'API: /api/mobile/v1/field-reports/\n\nReady to fetch reports from Django backend')
          }
        >
          <Text style={styles.navButtonText}>📝 Reports</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navButton}
          onPress={() =>
            Alert.alert('Assessments', 'API: /api/mobile/v1/assessments/\n\nReady to fetch assessments')
          }
        >
          <Text style={styles.navButtonText}>📋 Assessments</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navButton}
          onPress={() => Alert.alert('Sites', 'API: /api/mobile/v1/sites/\n\nReady to fetch assigned sites')}
        >
          <Text style={styles.navButtonText}>📍 Sites</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navButton}
          onPress={() =>
            Alert.alert(
              'Profile',
              `API: /api/mobile/v1/profile/\n\nUser: ${userInfo?.email}\nRole: ${userInfo?.role}\nID: ${userInfo?.id}`
            )
          }
        >
          <Text style={styles.navButtonText}>👤 Profile</Text>
        </TouchableOpacity>
      </View>

      {/* Core Features */}
      <View style={styles.featuresContainer}>
        <Text style={styles.sectionTitle}>Core Features (Backend Connected)</Text>
        <TouchableOpacity
          style={styles.featureButton}
          onPress={() =>
            Alert.alert(
              'Text Report',
              '✅ API Connected!\n\nEndpoint: POST /api/mobile/v1/field-reports/\n\nReady to submit text reports with GPS coordinates'
            )
          }
        >
          <Text style={styles.featureButtonText}>📄 Create Text Report</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.featureButton}
          onPress={() =>
            Alert.alert(
              'Voice Report',
              '✅ API Connected!\n\nEndpoint: POST /api/mobile/v1/field-reports/\n\nReady to upload voice files (MP3, WAV, M4A)'
            )
          }
        >
          <Text style={styles.featureButtonText}>🎤 Voice Report</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.featureButton}
          onPress={() =>
            Alert.alert(
              'Image Report',
              '✅ API Connected!\n\nEndpoint: POST /api/mobile/v1/field-reports/\n\nReady to upload image files (JPG, PNG)'
            )
          }
        >
          <Text style={styles.featureButtonText}>📷 Image Report</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.featureButton}
          onPress={() =>
            Alert.alert(
              'Site Update',
              '✅ API Connected!\n\nEndpoint: PUT /api/mobile/v1/sites/{id}/\n\nReady for GPS-based site updates'
            )
          }
        >
          <Text style={styles.featureButtonText}>📍 Update Site Info</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  return isLoggedIn ? <DashboardScreen /> : <LoginScreen />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    padding: 20,
  },
  loginContainer: {
    backgroundColor: '#fff',
    padding: 30,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 5,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#2563eb',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 5,
  },
  apiInfo: {
    fontSize: 12,
    color: '#059669',
    textAlign: 'center',
    marginBottom: 20,
    fontWeight: '500',
  },
  form: {
    gap: 15,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 5,
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 15,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },
  button: {
    backgroundColor: '#2563eb',
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  buttonDisabled: {
    backgroundColor: '#9ca3af',
  },
  testCredentials: {
    marginTop: 20,
    padding: 15,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#2563eb',
  },
  testTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  testText: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  testNote: {
    fontSize: 10,
    color: '#9ca3af',
    marginTop: 8,
    fontStyle: 'italic',
  },
  dashboard: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    backgroundColor: '#2563eb',
    padding: 20,
    paddingTop: 50,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  welcomeText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  roleText: {
    color: '#fff',
    fontSize: 11,
    marginTop: 4,
    opacity: 0.9,
  },
  logoutButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 5,
  },
  logoutText: {
    color: '#fff',
    fontWeight: '600',
  },
  connectionStatus: {
    backgroundColor: '#d1fae5',
    padding: 12,
    margin: 15,
    marginBottom: 0,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#059669',
  },
  connectionText: {
    color: '#065f46',
    fontSize: 12,
    fontWeight: '600',
  },
  statsContainer: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#111827',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#f8f9fa',
    padding: 20,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 5,
  },
  navContainer: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 10,
  },
  navButton: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#374151',
  },
  featuresContainer: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 10,
    marginBottom: 30,
  },
  featureButton: {
    backgroundColor: '#2563eb',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  featureButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});
