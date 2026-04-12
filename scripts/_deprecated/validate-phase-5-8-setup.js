#!/usr/bin/env node

/**
 * Phase 5-8 Setup Validation
 * 驗證執行前的環境和配置
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";
import fs from "fs";

const BLOG_ID = 133512998;

async function validateEnvironment() {
  console.log("\n🔍 驗證 Phase 5-8 執行環境\n");
  console.log("=".repeat(60));

  let allGood = true;

  // 1. 檢查 Node.js 版本
  console.log("\n1️⃣  Node.js 版本");
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.split(".")[0].slice(1));
  if (majorVersion >= 24) {
    console.log(`   ✅ ${nodeVersion}`);
  } else {
    console.log(`   ❌ ${nodeVersion} (需要 v24+)`);
    allGood = false;
  }

  // 2. 檢查 Anthropic SDK
  console.log("\n2️⃣  Anthropic SDK");
  try {
    const client = new Anthropic();
    console.log(`   ✅ @anthropic-ai/sdk 已安裝`);

    // 測試 API 連接
    console.log("   ⏳ 測試 API 連接...");
    const testMessage = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 10,
      messages: [
        {
          role: "user",
          content: "Hi",
        },
      ],
    });
    console.log(`   ✅ API 連接成功`);
  } catch (error) {
    console.log(`   ❌ API 連接失敗: ${error.message}`);
    allGood = false;
  }

  // 3. 檢查 WPCOM_TOKEN
  console.log("\n3️⃣  WordPress.com Token");
  const token = process.env.WPCOM_TOKEN;
  if (token) {
    console.log(`   ✅ WPCOM_TOKEN 已設定 (${token.substring(0, 10)}...)`);

    // 測試 API 連接
    console.log("   ⏳ 測試 WordPress.com API...");
    try {
      const response = await fetch(
        `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        const site = await response.json();
        console.log(`   ✅ WordPress.com 連接成功`);
        console.log(`      網站: ${site.name}`);
      } else {
        console.log(`   ❌ Token 無效或權限不足`);
        allGood = false;
      }
    } catch (error) {
      console.log(`   ❌ WordPress.com 連接失敗: ${error.message}`);
      allGood = false;
    }
  } else {
    console.log(`   ❌ WPCOM_TOKEN 未設定`);
    console.log(`      請運行: export WPCOM_TOKEN="your_token"`);
    allGood = false;
  }

  // 4. 檢查測試文章
  console.log("\n4️⃣  測試文章存取");
  if (token) {
    try {
      const response = await fetch(
        `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts/34600?context=edit`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        const post = await response.json();
        console.log(`   ✅ 文章 #34600 存在`);
        console.log(`      標題: ${post.title.rendered.substring(0, 40)}...`);
        console.log(`      有 meta: ${post.meta ? "是" : "否"}`);
      } else {
        console.log(`   ❌ 無法存取文章 #34600`);
        allGood = false;
      }
    } catch (error) {
      console.log(`   ❌ 測試失敗: ${error.message}`);
      allGood = false;
    }
  }

  // 5. 檢查磁碟空間
  console.log("\n5️⃣  磁碟空間");
  const scriptDir = "./scripts";
  if (fs.existsSync(scriptDir)) {
    console.log(`   ✅ 腳本目錄存在: ${scriptDir}`);
  } else {
    console.log(`   ⚠️  腳本目錄不存在: ${scriptDir}`);
  }

  // 6. 檢查現有進度文件
  console.log("\n6️⃣  進度文件");
  const progressFiles = [
    "phase5-progress.json",
    "phase6-progress.json",
    "phase7-progress.json",
    "phase8-progress.json",
  ];
  let existingPhases = [];
  for (const file of progressFiles) {
    if (fs.existsSync(file)) {
      const data = JSON.parse(fs.readFileSync(file, "utf-8"));
      existingPhases.push(
        `${file} (已處理 ${data.success.length} 篇)`
      );
    }
  }
  if (existingPhases.length > 0) {
    console.log(`   ℹ️  找到現有進度:`);
    existingPhases.forEach((p) => console.log(`      - ${p}`));
    console.log(`   ℹ️  重新執行將恢復進度`);
  } else {
    console.log(`   ✅ 無現有進度（新開始）`);
  }

  // 7. 檢查必要的腳本
  console.log("\n7️⃣  腳本檔案");
  const scriptFile = "./scripts/phase-5-8-batch-seo-optimizer.js";
  if (fs.existsSync(scriptFile)) {
    console.log(`   ✅ 主腳本存在: ${scriptFile}`);
  } else {
    console.log(`   ❌ 主腳本不存在: ${scriptFile}`);
    allGood = false;
  }

  // 最終結果
  console.log("\n" + "=".repeat(60));
  if (allGood) {
    console.log("\n✅ 所有環境檢查通過，可以開始執行！\n");
    console.log("運行命令：");
    console.log("  node scripts/phase-5-8-batch-seo-optimizer.js\n");
  } else {
    console.log("\n❌ 環境檢查失敗，請修復上述問題後重試\n");
    process.exit(1);
  }
}

validateEnvironment().catch((err) => {
  console.error("\n❌ 驗證失敗:", err.message);
  process.exit(1);
});
