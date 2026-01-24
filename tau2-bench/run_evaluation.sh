#!/bin/bash
# TAU2-Bench Evaluation Automation Script
# Clean, professional, and automated.

set -e

MODELS=(
    "openrouter/meta-llama/llama-3.3-70b-instruct"
    "openrouter/mistralai/mistral-small-3.2-24b-instruct"
    "openrouter/qwen/qwen3-32b"
    "openrouter/qwen/qwen3-14b"
    "openrouter/qwen/qwen3-next-80b-a3b-instruct"
)

DOMAINS=("retail" "airline" "telecom")
NUM_TRIALS=4
TEMP=0.0

sanitize_model_name() {
    echo "$1" | sed 's/openrouter\///' | sed 's/\//_/g' | sed 's/:/_/g'
}

echo "Starting TAU2-Bench Evaluation..."
echo "Trials: $NUM_TRIALS | Temp: $TEMP"

for model in "${MODELS[@]}"; do
    sanitized=$(sanitize_model_name "$model")
    echo "------------------------------------------"
    echo "Model: ${model##*/}"
    
    for domain in "${DOMAINS[@]}"; do
        echo "  Domain: $domain"
        
        # Ensure clean run
        rm -f "data/simulations/${sanitized}_${domain}.json" 2>/dev/null
        
        tau2 run \
            --domain "$domain" \
            --agent-llm "$model" \
            --agent-llm-args "{\"temperature\": $TEMP}" \
            --user-llm "$model" \
            --user-llm-args "{\"temperature\": $TEMP}" \
            --num-trials "$NUM_TRIALS" \
            --save-to "${sanitized}_${domain}" \
            --max-concurrency 3 \
            --log-level ERROR
    done
    
    # Generate intermediate report
    python3 generate_excel_report.py
    echo "  Intermediate report updated."
done

echo "------------------------------------------"
echo "Evaluation Complete."
echo "Final Report: tau2_evaluation_report.xlsx"
