#!/usr/bin/env bash
# Lance le serveur mAIntenance & Assistance
set -e
pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
uvicorn app.main:app --reload
