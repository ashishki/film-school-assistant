#!/usr/bin/env bash
set -euo pipefail

mkdir -p data data/audio
PYTHONPATH=. python3 -c "import asyncio; from src.db import init_db; asyncio.run(init_db('data/assistant.db'))"
echo "Database initialized."
