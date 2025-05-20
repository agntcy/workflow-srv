#!/bin/bash

# Base URL for the API
BASE_URL="http://localhost:8000"  # Replace with the actual base URL

# Payload for the first POST request
PAYLOAD=$(cat <<EOF
{
  "agent_id": "4125fdcc-1a27-4aac-b566-b379ca31afbf",
  "input": {
    "messages": [
      {
        "type": "human",
        "content": "hello"
      }
    ]
  },
  "metadata": {},
  "config": {
    "configurable": {
      "to_upper": true
    }
  }
}
EOF
)

# Make the first POST request to /runs/ and extract the ID
RESPONSE=$(curl -s -X POST "$BASE_URL/runs" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo "$RESPONSE"

# Extract the ID from the response
ID=$(echo "$RESPONSE" | jq -r '.run_id')

# Check if the ID was successfully extracted
if [ -z "$ID" ] || [ "$ID" == "null" ]; then
  echo "Failed to extract ID from the response. Response was:"
  echo "$RESPONSE"
  exit 1
fi

echo "Extracted ID: $ID"

# Make the second POST request to /runs/{id}/wait
WAIT_RESPONSE=$(curl -s -X GET "$BASE_URL/runs/$ID/wait" \
  -H "Content-Type: application/json")

# Output the response from the second call
echo "Response from /runs/$ID/wait:"
echo "$WAIT_RESPONSE"


# agent-workflow-server-py3.12MTRINELL-M-P41H:workflow-srv mtrinell$ ./test.sh 
# {"run_id":"5976c7c4-7047-4085-ad76-d095416e0149","thread_id":"a564028a-f532-4706-87ce-2a7681ca5ecb","agent_id":"4125fdcc-1a27-4aac-b566-b379ca31afbf","created_at":"2025-05-20T16:50:23.370562","updated_at":"2025-05-20T16:50:23.370562","status":"pending","creation":{"agent_id":"4125fdcc-1a27-4aac-b566-b379ca31afbf","input":{"messages":[{"type":"human","content":"hello"}]},"metadata":{},"config":{"tags":null,"recursion_limit":null,"configurable":{"to_upper":true}},"webhook":null,"stream_mode":null,"on_disconnect":"cancel","multitask_strategy":"reject","after_seconds":null,"on_completion":"delete"}}
# Extracted ID: 5976c7c4-7047-4085-ad76-d095416e0149
# Response from /runs/5976c7c4-7047-4085-ad76-d095416e0149/wait:
# {"run":{"run_id":"5976c7c4-7047-4085-ad76-d095416e0149","thread_id":"a564028a-f532-4706-87ce-2a7681ca5ecb","agent_id":"4125fdcc-1a27-4aac-b566-b379ca31afbf","created_at":"2025-05-20T16:50:23.370562","updated_at":"2025-05-20T16:50:23.386006","status":"success","creation":{"agent_id":"4125fdcc-1a27-4aac-b566-b379ca31afbf","input":{"messages":[{"type":"human","content":"hello"}]},"metadata":{},"config":{"tags":null,"recursion_limit":null,"configurable":{"to_upper":true,"thread_id":"a564028a-f532-4706-87ce-2a7681ca5ecb"}},"webhook":null,"stream_mode":null,"on_disconnect":"cancel","multitask_strategy":"reject","after_seconds":null,"on_completion":"delete"}},"output":{"type":"result","values":{"messages":[{"type":"human","content":"hello"},{"type":"assistant","content":"HELLO"}]}}}