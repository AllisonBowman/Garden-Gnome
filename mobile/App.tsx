import React, { useEffect } from 'react';
import { Text } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Provider as PaperProvider, MD3LightTheme } from 'react-native-paper';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import PlantsScreen        from './src/screens/PlantsScreen';
import PlantDetailScreen   from './src/screens/PlantDetailScreen';
import AddPlantScreen      from './src/screens/AddPlantScreen';
import SpeciesScreen       from './src/screens/SpeciesScreen';
import SpeciesDetailScreen from './src/screens/SpeciesDetailScreen';
import EnvironmentsScreen  from './src/screens/EnvironmentsScreen';
import CensusScreen        from './src/screens/CensusScreen';
import SettingsScreen      from './src/screens/SettingsScreen';
import { rescheduleAllReminders } from './src/notifications/reminders';

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

type RootTabParamList = {
  Plants:       undefined;
  Species:      undefined;
  Environments: undefined;
  Census:       undefined;
  Settings:     undefined;
};

// ── Stack navigators ──────────────────────────────────────────────────────────
const PlantsStack  = createNativeStackNavigator<PlantsStackParamList>();
const SpeciesStack = createNativeStackNavigator<SpeciesStackParamList>();
const Tab          = createBottomTabNavigator<RootTabParamList>();

const HEADER_OPTS = {
  headerStyle:      { backgroundColor: '#2D6A4F' },
  headerTintColor:  '#fff',
  headerTitleStyle: { fontWeight: '700' as const },
};

function PlantsNavigator() {
  return (
    <PlantsStack.Navigator screenOptions={HEADER_OPTS}>
      <PlantsStack.Screen name="PlantsList"  component={PlantsScreen}      options={{ title: 'My Plants' }} />
      <PlantsStack.Screen name="PlantDetail" component={PlantDetailScreen} options={{ title: 'Plant' }} />
      <PlantsStack.Screen name="AddPlant"    component={AddPlantScreen}    options={{ title: 'Add plant' }} />
    </PlantsStack.Navigator>
  );
}

function SpeciesNavigator() {
  return (
    <SpeciesStack.Navigator screenOptions={HEADER_OPTS}>
      <SpeciesStack.Screen name="SpeciesList"   component={SpeciesScreen}       options={{ title: 'Species catalog' }} />
      <SpeciesStack.Screen name="SpeciesDetail" component={SpeciesDetailScreen} options={{ title: 'Species' }} />
    </SpeciesStack.Navigator>
  );
}

// ── Theme ─────────────────────────────────────────────────────────────────────
const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary:    '#2D6A4F',
    secondary:  '#52796F',
    background: '#F6FAF7',
    surface:    '#FFFFFF',
  },
};

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
export default function App() {
  // Refresh the reminder schedule on every launch so it stays accurate even
  // if the app was closed for days (no-op on web / when reminders are off)
  useEffect(() => {
    void rescheduleAllReminders();
  }, []);

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <PaperProvider theme={theme}>
          <NavigationContainer>
            <StatusBar style="light" />
            <Tab.Navigator
              screenOptions={{
                tabBarActiveTintColor: '#2D6A4F',
                tabBarStyle: { paddingBottom: 4 },
                ...HEADER_OPTS,
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
                component={EnvironmentsScreen}
                options={{
                  title: 'Environments',
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
          </NavigationContainer>
        </PaperProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
