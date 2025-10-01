import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Platform, Text, View } from 'react-native';

// Import screen components (we'll create these next)
import HomeScreen from '../screens/main/HomeScreen';
import ReportsScreen from '../screens/main/ReportsScreen';
import AssessmentsScreen from '../screens/main/AssessmentsScreen';
import SitesScreen from '../screens/main/SitesScreen';
import ProfileScreen from '../screens/main/ProfileScreen';

// Types
import type { BottomTabParamList } from '../types';

const Tab = createBottomTabNavigator<BottomTabParamList>();

// Simple icon component to replace vector icons
const TabIcon = ({ name, focused }: { name: string; focused: boolean }) => (
  <View style={{
    width: 24,
    height: 24,
    backgroundColor: focused ? '#2563eb' : '#9ca3af',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  }}>
    <Text style={{
      color: 'white',
      fontSize: 10,
      fontWeight: 'bold'
    }}>
      {name.charAt(0)}
    </Text>
  </View>
);

const MainTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          return <TabIcon name={route.name} focused={focused} />;
        },
        tabBarActiveTintColor: '#2563eb',
        tabBarInactiveTintColor: '#9ca3af',
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth: 1,
          borderTopColor: '#e5e7eb',
          height: Platform.OS === 'ios' ? 90 : 60,
          paddingBottom: Platform.OS === 'ios' ? 20 : 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
        headerStyle: {
          backgroundColor: '#fff',
          shadowColor: '#000',
          shadowOffset: {
            width: 0,
            height: 2,
          },
          shadowOpacity: 0.1,
          shadowRadius: 3.84,
          elevation: 5,
        },
        headerTitleStyle: {
          fontSize: 18,
          fontWeight: '600',
          color: '#111827',
        },
        headerTintColor: '#2563eb',
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: 'Dashboard',
          headerTitle: 'UnityAid Dashboard',
        }}
      />
      <Tab.Screen
        name="Reports"
        component={ReportsScreen}
        options={{
          title: 'Reports',
          headerTitle: 'Field Reports',
        }}
      />
      <Tab.Screen
        name="Assessments"
        component={AssessmentsScreen}
        options={{
          title: 'Assessments',
          headerTitle: 'Assessments',
        }}
      />
      <Tab.Screen
        name="Sites"
        component={SitesScreen}
        options={{
          title: 'Sites',
          headerTitle: 'Sites',
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: 'Profile',
          headerTitle: 'Profile',
        }}
      />
    </Tab.Navigator>
  );
};

export default MainTabNavigator;