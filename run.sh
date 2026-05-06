#!/bin/bash
set -e

# Required environment variables:
#   HF_TOKEN        — Hugging Face write token
#   VULTR_API_KEY   — Vultr API key
#   VULTR_INSTANCE_ID — this instance's ID (from Vultr dashboard)

echo "Starting training..."
python3 -m evaluator.neural_eval.train

echo "Training done. Deleting instance..."
curl -s -X DELETE "https://api.vultr.com/v2/instances/${VULTR_INSTANCE_ID}" \
    -H "Authorization: Bearer ${VULTR_API_KEY}"

echo "Instance deletion requested. Goodbye."


