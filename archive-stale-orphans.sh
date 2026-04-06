#!/bin/bash

echo "=== Phase 3 Step 7: Archive Stale Orphaned Notes ==="

# 歸檔 batch-* 工件
echo "Archiving batch-* artifacts..."
for note in batch-update-page6 BATCH_UPDATE_STRATEGY COMPLETION_REPORT_TEMPLATE EXECUTION_STATUS FINAL-CHECKLIST IMPLEMENTATION-ROADMAP manual-plugin-deactivation README; do
  /c/Users/User/AppData/Roaming/npm/clausidian archive --note "$note" --quiet 2>/dev/null
done

# 歸檔 seo-batch-* 工件
echo "Archiving seo-batch-* artifacts..."
for note in seo-batch-3-4-execution-timeline seo-batch-3-4-keyword-strategy seo-batch-3-4-quick-reference seo-batch3-articles-21-30 seo-batch4-articles-31-40 seo-batches-3-4-summary README-BATCH-3-4; do
  /c/Users/User/AppData/Roaming/npm/clausidian archive --note "$note" --quiet 2>/dev/null
done

# 歸檔 spec/review 舊版本
echo "Archiving spec/review iterations..."
for note in spec-current spec-v0 spec-v1 spec-v2 spec-v3 spec-v4 review-input-r1 review-input-r2 review-r1 review-r2 review-r3 review-r4 review-r5; do
  /c/Users/User/AppData/Roaming/npm/clausidian archive --note "$note" --quiet 2>/dev/null
done

# 歸檔 wave 筆記
echo "Archiving wave/sprint notes..."
for note in wave0_cli_findings s0_brief_spec s1_dev_spec s3_implementation_plan; do
  /c/Users/User/AppData/Roaming/npm/clausidian archive --note "$note" --quiet 2>/dev/null
done

# 注意：duplicate README/CHANGELOG/AGENTS/CLAUDE/CHANGELOG/pitfalls 等未歸檔
# 因為它們可能有不同的含義（不同 repo 的文件），需要手動檢查

echo "✅ Stale orphan archival complete"
echo ""
echo "Syncing vault..."
/c/Users/User/AppData/Roaming/npm/clausidian sync --quiet

echo ""
echo "Health check after cleanup..."
/c/Users/User/AppData/Roaming/npm/clausidian health --json | jq '{overall: .overall, grade: .grade, completeness: .scores.completeness, connectivity: .scores.connectivity, orphans: .orphans}'

