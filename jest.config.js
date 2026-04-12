export default {
  testEnvironment: 'node',
  roots: ['<rootDir>/.claude/lib'],
  testMatch: [
    '**/proposal-engine*.test.js',
  ],
  testPathIgnorePatterns: [
    'node_modules',
    'projects',
  ],
  collectCoverageFrom: [
    '.claude/lib/**/*.js',
    '!.claude/lib/**/*.test.js',
  ],
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1',
  },
  transform: {},
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
};
