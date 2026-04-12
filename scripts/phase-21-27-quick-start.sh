#!/bin/bash

# Phase 21-27 SEO 優化快速啟動腳本
# 用途: 一鍵啟動 Phase 21-27 SEO 批量優化

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Phase 21-27 SEO 批量優化 - 快速啟動${NC}"
echo -e "${BLUE}║  yololab.net (Site ID: 133512998)${NC}"
echo -e "${BLUE}║  700 篇文章優化 (Post ID ~33000-31600)${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

# 檢查環境
echo -e "${YELLOW}📋 檢查環境...${NC}\n"

if [ -z "$WPCOM_TOKEN" ]; then
    echo -e "${RED}❌ 缺少 WPCOM_TOKEN 環境變數${NC}"
    echo -e "${YELLOW}解決方案:${NC}"
    echo "  1. 訪問 https://developer.wordpress.com/apps/"
    echo "  2. 建立或複製現有的 API Token"
    echo "  3. 運行: export WPCOM_TOKEN=\"your_token_here\""
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ WPCOM_TOKEN 已設置${NC}"

# 檢查必要檔案
echo -e "\n${YELLOW}📂 檢查必要檔案...${NC}\n"

FILES=(
    "scripts/phase-21-27-batch-seo-optimizer.js"
    "scripts/phase-21-27-continuous-executor.js"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ 找到 $file${NC}"
    else
        echo -e "${RED}❌ 缺少 $file${NC}"
        exit 1
    fi
done

# 檢查 npm 依賴
echo -e "\n${YELLOW}📦 檢查 npm 依賴...${NC}\n"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安裝${NC}"
    exit 1
fi

echo -e "${GREEN}✅ npm 已安裝${NC}"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚙️  安裝依賴...${NC}"
    npm install
fi

# 顯示執行計畫
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  執行計畫${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}7 個 Phase，每個 100 篇文章${NC}"
echo ""
echo "  Phase 21: ID 33000 → 32901 (100 篇)"
echo "  Phase 22: ID 32900 → 32801 (100 篇)"
echo "  Phase 23: ID 32800 → 32701 (100 篇)"
echo "  Phase 24: ID 32700 → 32601 (100 篇)"
echo "  Phase 25: ID 32600 → 32501 (100 篇)"
echo "  Phase 26: ID 32500 → 32401 (100 篇)"
echo "  Phase 27: ID 32400 → 32301 (100 篇)"
echo ""

# 預期耗時
echo -e "${YELLOW}預期耗時:${NC}"
echo "  ⏱️  每 Phase: ~5-8 分鐘"
echo "  ⏱️  全部 7 Phase: ~40-60 分鐘"
echo "  ⏱️  含延遲和監控: ~2-3 小時"
echo ""

# 確認開始
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  準備開始?${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

read -p "確認執行 Phase 21-27 優化? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}已取消執行${NC}"
    exit 0
fi

# 開始執行
echo -e "\n${GREEN}🚀 啟動 Phase 21-27 SEO 優化執行器${NC}\n"
echo "時間戳: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 執行主程序
node scripts/phase-21-27-continuous-executor.js

# 執行完成
echo -e "\n${GREEN}✅ Phase 21-27 SEO 優化完成!${NC}\n"
echo "生成的報告："
echo "  📊 進度文件: phase21-progress.json, phase22-progress.json, ..."
echo "  📋 完整報告: seo-optimization-output/PHASE-21-27-FINAL-REPORT-*.json"
echo ""
echo "下一步:"
echo "  1. 檢查 seo-optimization-output/ 目錄中的報告"
echo "  2. 隨機驗證 10-20 篇文章"
echo "  3. 監控 Google Search Console 中的排名變化"
echo ""
echo "祝賀！"
