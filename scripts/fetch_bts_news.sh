#!/bin/bash
# Fetch BTS News - Quick Script
# Usage: ./scripts/fetch_bts_news.sh [--telegram]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  BTS News Fetcher${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if test script exists
if [ ! -f "tests/test_bts_news_fetch.py" ]; then
    echo -e "${RED}Error: Test script not found at tests/test_bts_news_fetch.py${NC}"
    exit 1
fi

# Check for Telegram flag
TELEGRAM_FLAG=""
if [[ "$*" == *"--telegram"* ]] || [[ "$*" == *"-t"* ]]; then
    TELEGRAM_FLAG="--telegram"
    echo -e "${YELLOW}Telegram notification enabled${NC}"
fi

# Check for verbose flag
VERBOSE_FLAG=""
if [[ "$*" == *"--verbose"* ]] || [[  "$*" == *"-v"* ]]; then
    VERBOSE_FLAG="--verbose"
    echo -e "${YELLOW}Verbose mode enabled${NC}"
fi

echo -e "${GREEN}Running BTS news fetcher...${NC}"
echo ""

# Run the Python script
python3 tests/test_bts_news_fetch.py $TELEGRAM_FLAG $VERBOSE_FLAG

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ BTS news fetch completed successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ BTS news fetch failed with exit code $EXIT_CODE${NC}"
    exit $EXIT_CODE
fi
