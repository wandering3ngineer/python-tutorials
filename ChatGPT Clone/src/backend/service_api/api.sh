#!/bin/bash
# This shell script contains a curl request for testing the API service

# Check if an argument is provided
usage() {
  echo "Usage: $0 [type] [model|cmd] [text]"
  echo ""
  echo "Examples:"
  echo "  ./api.sh query gpt-4 \"Who is the fastest runner?\""
  echo "  ./api.sh history clear"
  echo "  ./api.sh history list"
  echo "  ./api.sh tokens"
  echo "  ./api.sh tokens 100" 
  echo "  ./api.sh transcribe google-sr"
  echo "  ./api.sh speech gtts \"This is some text to convert to speech\""
}

# The parameters from command line
TYPE="$1"
MODEL="$2"
TEXT="$3"
PORT=8002
IP="0.0.0.0"
OUTPUT="api_out.wav"
INPUT="api_in.wav"

# Send a query to the given LLM mode
if [ "$TYPE" == "query" ]; then
    echo "Sending query"
    TEXT_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$TEXT'''))")
    curl -X GET "http://$IP:$PORT/query/$MODEL/$TEXT_ENCODED" 
# Clear out or display conversation history in database
elif [ "$TYPE" == "history" ]; then
    echo "Getting/clearing history"
    curl -X GET "http://$IP:$PORT/$TYPE/$MODEL"
# Display or set number of max tokens 
elif [ "$TYPE" == "tokens" ]; then
    echo "Getting/setting tokens"
    curl -X GET "http://$IP:$PORT/$TYPE/max"
    if [ "$MODEL" != "" ]; then
        curl -X GET "http://$IP:$PORT/$TYPE/max/$MODEL"
    fi
    curl -X GET "http://$IP:$PORT/$TYPE/max"
# Transcribe audio from audio file into text
elif [ "$TYPE" == "transcribe" ]; then
    echo "Transcribing audio"
    curl -X GET "http://$IP:$PORT/$TYPE/$MODEL" --data-binary @$INPUT -H "Content-Type: application/octet-stream"
# Convert text into speech
elif [ "$TYPE" == "speech" ]; then
    echo "Synthesizing speech"
    TEXT_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$TEXT'''))")
    curl -X POST "http://$IP:$PORT/$TYPE/$MODEL/$TEXT_ENCODED" -o $OUTPUT
fi

echo ""

