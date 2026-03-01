#!/bin/bash
# Test script to fetch trader@example.com account data

BACKEND_URL="http://localhost:8000"
EMAIL="trader@example.com"

echo "🔍 Fetching trader data for: $EMAIL"
echo ""

curl -X GET "${BACKEND_URL}/dev/trader-data?email=${EMAIL}" \
  -H "Content-Type: application/json" \
  -s | jq '.'

echo ""
echo "✅ Done"
