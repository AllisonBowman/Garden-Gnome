// Minimal jest for pure-logic unit tests (no React Native runtime needed).
// ts-jest compiles TypeScript directly against tsconfig.json, so this does NOT
// add a babel.config.js that would interfere with Expo's Metro bundling.
// Component tests, if ever needed, can layer on jest-expo separately.
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts'],
  // The file crawler only: watchman cannot write its state file in some
  // sandboxes, and these tests never watch.
  watchman: false,
  // One time zone for every run, west of UTC (see the file).
  globalSetup: '<rootDir>/jest.globalSetup.js',
  // expo-localization is a native module; the i18n tests choose the locale.
  moduleNameMapper: {
    '^expo-localization$': '<rootDir>/src/i18n/testing/expoLocalization.ts',
  },
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.jest.json' }],
  },
};
