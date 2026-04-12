#!/bin/bash
#
# YOLO LAB SEO 批量自动化启动脚本
# 处理 2,600+ 篇文章的 SEO 优化
#
# 使用方式:
#   bash scripts/run-seo-automation.sh [--demo] [--dry-run]
#
# 参数:
#   --demo      运行演示模式（不需要真实凭证）
#   --dry-run   模拟运行，不进行实际更新
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 脚本参数
DEMO_MODE=false
DRY_RUN=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 解析命令行参数
for arg in "$@"; do
  case $arg in
    --demo)
      DEMO_MODE=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "未知参数: $arg"
      exit 1
      ;;
  esac
done

# 打印颜色日志函数
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
  echo -e "${RED}[✗]${NC} $1"
}

log_section() {
  echo ""
  echo -e "${CYAN}${'='*80}${NC}"
  echo -e "${CYAN}  $1${NC}"
  echo -e "${CYAN}${'='*80}${NC}"
  echo ""
}

# 主函数
main() {
  log_section "🚀 YOLO LAB SEO 批量自动化启动"

  # 检查 Node.js
  if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装"
    exit 1
  fi
  log_success "Node.js 已检测: $(node --version)"

  # 检查脚本文件
  if [ "$DEMO_MODE" = true ]; then
    SCRIPT="$SCRIPT_DIR/seo-batch-automation-demo.js"
    log_info "运行模式: 演示 (无需凭证)"
  else
    SCRIPT="$SCRIPT_DIR/seo-batch-automation.js"
    log_info "运行模式: 生产 (需要凭证)"
  fi

  if [ ! -f "$SCRIPT" ]; then
    log_error "脚本未找到: $SCRIPT"
    exit 1
  fi
  log_success "脚本文件已检测"

  # 检查凭证（非演示模式）
  if [ "$DEMO_MODE" = false ]; then
    log_section "🔐 凭证检查"

    # 检查环境变量或 .env 文件
    if [ -z "$WP_USERNAME" ] && [ -z "$WP_APP_PASSWORD" ]; then
      if [ -f "$PROJECT_DIR/.env" ]; then
        log_info "从 .env 文件读取凭证..."
        set -a
        source "$PROJECT_DIR/.env"
        set +a
      else
        log_error "缺少 WordPress.com 凭证"
        log_info "请设置环境变量或创建 .env 文件:"
        log_info "  export WP_USERNAME='username'"
        log_info "  export WP_APP_PASSWORD='password'"
        exit 1
      fi
    fi

    if [ -z "$ANTHROPIC_API_KEY" ]; then
      if [ -f "$PROJECT_DIR/.env" ]; then
        # 已尝试从 .env 读取
        log_error "缺少 ANTHROPIC_API_KEY"
        exit 1
      else
        log_error "缺少 Anthropic API 密钥"
        log_info "请设置环境变量或创建 .env 文件:"
        log_info "  export ANTHROPIC_API_KEY='key'"
        exit 1
      fi
    fi

    # 验证凭证格式
    if [[ ! "$WP_USERNAME" || ! "$WP_APP_PASSWORD" || ! "$ANTHROPIC_API_KEY" ]]; then
      log_error "凭证不完整"
      exit 1
    fi

    log_success "凭证已验证"
    log_info "  WordPress.com 用户: ${WP_USERNAME:0:3}..."
    log_info "  Anthropic API 密钥: ${ANTHROPIC_API_KEY:0:5}..."
  fi

  # 导出环境变量
  export WP_USERNAME
  export WP_APP_PASSWORD
  export ANTHROPIC_API_KEY

  # 日志目录准备
  LOG_DIR="$PROJECT_DIR/seo-batch-logs"
  if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    log_success "创建日志目录: $LOG_DIR"
  fi

  # 启动脚本
  log_section "📊 处理进度"
  log_info "脚本: $SCRIPT"
  log_info "日志: $LOG_DIR"
  log_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  # 运行脚本
  if [ "$DRY_RUN" = true ]; then
    log_warn "DRY-RUN 模式 (不会进行实际更新)"
    node "$SCRIPT" --dry-run
  else
    node "$SCRIPT"
  fi

  EXIT_CODE=$?

  # 完成报告
  echo ""
  log_section "✅ 处理完成"

  if [ $EXIT_CODE -eq 0 ]; then
    log_success "自动化流程已完成"
    log_info "日志位置: $LOG_DIR"
    log_info "进度文件: $LOG_DIR/progress.json"
    log_info "失败列表: $LOG_DIR/failed-posts.json"

    # 显示最终统计
    if [ -f "$LOG_DIR/progress.json" ]; then
      log_info ""
      log_info "最终统计:"
      grep -E '"(processed|successful|failed)"' "$LOG_DIR/progress.json" | head -3
    fi
  else
    log_error "自动化流程失败 (退出码: $EXIT_CODE)"
    exit $EXIT_CODE
  fi
}

# 执行主函数
main "$@"
