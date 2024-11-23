#!/bin/bash

# This shell script contains a curl request for testing the LLM service

# Check if an argument is provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 [model] [text]"
  exit 1
fi

# The text and model to use
TEXT="$2"
MODEL="$1"
PORT=8003
IP="0.0.0.0"
AUTH_KEY="*******"

# Setup the model
curl -X PUT "http://$IP:$PORT/model/$MODEL"

# Prepare the authorization header if the model is gpt-4
if [ "$MODEL" == "gpt-4" ]; then
     echo "Sending to cloud model"
     curl -X POST "http://$IP:$PORT/relay/v1/chat/completions" \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer $AUTH_KEY" \
          -d "{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"$TEXT\"}]}"
else
     echo "Sending to private model"
     curl -X POST "http://$IP:$PORT/relay/v1/chat/completions" \
          -H "Content-Type: application/json" \
          -d "{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"$TEXT\"}]}"
fi
