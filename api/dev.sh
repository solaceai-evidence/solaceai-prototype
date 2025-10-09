#!/bin/bash
exec uvicorn \
    --workers 1 \
    --timeout-keep-alive 0 \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --factory \
    'solaceai.app:create_app'
