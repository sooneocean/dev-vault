#!/bin/bash

# YOLO LAB SEO Bulk Optimization Executor
# Runs the full batch SEO optimization for all 2,645+ articles

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js v24+"
    exit 1
fi

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY environment variable not set"
    echo "请执行: export ANTHROPIC_API_KEY='your-key-here'"
    exit 1
fi

echo "🚀 YOLO LAB SEO 全量优化执行器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "目标: yololab.net 全部 2,645+ 篇文章"
echo "方案: 分页获取 → 跳过已优化 → 生成元数据 → 更新文章"
echo ""
echo "配置:"
echo "  - API: Anthropic Claude Opus 4.6"
echo "  - 延迟: 1.5 秒/篇 (避免限流)"
echo "  - 重试: 3 次"
echo "  - 报告: 每 10 篇 + 每 100 篇里程碑"
echo ""

# Create reports directory
mkdir -p "$PROJECT_ROOT/seo-optimization-reports"

# Execute the optimizer
echo "⏳ 开始处理... (首页可能需要 5-10 秒加载)"
echo ""

node "$SCRIPT_DIR/yololab-seo-full-batch.js"

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo ""
    echo "✅ 执行完成！"
    echo "📄 报告位置: $PROJECT_ROOT/seo-optimization-reports/"
else
    echo ""
    echo "❌ 执行出错 (错误码: $RESULT)"
    exit $RESULT
fi
