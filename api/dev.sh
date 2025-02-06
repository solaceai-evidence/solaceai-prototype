#!/bin/bash
exec python scholarqa/run.py \
  --target "scholarqa.app:create_app" \
    --workers 1 \
    --timeout-keep-alive 0 \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level warning
