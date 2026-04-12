#!/usr/bin/env python3
"""
maturity-promote.py — Automatic note maturity promotion
Transitions: seed → growing → mature based on content criteria

Criteria:
  seed → growing: body > 200 words, ≥1 related link, updated within 14 days
  growing → mature: body > 800 words, ≥3 related links, NOT updated in 30+ days (stable)

Excludes: journal, index notes
"""

import json
import subprocess
import os
import sys
from datetime import datetime, timedelta

VAULT_PATH = os.environ.get('VAULT_PATH', '/c/DEX_data/Claude Code DEV')
CLAUSIDIAN = os.environ.get('CLAUSIDIAN', os.path.expanduser('~/.local/bin/clausidian'))
DRY_RUN = '--fix' not in sys.argv

def get_all_notes():
    """Get all notes as JSON from clausidian"""
    try:
        result = subprocess.run(
            [CLAUSIDIAN, 'list', '--json', '--vault', VAULT_PATH],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"❌ Error fetching notes: {e}", file=sys.stderr)
    return []

def get_note_body_length(file_path):
    """Estimate word count from note file"""
    try:
        full_path = os.path.join(VAULT_PATH, file_path.replace('.md', '') + '.md')
        if not os.path.exists(full_path):
            # Try direct path
            full_path = os.path.join(VAULT_PATH, file_path)

        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Skip frontmatter (between ---)
                parts = content.split('---')
                body = parts[2] if len(parts) > 2 else content
                words = len(body.split())
                return words
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}", file=sys.stderr)
    return 0

def promote_maturity(note_slug, current_maturity, new_maturity):
    """Update note maturity via clausidian"""
    try:
        result = subprocess.run(
            [CLAUSIDIAN, 'update', '--note', note_slug, '--maturity', new_maturity, '--vault', VAULT_PATH],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"  ✅ {note_slug}: {current_maturity} → {new_maturity}")
            return True
        else:
            print(f"  ❌ Failed to promote {note_slug}: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"  ❌ Error promoting {note_slug}: {e}", file=sys.stderr)
    return False

# ==================== Main ====================

print("🌱 Maturity Promotion Check")
print(f"Vault: {VAULT_PATH}")
print(f"Mode: {'DRY_RUN' if DRY_RUN else 'APPLY_FIXES'}")
print()

notes = get_all_notes()
if not notes:
    print("⚠️  No notes found")
    sys.exit(1)

today = datetime.now()
promoted_count = 0
checked_count = 0

for note in notes:
    # Skip journal, index, and archived notes
    note_type = note.get('type', '')
    status = note.get('status', '')
    maturity = note.get('maturity', 'seed')

    if note_type in ['journal', 'index'] or status == 'archived':
        continue

    checked_count += 1
    file_slug = note.get('file', '')
    updated_str = note.get('updated', '2020-01-01')
    related = note.get('related', [])

    try:
        updated = datetime.fromisoformat(updated_str)
    except:
        updated = datetime.fromisoformat('2020-01-01')

    age_days = (today - updated).days
    body_words = get_note_body_length(file_slug)
    related_count = len([r for r in related if r])  # Count non-empty related links

    # Promotion logic
    if maturity == 'seed' and body_words > 200 and related_count >= 1 and age_days <= 14:
        # seed → growing
        print(f"📈 {file_slug}")
        print(f"   Words: {body_words}, Related: {related_count}, Age: {age_days}d")

        if not DRY_RUN:
            if promote_maturity(file_slug, 'seed', 'growing'):
                promoted_count += 1
        else:
            print(f"  [DRY_RUN] Would promote to: growing")
            promoted_count += 1

    elif maturity == 'growing' and body_words > 800 and related_count >= 3 and age_days >= 30:
        # growing → mature
        print(f"🌳 {file_slug}")
        print(f"   Words: {body_words}, Related: {related_count}, Age: {age_days}d (stable)")

        if not DRY_RUN:
            if promote_maturity(file_slug, 'growing', 'mature'):
                promoted_count += 1
        else:
            print(f"  [DRY_RUN] Would promote to: mature")
            promoted_count += 1

print()
print(f"📊 Results:")
print(f"  Checked: {checked_count} notes")
print(f"  Promoted: {promoted_count}")
if DRY_RUN:
    print(f"  Mode: DRY_RUN (use --fix to apply)")

sys.exit(0)
