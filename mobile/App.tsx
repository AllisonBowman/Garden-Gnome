import React, { useEffect, useState } from 'react';
import { Text } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, useNavigationContainerRef } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AppThemeProvider, useAppTheme } from './src/theme/ThemeProvider';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import PlantsScreen        from './src/screens/PlantsScreen';
import PlantDetailScreen   from './src/screens/PlantDetailScreen';
import AddPlantScreen      from './src/screens/AddPlantScreen';
import SpeciesScreen       from './src/screens/SpeciesScreen';
import SpeciesDetailScreen from './src/screens/SpeciesDetailScreen';
import EnvironmentsScreen  from './src/screens/EnvironmentsScreen';
import EnvironmentDetailScreen from './src/screens/EnvironmentDetailScreen';
import CensusScreen        from './src/screens/CensusScreen';
import SettingsScreen      from './src/screens/SettingsScreen';
import { rescheduleAllReminders } from './src/notifications/reminders';
import Onboarding from './src/onboarding/Onboarding';
import { getOnboardingSeen, setOnboardingSeen } from './src/onboarding/storage';
import { fetchPlants } from './src/api/plants';
import { AuthProvider, useAuth } from './src/auth/AuthContext';
import LoginScreen from './src/auth/LoginScreen';

// ── Param lists (imported by child screens) ───────────────────────────────────
export type PlantsStackParamList = {
  PlantsList:  undefined;
  PlantDetail: { plantId: number };
  AddPlant:    undefined;
};

export type SpeciesStackParamList = {
  SpeciesList:   undefined;
  SpeciesDetail: { speciesId: number };
};

export type EnvironmentsStackParamList = {
  EnvironmentsList:  undefined;
  EnvironmentDetail: { environmentId: number; name?: string };
};

type RootTabParamList = {
  Plants:       undefined;
  Species:      undefined;
  Environments: undefined;
  Census:       undefined;
  Settings:     undefined;
};

// ── Stack navigators ──────────────────────────────────────────────────────────
const PlantsStack       = createNativeStackNavigator<PlantsStackParamList>();
const SpeciesStack      = createNativeStackNavigator<SpeciesStackParamList>();
const EnvironmentsStack = createNativeStackNavigator<EnvironmentsStackParamList>();
const Tab               = createBottomTabNavigator<RootTabParamList>();

// Header colors come from the active theme so the nav bar matches Almanac /
// Observatory (hook, so each navigator recomputes on a theme toggle).
function useHeaderOpts() {
  const { palette } = useAppTheme();
  return {
    headerStyle:      { backgroundColor: palette.acc },
    headerTintColor:  palette.btnInk,
    headerTitleStyle: { fontWeight: '700' as const },
  };
}

function PlantsNavigator() {
  return (
    <PlantsStack.Navigator screenOptions={useHeaderOpts()}>
      <PlantsStack.Screen name="PlantsList"  component={PlantsScreen}      options={{ title: 'My Plants' }} />
      <PlantsStack.Screen name="PlantDetail" component={PlantDetailScreen} options={{ title: 'Plant' }} />
      <PlantsStack.Screen name="AddPlant"    component={AddPlantScreen}    options={{ title: 'Add plant' }} />
    </PlantsStack.Navigator>
  );
}

function SpeciesNavigator() {
  return (
    <SpeciesStack.Navigator screenOptions={useHeaderOpts()}>
      <SpeciesStack.Screen name="SpeciesList"   component={SpeciesScreen}       options={{ title: 'Species catalog' }} />
      <SpeciesStack.Screen name="SpeciesDetail" component={SpeciesDetailScreen} options={{ title: 'Species' }} />
    </SpeciesStack.Navigator>
  );
}

function EnvironmentsNavigator() {
  return (
    <EnvironmentsStack.Navigator screenOptions={useHeaderOpts()}>
      <EnvironmentsStack.Screen name="EnvironmentsList" component={EnvironmentsScreen} options={{ title: 'Environments' }} />
      <EnvironmentsStack.Screen
        name="EnvironmentDetail"
        component={EnvironmentDetailScreen}
        options={({ route }) => ({ title: route.params.name ?? 'Environment' })}
      />
    </EnvironmentsStack.Navigator>
  );
}

// ── React Query ───────────────────────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

// ── Tab icon ──────────────────────────────────────────────────────────────────
function TabIcon({ emoji, focused }: { emoji: string; focused: boolean }) {
  return (
    <Text style={{ fontSize: focused ? 22 : 18, opacity: focused ? 1 : 0.5 }}>
      {emoji}
    </Text>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
// AuthGate decides between the login screen and the app proper; it must live
// inside AuthProvider, so App wraps it below.
function AuthGate() {
  const { status } = useAuth();
  const { palette, name: themeName } = useAppTheme();
  const headerOpts = useHeaderOpts();
  const navigationRef = useNavigationContainerRef();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const signedIn = status === 'signedIn';

  // Refresh the reminder schedule on every launch so it stays accurate even
  // if the app was closed for days (no-op on web / when reminders are off)
  useEffect(() => {
    if (signedIn) void rescheduleAllReminders();
  }, [signedIn]);

  // First-run onboarding: show only if it hasn't been seen AND the account
  // has no plants. Runs only once signed in (the plants call needs a token).
  useEffect(() => {
    if (!signedIn) return;
    (async () => {
      if (await getOnboardingSeen()) return;
      try {
        const plants = await fetchPlants();
        if (plants.length === 0) setShowOnboarding(true);
        else await setOnboardingSeen(); // returning user — remember, don't show
      } catch {
        // Offline or backend unreachable — defer the decision to next launch
      }
    })();
  }, [signedIn]);

  const dismissOnboarding = () => {
    void setOnboardingSeen();
    setShowOnboarding(false);
  };
  const onboardingAddPlant = () => {
    void setOnboardingSeen();
    setShowOnboarding(false);
    // Tab 'Plants' contains a stack with the 'AddPlant' screen. The ref has no
    // typed param list, so cast navigate to a permissive signature.
    (navigationRef.navigate as (name: string, params?: object) => void)(
      'Plants', { screen: 'AddPlant' },
    );
  };

  // Booting: keep the splash background, no flicker to login
  if (status === 'loading') return null;

  if (!signedIn) {
    return (
      <>
        <StatusBar style={themeName === 'observatory' ? 'light' : 'dark'} />
        <LoginScreen />
      </>
    );
  }

  return (
    <NavigationContainer ref={navigationRef}>
      <StatusBar style="light" />
      <Tab.Navigator
              screenOptions={{
                tabBarActiveTintColor: palette.acc,
                tabBarInactiveTintColor: palette.sub,
                tabBarStyle: {
                  paddingBottom: 4,
                  backgroundColor: palette.card,
                  borderTopColor: palette.line,
                },
                ...headerOpts,
              }}
            >
              <Tab.Screen
                name="Plants"
                component={PlantsNavigator}
                options={{
                  headerShown: false,
                  tabBarIcon: ({ focused }) => <TabIcon emoji="🌱" focused={focused} />,
                }}
              />
              <Tab.Screen
                name="Species"
                component={SpeciesNavigator}
                options={{
                  headerShown: false,
                  tabBarIcon: ({ focused }) => <TabIcon emoji="📚" focused={focused} />,
                }}
              />
              <Tab.Screen
                name="Environments"
                component={EnvironmentsNavigator}
                options={{
                  headerShown: false,
                  tabBarIcon: ({ focused }) => <TabIcon emoji="🌍" focused={focused} />,
                }}
              />
              <Tab.Screen
                name="Census"
                component={CensusScreen}
                options={{
                  title: 'Census',
                  tabBarIcon: ({ focused }) => <TabIcon emoji="📊" focused={focused} />,
                }}
              />
              <Tab.Screen
                name="Settings"
                component={SettingsScreen}
                options={{
                  title: 'Settings',
                  tabBarIcon: ({ focused }) => <TabIcon emoji="⚙️" focused={focused} />,
                }}
              />
      </Tab.Navigator>
      {showOnboarding && (
        <Onboarding onSkip={dismissOnboarding} onAddPlant={onboardingAddPlant} />
      )}
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AppThemeProvider>
          <AuthProvider>
            <AuthGate />
          </AuthProvider>
        </AppThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
