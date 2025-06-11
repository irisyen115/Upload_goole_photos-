#!/bin/sh
# 每 7 天執行一次（從 UNIX 時間戳 epoch 起算）
docker exec line-reply python3 /app/webhook_service.py >> /var/log/myscript2.log 2>&1
# docker exec line-reply python3 /app/webhook_service.py >> /var/log/myscript2.log 2>&1
