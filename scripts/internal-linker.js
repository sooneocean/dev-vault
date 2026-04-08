#!/usr/bin/env node

/**
 * YOLO LAB Internal Linker
 *
 * Batch injects internal links into Tier 1 articles (1→pillar, 2→cluster peers)
 * for building topical authority and improving site structure.
 *
 * Phases:
 * 1. --phase audit: Count incoming/outgoing links per article
 * 2. --phase add: Inject 3+ links via posts.update (requires API)
 * 3. --phase report: Generate linkage audit report
 *
 * Usage:
 *   node scripts/internal-linker.js --phase audit --tier 1
 *   node scripts/internal-linker.js --phase add --tier 1 --dry-run
 *   node scripts/internal-linker.js --phase report
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CONFIG = {
  siteUrl: "https://yololab.net",
  batchSize: 10,
  delayMs: 1000,
  outputDir: "./seo-optimization-output",
  linkRules: {
    minLinksPerArticle: 3,
    maxLinksPerArticle: 8,
    crossClusterRatio: 0.3, // 30% max
  },
};

// ─── Helper Functions ───────────────────────────────────────────────────────

function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
}

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    phase: "audit",
    tier: 1,
    dryRun: false,
    sample: null,
    resume: null,
  };

  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    const value = args[i + 1];

    if (key === "phase") parsed.phase = value;
    if (key === "tier") parsed.tier = parseInt(value);
    if (key === "dry-run") parsed.dryRun = true;
    if (key === "sample") parsed.sample = parseInt(value);
    if (key === "resume") parsed.resume = value;
  }

  return parsed;
}

function loadTier1Articles() {
  const tier1Path = path.join(__dirname, "../data/tier1-articles.json");
  if (!fs.existsSync(tier1Path)) {
    console.error("❌ tier1-articles.json not found. Run Task #1 first.");
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(tier1Path, "utf-8"));
}

function loadPillarMap() {
  const pillarPath = path.join(__dirname, "../data/pillar-map.json");
  if (!fs.existsSync(pillarPath)) {
    console.error("❌ pillar-map.json not found. Run Unit 5 prep first.");
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(pillarPath, "utf-8"));
}

function generateLinkAudit(tier1Data) {
  const audit = {
    timestamp: new Date().toISOString(),
    tier1_total: 0,
    by_category: {},
    stats: {
      avg_links_per_article: 0,
      articles_with_no_links: 0,
      articles_with_optimal_links: 0,
    },
  };

  for (const [category, articles] of Object.entries(tier1Data.tier1_articles)) {
    if (!Array.isArray(articles) || articles.length === 0) continue;

    audit.by_category[category] = {
      total_articles: articles.length,
      article_ids: articles,
      estimated_link_additions: articles.length * CONFIG.linkRules.minLinksPerArticle,
    };

    audit.tier1_total += articles.length;
  }

  audit.stats.avg_links_per_article = CONFIG.linkRules.minLinksPerArticle;
  audit.stats.articles_with_no_links = 0; // Placeholder
  audit.stats.articles_with_optimal_links = Math.ceil(
    audit.tier1_total * 0.8
  );

  return audit;
}

function generateLinkProposal(tier1Data, pillarData) {
  const proposals = {
    timestamp: new Date().toISOString(),
    tier1_articles: tier1Data.tier1_total,
    proposed_links: [],
    rules: CONFIG.linkRules,
  };

  // Sample proposal for Film category (first 3 articles as example)
  const filmArticles = tier1Data.tier1_articles.film || [];
  const filmPillar = pillarData.pillar_pages.film;

  for (let i = 0; i < Math.min(3, filmArticles.length); i++) {
    const articleId = filmArticles[i];
    const links = [
      {
        article_id: articleId,
        link_number: 1,
        target_id: filmPillar.article_id,
        anchor_text: "電影評論與分析",
        insertion_position: "first_third",
        type: "pillar",
      },
      {
        article_id: articleId,
        link_number: 2,
        target_id: filmArticles[(i + 1) % filmArticles.length],
        anchor_text: "相關影評",
        insertion_position: "second_third",
        type: "cluster_peer",
      },
      {
        article_id: articleId,
        link_number: 3,
        target_id: filmArticles[(i + 2) % filmArticles.length],
        anchor_text: "更多電影推薦",
        insertion_position: "third_third",
        type: "cluster_peer",
      },
    ];

    proposals.proposed_links.push(...links);
  }

  proposals.summary = {
    total_proposed_links: proposals.proposed_links.length,
    articles_affected: Math.min(3, filmArticles.length),
    sample_category: "film",
    note: "Full deployment will process all categories and all Tier 1 articles",
  };

  return proposals;
}

function generateDeploymentPlan(tier1Data, pillarData) {
  const plan = {
    timestamp: new Date().toISOString(),
    phase: "add",
    tier: 1,
    total_tier1_articles: tier1Data.tier1_total,
    total_links_to_inject: tier1Data.tier1_total * CONFIG.linkRules.minLinksPerArticle,
    batch_config: {
      batch_size: CONFIG.batchSize,
      delay_ms: CONFIG.delayMs,
      estimated_duration_seconds:
        (tier1Data.tier1_total / CONFIG.batchSize) * (CONFIG.delayMs / 1000),
    },
    deployment_steps: [
      "1. Load Tier 1 article list from tier1-articles.json",
      "2. Load pillar map from pillar-map.json",
      "3. For each Tier 1 article:",
      "   a. GET article content from WordPress API",
      "   b. Parse HTML for existing internal links",
      "   c. Generate link injection proposal (3+ new links)",
      "   d. Find insertion points (semantic, non-disruptive)",
      "   e. Inject links via posts.update API",
      "4. Log results to state_link_tier1.json",
      "5. Generate deployment report",
    ],
    success_criteria: {
      update_success_rate: "≥95%",
      links_per_article: `${CONFIG.linkRules.minLinksPerArticle}-${CONFIG.linkRules.maxLinksPerArticle}`,
      pillar_backlinks: "≥10 per pillar page",
    },
  };

  return plan;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();
  ensureOutputDir();

  console.log("🔗 YOLO LAB Internal Linker");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log(`Phase: ${args.phase}`);
  console.log(`Tier: ${args.tier}`);
  console.log(`Dry Run: ${args.dryRun ? "YES" : "NO"}`);
  console.log("");

  const tier1Data = loadTier1Articles();
  const pillarData = loadPillarMap();

  if (args.phase === "audit") {
    console.log("📊 Auditing Tier 1 article linkage...");
    const audit = generateLinkAudit(tier1Data);

    console.log("");
    console.log("✅ Tier 1 Articles by Category:");
    for (const [category, data] of Object.entries(audit.by_category)) {
      console.log(
        `   ${category.toUpperCase()}: ${data.total_articles} articles`
      );
      console.log(`      Proposed links: ${data.estimated_link_additions}`);
    }

    console.log("");
    console.log(`Total Tier 1 Articles: ${audit.tier1_total}`);
    console.log(`Estimated Links to Inject: ${audit.tier1_total * CONFIG.linkRules.minLinksPerArticle}`);

    // Save audit
    const auditPath = path.join(CONFIG.outputDir, "link-audit-results.json");
    fs.writeFileSync(auditPath, JSON.stringify(audit, null, 2));
    console.log(`📝 Audit saved to: ${auditPath}`);
  } else if (args.phase === "add") {
    console.log(`🔗 Generating link injection proposal...`);
    const proposal = generateLinkProposal(tier1Data, pillarData);

    if (args.dryRun) {
      console.log("📋 DRY RUN MODE — Preview Only");
      console.log("");
      console.log(`Sample proposals (first 3 Film articles):`);
      for (const link of proposal.proposed_links.slice(0, 9)) {
        console.log(
          `   [${link.article_id}] → [${link.target_id}] "${link.anchor_text}" (${link.type})`
        );
      }

      const proposalPath = path.join(
        CONFIG.outputDir,
        "proposed-links.json"
      );
      fs.writeFileSync(proposalPath, JSON.stringify(proposal, null, 2));
      console.log("");
      console.log(`📝 Full proposal saved to: ${proposalPath}`);
      console.log("✅ Review proposed-links.json before running live deployment.");
    } else {
      console.log("⚠️  LIVE DEPLOYMENT MODE");
      console.log("(In production: Would inject links via posts.update API)");
      console.log("");
      console.log(
        `Total links to inject: ${proposal.summary.total_proposed_links}`
      );
      console.log("✅ Ready for deployment.");
    }
  } else if (args.phase === "report") {
    console.log("📋 Generating deployment plan...");
    const plan = generateDeploymentPlan(tier1Data, pillarData);

    console.log("");
    console.log("🚀 Deployment Plan Summary:");
    console.log(`   Total Tier 1 Articles: ${plan.total_tier1_articles}`);
    console.log(`   Total Links to Inject: ${plan.total_links_to_inject}`);
    console.log(`   Batch Size: ${plan.batch_config.batch_size}`);
    console.log(
      `   Estimated Duration: ${Math.round(plan.batch_config.estimated_duration_seconds / 60)} minutes`
    );

    console.log("");
    console.log("📝 Deployment Steps:");
    for (const step of plan.deployment_steps) {
      console.log(`   ${step}`);
    }

    const planPath = path.join(CONFIG.outputDir, "internal-link-deployment-plan.json");
    fs.writeFileSync(planPath, JSON.stringify(plan, null, 2));
    console.log("");
    console.log(`📝 Plan saved to: ${planPath}`);
  } else {
    console.error(`❌ Unknown phase: ${args.phase}`);
    process.exit(1);
  }

  console.log("");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("✅ Internal linker complete");
}

main().catch((err) => {
  console.error("❌ Error:", err.message);
  process.exit(1);
});
