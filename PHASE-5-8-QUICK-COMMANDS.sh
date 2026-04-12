#!/bin/bash

# Phase 5-8 SEO 優化 - 快速命令參考
# 2026-04-08

echo "🚀 Phase 5-8 SEO 優化快速命令"
echo "======================================\n"

# 設定 Token（必須先執行）
# export WPCOM_TOKEN="your_token_here"

# ─── 環境驗證 ────────────────────────────────────────

echo "1️⃣  環境驗證"
echo "   node scripts/validate-phase-5-8-setup.js"
echo ""

# ─── 執行優化 ────────────────────────────────────────

echo "2️⃣  執行優化"
echo "   # 完整執行（所有 4 個 Phase，1.5-2 小時）"
echo "   node scripts/phase-5-8-batch-seo-optimizer.js"
echo ""

# ─── 監控進度 ────────────────────────────────────────

echo "3️⃣  監控進度"
echo "   # 即時進度報告"
echo "   node scripts/phase-5-8-report.js"
echo ""
echo "   # 監控特定 Phase 進度（每 5 秒更新）"
echo "   watch -n 5 'jq \".success | length\" phase5-progress.json'"
echo ""

# ─── 驗證結果 ────────────────────────────────────────

echo "4️⃣  驗證結果"
echo "   # 檢查文章 #34600 的 SEO meta"
echo "   curl -s -H \"Authorization: Bearer \$WPCOM_TOKEN\" \\"
echo "     \"https://public-api.wordpress.com/wp/v2/sites/133512998/posts/34600\" \\"
echo "     | jq '.meta | {jetpack_seo_html_title, advanced_seo_description}'"
echo ""
echo "   # 列出 Phase 5 的失敗文章"
echo "   jq '.failed' phase5-progress.json"
echo ""

# ─── 導出報告 ────────────────────────────────────────

echo "5️⃣  導出報告"
echo "   # 生成 JSON 報告"
echo "   node scripts/phase-5-8-report.js --json seo-report.json"
echo ""
echo "   # 生成文本統計"
echo "   jq -r '.[] | \"Phase \\(.phase): \\(.success | length) 成功\"' phase*-progress.json"
echo ""

# ─── 故障恢復 ────────────────────────────────────────

echo "6️⃣  故障恢復"
echo "   # 恢復被中斷的執行（進度已保存）"
echo "   node scripts/phase-5-8-batch-seo-optimizer.js"
echo ""
echo "   # 清除 Phase 5 進度重新開始"
echo "   rm phase5-progress.json"
echo "   node scripts/phase-5-8-batch-seo-optimizer.js"
echo ""

# ─── 日誌記錄 ────────────────────────────────────────

echo "7️⃣  日誌記錄"
echo "   # 記錄到文件"
echo "   node scripts/phase-5-8-batch-seo-optimizer.js 2>&1 | tee seo-execution.log"
echo ""
echo "   # 查看日誌"
echo "   tail -f seo-execution.log"
echo ""

# ─── 進階選項 ────────────────────────────────────────

echo "8️⃣  進階選項"
echo "   # 修改 Batch Size（編輯 phase-5-8-batch-seo-optimizer.js）"
echo "   const BATCH_SIZE = 5;  # 更穩定，但更慢"
echo ""
echo "   # 增加延遲（避免 429 限流）"
echo "   const DELAY_MS = 2500;  # 從 1500 改為 2500"
echo ""
echo "   # 更改模型（速度 vs 質量）"
echo "   model: \"claude-opus-4\",  # 改為 opus-4（較快）"
echo ""

echo "======================================"
echo "✅ 設定完成！"
echo ""
echo "快速開始："
echo "  export WPCOM_TOKEN=\"your_token\""
echo "  node scripts/phase-5-8-batch-seo-optimizer.js"
echo ""
