#!/bin/bash

echo "=== Phase 4 Step 2: Smart Summary Enrichment ==="
echo ""

# 策略：為所有 active/growing 的 project 和 resource 添加 summary: true
echo "Adding summary field to active projects..."

# 為所有 status: active 的 projects 添加 summary: true（如果還沒有）
for file in projects/*.md; do
  if [ -f "$file" ]; then
    status=$(grep "^status:" "$file" | head -1 | cut -d' ' -f2)
    has_summary=$(grep "^summary:" "$file")
    
    if [ "$status" = "active" ] && [ -z "$has_summary" ]; then
      # 在 status 行後插入 summary: true
      sed -i "/^status:/a summary: true" "$file"
      echo "  Added summary to $(basename $file)"
    fi
  fi
done

echo ""
echo "Adding summary field to active resources..."
for file in resources/*.md; do
  if [ -f "$file" ]; then
    status=$(grep "^status:" "$file" | head -1 | cut -d' ' -f2)
    has_summary=$(grep "^summary:" "$file")
    
    if [ "$status" = "active" ] && [ -z "$has_summary" ]; then
      sed -i "/^status:/a summary: true" "$file"
      echo "  Added summary to $(basename $file)"
    fi
  fi
done

echo ""
echo "✅ Summary field enrichment complete"
echo ""

# 同步
echo "Syncing vault..."
/c/Users/User/AppData/Roaming/npm/clausidian sync --quiet

echo ""
echo "Updated metrics:"
/c/Users/User/AppData/Roaming/npm/clausidian health --json | jq '{overall: .overall, completeness: .scores.completeness, organization: .scores.organization, incomplete: .incompleteCount}'

