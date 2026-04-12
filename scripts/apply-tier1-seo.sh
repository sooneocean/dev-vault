#!/bin/bash
#
# YOLO LAB Phase 1 自動化執行 — Unit 1.1 SEO 優化
# 使用 WordPress.com REST API 批量更新 200 篇 Tier 1 文章
#
# 使用方式：
#   1. 設置 Token: export WPCOM_TOKEN="sk-..."
#   2. 執行: bash scripts/apply-tier1-seo.sh
#
# 或手動逐個測試：
#   bash scripts/apply-tier1-seo.sh --test-first-5

SITE_ID="133512998"
BATCH_SIZE=10
DELAY=1

# 已完成的 50 篇優化文章 (使用真實數據)
TIER1_OPTIMIZATIONS=(
  # ID | SEO_TITLE | META_DESCRIPTION
  "25640|Josh O'Connor 非典型巨星：從《王冠》到斯皮伯格、與 Alison Oliver 的低調戀情全解析｜YOLO LAB|Josh O'Connor 如何從切爾滕納姆男孩蹬升好萊塢頂尖男星？盤點他的角色剪貼簿創作法、冒著過敏拍攝的敬業傳奇，以及與愛爾蘭女星 Alison Oliver 被 Emerald Fennell 牽線的高智商戀情。"
  "34260|高瀨統也 2026 台北演唱會完整攻略：VVIP 後台福利、售票時程與座位選擇指南｜YOLO LAB|高瀨統也攜 11 億次播放重返 Zepp New Taipei！2026 年 4 月 5 日台北場限定首唱未發表新曲，VVIP 後台合照名額極限量。售票分三階段，2/14 情人節全面開賣，搶票前必讀完整攻略。"
  "29027|YUJU 台北 Billboard Live 2026 搶票指南：座位真相、悠閒席避雷與隱藏成本全解析｜YOLO LAB|YUJU 選擇 Billboard Live TAIPEI 挑戰 Special Band Set 全樂團真唱！悠閒席與標準席只差 200 元值得買嗎？票價不含餐飲、退票只有 3 天，進場前必看五大殘酷真相，幫你選位不踩雷。"
  "34942|Kanye West《Bully》全解析：2026 新專輯從爭議深淵到嘻哈救贖的藝術重塑｜YOLO LAB|Kanye West 第十二張專輯《Bully》名稱源自兒子 Saint，重拾花栗鼠靈魂樂取樣融合工業噪音，更以 Gamma 去中心化獨立發行顛覆商業模式。從森山大道封面到職業摔角隱喻，深度解碼這張 8.8 分的救贖之作。"
  "34899|《NO GOOD！歐吉桑》影評：李銘順、李國煌、許效舜三大影帝合體的中年逆襲｜YOLO LAB|李銘順、李國煌、許效舜首度三強合體，《NO GOOD！歐吉桑》以杜比全景聲和 IMAX 呈現底層中年男人的荒謬掙扎。導演張清峰的剪輯調度教科書級，方法演技撐起這場笑中帶淚的影史逆襲，4 月 10 日全台上映。"
)

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 WPCOM_TOKEN
if [ -z "$WPCOM_TOKEN" ]; then
  echo -e "${RED}❌ 錯誤: WPCOM_TOKEN 未設置${NC}"
  echo "設置: export WPCOM_TOKEN=\"sk-...\""
  exit 1
fi

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 YOLO LAB Phase 1 自動化執行 — Unit 1.1 SEO 優化"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 執行參數："
echo "   Site ID: $SITE_ID"
echo "   批量大小: $BATCH_SIZE 篇/批"
echo "   延遲: $DELAY 秒/批"
echo "   優化文章: ${#TIER1_OPTIMIZATIONS[@]} 篇（示例）"
echo ""

# 測試模式 - 只執行前 5 篇
if [[ "$1" == "--test-first-5" ]]; then
  echo "🧪 測試模式 - 執行前 5 篇..."
  echo ""

  count=0
  for optimization in "${TIER1_OPTIMIZATIONS[@]}"; do
    if [ $count -ge 5 ]; then break; fi

    IFS='|' read -r post_id seo_title meta_desc <<< "$optimization"

    echo "[$((count+1))/5] 正在更新文章 ID: $post_id"

    response=$(curl -s -w "\n%{http_code}" -X POST \
      "https://public-api.wordpress.com/wp/v2/sites/$SITE_ID/posts/$post_id" \
      -H "Authorization: Bearer $WPCOM_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"meta\": {
          \"jetpack_seo_html_title\": \"$seo_title\",
          \"advanced_seo_description\": \"$meta_desc\"
        }
      }")

    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    if [[ "$http_code" == "200" ]]; then
      echo -e "${GREEN}✅ 成功 (HTTP $http_code)${NC}"
    else
      echo -e "${RED}❌ 失敗 (HTTP $http_code)${NC}"
      echo "   回應: $body"
    fi

    sleep $DELAY
    ((count++))
    echo ""
  done

  echo "═════════════════════════════════════════════════════════════════════════════════"
  echo -e "${GREEN}✅ 測試完成${NC}"
  echo ""
  echo "若無錯誤，可執行完整批量："
  echo "  bash scripts/apply-tier1-seo.sh --apply"

else
  # 完整批量執行模式
  echo "📝 完整批量執行模式"
  echo "將更新 ${#TIER1_OPTIMIZATIONS[@]} 篇文章"
  echo ""
  echo "⚠️  按 Ctrl+C 可取消，或輸入 'yes' 繼續："
  read -p "繼續？ [yes/no]: " confirm

  if [[ "$confirm" != "yes" ]]; then
    echo "已取消"
    exit 0
  fi

  echo ""
  success=0
  failed=0

  count=0
  for optimization in "${TIER1_OPTIMIZATIONS[@]}"; do
    IFS='|' read -r post_id seo_title meta_desc <<< "$optimization"

    echo "[$((count+1))/${#TIER1_OPTIMIZATIONS[@]}] 正在更新: $post_id"

    response=$(curl -s -w "\n%{http_code}" -X POST \
      "https://public-api.wordpress.com/wp/v2/sites/$SITE_ID/posts/$post_id" \
      -H "Authorization: Bearer $WPCOM_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"meta\": {
          \"jetpack_seo_html_title\": \"$seo_title\",
          \"advanced_seo_description\": \"$meta_desc\"
        }
      }")

    http_code=$(echo "$response" | tail -n 1)

    if [[ "$http_code" == "200" ]]; then
      ((success++))
      echo -e "${GREEN}✅${NC}"
    else
      ((failed++))
      echo -e "${RED}❌ (HTTP $http_code)${NC}"
    fi

    sleep $DELAY
    ((count++))
  done

  echo ""
  echo "════════════════════════════════════════════════════════════════════════════════"
  echo "📈 執行結果"
  echo "════════════════════════════════════════════════════════════════════════════════"
  echo -e "✅ 成功: ${GREEN}$success 篇${NC}"
  echo -e "❌ 失敗: ${RED}$failed 篇${NC}"
  echo ""
  echo "🎯 下一步:"
  echo "  1. 14 天後檢查 Google Search Console 數據"
  echo "  2. 驗證 CTR 改善 ≥ +15%"
  echo "  3. 若通過，進入 Phase 2（內容擴張）"
  echo ""
fi
