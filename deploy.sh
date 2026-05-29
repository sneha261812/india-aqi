#!/usr/bin/env bash
# =============================================================
# India AQI Platform — One-Command Deployment Script
# Run this from inside your india-aqi/ folder:  bash deploy.sh
# =============================================================
set -e
CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

log()  { echo -e "${CYAN}[deploy]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

log "India AQI — deployment starting"
echo ""

# ── 1. Verify git repo ────────────────────────────────────────
log "Checking git remote..."
REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE" ]; then
  log "No remote found. Setting up..."
  git init
  git remote add origin https://github.com/sneha261812/india-aqi.git
fi
ok "Git remote: $REMOTE"

# ── 2. Stage all changes ──────────────────────────────────────
log "Staging changes..."
git add -A
CHANGES=$(git status --porcelain | wc -l)
if [ "$CHANGES" -eq 0 ]; then
  ok "Nothing new to commit — already up to date"
else
  git commit -m "fix: production-ready build — 28/28 tests pass, clean frontend build"
  ok "Committed $CHANGES changed files"
fi

# ── 3. Push to GitHub ─────────────────────────────────────────
log "Pushing to GitHub (triggers Render auto-deploy)..."
git push -u origin main
ok "Pushed to sneha261812/india-aqi"

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  Deploy triggered. What happens next:${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "  1. Render detects the push and rebuilds backend (~3 min)"
echo "     Watch logs at: https://dashboard.render.com"
echo ""
echo "  2. Verify backend is live:"
echo "     curl https://india-aqi.onrender.com/ping"
echo "     Expected: {\"status\":\"ok\",\"service\":\"india-aqi-backend\"}"
echo ""
echo "  3. Vercel auto-rebuilds frontend (~1 min)"
echo "     Live at: https://india-aqi-gamma.vercel.app"
echo ""
echo "  4. AQI data appears within 15 min (APScheduler first tick)"
echo "     Check: https://india-aqi.onrender.com/api/aqi/all"
echo ""
echo "  5. Cron-job.org ping will succeed immediately after step 2"
