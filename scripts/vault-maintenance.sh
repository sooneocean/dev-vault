#!/bin/bash
# Clausidian Vault 自動化維護腳本
# Usage: ./vault-maintenance.sh [daily|weekly|monthly|all]

set -e

VAULT_PATH="/c/DEX_data/Claude Code DEV"
CLAUSIDIAN="/c/Users/User/AppData/Roaming/npm/clausidian"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="$VAULT_PATH/logs/maintenance-$TIMESTAMP.log"

# 建立日誌目錄
mkdir -p "$VAULT_PATH/logs"

# 日誌函數
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 錯誤處理
error_exit() {
    log "❌ Error: $1"
    exit 1
}

log "🚀 開始 Vault 維護任務"

# ==================== 日常任務 ====================
daily_maintenance() {
    log "📋 執行日常維護..."

    # 建立今日日誌
    log "  • 建立日誌條目..."
    cd "$VAULT_PATH"
    "$CLAUSIDIAN" journal || log "  ⚠️  日誌條目已存在"

    # 同步索引
    log "  • 重建索引..."
    "$CLAUSIDIAN" sync

    # 檢查新笔記
    log "  • 檢查新笔記..."
    NEW_NOTES=$("$CLAUSIDIAN" list --json 2>/dev/null | grep -c '"created":"'$(date +%Y-%m-%d)'"' || echo "0")
    log "  ✅ 今日新笔記: $NEW_NOTES 個"
}

# ==================== 周間任務 ====================
weekly_maintenance() {
    log "📅 執行周間維護..."

    cd "$VAULT_PATH"

    # 自動連結
    log "  • 執行自動連結..."
    "$CLAUSIDIAN" link 2>/dev/null || log "  ⚠️  未發現新連結"

    # 同步
    log "  • 重建索引..."
    "$CLAUSIDIAN" sync

    # 統計孤立笔記
    log "  • 分析孤立笔記..."
    ORPHANS=$("$CLAUSIDIAN" stats 2>/dev/null | grep "Orphan notes:" | awk '{print $NF}' || echo "unknown")
    log "  📊 孤立笔記: $ORPHANS 個"

    # 生成周報
    log "  • 生成周報..."
    "$CLAUSIDIAN" review > "weekly_review_$(date +%Y-W%V).txt" || true
    log "  ✅ 周報已保存"
}

# ==================== 月度任務 ====================
monthly_maintenance() {
    log "📆 執行月度維護..."

    cd "$VAULT_PATH"

    # 完整健康檢查
    log "  • 執行健康檢查..."
    "$CLAUSIDIAN" health > "health_report_$(date +%Y-%m-%d).txt" || true

    # 備份
    log "  • 建立備份..."
    mkdir -p backups
    "$CLAUSIDIAN" export "backups/vault_$(date +%Y-%m-%d).json" || true
    log "  ✅ 備份已建立"

    # 月度回顧
    log "  • 生成月度回顧..."
    "$CLAUSIDIAN" review monthly > "monthly_review_$(date +%Y-%m).txt" || true

    # 更新指標
    log "  • 更新追蹤指標..."
    HEALTH_SCORE=$("$CLAUSIDIAN" health 2>/dev/null | grep "Overall:" | grep -oP '\d+(?=%)' || echo "unknown")
    log "  📊 當前健康評分: $HEALTH_SCORE%"
}

# ==================== 主程式 ====================
TASK="${1:-daily}"

case "$TASK" in
    daily)
        daily_maintenance
        ;;
    weekly)
        daily_maintenance
        weekly_maintenance
        ;;
    monthly)
        daily_maintenance
        weekly_maintenance
        monthly_maintenance
        ;;
    all)
        daily_maintenance
        weekly_maintenance
        monthly_maintenance
        ;;
    *)
        error_exit "未知任務: $TASK. 使用: daily|weekly|monthly|all"
        ;;
esac

log "✅ 維護任務完成"
log "📝 日誌已保存至: $LOG_FILE"
