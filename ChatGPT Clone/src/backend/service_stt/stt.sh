#!/bin/bash

# This shell script contains a curl request for testing the STT service

# Check if an argument is provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 [model] [audiofile]"
  exit 1
fi

# The model and audio file to use
AUDIOFILE="$2"
MODEL="$1"
PORT=8005
IP="0.0.0.0"

# URL-encode the TEXT variable (replace spaces with %20)
TEXT_=$(echo $TEXT | sed 's/ /%20/g')

curl -X POST "http://$IP:$PORT/audio/$MODEL" --data-binary @$AUDIOFILE -H "Content-Type: application/octet-stream"