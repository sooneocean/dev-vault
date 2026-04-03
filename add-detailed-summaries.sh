#!/bin/bash

echo "=== Auto-Adding Summaries to 30 Core Projects ==="
echo ""

# 30 個核心活躍項目清單
declare -a projects=(
  "claude-session-manager|Claude Session Manager — AI 輔助的多工作階段管理 TUI，支援實時流式輸出、成本追蹤、自動壓縮"
  "csm-feature-roadmap|Claude Session Manager 功能路線圖 — v0.53 到 v2 重構計畫，涵蓋 TUI、測試、外掛系統、跨機器同步"
  "dev-vault-status|Dev Vault 開發知識庫 — PARA 結構的開源知識管理系統，支援持續自迭代"
  "tech-research-squad|AI 工程深度研究隊 — Prompt/Context/Harness/Compound 四大學科研究與知識複利"
  "Unit4-Gospel-Recruitment-Plan|第四單元福音樂寫手招募與協作完整方案 — 招募框架、寫作流程、品質檢查、發佈時程"
  "Unit4-Gospel-Writer-WorkPackage|福音樂文章寫手工作包 — 2800-3200 字、核心人物 Mahalia Jackson & Sister Rosetta Tharpe"
  "Unit4-Gospel-Collaboration-Matrix|第四單元 Gospel 協作矩陣 — 編輯、寫手、審核流程與責任分配"
  "yololab-optimization-report|YOLO LAB 網站優化審計報告 — 23 個外掛、Gzip、快取、SEO、Core Web Vitals 完整優化方案"
  "YOLO_LAB_Design_System|YOLO LAB 2026 設計系統 — 色彩調色板、排版規範、圖標系統、互動模式標準化"
  "claude-code-configuration|Claude Code 完整配置指南 — 外掛、Hook、MCP 伺服器、專案層級設定最佳實踐"
  "compound-engineering-plugin|Compound Engineering 外掛 — 累積式工程工作流，含規劃、審查、知識複利六大指令"
  "context-engineering-research|Context Engineering 深度研究 — 1M context window 實測、compaction 策略、memory 架構"
  "harness-engineering-research|Harness Engineering 深度研究 — 22 個 hook 事件、MCP 生態系、外掛架構評估框架"
  "prompt-engineering-complete-guide|Prompt Engineering 完整指南 — Claude 4.x 提示技巧、XML 結構化、CoT、Few-shot"
)

# 為每個項目添加摘要
count=0
for item in "${projects[@]}"; do
  IFS='|' read -r note summary <<< "$item"
  
  # 檢查檔案是否存在
  if [ -f "projects/$note.md" ]; then
    # 檢查是否已有詳細摘要（不只是 summary: true）
    if ! grep -q "^summary: " "projects/$note.md" || grep -q "^summary: true$" "projects/$note.md"; then
      # 用 summary 值替換 summary: true
      sed -i "s/^summary: true$/summary: \"$summary\"/" "projects/$note.md"
      echo "✅ Added summary to $note"
      ((count++))
    fi
  fi
done

echo ""
echo "✓ Processed $count core projects"
echo ""

# 同步
echo "Syncing vault..."
/c/Users/User/AppData/Roaming/npm/clausidian sync --quiet

echo ""
echo "Health check after summary enrichment..."
/c/Users/User/AppData/Roaming/npm/clausidian health --json | jq '{overall: .overall, completeness: .scores.completeness, organization: .scores.organization, freshness: .scores.freshness, connectivity: .scores.connectivity}'

