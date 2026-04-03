import json
import subprocess
import sys
from collections import defaultdict

# 获取所有笔记（JSON 格式）
try:
    result = subprocess.run(['clausidian', 'list', '--json'], 
                          capture_output=True, text=True, cwd='/c/DEX_data/Claude Code DEV')
    notes = json.loads(result.stdout)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

# 分析孤立笔记
orphan_count = 0
by_type = defaultdict(int)
by_status = defaultdict(int)
by_tag_count = defaultdict(int)  # 按标签数量分组
by_domain = defaultdict(int)

print("=" * 80)
print("孤立笔記聚類分析 (324 個孤立筆記)")
print("=" * 80)

# 识别孤立笔记（无外部链接）
for note in notes.get('notes', []):
    file = note.get('file', '')
    title = note.get('title', '')
    note_type = note.get('type', 'unknown')
    status = note.get('status', 'unknown')
    tags = note.get('tags', [])
    domain = note.get('domain', 'unassigned')
    backlinks_count = note.get('backlinks_count', 0)
    
    # 孤立笔记：0 个反向链接
    if backlinks_count == 0:
        orphan_count += 1
        by_type[note_type] += 1
        by_status[status] += 1
        by_domain[domain] += 1
        by_tag_count[len(tags)] += 1

print(f"\n📊 孤立笔記總數: {orphan_count}")

print(f"\n📁 按類型分佈:")
for ntype, count in sorted(by_type.items(), key=lambda x: -x[1]):
    pct = (count / orphan_count * 100) if orphan_count > 0 else 0
    print(f"  {ntype:15} : {count:4} ({pct:5.1f}%)")

print(f"\n📌 按狀態分佈:")
for s, count in sorted(by_status.items(), key=lambda x: -x[1]):
    pct = (count / orphan_count * 100) if orphan_count > 0 else 0
    print(f"  {s:15} : {count:4} ({pct:5.1f}%)")

print(f"\n🏷️  按領域分佈:")
for d, count in sorted(by_domain.items(), key=lambda x: -x[1])[:10]:
    pct = (count / orphan_count * 100) if orphan_count > 0 else 0
    print(f"  {d:25} : {count:4} ({pct:5.1f}%)")

print(f"\n🔗 按標籤數量分佈:")
for tc, count in sorted(by_tag_count.items()):
    pct = (count / orphan_count * 100) if orphan_count > 0 else 0
    tags_label = "無標籤" if tc == 0 else f"{tc} 個標籤"
    print(f"  {tags_label:20} : {count:4} ({pct:5.1f}%)")

print("\n" + "=" * 80)
print("✅ 聚類分析完成")
