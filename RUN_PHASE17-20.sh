#!/bin/bash
# Phase 17-20 SEO 批量優化快速啟動腳本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================="
echo "Phase 17-20 SEO 批量優化 - yololab.net"
echo "========================================================================="
echo ""

# 檢查環境
echo "[1/4] 檢查環境..."

if [ -z "$WPCOM_TOKEN" ]; then
  echo "❌ 缺少 WPCOM_TOKEN 環境變數"
  echo ""
  echo "設置方法："
  echo "  export WPCOM_TOKEN='your_wordpress_com_api_token'"
  echo ""
  echo "如何取得 Token："
  echo "  1. 訪問 https://developer.wordpress.com/apps/"
  echo "  2. 創建或選擇應用"
  echo "  3. 複製 API Token"
  echo ""
  exit 1
else
  echo "✓ WPCOM_TOKEN 已設置"
fi

if [ ! -f "scripts/phase17-20-seo-batch-optimizer.js" ]; then
  echo "❌ 腳本文件不存在：scripts/phase17-20-seo-batch-optimizer.js"
  exit 1
else
  echo "✓ 腳本文件存在"
fi

if ! command -v node &> /dev/null; then
  echo "❌ Node.js 未安裝"
  exit 1
else
  echo "✓ Node.js 已安裝：$(node -v)"
fi

echo ""

# 檢查依賴
echo "[2/4] 檢查依賴..."

if ! npm list @anthropic-ai/sdk > /dev/null 2>&1; then
  echo "⚠️  缺少 @anthropic-ai/sdk，嘗試安裝..."
  npm install @anthropic-ai/sdk
else
  echo "✓ @anthropic-ai/sdk 已安裝"
fi

echo ""

# 驗證 API 連接
echo "[3/4] 驗證 WordPress.com API 連接..."

BLOG_ID="133512998"
TOKEN_TEST=$(curl -s -H "Authorization: Bearer $WPCOM_TOKEN" \
  "https://public-api.wordpress.com/wp/v2/sites/$BLOG_ID/posts?page=1&per_page=1" \
  | head -c 100)

if echo "$TOKEN_TEST" | grep -q "id"; then
  echo "✓ WordPress.com API 連接成功"
else
  echo "❌ WordPress.com API 連接失敗"
  echo "   請檢查 WPCOM_TOKEN 是否有效"
  exit 1
fi

echo ""

# 準備目錄
echo "[4/4] 準備目錄..."
mkdir -p phase17-20-progress phase17-20-output
echo "✓ 目錄已創建"

echo ""
echo "========================================================================="
echo "開始執行 Phase 17-20 SEO 優化"
echo "========================================================================="
echo ""

# 執行腳本
node scripts/phase17-20-seo-batch-optimizer.js

echo ""
echo "========================================================================="
echo "Phase 17-20 執行完成"
echo "查看結果："
echo "  - 進度：ls -la phase17-20-progress/"
echo "  - 輸出：ls -la phase17-20-output/"
echo "  - 統計：cat phase17-20-output/phase17-20-summary.json"
echo "========================================================================="
