// Minimal jest for pure-logic unit tests (no React Native runtime needed).
// ts-jest compiles TypeScript directly against tsconfig.json, so this does NOT
// add a babel.config.js that would interfere with Expo's Metro bundling.
// Component tests, if ever needed, can layer on jest-expo separately.
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts'],
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.jest.json' }],
  },
};
