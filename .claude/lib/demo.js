#!/usr/bin/env node

/**
 * Demo: Proposal Engine
 * Simple demonstration of how the proposal engine works
 *
 * Usage: node demo.js
 */

const { generateProposals } = require('./proposal-engine');

// Mock GitHub context
const mockGithubContext = {
  lastRelease: `v2.0.0 released 2026-03-15
    - Added dark mode support
    - Improved document loading performance
    - Fixed several critical bugs in real-time sync`,
  
  openIssues: [
    { title: 'Support for LaTeX math rendering', labels: ['feature', 'math'] },
    { title: 'API for third-party integrations', labels: ['feature', 'api'] },
    { title: 'Mobile app native version', labels: ['feature', 'mobile'] },
    { title: 'Advanced search with filters', labels: ['enhancement', 'search'] },
    { title: 'Keyboard shortcuts customization', labels: ['feature', 'ux'] },
  ],
  
  closedPRs: [
    { title: 'feat: Dark mode implementation', labels: ['feature'] },
    { title: 'perf: Optimize document rendering', labels: ['performance'] },
    { title: 'fix: Real-time sync race condition', labels: ['bugfix'] },
    { title: 'docs: Update API documentation', labels: ['docs'] },
  ]
};

// Mock vault context
const mockVaultContext = {
  projectGoals: `Build a collaborative document editing platform that rivals Google Docs but with superior customization and privacy.
                  Target users: teams, students, researchers who need open-source alternatives.`,
  
  learnings: `From user interviews: 
               - 70% of users want offline-first functionality
               - 45% need advanced permission systems
               - 30% need data export to multiple formats
               - Architecture decision: Built on PostgreSQL + Node.js
               - Team velocity: 20 story points per sprint`,
};

async function main() {
  console.log('🚀 Proposal Engine Demo\n');
  console.log('='.repeat(60));
  
  try {
    console.log('\n📊 Input Context:');
    console.log('  Last Release: v2.0.0 with 3 major features');
    console.log('  Open Issues: 5 feature requests');
    console.log('  Closed PRs: 4 merged PRs');
    console.log('  Vault Context: Project goals + user learnings\n');
    
    console.log('🤖 Calling Claude API to generate proposals...\n');
    
    const proposals = await generateProposals(
      mockGithubContext,
      mockVaultContext,
      { debug: false }
    );
    
    console.log('✅ Proposals generated successfully!\n');
    console.log('='.repeat(60));
    console.log('\n📋 Proposed Features for Next Version:\n');
    
    proposals.forEach((proposal, index) => {
      console.log(`${index + 1}. ${proposal.title}`);
      console.log(`   Effort: ${proposal.effort.padEnd(1)} │ Value: ${proposal.value.padEnd(1)} │ Priority: ${proposal.priority}`);
      console.log(`   Problem: ${proposal.problem}`);
      console.log(`   Rationale: ${proposal.rationale}`);
      
      if (proposal.relatedIssues.length > 0) {
        console.log(`   Related Issues: ${proposal.relatedIssues.map(i => '#' + i).join(', ')}`);
      }
      console.log();
    });
    
    console.log('='.repeat(60));
    console.log('\n📊 Summary:');
    console.log(`  Total Proposals: ${proposals.length}`);
    
    const effortCounts = { S: 0, M: 0, L: 0 };
    const valueCounts = { L: 0, M: 0, H: 0 };
    
    proposals.forEach(p => {
      effortCounts[p.effort]++;
      valueCounts[p.value]++;
    });
    
    console.log(`  Effort Distribution: S=${effortCounts.S}, M=${effortCounts.M}, L=${effortCounts.L}`);
    console.log(`  Value Distribution: L=${valueCounts.L}, M=${valueCounts.M}, H=${valueCounts.H}`);
    
    const totalEffort = effortCounts.S * 0.5 + effortCounts.M * 2 + effortCounts.L * 5;
    console.log(`  Estimated Total Effort: ${totalEffort} person-days\n`);
    
  } catch (error) {
    console.error('❌ Error generating proposals:');
    console.error(`   ${error.message}\n`);
    
    if (error.message.includes('ANTHROPIC_API_KEY')) {
      console.log('💡 Tip: Set your API key with:');
      console.log('   export ANTHROPIC_API_KEY=sk-...');
    }
    
    process.exit(1);
  }
}

main();
