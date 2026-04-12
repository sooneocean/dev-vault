export default {
  testEnvironment: 'node',
  roots: ['<rootDir>/.claude/lib'],
  testMatch: ['**/*.test.js'],
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
};
