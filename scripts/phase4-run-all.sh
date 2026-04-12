#!/bin/bash

# Phase 4 Complete SEO Optimization Runner
# 為 yololab.net 的 2,725 篇文章生成和應用 SEO 優化

set -e

# ─── Configuration ────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/../seo-optimization-output"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ─── Functions ─────────────────────────────────────────────────────────────

log_info() {
  echo -e "${BLUE}ℹ️  ${NC}$1"
}

log_success() {
  echo -e "${GREEN}✓${NC} $1"
}

log_error() {
  echo -e "${RED}❌${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}⚠️ ${NC}$1"
}

print_header() {
  echo ""
  echo "════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════"
  echo ""
}

# ─── Environment Check ────────────────────────────────────────────────────

check_environment() {
  print_header "環境檢查"

  # 檢查 Node.js
  if ! command -v node &> /dev/null; then
    log_error "Node.js 未安裝"
    exit 1
  fi
  log_success "Node.js 已安裝: $(node --version)"

  # 檢查環境變數
  if [ -z "$WPCOM_TOKEN" ]; then
    log_error "缺少 WPCOM_TOKEN 環境變數"
    echo "  請運行: export WPCOM_TOKEN=your_token"
    exit 1
  fi
  log_success "WPCOM_TOKEN 已設置"

  if [ -z "$ANTHROPIC_API_KEY" ]; then
    log_error "缺少 ANTHROPIC_API_KEY 環境變數"
    echo "  請運行: export ANTHROPIC_API_KEY=your_key"
    exit 1
  fi
  log_success "ANTHROPIC_API_KEY 已設置"

  # 檢查輸出目錄
  mkdir -p "$OUTPUT_DIR"
  log_success "輸出目錄已準備: $OUTPUT_DIR"
}

# ─── Demo Mode ────────────────────────────────────────────────────────────

run_demo() {
  print_header "演示模式 (2 篇文章)"

  log_info "測試 Meta 優化..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task meta --demo || true

  log_info "測試 Schema 優化..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task schema --demo || true

  log_info "測試 OG Tags 優化..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task og --demo || true

  log_success "演示模式完成"
}

# ─── Sample Mode ──────────────────────────────────────────────────────────

run_sample() {
  local sample_size="${1:-10}"

  print_header "樣本模式 ($sample_size 篇文章)"

  log_info "生成 $sample_size 篇文章的 Meta 優化..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task meta --sample "$sample_size" || true

  log_info "生成 $sample_size 篇文章的 Schema 優化..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task schema --sample "$sample_size" || true

  log_info "生成 $sample_size 篇文章的 OG Tags 優化..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task og --sample "$sample_size" || true

  log_info "驗證數據質量..."
  node "$SCRIPT_DIR/phase4-seo-quality-validator.js" --task all || true

  log_success "樣本模式完成，請檢查生成的數據質量"
}

# ─── Full Mode (Parallel) ─────────────────────────────────────────────────

run_full_parallel() {
  print_header "完整模式 - 並行執行 (13-15 小時)"

  log_warning "開始並行執行三個任務"
  log_info "任務 1: Meta 優化 (2,725 篇)"
  log_info "任務 2: Schema 優化 (2,725 篇)"
  log_info "任務 3: OG Tags 優化 (2,725 篇)"
  echo ""

  # 並行執行三個任務
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task meta &
  local pid_meta=$!

  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task schema &
  local pid_schema=$!

  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task og &
  local pid_og=$!

  # 等待所有任務完成
  wait $pid_meta
  local status_meta=$?
  wait $pid_schema
  local status_schema=$?
  wait $pid_og
  local status_og=$?

  if [ $status_meta -eq 0 ] && [ $status_schema -eq 0 ] && [ $status_og -eq 0 ]; then
    log_success "所有優化任務完成"
  else
    log_error "某些任務失敗，請檢查日誌"
    return 1
  fi

  # 驗證數據質量
  print_header "質量驗證"
  log_info "驗證所有生成的數據..."
  node "$SCRIPT_DIR/phase4-seo-quality-validator.js" --task all || true

  log_success "完整並行模式完成"
}

# ─── Full Mode (Sequential) ───────────────────────────────────────────────

run_full_sequential() {
  print_header "完整模式 - 序列執行 (24-26 小時)"

  # Task 1: Meta
  print_header "Task 1: Meta 優化"
  log_info "生成 2,725 篇文章的 Meta 數據..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task meta || {
    log_error "Meta 優化失敗"
    return 1
  }
  log_success "Meta 優化完成，驗證中..."
  node "$SCRIPT_DIR/phase4-seo-quality-validator.js" --task meta || true

  # Task 2: Schema
  print_header "Task 2: Schema 優化"
  log_info "生成 2,725 篇文章的 Schema 數據..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task schema || {
    log_error "Schema 優化失敗"
    return 1
  }
  log_success "Schema 優化完成，驗證中..."
  node "$SCRIPT_DIR/phase4-seo-quality-validator.js" --task schema || true

  # Task 3: OG Tags
  print_header "Task 3: OG Tags 優化"
  log_info "生成 2,725 篇文章的 OG Tags..."
  node "$SCRIPT_DIR/phase4-complete-seo-batch-generator.js" --task og || {
    log_error "OG Tags 優化失敗"
    return 1
  }
  log_success "OG Tags 優化完成，驗證中..."
  node "$SCRIPT_DIR/phase4-seo-quality-validator.js" --task og || true

  # 全面驗證
  print_header "全面驗證"
  node "$SCRIPT_DIR/phase4-seo-quality-validator.js" --task all || true

  log_success "完整序列模式完成"
}

# ─── Apply to WordPress ────────────────────────────────────────────────────

apply_to_wordpress() {
  print_header "應用到 WordPress"

  log_warning "準備應用 SEO 數據到 WordPress"
  log_info "Dry-run 模式 (不實際更新)..."
  node "$SCRIPT_DIR/phase4-apply-seo-to-wordpress.js" --dry-run --demo || true

  echo ""
  read -p "確認應用到 WordPress 嗎？(y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "開始應用到 WordPress..."
    node "$SCRIPT_DIR/phase4-apply-seo-to-wordpress.js" || {
      log_error "應用失敗"
      return 1
    }
    log_success "應用完成"
  else
    log_warning "已取消應用"
  fi
}

# ─── Show Results ──────────────────────────────────────────────────────────

show_results() {
  print_header "執行結果"

  if [ -f "$OUTPUT_DIR/PHASE4_QUALITY_VALIDATION_REPORT.json" ]; then
    log_success "質量驗證報告已生成"
    echo "  位置: $OUTPUT_DIR/PHASE4_QUALITY_VALIDATION_REPORT.json"
  fi

  if [ -f "$OUTPUT_DIR/PHASE4_APPLICATION_REPORT.json" ]; then
    log_success "應用報告已生成"
    echo "  位置: $OUTPUT_DIR/PHASE4_APPLICATION_REPORT.json"
  fi

  if [ -f "$OUTPUT_DIR/meta_optimization_results.json" ]; then
    log_success "Meta 優化結果已生成"
    echo "  位置: $OUTPUT_DIR/meta_optimization_results.json"
  fi

  if [ -f "$OUTPUT_DIR/schema_optimization_results.json" ]; then
    log_success "Schema 優化結果已生成"
    echo "  位置: $OUTPUT_DIR/schema_optimization_results.json"
  fi

  if [ -f "$OUTPUT_DIR/og_optimization_results.json" ]; then
    log_success "OG Tags 優化結果已生成"
    echo "  位置: $OUTPUT_DIR/og_optimization_results.json"
  fi

  echo ""
}

# ─── Main Menu ─────────────────────────────────────────────────────────────

show_menu() {
  echo ""
  echo "════════════════════════════════════════"
  echo "  Phase 4 SEO 優化執行菜單"
  echo "════════════════════════════════════════"
  echo ""
  echo "1. 演示模式 (2 篇文章) - 快速測試"
  echo "2. 樣本模式 (10 篇文章) - 質量檢驗"
  echo "3. 完整並行執行 (2,725 篇) - 推薦"
  echo "4. 完整序列執行 (2,725 篇) - 保守"
  echo "5. 應用到 WordPress"
  echo "6. 查看結果"
  echo "0. 退出"
  echo ""
}

main() {
  check_environment

  while true; do
    show_menu
    read -p "請選擇 (0-6): " -n 1 -r choice
    echo

    case $choice in
      1)
        run_demo
        ;;
      2)
        run_sample 10
        ;;
      3)
        run_full_parallel
        ;;
      4)
        run_full_sequential
        ;;
      5)
        apply_to_wordpress
        ;;
      6)
        show_results
        ;;
      0)
        log_info "退出"
        exit 0
        ;;
      *)
        log_error "無效選擇"
        ;;
    esac

    echo ""
  done
}

# 檢查是否有命令行參數
if [ $# -eq 0 ]; then
  main
else
  # 直接執行指定模式
  case "$1" in
    demo)
      check_environment
      run_demo
      ;;
    sample)
      check_environment
      run_sample "${2:-10}"
      ;;
    full-parallel)
      check_environment
      run_full_parallel
      ;;
    full-sequential)
      check_environment
      run_full_sequential
      ;;
    apply)
      check_environment
      apply_to_wordpress
      ;;
    check)
      check_environment
      show_results
      ;;
    *)
      echo "使用方式: $0 [demo|sample|full-parallel|full-sequential|apply|check]"
      exit 1
      ;;
  esac
fi
