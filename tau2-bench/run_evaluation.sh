#!/bin/bash
# TAU2-Bench Evaluation Automation Script
# Clean, professional, and automated.

set -e

# API 키가 없으면 .env에서 로드(옵션)
# - 우선순위: 환경변수(이미 설정됨) > tau2-bench/.env > repo 루트 ../.env
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    for ENV_FILE in ".env" "../.env" ".env.local" "../.env.local"; do
        if [ -f "$ENV_FILE" ]; then
            set -a
            # shellcheck disable=SC1090
            source "$ENV_FILE"
            set +a
            break
        fi
    done
fi

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "[WARN] OPENROUTER_API_KEY is not set. OpenRouter calls will fail unless the key is provided."
fi

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
# OpenRouter API 안정화를 위한 호출 간 딜레이(초). 기본 1초.
# 필요하면 실행 시 `DELAY_SEC=0` 또는 `DELAY_SEC=2`처럼 조절.
DELAY_SEC="${DELAY_SEC:-1}"

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
        
        if ! tau2 run \
            --domain "$domain" \
            --agent-llm "$model" \
            --agent-llm-args "{\"temperature\": $TEMP}" \
            --user-llm "$model" \
            --user-llm-args "{\"temperature\": $TEMP}" \
            --num-trials "$NUM_TRIALS" \
            --save-to "${sanitized}_${domain}" \
            --max-concurrency 3 \
            --log-level ERROR; then
            echo "  [WARN] tau2 run failed (model=$model domain=$domain). Continuing."
        fi

        # provider rate-limit/용량 이슈 완화용
        if [ "$DELAY_SEC" != "0" ]; then
            sleep "$DELAY_SEC"
        fi
    done
    
    # Generate intermediate report
    if ! python3 generate_excel_report.py; then
        echo "  [WARN] generate_excel_report.py failed. Continuing."
    fi
    echo "  Intermediate report updated."
done

echo "------------------------------------------"
echo "Evaluation Complete."
echo "Final Report: tau2_evaluation_report.xlsx"
