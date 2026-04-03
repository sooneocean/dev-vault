#!/bin/bash

echo "=== Phase 3 Step 6: Cross-Domain Strategic Linking ==="

# 建立 claude-code ↔ ai-engineering 連結
echo "Creating claude-code ↔ ai-engineering links..."
/c/Users/User/AppData/Roaming/npm/clausidian update --note "claude-session-manager" --related "[[tech-research-squad]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "tech-research-squad" --related "[[claude-session-manager]]" --quiet

/c/Users/User/AppData/Roaming/npm/clausidian update --note "dev-vault-status" --related "[[prompt-engineering-complete-guide]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "prompt-engineering-complete-guide" --related "[[dev-vault-status]]" --quiet

# 建立 ai-engineering ↔ collaboration 連結
echo "Creating ai-engineering ↔ collaboration links..."
/c/Users/User/AppData/Roaming/npm/clausidian update --note "article-ai-coding-assistants-2026" --related "[[Unit4-Gospel-Recruitment-Plan]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "Unit4-Gospel-Recruitment-Plan" --related "[[article-ai-coding-assistants-2026]]" --quiet

/c/Users/User/AppData/Roaming/npm/clausidian update --note "llm-model-comparison-2026" --related "[[Unit4-Gospel-Collaboration-Matrix]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "Unit4-Gospel-Collaboration-Matrix" --related "[[llm-model-comparison-2026]]" --quiet

# 建立 collaboration ↔ knowledge-management 連結
echo "Creating collaboration ↔ knowledge-management links..."
/c/Users/User/AppData/Roaming/npm/clausidian update --note "Unit4-Gospel-Writer-WorkPackage" --related "[[dev-vault-status]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "dev-vault-status" --related "[[Unit4-Gospel-Writer-WorkPackage]]" --quiet

# 建立 content/seo ↔ knowledge-management 連結
echo "Creating content/seo ↔ knowledge-management links..."
/c/Users/User/AppData/Roaming/npm/clausidian update --note "yololab-optimization-report" --related "[[tech-research-squad]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "tech-research-squad" --related "[[yololab-optimization-report]]" --quiet

/c/Users/User/AppData/Roaming/npm/clausidian update --note "YOLO_LAB_Design_System" --related "[[context-engineering-research]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "context-engineering-research" --related "[[YOLO_LAB_Design_System]]" --quiet

# 建立 knowledge-management internal 連結
echo "Creating knowledge-management internal links..."
/c/Users/User/AppData/Roaming/npm/clausidian update --note "claude-code-configuration" --related "[[compound-engineering-plugin]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "compound-engineering-plugin" --related "[[claude-code-configuration]]" --quiet

/c/Users/User/AppData/Roaming/npm/clausidian update --note "context-engineering-hygiene" --related "[[harness-engineering-research]]" --quiet
/c/Users/User/AppData/Roaming/npm/clausidian update --note "harness-engineering-research" --related "[[context-engineering-hygiene]]" --quiet

echo "✅ Cross-domain linking complete — 10 strategic links created"
echo ""
echo "Syncing vault index..."
/c/Users/User/AppData/Roaming/npm/clausidian sync --quiet
echo "✅ Vault synced"

echo ""
echo "Running health check..."
/c/Users/User/AppData/Roaming/npm/clausidian health --json | jq '{overall: .overall, grade: .grade, connectivity: .scores.connectivity, orphans: .orphans}'

