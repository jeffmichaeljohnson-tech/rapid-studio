#!/bin/bash

echo "🏃‍♂️ RAPID STUDIO PREFETCH PERFORMANCE TEST"
echo "=========================================="
echo "Testing multi-tier prefetching for zero-delay experience"

API_BASE="http://100.103.213.111:8000"

# Test each tier
echo "Testing Tier 1: Universal base images..."
curl -X GET "$API_BASE/images/universal?count=25" \
  -H "X-Tier: universal" \
  -w "Time: %{time_total}s\n"

echo "Testing Tier 2: Demographic clustering..."
curl -X GET "$API_BASE/images/demographic?age=25-34&location=US" \
  -H "X-Tier: demographic" \
  -w "Time: %{time_total}s\n"

echo "Testing Tier 3: Personal model..."
curl -X POST "$API_BASE/images/personal" \
  -H "Content-Type: application/json" \
  -H "X-Tier: personal" \
  -d '{"user_preferences": "test", "count": 25}' \
  -w "Time: %{time_total}s\n"

echo "✅ Prefetch performance test complete"
