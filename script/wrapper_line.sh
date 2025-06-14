#!/bin/sh
docker exec line-reply python3 /app/webhook_service.py >> /var/log/myscript2.log 2>&1
