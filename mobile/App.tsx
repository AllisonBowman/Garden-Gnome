import React, { useEffect, useState } from 'react';
import { AppState, Platform, Text } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, useNavigationContainerRef } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AppThemeProvider, useAppTheme } from './src/theme/ThemeProvider';
import { QueryClient, QueryClientProvider, focusManager } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import PlantsScreen        from './src/screens/PlantsScreen';
import PlantDetailScreen   from './src/screens/PlantDetailScreen';
import AddPlantScreen      from './src/screens/AddPlantScreen';
import CaptureGardenScreen from './src/screens/CaptureGardenScreen';
import SpeciesScreen       from './src/screens/SpeciesScreen';
import SpeciesDetailScreen from './src/screens/SpeciesDetailScreen';
import GrowingAreasScreen  from './src/screens/GrowingAreasScreen';
import GrowingAreaDetailScreen from './src/screens/GrowingAreaDetailScreen';
import CensusScreen        from './src/screens/CensusScreen';
import AlmanacScreen      from './src/screens/AlmanacScreen';
import SettingsScreen      from './src/screens/SettingsScreen';
import { rescheduleAllReminders } from './src/notifications/reminders';
import Onboarding from './src/onboarding/Onboarding';
import { GROWING_AREAS_TAB } from './src/onboarding/slides';
import { getOnboardingSeen, setOnboardingSeen } from './src/onboarding/storage';
import { fetchPlants } from './src/api/plants';
import { dropSessionData } from './src/api/sessionData';
import { retryOnceIfPassing } from './src/api/errorMessage';
import { AuthProvider, useAuth } from './src/auth/AuthContext';
import LoginScreen from './src/auth/LoginScreen';
import ErrorBoundary, { guarded } from './src/components/ErrorBoundary';

// ── Param lists (imported by child screens) ───────────────────────────────────
/** What Add Plant may be opened with: `growingAreaId` preselects where the
 *  plant goes, set when it is opened from an area's own screen. */
export type AddPlantParams = { growingAreaId?: number } | undefined;

/** A species, and — when it was opened from an area's candidates or the
 *  Almanac's area filter — the area it was being read against, whose full
 *  findings the page then shows. */
export type SpeciesDetailParams = { speciesId: number; growingAreaId?: number };

/** The Almanac, and the growing area to open it narrowed to — set when it
 *  is opened from that area's screen to see the rest of its candidates. */
export type AlmanacParams = { growingAreaId?: number } | undefined;

export type PlantsStackParamList = {
  PlantsList:    undefined;
  PlantDetail:   { plantId: number };
  AddPlant:      AddPlantParams;
  CaptureGarden: undefined;
};

export type SpeciesStackParamList = {
  SpeciesList:   undefined;
  SpeciesDetail: SpeciesDetailParams;
  // The catalog narrowed to a growing area, which this tab's list can't do.
  Almanac:       AlmanacParams;
};

export type GrowingAreasStackParamList = {
  GrowingAreasList:  undefined;
  GrowingAreaDetail: { growingAreaId: number; name?: string };
  // Reached from an area, so "see what suits it, read about it, put one in"
  // stays in this tab and Back returns to the area, which then shows it.
  AddPlant:          AddPlantParams;
  SpeciesDetail:     SpeciesDetailParams;
  // The rest of an area's candidates, past the few its screen shows.
  Almanac:           AlmanacParams;
};

export type CensusStackParamList = {
  CensusSummary: undefined;
  Almanac:       AlmanacParams;
  SpeciesDetail: SpeciesDetailParams;
};

type RootTabParamList = {
  Plants:       undefined;
  Species:      undefined;
  GrowingAreas: undefined;
  Census:       undefined;
  Settings:     undefined;
};

// ── React Query ───────────────────────────────────────────────────────────────
// One automatic retry, and only for a failure that can pass: no signal, a
// timeout, or a server that scaled to zero and is still waking up (the first
// request after a quiet spell can take several seconds, and the first boot
// after a deploy longer). A 404 or a 422 will answer the same again, and
// retrying it only doubles the wait before the screen can say so.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: retryOnceIfPassing,
      staleTime: 30_000,
    },
  },
});

// After a crash, drop every cached answer and fetch it fresh: a malformed
// server answer is the likeliest cause, and redrawing from the same cache
// would only crash again.
const resetData = () => { void queryClient.resetQueries(); };

// ── Screens, each behind its own error boundary ───────────────────────────────
// A render error costs one screen: the header's back button, the tab bar and
// every other tab keep working. Wrapped once here, never inside a render, so
// each wrapper keeps its identity.
const Plants        = guarded(PlantsScreen, 'My Plants', resetData);
const PlantDetail   = guarded(PlantDetailScreen, 'Plant', resetData);
const AddPlant      = guarded(AddPlantScreen, 'Add plant', resetData);
const CaptureGarden = guarded(CaptureGardenScreen, 'Walk the garden', resetData);
const Species       = guarded(SpeciesScreen, 'Species catalog', resetData);
const SpeciesDetail = guarded(SpeciesDetailScreen, 'Species', resetData);
const Almanac       = guarded(AlmanacScreen, 'Species Almanac', resetData);
const GrowingAreas  = guarded(GrowingAreasScreen, 'Growing areas', resetData);
const GrowingAreaDetail = guarded(GrowingAreaDetailScreen, 'Growing area', resetData);
const Census        = guarded(CensusScreen, 'Census', resetData);
const Settings      = guarded(SettingsScreen, 'Settings', resetData);

// ── Stack navigators ──────────────────────────────────────────────────────────
const PlantsStack       = createNativeStackNavigator<PlantsStackParamList>();
const SpeciesStack      = createNativeStackNavigator<SpeciesStackParamList>();
const GrowingAreasStack = createNativeStackNavigator<GrowingAreasStackParamList>();
const CensusStack       = createNativeStackNavigator<CensusStackParamList>();
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
      <PlantsStack.Screen name="PlantsList"  component={Plants}      options={{ title: 'My Plants' }} />
      <PlantsStack.Screen name="PlantDetail" component={PlantDetail} options={{ title: 'Plant' }} />
      <PlantsStack.Screen name="AddPlant"    component={AddPlant}    options={{ title: 'Add plant' }} />
      <PlantsStack.Screen name="CaptureGarden" component={CaptureGarden} options={{ title: 'Walk the garden' }} />
    </PlantsStack.Navigator>
  );
}

function SpeciesNavigator() {
  return (
    <SpeciesStack.Navigator screenOptions={useHeaderOpts()}>
      <SpeciesStack.Screen name="SpeciesList"   component={Species}       options={{ title: 'Species catalog' }} />
      <SpeciesStack.Screen name="SpeciesDetail" component={SpeciesDetail} options={{ title: 'Species' }} />
      <SpeciesStack.Screen name="Almanac" component={Almanac} options={{ title: 'Species Almanac' }} />
    </SpeciesStack.Navigator>
  );
}

function CensusNavigator() {
  return (
    <CensusStack.Navigator screenOptions={useHeaderOpts()}>
      <CensusStack.Screen name="CensusSummary" component={Census}  options={{ title: 'Census' }} />
      <CensusStack.Screen name="Almanac"       component={Almanac} options={{ title: 'Species Almanac' }} />
      <CensusStack.Screen name="SpeciesDetail" component={SpeciesDetail} options={{ title: 'Species' }} />
    </CensusStack.Navigator>
  );
}

function GrowingAreasNavigator() {
  return (
    <GrowingAreasStack.Navigator screenOptions={useHeaderOpts()}>
      <GrowingAreasStack.Screen name="GrowingAreasList" component={GrowingAreas} options={{ title: GROWING_AREAS_TAB }} />
      <GrowingAreasStack.Screen
        name="GrowingAreaDetail"
        component={GrowingAreaDetail}
        options={({ route }) => ({ title: route.params.name ?? 'Growing area' })}
      />
      <GrowingAreasStack.Screen name="AddPlant" component={AddPlant} options={{ title: 'Add plant' }} />
      <GrowingAreasStack.Screen name="SpeciesDetail" component={SpeciesDetail} options={{ title: 'Species' }} />
      <GrowingAreasStack.Screen name="Almanac" component={Almanac} options={{ title: 'Species Almanac' }} />
    </GrowingAreasStack.Navigator>
  );
}

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

  // What one account had cached must not show to the next one to sign in on
  // this phone: the query cache and the garden load still in flight both go
  // (api/sessionData.ts). Every way a session ends lands on 'signedOut'.
  useEffect(() => {
    if (status === 'signedOut') dropSessionData(queryClient);
  }, [status]);

  // First-run onboarding: show only if it hasn't been seen AND the account
  // has no plants. Runs only once signed in (the plants call needs a token).
  // Asked through the query cache, so it gets the same one automatic retry
  // as every screen (the first request after a quiet spell meets a server
  // still waking up) and the Plants tab reuses the answer instead of asking
  // again.
  useEffect(() => {
    if (!signedIn) return;
    (async () => {
      if (await getOnboardingSeen()) return;
      try {
        const plants = await queryClient.fetchQuery({ queryKey: ['plants'], queryFn: fetchPlants });
        if (plants.length === 0) setShowOnboarding(true);
        else await setOnboardingSeen(); // returning user — remember, don't show
      } catch {
        // Still unreachable after the retry: decide on the next launch
        // rather than greet a returning gardener as new.
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
                name="GrowingAreas"
                component={GrowingAreasNavigator}
                options={{
                  headerShown: false,
                  // The tab label falls back to the route name, which is
                  // an identifier, not a word anyone should read. First-run
                  // onboarding sends people here by this title.
                  title: GROWING_AREAS_TAB,
                  tabBarIcon: ({ focused }) => <TabIcon emoji="🌍" focused={focused} />,
                }}
              />
              <Tab.Screen
                name="Census"
                component={CensusNavigator}
                options={{
                  headerShown: false,
                  tabBarIcon: ({ focused }) => <TabIcon emoji="📊" focused={focused} />,
                }}
              />
              <Tab.Screen
                name="Settings"
                component={Settings}
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

// Tell React Query when the app comes back to the foreground, so a screen
// whose load failed (no signal on the walk out, a server still waking up)
// asks again on its own instead of staying on its error until it is tapped.
// The TanStack React Native recipe: AppState stands in for window focus.
function useRefetchOnForeground() {
  useEffect(() => {
    if (Platform.OS === 'web') return undefined;
    const sub = AppState.addEventListener('change', (state) => {
      focusManager.setFocused(state === 'active');
    });
    return () => sub.remove();
  }, []);
}

export default function App() {
  useRefetchOnForeground();
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AppThemeProvider>
          {/* The last line of defence: anything the per-screen boundaries
              don't cover (sign-in, the tab bar, onboarding) shows a card
              with Try again instead of closing the app. */}
          <ErrorBoundary where="the app" onReset={resetData}>
            <AuthProvider>
              <AuthGate />
            </AuthProvider>
          </ErrorBoundary>
        </AppThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
