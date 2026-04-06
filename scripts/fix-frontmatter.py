#!/usr/bin/env python3
"""
Fix missing frontmatter in vault notes.
Archives obsolete files, fixes valid ones.
"""

import os
import re
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path("C:/DEX_data/Claude Code DEV")
OBSOLETE_PATTERNS = [
    'BATCH_', 'batch-', 'SEO', 'seo-',
    'TEMPLATE', 'template', 'COMPLETION',
    'EXECUTION_STATUS', 'IMPLEMENTATION-ROADMAP',
    'FINAL-CHECKLIST', 'README'
]

def is_obsolete(filename):
    """Check if file matches obsolete patterns."""
    return any(pattern in filename for pattern in OBSOLETE_PATTERNS)

def has_frontmatter(content):
    """Check if content starts with YAML frontmatter."""
    return content.strip().startswith('---')

def extract_title_from_content(content):
    """Extract title from first heading."""
    match = re.search(r'^#+\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"

def create_frontmatter(filename, title, note_type="project"):
    """Create YAML frontmatter."""
    now = datetime.now().strftime("%Y-%m-%d")
    return f"""---
title: {title}
type: {note_type}
tags: [project, active]
created: {now}
updated: {now}
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

"""

def process_file(filepath):
    """Process a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        filename = filepath.name

        # Check if should be archived
        if is_obsolete(filename):
            return ('archive', f'Obsolete: {filename}')

        # Check if already has frontmatter
        if has_frontmatter(content):
            return ('skip', f'Has frontmatter: {filename}')

        # Extract title from content
        title = extract_title_from_content(content)

        # Create new content with frontmatter
        frontmatter = create_frontmatter(filename, title)
        new_content = frontmatter + content

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return ('fixed', f'Fixed: {filename}')

    except Exception as e:
        return ('error', f'Error {filename}: {str(e)}')

def main():
    """Main execution."""
    stats = {'fixed': [], 'archive': [], 'skip': [], 'error': []}

    # Process all .md files recursively
    for filepath in sorted(VAULT_PATH.glob('**/*.md')):
        # Skip index files and archived files
        if '_index' in filepath.name or filepath.parent.name == 'archive':
            continue

        action, message = process_file(filepath)
        stats[action].append(message)
        print(f"[{action.upper()}] {message}")

    # Summary
    print(f"\n" + "="*60)
    print(f"Fixed: {len(stats['fixed'])}")
    print(f"Archive: {len(stats['archive'])}")
    print(f"Skipped: {len(stats['skip'])}")
    print(f"Errors: {len(stats['error'])}")
    print(f"Total: {sum(len(v) for v in stats.values())}")

if __name__ == '__main__':
    main()
