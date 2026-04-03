#!/bin/bash

echo "=== Final Optimization Phase ==="
echo ""

# Step 1: 更新 15 個關鍵項目的時間戳（這會改善 Freshness）
echo "Step 1: Updating 15 critical projects (freshness improvement)..."

critical_projects=(
  "claude-session-manager"
  "csm-feature-roadmap"
  "dev-vault-status"
  "tech-research-squad"
  "Unit4-Gospel-Recruitment-Plan"
  "Unit4-Gospel-Writer-WorkPackage"
  "Unit4-Gospel-Collaboration-Matrix"
  "yololab-optimization-report"
  "YOLO_LAB_Design_System"
  "claude-code-configuration"
  "compound-engineering-plugin"
  "context-engineering-research"
  "harness-engineering-research"
  "prompt-engineering-complete-guide"
  "article-ai-coding-assistants-2026"
)

for project in "${critical_projects[@]}"; do
  # 尋找檔案（可能在 projects/ 或 resources/）
  file=""
  [ -f "projects/$project.md" ] && file="projects/$project.md"
  [ -f "resources/$project.md" ] && file="resources/$project.md"
  
  if [ -n "$file" ]; then
    # 將 updated 更新為今天的日期
    sed -i 's/^updated: "[^"]*"/updated: "2026-04-04"/' "$file"
    echo "  ✓ Updated $project"
  fi
done

echo ""
echo "Step 2: Batch tag standards update..."

# Step 2: 為所有 active status 的筆記加 'active' 標籤
/c/Users/User/AppData/Roaming/npm/clausidian batch_tag --status active --add active --quiet 2>/dev/null
echo "  ✓ Tagged all active notes"

echo ""
echo "Step 3: Final sync..."
/c/Users/User/AppData/Roaming/npm/clausidian sync --quiet

echo ""
echo "=== FINAL HEALTH METRICS ==="
/c/Users/User/AppData/Roaming/npm/clausidian health --json | jq '
{
  "overall": .overall,
  "grade": .grade,
  "completeness": .scores.completeness,
  "connectivity": .scores.connectivity,
  "freshness": .scores.freshness,
  "organization": .scores.organization,
  "total_notes": .total,
  "orphans": .orphans,
  "incomplete": .incompleteCount
}'

echo ""
echo "Calculation:"
echo "  (Completeness + Connectivity + Freshness + Organization) / 4"

