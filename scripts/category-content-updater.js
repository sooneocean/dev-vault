#!/usr/bin/env node

/**
 * YOLO LAB Category Content Updater
 *
 * Generates unique editorial descriptions for 5 main categories:
 * Film, Music, Tech, Sports, Entertainment
 *
 * Uses Claude API to generate SEO-optimized category descriptions.
 *
 * Usage:
 *   export ANTHROPIC_API_KEY="sk-ant-..."
 *   node scripts/category-content-updater.js --dry-run
 *   node scripts/category-content-updater.js
 */

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const client = new Anthropic();

const CONFIG = {
  outputDir: "./seo-optimization-output",
  model: "claude-haiku-4-5-20251001",
};

const CATEGORIES = [
  {
    slug: "film",
    name: "Film",
    zhName: "電影",
    keywords: "電影評論、院線新片、串流平台推薦、導演分析",
    angle:
      "從導演風格、敘事技巧、視覺美學的深度視角評析電影。涵蓋院線大片、獨立製片、國際電影節精選，以及串流平台原創內容。",
  },
  {
    slug: "music",
    name: "Music",
    zhName: "音樂",
    keywords: "新專輯評論、藝人動態、音樂產業解析、華語/韓語/歐美跨域",
    angle:
      "評論新專輯製作理念、追蹤藝人職業軌跡、解析音樂產業趨勢。涵蓋華語、韓語、歐美等多語言音樂，從流行到獨立樂壇。",
  },
  {
    slug: "tech",
    name: "Tech",
    zhName: "科技",
    keywords: "科技產業趨勢、AI工具評測、消費電子、數位政策",
    angle:
      "探討 AI、雲端、 semiconductors 等前沿技術。評測消費電子產品，追蹤科技企業動態，分析數位政策對產業的影響。",
  },
  {
    slug: "sports",
    name: "Sports",
    zhName: "運動",
    keywords: "職業賽事分析、運動員人物誌、體育產業數據",
    angle:
      "深入分析職業運動賽事、運動員職涯發展與心理素質。融合數據分析與人文關懷，透視體育產業商業與文化意義。",
  },
  {
    slug: "entertainment",
    name: "Entertainment",
    zhName: "娛樂",
    keywords: "影視綜合、明星動態、文化評論、娛樂產業觀察",
    angle:
      "綜合影視綜藝、明星八卦、文化現象的評論。追蹤娛樂產業趨勢，分析文化符號的社會影響與商業價值。",
  },
];

function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
}

async function generateCategoryDescription(category) {
  const prompt = `You are an expert SEO content writer for a Taiwanese media and entertainment blog (YOLO LAB).

Generate a unique, 150-250 word editorial description for the "${category.zhName} (${category.name})" category page.

Requirements:
- Language: Traditional Chinese
- Include 2-3 primary keywords: ${category.keywords}
- Unique angle/perspective: ${category.angle}
- Target audience: Media/entertainment enthusiasts, tech-savvy readers
- Include a call-to-action subtle reference to exploring more content
- Write naturally, not stiff or formulaic
- Avoid repeating descriptions from other categories (Film, Music, Tech, Sports, Entertainment are all different)
- SEO optimized: H2 headers, keyword placement, readability

Output ONLY the description text, no intro/outro/explanation.`;

  try {
    const response = await client.messages.create({
      model: CONFIG.model,
      max_tokens: 300,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
    });

    return response.content[0].type === "text" ? response.content[0].text : "";
  } catch (error) {
    console.error(
      `❌ Error generating description for ${category.zhName}:`,
      error.message
    );
    return null;
  }
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");

  ensureOutputDir();

  console.log("🎬 YOLO LAB Category Content Generator");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log(`Model: ${CONFIG.model}`);
  console.log(`Categories: ${CATEGORIES.length}`);
  console.log("");

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error(
      "❌ ANTHROPIC_API_KEY environment variable not set. Exiting."
    );
    process.exit(1);
  }

  const descriptions = {};

  for (const category of CATEGORIES) {
    console.log(
      `⏳ Generating description for ${category.zhName} (${category.name})...`
    );

    const description = await generateCategoryDescription(category);

    if (description) {
      descriptions[category.slug] = {
        name: category.name,
        zhName: category.zhName,
        description: description.trim(),
        wordCount: description.split(/\s+/).length,
        timestamp: new Date().toISOString(),
      };

      console.log(
        `   ✅ ${description.substring(0, 60).replace(/\n/g, " ")}...`
      );
    } else {
      console.log(`   ❌ Failed to generate description`);
    }

    // Rate limiting: wait 1 second between API calls
    if (CATEGORIES.indexOf(category) < CATEGORIES.length - 1) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }

  console.log("");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

  if (dryRun) {
    console.log("📋 DRY RUN — Preview Only");
    console.log("");
    for (const [slug, data] of Object.entries(descriptions)) {
      console.log(`\n${data.zhName} (${data.name})`);
      console.log(`Word count: ${data.wordCount}`);
      console.log(`${data.description}`);
      console.log("---");
    }
  } else {
    console.log("✅ Generated Descriptions Summary:");
    for (const [slug, data] of Object.entries(descriptions)) {
      console.log(`  • ${data.zhName}: ${data.wordCount} words`);
    }
  }

  // Save to file
  const outputPath = path.join(
    CONFIG.outputDir,
    "category-descriptions.json"
  );
  fs.writeFileSync(outputPath, JSON.stringify(descriptions, null, 2));

  console.log("");
  console.log(`📝 Descriptions saved to: ${outputPath}`);
  console.log("");
  console.log("Next steps:");
  console.log("1. Review category-descriptions.json for quality");
  console.log("2. Update WordPress category description fields via wpcom-mcp");
  console.log("3. Verify descriptions display on category archive pages");
}

main().catch((err) => {
  console.error("❌ Error:", err.message);
  process.exit(1);
});
