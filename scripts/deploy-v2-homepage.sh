#!/bin/bash
# YOLO LAB v2 首頁自動部署腳本
# 使用方式: ./deploy-v2-homepage.sh

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}YOLO LAB v2 首頁自動部署${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 配置
SITE_ID="133512998"
SITE_URL="https://yololab.net"
HTML_FILE="./seo-optimization-output/homepage-v2-ultramodern.html"
CSS_FILE="./seo-optimization-output/homepage-v2-custom.css"

echo -e "${YELLOW}[1] 檢查部署文件...${NC}"
if [ ! -f "$HTML_FILE" ]; then
  echo -e "${RED}❌ 找不到: $HTML_FILE${NC}"
  exit 1
fi
echo -e "${GREEN}✓ HTML 文件: $HTML_FILE${NC}"

if [ ! -f "$CSS_FILE" ]; then
  echo -e "${YELLOW}⚠ CSS 文件不存在，這是可選的${NC}"
fi
echo ""

echo -e "${YELLOW}[2] 準備部署內容...${NC}"
# 讀取 HTML 內容
HTML_CONTENT=$(cat "$HTML_FILE")
echo -e "${GREEN}✓ 已讀取 $(echo "$HTML_FILE" | wc -c) 字節的 HTML${NC}"

# 讀取 CSS 內容（可選）
if [ -f "$CSS_FILE" ]; then
  CSS_CONTENT=$(cat "$CSS_FILE")
  CSS_SIZE=$(wc -c < "$CSS_FILE")
  echo -e "${GREEN}✓ 已讀取 $CSS_SIZE 字節的 CSS${NC}"
fi
echo ""

echo -e "${YELLOW}[3] 部署指示 - 請在 WordPress 後台手動執行：${NC}"
echo ""
echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "步驟 A：貼入首頁 HTML"
echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "1. 進入: $SITE_URL/wp-admin"
echo "2. 左側菜單 → Pages（頁面）"
echo "3. 找到 Homepage 或 首頁"
echo "4. 點擊編輯"
echo "5. 切換到 Code Editor（代碼編輯器）"
echo "6. 全選現有代碼（Ctrl+A）"
echo "7. 刪除"
echo "8. 貼入以下代碼："
echo ""
echo -e "${GREEN}$HTML_CONTENT${NC}"
echo ""
echo "9. 點擊 Update / Publish（更新/發布）"
echo ""

echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "步驟 B：貼入自訂 CSS（可選但推薦）"
echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "1. 進入: $SITE_URL/wp-admin"
echo "2. 左側菜單 → Appearance（外觀）→ Customize（自訂）"
echo "3. 或直接進: Appearance → Additional CSS"
echo "4. 在文本框中貼入："
echo ""
echo -e "${GREEN}$CSS_CONTENT${NC}"
echo ""
echo "5. 點擊 Publish（發布）"
echo ""

echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "步驟 C：驗證部署"
echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "1. 訪問: $SITE_URL"
echo "2. 檢查以下元素："
echo "   ✓ Hero 區域（深黑 + 綠色光暈）"
echo "   ✓ Stats Bar（898+ / 4 / 2025）"
echo "   ✓ Glassmorphism 卡片（毛玻璃效果）"
echo "   ✓ 4 個分類卡片（紅紫藍綠）"
echo "   ✓ 最新文章雜誌版（左大右小）"
echo "3. 測試響應式："
echo "   - 桌面 (1200px+)"
echo "   - 平板 (768px)"
echo "   - 手機 (320px)"
echo "4. 用 F12 測試 Dark Mode"
echo ""

echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "步驟 D：圖片替換（可選）"
echo -e "${BLUE}─────────────────────────────────────────────${NC}"
echo "HTML 中包含以下圖片 URL（需要替換）："
echo "- hero-bg.jpg (1920×400px)"
echo "- featured-hero.jpg (800×500px)"
echo "- post-2.jpg (800×500px)"
echo "- post-3.jpg (800×500px)"
echo "- post-4.jpg (800×500px)"
echo "- latest-hero.jpg (800×400px)"
echo ""
echo "替換方法："
echo "1. 上傳圖片到 WordPress 媒體庫"
echo "2. 編輯首頁"
echo "3. 找到 <img src=\"...\" 並替換 URL"
echo ""

echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}部署文件已準備完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo "📋 快速清單："
echo "  ☐ 複製 HTML 代碼到首頁編輯器"
echo "  ☐ 複製 CSS 代碼到 Additional CSS"
echo "  ☐ 訪問 $SITE_URL 驗證效果"
echo "  ☐ 測試響應式（F12 DevTools）"
echo "  ☐ 替換圖片 URL"
echo ""
echo "📍 文件位置："
echo "  - HTML: $HTML_FILE"
echo "  - CSS: $CSS_FILE"
echo ""
echo -e "${YELLOW}[!] 部署完成後，請回報結果！${NC}"
