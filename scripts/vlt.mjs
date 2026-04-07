#!/usr/bin/env node
/**
 * vlt — clausidian v1.0 wrapper
 *
 * Fills gaps that clausidian v3.5 doesn't cover:
 *   vlt capture "<text>"              → inbox note (not ideas/)
 *   vlt note "<title>" <type>         → supports inbox|permanent|literature types
 *   vlt set "<note>" <field> <value>  → arbitrary frontmatter field update
 *   vlt upgrade "<note>" <class>      → upgrade note_class + move + set zettel_id
 *   vlt inbox [--stale]               → list inbox notes with age
 *
 * Delegates everything else to clausidian.
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync, renameSync } from 'fs';
import { resolve, join, basename, extname } from 'path';
import { execSync, spawnSync } from 'child_process';

// ── Vault root ────────────────────────────────────────────────────────────────

const VAULT = process.env.OA_VAULT || process.cwd();

// ── Helpers ───────────────────────────────────────────────────────────────────

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function nowStamp() {
  const d = new Date();
  return d.getFullYear().toString()
    + String(d.getMonth() + 1).padStart(2, '0')
    + String(d.getDate()).padStart(2, '0')
    + String(d.getHours()).padStart(2, '0')
    + String(d.getMinutes()).padStart(2, '0');
}

function nowFileStamp() {
  const d = new Date();
  return `${todayStr()}-${String(d.getHours()).padStart(2, '0')}${String(d.getMinutes()).padStart(2, '0')}`;
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
    .replace(/(^-|-$)/g, '')
    .slice(0, 60);
}

function vaultPath(...segments) {
  return join(resolve(VAULT), ...segments);
}

// ── Frontmatter helpers ───────────────────────────────────────────────────────

function formatFmValue(val) {
  if (Array.isArray(val)) return `[${val.join(', ')}]`;
  if (typeof val === 'string') return `"${val}"`;
  return String(val);
}

/** Update or insert a frontmatter field. Handles booleans without quotes. */
function setField(content, key, value) {
  const formatted = (typeof value === 'boolean') ? String(value) : formatFmValue(value);
  const re = new RegExp(`^(${key}:)\\s*.*$`, 'm');
  if (content.match(re)) {
    return content.replace(re, `$1 ${formatted}`);
  }
  return content.replace(/^---\n/, `---\n${key}: ${formatted}\n`);
}

function parseFrontmatter(content) {
  const m = content.match(/^---\n([\s\S]*?)\n---/);
  if (!m) return {};
  const fm = {};
  for (const line of m[1].split('\n')) {
    const [k, ...rest] = line.split(':');
    if (k && rest.length) fm[k.trim()] = rest.join(':').trim().replace(/^"|"$/g, '');
  }
  return fm;
}

// ── Note finder ───────────────────────────────────────────────────────────────

function scanAll() {
  const dirs = ['areas', 'projects', 'resources', 'journal', 'ideas', 'inbox'];
  const notes = [];
  for (const dir of dirs) {
    const full = vaultPath(dir);
    if (!existsSync(full)) continue;
    const files = readdirSync(full, { withFileTypes: true });
    for (const f of files) {
      if (f.isFile() && f.name.endsWith('.md') && !f.name.startsWith('_')) {
        const slug = basename(f.name, '.md');
        notes.push({ dir, file: slug, path: join(full, f.name) });
      }
      // Recurse one level (resources/permanent, resources/literature)
      if (f.isDirectory()) {
        const subDir = join(full, f.name);
        try {
          for (const sf of readdirSync(subDir)) {
            if (sf.endsWith('.md') && !sf.startsWith('_')) {
              notes.push({ dir: `${dir}/${f.name}`, file: basename(sf, '.md'), path: join(subDir, sf) });
            }
          }
        } catch { /* skip */ }
      }
    }
  }
  return notes;
}

function findNote(query) {
  const notes = scanAll();
  const q = query.toLowerCase();
  return notes.find(n => n.file === q)
    || notes.find(n => n.file.toLowerCase() === q)
    || notes.filter(n => n.file.toLowerCase().includes(q)).sort((a, b) => a.file.length - b.file.length)[0]
    || null;
}

// ── Commands ──────────────────────────────────────────────────────────────────

/**
 * vlt capture "<text>"
 * Creates an inbox/fleeting note. Routes to inbox/ instead of ideas/.
 */
function cmdCapture(text) {
  if (!text) { console.error('Usage: vlt capture "<text>"'); process.exit(1); }

  const stamp = nowFileStamp();
  const slug = slugify(text.split(/[。.!！?\n]/)[0].trim().slice(0, 60));
  const filename = `${stamp}-${slug}.md`;
  const dir = vaultPath('inbox');
  const filePath = join(dir, filename);

  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  if (existsSync(filePath)) { console.log(`Already exists: inbox/${filename}`); return; }

  const today = todayStr();
  const content = `---
title: "${text.slice(0, 80)}"
type: inbox
note_class: fleeting
tags: []
created: "${today}"
updated: "${today}"
status: active
summary: ""
source: ""
agent_written: false
---

# ${text.slice(0, 80)}

${text}

## Process Next

- [ ] Expand into literature note?
- [ ] Distill into permanent note?
- [ ] Route to project?
- [ ] Discard?
`;

  writeFileSync(filePath, content, 'utf8');
  console.log(`Captured: inbox/${filename}`);
  clausidianSync();
}

/**
 * vlt note "<title>" <type>
 * Supports types clausidian doesn't: inbox, permanent, literature.
 * Delegates to clausidian for: area, project, resource, idea.
 */
function cmdNote(title, type) {
  if (!title || !type) { console.error('Usage: vlt note "<title>" <type>'); process.exit(1); }

  // Delegate built-in types to clausidian
  if (['area', 'project', 'resource', 'idea'].includes(type)) {
    const result = spawnSync(CLAUSIDIAN_BIN, ['note', title, type], { stdio: 'inherit' });
    process.exit(result.status ?? 0);
  }

  const today = todayStr();
  const slug = slugify(title);

  if (type === 'inbox') {
    const stamp = nowFileStamp();
    const filename = `${stamp}-${slug}.md`;
    const dir = vaultPath('inbox');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    const filePath = join(dir, filename);
    if (existsSync(filePath)) { console.log(`Already exists: inbox/${filename}`); return; }

    writeFileSync(filePath, `---
title: "${title}"
type: inbox
note_class: fleeting
tags: []
created: "${today}"
updated: "${today}"
status: active
summary: ""
source: ""
agent_written: false
---

# ${title}

## Process Next

- [ ] Expand into literature note?
- [ ] Distill into permanent note?
- [ ] Route to project?
- [ ] Discard?
`, 'utf8');
    console.log(`Created: inbox/${filename}`);

  } else if (type === 'literature') {
    const dir = vaultPath('resources', 'literature');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    const filename = `lit-${slug}.md`;
    const filePath = join(dir, filename);
    if (existsSync(filePath)) { console.log(`Already exists: resources/literature/${filename}`); return; }

    writeFileSync(filePath, `---
title: "${title}"
type: resource
subtype: research
note_class: literature
tags: []
created: "${today}"
updated: "${today}"
status: active
maturity: growing
domain: ""
summary: ""
source: ""
source_type: ""
related: []
relation_map: ""
distilled_from: []
agent_written: false
agent_reviewed: false
---

# ${title}

## Core Claim

## Key Findings

-

## My Interpretation

## Permanent Notes to Write

- [ ]

## Quotes

>
`, 'utf8');
    console.log(`Created: resources/literature/${filename}`);

  } else if (type === 'permanent') {
    const zettelId = nowStamp();
    const dir = vaultPath('resources', 'permanent');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    const filename = `${zettelId}-${slug}.md`;
    const filePath = join(dir, filename);
    if (existsSync(filePath)) { console.log(`Already exists: resources/permanent/${filename}`); return; }

    writeFileSync(filePath, `---
title: "${title}"
type: resource
subtype: reference
note_class: permanent
zettel_id: "${zettelId}"
atomic: true
tags: []
created: "${today}"
updated: "${today}"
status: active
maturity: mature
domain: ""
summary: ""
related: []
relation_map: ""
distilled_from: []
agent_written: false
agent_reviewed: false
confidence: high
---

# ${title}

<!-- Single atomic idea — one claim, fully self-contained. -->

## The Idea

## Evidence

-

## Implications

-

## Related

-
`, 'utf8');
    console.log(`Created: resources/permanent/${filename}`);
    console.log(`zettel_id: ${zettelId}`);

  } else {
    console.error(`Unknown type: ${type}. Supported: area, project, resource, idea, inbox, literature, permanent`);
    process.exit(1);
  }

  clausidianSync();
}

/**
 * vlt set "<note>" <field> <value>
 * Updates any frontmatter field on an existing note.
 * Supports: booleans (true/false), strings, simple arrays (comma-separated → array).
 */
function cmdSet(noteQuery, field, value) {
  if (!noteQuery || !field || value === undefined) {
    console.error('Usage: vlt set "<note>" <field> <value>');
    console.error('Examples:');
    console.error('  vlt set "my-note" note_class permanent');
    console.error('  vlt set "my-note" agent_written true');
    console.error('  vlt set "my-note" confidence high');
    console.error('  vlt set "my-note" zettel_id 202604061430');
    process.exit(1);
  }

  const note = findNote(noteQuery);
  if (!note) { console.error(`Note not found: ${noteQuery}`); process.exit(1); }

  let content = readFileSync(note.path, 'utf8');

  // Parse value type
  let parsed;
  if (value === 'true') parsed = true;
  else if (value === 'false') parsed = false;
  else if (value.includes(',')) parsed = value.split(',').map(v => v.trim());
  else parsed = value;

  content = setField(content, field, parsed);
  content = setField(content, 'updated', todayStr());
  writeFileSync(note.path, content, 'utf8');
  console.log(`Updated ${note.dir}/${note.file}.md: ${field} = ${JSON.stringify(parsed)}`);
}

/**
 * vlt upgrade "<note>" <target-class>
 * Upgrades a note's note_class and moves it to the canonical directory.
 *
 * Transitions:
 *   fleeting  → literature  (inbox/ → resources/literature/)
 *   literature → permanent  (resources/literature/ → resources/permanent/)
 *   * → permanent           (anywhere → resources/permanent/ + zettel_id)
 */
function cmdUpgrade(noteQuery, targetClass) {
  if (!noteQuery || !targetClass) {
    console.error('Usage: vlt upgrade "<note>" <class>');
    console.error('Classes: literature, permanent');
    process.exit(1);
  }

  const note = findNote(noteQuery);
  if (!note) { console.error(`Note not found: ${noteQuery}`); process.exit(1); }

  let content = readFileSync(note.path, 'utf8');
  const fm = parseFrontmatter(content);
  const today = todayStr();

  if (targetClass === 'literature') {
    const dir = vaultPath('resources', 'literature');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

    const newSlug = note.file.replace(/^\d{4}-\d{2}-\d{2}-\d{4}-/, ''); // strip inbox timestamp
    const newFilename = `lit-${newSlug}.md`;
    const newPath = join(dir, newFilename);

    content = setField(content, 'type', 'resource');
    content = setField(content, 'subtype', 'research');
    content = setField(content, 'note_class', 'literature');
    content = setField(content, 'maturity', 'growing');
    content = setField(content, 'updated', today);

    writeFileSync(newPath, content, 'utf8');
    // Mark old note as processed instead of deleting (safer)
    const markedContent = setField(readFileSync(note.path, 'utf8'), 'status', 'archived');
    writeFileSync(note.path, markedContent, 'utf8');

    console.log(`Upgraded: ${note.dir}/${note.file}.md → resources/literature/${newFilename}`);
    console.log(`Original archived (not deleted). Run \`clausidian delete ${note.file}\` to clean up.`);

  } else if (targetClass === 'permanent') {
    const dir = vaultPath('resources', 'permanent');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

    const zettelId = fm.zettel_id || nowStamp();
    const baseSlug = note.file
      .replace(/^\d{4}-\d{2}-\d{2}-\d{4}-/, '')  // strip inbox timestamp
      .replace(/^lit-/, '');                         // strip lit- prefix
    const newFilename = `${zettelId}-${baseSlug}.md`;
    const newPath = join(dir, newFilename);

    content = setField(content, 'type', 'resource');
    content = setField(content, 'subtype', 'reference');
    content = setField(content, 'note_class', 'permanent');
    content = setField(content, 'zettel_id', zettelId);
    content = setField(content, 'atomic', true);
    content = setField(content, 'maturity', 'mature');
    content = setField(content, 'updated', today);

    // Add distilled_from if not already set
    if (!fm.distilled_from || fm.distilled_from === '[]') {
      content = setField(content, 'distilled_from', [`${note.dir}/${note.file}.md`]);
    }

    writeFileSync(newPath, content, 'utf8');
    const markedContent = setField(readFileSync(note.path, 'utf8'), 'status', 'archived');
    writeFileSync(note.path, markedContent, 'utf8');

    console.log(`Upgraded: ${note.dir}/${note.file}.md → resources/permanent/${newFilename}`);
    console.log(`zettel_id: ${zettelId}`);
    console.log(`Original archived. Run \`clausidian delete ${note.file}\` to clean up.`);

  } else {
    console.error(`Unknown target class: ${targetClass}. Supported: literature, permanent`);
    process.exit(1);
  }

  clausidianSync();
}

/**
 * vlt inbox [--stale]
 * Lists inbox notes with age. --stale shows only notes older than 7 days.
 */
function cmdInbox(staleOnly = false) {
  const dir = vaultPath('inbox');
  if (!existsSync(dir)) { console.log('inbox/ directory not found.'); return; }

  const files = readdirSync(dir).filter(f => f.endsWith('.md') && !f.startsWith('_'));
  if (!files.length) { console.log('Inbox is empty.'); return; }

  const today = new Date();
  const rows = files.map(f => {
    const content = readFileSync(join(dir, f), 'utf8');
    const fm = parseFrontmatter(content);
    const created = fm.created ? new Date(fm.created) : today;
    const age = Math.floor((today - created) / (1000 * 60 * 60 * 24));
    const status = fm.status || 'active';
    return { file: f, age, status, title: fm.title || f, archived: status === 'archived' };
  }).filter(r => {
    if (staleOnly) return !r.archived && r.age >= 7;
    return !r.archived;
  }).sort((a, b) => b.age - a.age);

  if (!rows.length) {
    console.log(staleOnly ? 'No stale inbox notes (all < 7 days old).' : 'No active inbox notes.');
    return;
  }

  console.log(`\nInbox (${rows.length} note${rows.length > 1 ? 's' : ''}):\n`);
  for (const r of rows) {
    const flag = r.age >= 7 ? ' ⚠ STALE' : '';
    console.log(`  [${r.age}d] ${r.file}${flag}`);
  }
  console.log('');
}

// ── Sync helper ───────────────────────────────────────────────────────────────

// Resolve clausidian binary path once, silently
function clausidianBin() {
  try {
    // npm global bin resolution — most reliable cross-platform approach
    const npmBin = execSync('npm bin -g', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
    const candidate = join(npmBin, 'clausidian');
    if (existsSync(candidate)) return candidate;
  } catch { /* fall through */ }
  return 'clausidian'; // rely on PATH
}

const CLAUSIDIAN_BIN = clausidianBin();

function clausidianSync() {
  // execSync with fixed args — no user input, no injection risk
  try {
    const out = execSync(`"${CLAUSIDIAN_BIN}" sync`, { cwd: VAULT, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
    if (out) process.stdout.write(out);
  } catch (e) {
    if (e.stdout) process.stdout.write(e.stdout);
  }
}

// ── Help ──────────────────────────────────────────────────────────────────────

function showHelp() {
  console.log(`
vlt — clausidian v1.0 wrapper

COMMANDS (v1.0 extensions)
  vlt capture "<text>"              Quick inbox capture (fleeting note)
  vlt note "<title>" <type>         Create note; supports: inbox, literature, permanent
                                    (delegates area/project/resource/idea to clausidian)
  vlt set "<note>" <field> <value>  Update any frontmatter field
  vlt upgrade "<note>" <class>      Upgrade note_class and move to canonical dir
  vlt inbox [--stale]               List inbox notes; --stale shows only age >= 7 days

FIELD VALUES (for vlt set)
  note_class    fleeting | literature | permanent | structural | log
  zettel_id     YYYYMMDDHHMM (auto-generated by \`vlt note permanent\`)
  atomic        true | false
  agent_written true | false
  agent_reviewed true | false
  confidence    high | medium | low
  maturity      seed | growing | mature

UPGRADE TRANSITIONS
  fleeting  → literature   (inbox/ → resources/literature/)
  literature → permanent   (resources/literature/ → resources/permanent/ + zettel_id)
  * → permanent            (anywhere → resources/permanent/)

EXAMPLES
  vlt capture "PARA and ZK are orthogonal layers"
  vlt note "My atomic idea" permanent
  vlt note "Notes from Building a Second Brain" literature
  vlt set "my-note" agent_written true
  vlt set "my-note" confidence medium
  vlt upgrade "2026-04-06-1430-my-idea" literature
  vlt upgrade "lit-my-idea" permanent
  vlt inbox --stale

VAULT: ${VAULT}
`);
}

// ── Dispatch ──────────────────────────────────────────────────────────────────

const [,, cmd, ...args] = process.argv;

switch (cmd) {
  case 'capture': cmdCapture(args.join(' ')); break;
  case 'note':    cmdNote(args[0], args[1]); break;
  case 'set':     cmdSet(args[0], args[1], args[2]); break;
  case 'upgrade': cmdUpgrade(args[0], args[1]); break;
  case 'inbox':   cmdInbox(args.includes('--stale')); break;
  case 'help':
  case '--help':
  case '-h':
  case undefined: showHelp(); break;
  default:
    // Unknown command — pass through to clausidian
    const result = spawnSync(CLAUSIDIAN_BIN, [cmd, ...args], { stdio: 'inherit', cwd: VAULT });
    process.exit(result.status ?? 0);
}
