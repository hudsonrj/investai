#!/bin/bash
export PYTHONPATH=/data/inscesteAI:$PYTHONPATH
cd /data/inscesteAI
source venv/bin/activate
exec uvicorn api.main:app --host 0.0.0.0 --port 8091
