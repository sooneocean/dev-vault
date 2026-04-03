#!/bin/bash

echo "=== Phase 4 Step 1: Batch Domain Assignment ==="
echo ""

# Step 1: 查找所有無域的 project 筆記
echo "Scanning projects without domain assignment..."
projects_without_domain=$(grep -L "^domain:" projects/*.md 2>/dev/null | wc -l)
echo "Found $projects_without_domain projects without domain"
echo ""

# Step 2: 按檔案名稱推測域並分配
echo "Assigning domains by semantic analysis..."

# Claude Code 域相關
echo "Assigning claude-code domain..."
for note in claude-code claude-dev sessions session-manager; do
  /c/Users/User/AppData/Roaming/npm/clausidian list --type project 2>/dev/null | \
    grep -i "$note" | awk '{print $2}' | tr -d '[]' | while read file; do
      [ -n "$file" ] && /c/Users/User/AppData/Roaming/npm/clausidian update --note "$file" --domain "claude-code" --quiet 2>/dev/null
    done
done

# AI Engineering 域相關
echo "Assigning ai-engineering domain..."
for note in ai ai-engineering llm language-model prompt engineering research; do
  /c/Users/User/AppData/Roaming/npm/clausidian list --type project 2>/dev/null | \
    grep -i "$note" | awk '{print $2}' | tr -d '[]' | while read file; do
      [ -n "$file" ] && /c/Users/User/AppData/Roaming/npm/clausidian update --note "$file" --domain "ai-engineering" --quiet 2>/dev/null
    done
done

# Knowledge Management 域相關
echo "Assigning knowledge-management domain..."
for note in knowledge vault dev-vault learning memory; do
  /c/Users/User/AppData/Roaming/npm/clausidian list --type project 2>/dev/null | \
    grep -i "$note" | awk '{print $2}' | tr -d '[]' | while read file; do
      [ -n "$file" ] && /c/Users/User/AppData/Roaming/npm/clausidian update --note "$file" --domain "knowledge-management" --quiet 2>/dev/null
    done
done

# Collaboration 域相關
echo "Assigning collaboration domain..."
for note in gospel unit4 recruitment collaboration writing team; do
  /c/Users/User/AppData/Roaming/npm/clausidian list --type project 2>/dev/null | \
    grep -i "$note" | awk '{print $2}' | tr -d '[]' | while read file; do
      [ -n "$file" ] && /c/Users/User/AppData/Roaming/npm/clausidian update --note "$file" --domain "collaboration" --quiet 2>/dev/null
    done
done

# Content/SEO 域相關
echo "Assigning content-seo domain..."
for note in yololab seo optimization design brand content; do
  /c/Users/User/AppData/Roaming/npm/clausidian list --type project 2>/dev/null | \
    grep -i "$note" | awk '{print $2}' | tr -d '[]' | while read file; do
      [ -n "$file" ] && /c/Users/User/AppData/Roaming/npm/clausidian update --note "$file" --domain "content-seo" --quiet 2>/dev/null
    done
done

echo "✅ Domain assignment complete"
echo ""

# Step 3: 查找 active ideas 應升級為 project
echo "Identifying active ideas to promote to projects..."
active_ideas=$(grep -l "^status: active" ideas/*.md 2>/dev/null | wc -l)
echo "Found $active_ideas active ideas (ready for promotion)"
echo ""

# Step 4: 標籤標準化 — 為所有 project 添加 'project' 標籤
echo "Standardizing tags..."
/c/Users/User/AppData/Roaming/npm/clausidian batch_tag --type project --add project --quiet 2>/dev/null

echo "✅ Tag standardization complete"
echo ""

# Step 5: 同步並檢查結果
echo "Syncing vault..."
/c/Users/User/AppData/Roaming/npm/clausidian sync --quiet

echo ""
echo "Health check after domain/type standardization..."
/c/Users/User/AppData/Roaming/npm/clausidian health --json | jq '{overall: .overall, completeness: .scores.completeness, organization: .scores.organization, freshness: .scores.freshness, connectivity: .scores.connectivity}'

echo ""
echo "Organization score details:"
/c/Users/User/AppData/Roaming/npm/clausidian stats --json 2>/dev/null | jq '{total_notes: .total, projects: .byType.project, resources: .byType.resource, ideas: .byType.idea, tags_assigned: .tags}'

