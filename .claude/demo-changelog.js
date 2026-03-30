// Demo: Changelog Generator in Action

const { generateChangelog } = require('./lib/changelog-generator');

// Example: Generate a real-world changelog
const examplePRs = [
  {
    number: 101,
    title: 'feat: add dark mode support',
    merged_by: { login: 'alice' },
    html_url: 'https://github.com/owner/repo/pull/101',
  },
  {
    number: 102,
    title: 'feat: export data to CSV',
    merged_by: { login: 'bob' },
    html_url: 'https://github.com/owner/repo/pull/102',
  },
  {
    number: 103,
    title: 'fix: memory leak in data processing',
    merged_by: { login: 'alice' },
    html_url: 'https://github.com/owner/repo/pull/103',
  },
  {
    number: 104,
    title: 'fix: incorrect timezone calculation',
    merged_by: { login: 'charlie' },
    html_url: 'https://github.com/owner/repo/pull/104',
  },
  {
    number: 105,
    title: 'refactor: improve database query performance',
    merged_by: { login: 'bob' },
    html_url: 'https://github.com/owner/repo/pull/105',
  },
  {
    number: 106,
    title: 'docs: update API documentation',
    merged_by: { login: 'alice' },
    html_url: 'https://github.com/owner/repo/pull/106',
  },
  {
    number: 107,
    title: 'feat!: migrate to new authentication API',
    merged_by: { login: 'charlie' },
    html_url: 'https://github.com/owner/repo/pull/107',
  },
];

const changelog = generateChangelog({
  prs: examplePRs,
  version: '2.0.0',
  releaseDate: '2026-03-30',
  repoUrl: 'https://github.com/owner/repo',
});

console.log('\n=== Generated Changelog ===\n');
console.log(changelog);
