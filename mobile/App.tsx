import React, { useEffect, useState } from 'react';
import { AppState, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, useNavigationContainerRef } from '@react-navigation/native';
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
import HowWeKnowScreen     from './src/screens/HowWeKnowScreen';
import { UnitsProvider } from './src/units/UnitsProvider';
import { HeaderTextButton } from './src/components/HeaderTextButton';
import HomeScreen          from './src/screens/HomeScreen';
import PropertySetupScreen from './src/screens/PropertySetupScreen';
import LandScreen          from './src/screens/LandScreen';
import ZoneMapScreen       from './src/screens/ZoneMapScreen';
import SeasonScreen        from './src/screens/SeasonScreen';
import type { RootStackParamList } from './src/navigation/types';
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
import { refreshAfterCrash } from './src/components/crashRefresh';
import { t } from './src/i18n';

// ── Param lists ───────────────────────────────────────────────────────────────
// One stack, no tabs (build spec section 6). The param list lives in
// src/navigation/types.ts so screens can import it without importing this
// file; the old per-tab names are kept as aliases of it so the screens that
// import them keep compiling.
export type {
  RootStackParamList, AddPlantParams, SpeciesDetailParams, AlmanacParams,
} from './src/navigation/types';
export type PlantsStackParamList = RootStackParamList;
export type SpeciesStackParamList = RootStackParamList;
export type GrowingAreasStackParamList = RootStackParamList;
export type CensusStackParamList = RootStackParamList;

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

// After a crash, fetch fresh what the crashed screen was reading: a
// malformed server answer is the likeliest cause, and redrawing from the same
// cache would only crash again. Every other screen keeps what it is showing
// while that happens (components/crashRefresh.ts).
const resetData = () => refreshAfterCrash(queryClient);

// ── Screens, each behind its own error boundary ───────────────────────────────
// A render error costs one screen: the header's back button and every other
// screen keep working. Wrapped once here, never inside a render, so each
// wrapper keeps its identity.
const Home          = guarded(HomeScreen, 'Home', resetData);
const PropertySetup = guarded(PropertySetupScreen, 'Add your land', resetData);
const Land          = guarded(LandScreen, 'Your land', resetData);
const ZoneMap       = guarded(ZoneMapScreen, 'Zone map', resetData);
const Season        = guarded(SeasonScreen, 'The season', resetData);
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
const HowWeKnow     = guarded(HowWeKnowScreen, 'How we know', resetData);

// ── The one stack ─────────────────────────────────────────────────────────────
const Stack = createNativeStackNavigator<RootStackParamList>();

// Header colors come from the active theme so the nav bar matches Almanac /
// Observatory (hook, so the navigator recomputes on a theme toggle).
function useHeaderOpts() {
  const { palette } = useAppTheme();
  return {
    headerStyle:      { backgroundColor: palette.acc },
    headerTintColor:  palette.btnInk,
    headerTitleStyle: { fontWeight: '700' as const },
  };
}

function RootNavigator() {
  return (
    <Stack.Navigator initialRouteName="Home" screenOptions={useHeaderOpts()}>
      <Stack.Screen name="Home" component={Home} options={({ navigation }) => ({
        title: 'PlantAdvocate',
        // Settings one tap from the first screen, labeled in words.
        headerRight: () => (
          <HeaderTextButton
            label={t('controls.settings')}
            a11yLabel={t('controls.settingsA11y')}
            a11yHint={t('controls.settingsHint')}
            onPress={() => navigation.navigate('Settings')}
          />
        ),
      })} />
      <Stack.Screen name="PropertySetup" component={PropertySetup} options={{ title: t('nav.propertySetup') }} />
      <Stack.Screen name="Land"          component={Land}          options={{ title: t('nav.land') }} />
      <Stack.Screen name="ZoneMap"       component={ZoneMap}       options={{ title: t('nav.zoneMap') }} />
      <Stack.Screen name="Season"        component={Season}        options={{ title: t('nav.season') }} />
      {/* First-run onboarding sends people here by this title. */}
      <Stack.Screen name="Spaces"        component={GrowingAreas}  options={{
        title: GROWING_AREAS_TAB,
      }} />
      <Stack.Screen
        name="SpaceDetail"
        component={GrowingAreaDetail}
        options={({ route }) => ({ title: route.params.name ?? t('nav.growingArea') })}
      />
      <Stack.Screen name="Plants"        component={Plants}        options={{ title: t('nav.plants') }} />
      <Stack.Screen name="PlantDetail"   component={PlantDetail}   options={{ title: t('nav.plant') }} />
      <Stack.Screen name="AddPlant"      component={AddPlant}      options={{ title: t('nav.addPlant') }} />
      <Stack.Screen name="CaptureGarden" component={CaptureGarden} options={{ title: t('nav.captureGarden') }} />
      <Stack.Screen name="Species"       component={Species}       options={{ title: t('nav.species') }} />
      <Stack.Screen name="SpeciesDetail" component={SpeciesDetail} options={{ title: t('nav.speciesDetail') }} />
      <Stack.Screen name="Almanac"       component={Almanac}       options={{ title: t('nav.almanac') }} />
      <Stack.Screen name="Settings"      component={Settings}      options={{ title: t('nav.settings') }} />
      <Stack.Screen name="Census"        component={Census}        options={{ title: t('nav.census') }} />
      <Stack.Screen name="HowWeKnow" component={HowWeKnow} options={({ navigation }) => ({
        title: t('howWeKnow.title'),
        presentation: 'modal',
        headerRight: () => (
          <HeaderTextButton
            label={t('howWeKnow.close')}
            a11yLabel={t('howWeKnow.closeA11y')}
            onPress={() => navigation.goBack()}
          />
        ),
      })} />
    </Stack.Navigator>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
// AuthGate decides between the login screen and the app proper; it must live
// inside AuthProvider, so App wraps it below.
function AuthGate() {
  const { status } = useAuth();
  const { name: themeName } = useAppTheme();
  const navigationRef = useNavigationContainerRef<RootStackParamList>();
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
  // still waking up) and the Plants screen reuses the answer instead of asking
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
      {/* The header is the accent: dark green in Almanac (light text), light
          blue in Observatory (dark text). */}
      <StatusBar style={themeName === 'observatory' ? 'dark' : 'light'} />
      <RootNavigator />
      {showOnboarding && (
        <Onboarding onSkip={dismissOnboarding} />
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
          <UnitsProvider>
          {/* The last line of defence: anything the per-screen boundaries
              don't cover (sign-in, the header, onboarding) shows a card
              with Try again instead of closing the app. */}
          <ErrorBoundary where="the app" onReset={resetData}>
            <AuthProvider>
              <AuthGate />
            </AuthProvider>
          </ErrorBoundary>
          </UnitsProvider>
        </AppThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
