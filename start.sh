#!/bin/bash

./telegram-bot-api/build/telegram-bot-api --api-id=$API_ID --api-hash=$API_HASH --local --http-port=8081 --dir=/tmp/telegram-bot-api-data &

sleep 5

python main.py
