#!/bin/bash
#
# YOLO LAB SEO 自动化 - 快速启动脚本
# 一行命令启动 SEO 批量优化
#

echo "==========================================="
echo "YOLO LAB SEO 自动化 - 快速启动"
echo "==========================================="
echo ""
echo "此脚本将启动 2,600+ 篇文章的 SEO 优化"
echo ""

# 确认凭证已设置
if [ -z "$ANTHROPIC_API_KEY" ] || [ -z "$WP_USERNAME" ] || [ -z "$WP_APP_PASSWORD" ]; then
    echo "⚠️  未检测到凭证"
    echo ""
    echo "请先设置环境变量或创建 .env 文件："
    echo ""
    echo "  选项 1: 环境变量"
    echo "    export ANTHROPIC_API_KEY='your-key'"
    echo "    export WP_USERNAME='username'"
    echo "    export WP_APP_PASSWORD='password'"
    echo ""
    echo "  选项 2: .env 文件"
    echo "    在项目根目录创建 .env 文件包含上述变量"
    echo ""
    exit 1
fi

echo "✓ 凭证已检测"
echo ""

# 选择运行模式
echo "选择运行模式："
echo "  1) 演示模式 (不需要凭证，快速验证)"
echo "  2) 生产模式 (真实处理 2,725 篇文章)"
echo ""
read -p "请选择 (1 或 2): " choice

PROJECT_DIR="/c/DEX_data/Claude Code DEV"
cd "$PROJECT_DIR"

if [ "$choice" = "1" ]; then
    echo ""
    echo "启动演示模式..."
    echo ""
    node scripts/seo-batch-automation-demo.js --fast --total 100
elif [ "$choice" = "2" ]; then
    echo ""
    echo "启动生产模式..."
    echo "处理 2,725 篇文章..."
    echo ""
    node scripts/seo-batch-automation.js
else
    echo "无效选择"
    exit 1
fi
