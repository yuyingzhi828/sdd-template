#!/bin/bash
# pre-commit.sh — Git pre-commit hook
#
# 安装方法：
#   cp governance/pre-commit.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# 功能：
#   在每次 git commit 前自动运行：
#   1. arch-check.py  — 架构分层合规检查
#   2. lock-check.py  — 锁定文件保护检查
#
# 跳过方法（紧急情况）：
#   git commit --no-verify -m "your message"
#   ⚠️  仅在紧急情况下使用，事后需要补充说明

set -e

# 定位脚本目录（无论从哪里运行都能找到 governance/）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Running arch-check..."
python3 "$PROJECT_ROOT/governance/arch-check.py"

echo "🔒 Running lock-check..."
git diff --cached --name-only | python3 "$PROJECT_ROOT/governance/lock-check.py"

echo "✅ All checks passed."
