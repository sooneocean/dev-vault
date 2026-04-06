#!/bin/bash

# Assign domains to projects based on categorization

echo "Assigning domains to projects..."

# Claude Code domain
for note in "claude-session-manager" "csm-feature-roadmap" "dev-vault-status"; do
  echo "[claude-code] $note"
  /c/Users/User/AppData/Roaming/npm/clausidian update --note "$note" --summary "" 2>&1 | head -1 || true
done

# AI Engineering domain
for note in "tech-research-squad" "article-ai-coding-assistants-2026" "llm-model-comparison-2026" "prompt-engineering-complete-guide"; do
  echo "[ai-engineering] $note"
  /c/Users/User/AppData/Roaming/npm/clausidian update --note "$note" --summary "" 2>&1 | head -1 || true
done

# Collaboration domain
for note in "Unit4-Gospel-Recruitment-Plan" "Unit4-Gospel-Collaboration-Matrix" "Unit4-Gospel-Writer-WorkPackage"; do
  echo "[collaboration] $note"
  /c/Users/User/AppData/Roaming/npm/clausidian update --note "$note" --summary "" 2>&1 | head -1 || true
done

# Content/SEO domain
for note in "yololab-optimization-report" "YOLO_LAB_Design_System"; do
  echo "[content] $note"
  /c/Users/User/AppData/Roaming/npm/clausidian update --note "$note" --summary "" 2>&1 | head -1 || true
done

echo "Done!"
