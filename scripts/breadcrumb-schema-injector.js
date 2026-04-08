#!/usr/bin/env node

/**
 * YOLO LAB Breadcrumb Schema Injector
 *
 * Injects BreadcrumbList JSON-LD schema into single posts and category archives
 * for improved SERP display and Google understanding of site hierarchy.
 *
 * Paths:
 * - Single posts: Home > [Category] > [Article Title]
 * - Category archives: Home > [Category]
 *
 * Usage:
 *   node scripts/breadcrumb-schema-injector.js --phase generate
 *   node scripts/breadcrumb-schema-injector.js --phase validate --sample 10
 *   node scripts/breadcrumb-schema-injector.js --phase deploy --dry-run
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CONFIG = {
  siteUrl: "https://yololab.net",
  outputDir: "./seo-optimization-output",
};

const BREADCRUMB_TEMPLATES = {
  single_post: {
    type: "single",
    description: "Single post with category breadcrumb",
    path: "Home > Category > Article Title",
    schema_template: {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "{{siteUrl}}"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "{{categoryName}}",
          "item": "{{categoryUrl}}"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": "{{articleTitle}}",
          "item": "{{articleUrl}}"
        }
      ]
    }
  },
  category_archive: {
    type: "archive",
    description: "Category archive page breadcrumb",
    path: "Home > Category",
    schema_template: {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "{{siteUrl}}"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "{{categoryName}}",
          "item": "{{categoryUrl}}"
        }
      ]
    }
  }
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
    phase: "generate",
    sample: null,
    dryRun: false,
  };

  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    const value = args[i + 1];

    if (key === "phase") parsed.phase = value;
    if (key === "sample") parsed.sample = parseInt(value);
    if (key === "dry-run") parsed.dryRun = true;
  }

  return parsed;
}

function generateBreadcrumbSchema(type, variables) {
  const template = BREADCRUMB_TEMPLATES[type];
  if (!template) {
    console.error(`❌ Unknown breadcrumb type: ${type}`);
    return null;
  }

  const schemaJson = JSON.stringify(template.schema_template);
  let result = schemaJson;

  // Replace template variables
  for (const [key, value] of Object.entries(variables)) {
    result = result.replace(new RegExp(`{{${key}}}`, "g"), value);
  }

  return JSON.parse(result);
}

function validateBreadcrumbSchema(schema) {
  // Check required fields
  if (!schema["@context"] || !schema["@type"] || !schema.itemListElement) {
    return {
      valid: false,
      error: "Missing required fields: @context, @type, itemListElement",
    };
  }

  if (schema["@type"] !== "BreadcrumbList") {
    return { valid: false, error: "Invalid @type, must be BreadcrumbList" };
  }

  if (!Array.isArray(schema.itemListElement)) {
    return { valid: false, error: "itemListElement must be an array" };
  }

  // Check each item
  for (let i = 0; i < schema.itemListElement.length; i++) {
    const item = schema.itemListElement[i];
    if (!item["@type"] || !item.position || !item.name || !item.item) {
      return {
        valid: false,
        error: `Item ${i} missing required fields: @type, position, name, item`,
      };
    }
    if (item["@type"] !== "ListItem") {
      return {
        valid: false,
        error: `Item ${i} @type must be ListItem`,
      };
    }
  }

  return { valid: true };
}

function generateSampleSchemas() {
  const samples = {
    single_post_example: {
      path: "Single Post with Category",
      article: {
        id: 24748,
        title: "《小偷家族》是枝裕和",
        url: `${CONFIG.siteUrl}/article-slug-24748/`,
      },
      category: {
        name: "Film",
        slug: "film",
        url: `${CONFIG.siteUrl}/category/film/`,
      },
      schema: null,
    },
    category_archive_example: {
      path: "Category Archive",
      category: {
        name: "Film",
        slug: "film",
        url: `${CONFIG.siteUrl}/category/film/`,
      },
      schema: null,
    },
  };

  // Generate single post schema
  samples.single_post_example.schema = generateBreadcrumbSchema(
    "single_post",
    {
      siteUrl: CONFIG.siteUrl,
      categoryName: samples.single_post_example.category.name,
      categoryUrl: samples.single_post_example.category.url,
      articleTitle: samples.single_post_example.article.title,
      articleUrl: samples.single_post_example.article.url,
    }
  );

  // Generate category archive schema
  samples.category_archive_example.schema = generateBreadcrumbSchema(
    "category_archive",
    {
      siteUrl: CONFIG.siteUrl,
      categoryName: samples.category_archive_example.category.name,
      categoryUrl: samples.category_archive_example.category.url,
    }
  );

  return samples;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();
  ensureOutputDir();

  console.log("🍞 YOLO LAB Breadcrumb Schema Injector");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log(`Site: ${CONFIG.siteUrl}`);
  console.log(`Phase: ${args.phase}`);
  console.log("");

  if (args.phase === "generate") {
    console.log("📋 Generating breadcrumb schema templates...");
    const samples = generateSampleSchemas();

    // Validate schemas
    const singleValidation = validateBreadcrumbSchema(
      samples.single_post_example.schema
    );
    const categoryValidation = validateBreadcrumbSchema(
      samples.category_archive_example.schema
    );

    console.log("");
    console.log("✅ Single Post Breadcrumb:");
    console.log(
      `   Path: ${samples.single_post_example.path}`
    );
    if (singleValidation.valid) {
      console.log("   Validation: PASS ✓");
      console.log(`   Items: ${samples.single_post_example.schema.itemListElement.length}`);
    } else {
      console.log(`   Validation: FAIL ✗ — ${singleValidation.error}`);
    }

    console.log("");
    console.log("✅ Category Archive Breadcrumb:");
    console.log(`   Path: ${samples.category_archive_example.path}`);
    if (categoryValidation.valid) {
      console.log("   Validation: PASS ✓");
      console.log(`   Items: ${samples.category_archive_example.schema.itemListElement.length}`);
    } else {
      console.log(`   Validation: FAIL ✗ — ${categoryValidation.error}`);
    }

    // Save samples
    const outputPath = path.join(
      CONFIG.outputDir,
      "breadcrumb-templates.json"
    );
    fs.writeFileSync(outputPath, JSON.stringify(samples, null, 2));

    console.log("");
    console.log(`📝 Templates saved to: ${outputPath}`);
    console.log("");
    console.log("Deployment options:");
    console.log("1. Yoast SEO breadcrumb block in FSE templates (preferred)");
    console.log("2. Custom HTML block with JSON-LD in page/post footer");
    console.log("3. WordPress theme functions.php wp_head hook injection");
  } else if (args.phase === "validate") {
    console.log("✅ Validation mode: checking breadcrumb schema compliance");
    console.log("(In production: fetch 10 random posts and validate their schemas)");
    console.log("");
    console.log("Sample 10 articles would be validated here.");
    console.log("Expected: ≥90% pass rate for BreadcrumbList schemas");
  } else if (args.phase === "deploy") {
    console.log(
      `📤 Deploy mode: ${args.dryRun ? "DRY RUN (preview)" : "ACTUAL (write)"}`
    );
    console.log("(In production: inject schemas via posts.update API)");
    console.log("");
    console.log("This would inject BreadcrumbList into:");
    console.log("- 50 Tier 1 articles");
    console.log("- 5 category archive pages");
  } else {
    console.error(`❌ Unknown phase: ${args.phase}`);
    process.exit(1);
  }

  console.log("");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("✅ Breadcrumb schema generation complete");
}

main().catch((err) => {
  console.error("❌ Error:", err.message);
  process.exit(1);
});
