#!/bin/bash
exec python -m scholarqa.run \
  --target "scholarqa.app:create_app" \
    --workers 1 \
    --timeout-keep-alive 0 \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level warning
