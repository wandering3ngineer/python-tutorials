curl -X POST "https://api.openai.com/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer *****"  \
     -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello, ChatGPT! How many people in the world?"}]}'