#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  Aibase — One-click startup script
#
#  Usage:
#    ./start.sh            # local only  (http://localhost:5000)
#    ./start.sh --ngrok    # public URL  (share with anyone)
#    ./start.sh --port 8080 --ngrok
# ──────────────────────────────────────────────────────────────
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

echo -e "${CYAN}"
echo "  ⚡  Aibase — starting up…"
echo -e "${NC}"

# ── 1. Install Python dependencies ──────────────────────────
echo -e "${YELLOW}[1/3] Installing Python dependencies…${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}      ✓ Dependencies ready${NC}"

# ── 2. Check that Ollama is running ─────────────────────────
OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
echo -e "${YELLOW}[2/3] Checking Ollama at ${OLLAMA_URL}…${NC}"
if curl -sf "${OLLAMA_URL}/" > /dev/null 2>&1; then
    echo -e "${GREEN}      ✓ Ollama is running${NC}"
else
    echo -e "${RED}      ✗ Cannot reach Ollama at ${OLLAMA_URL}${NC}"
    echo ""
    echo "  Ollama must be running before the server can generate code."
    echo "  Install it from  https://ollama.com  then run:"
    echo ""
    echo "      ollama serve"
    echo "      ollama pull qwen2.5-coder:7b   # (first time only)"
    echo ""
    echo "  Then re-run this script."
    exit 1
fi

# ── 3. Start the API server ──────────────────────────────────
echo -e "${YELLOW}[3/3] Starting Aibase API server…${NC}"
echo ""

# Pass all arguments through to api_server.py (e.g. --ngrok, --port)
exec python api_server.py "$@"
