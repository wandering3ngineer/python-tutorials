#!/bin/bash

# This shell script contains a curl request for testing the TTS service

# Check if an argument is provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 [model] [text]"
  exit 1
fi

# The text and model to use
TEXT="$2"
MODEL="$1"
OUTPUT="tts.wav"
PORT=8006
IP="0.0.0.0"

# URL-encode the TEXT variable (replace spaces with %20)
TEXT_=$(echo $TEXT | sed 's/ /%20/g')

curl -X POST "http://$IP:$PORT/text/$MODEL/$TEXT_" -o $OUTPUT


