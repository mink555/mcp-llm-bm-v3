#!/bin/bash
# TAU2-Bench Evaluation Automation Script
# Clean, professional, and automated.

set -e

# 로그 노이즈/경고 최소화(평가 결과에는 영향 없음)
: "${LITELLM_LOG:=ERROR}"
export LITELLM_LOG
: "${PYTHONWARNINGS:=ignore:resource_tracker}"
export PYTHONWARNINGS
export LITELLM_DISABLE_TELEMETRY="${LITELLM_DISABLE_TELEMETRY:-1}"

# 재개(resume) 옵션
# - RESUME=1(기본): 결과 파일이 있으면 완료 여부를 판단해서 완료면 스킵, 미완료면 이어서 실행(자동 y 입력)
# - RESUME=0: 결과 파일이 있으면 에러(덮어쓰기/재개를 명시적으로 선택하게)
RESUME="${RESUME:-1}"
# - FORCE=1: 기존 결과 파일을 삭제하고 처음부터 다시 실행
FORCE="${FORCE:-0}"

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
# OpenRouter 402(크레딧/토큰 부족) 방지용: max_tokens 상한(기본 4096)
# 필요하면 실행 시 `MAX_TOKENS=2048` 처럼 조절
MAX_TOKENS="${MAX_TOKENS:-4096}"
# OpenRouter 라우팅은 기본 동작 사용(추가 provider 고정 로직 없음)
# OpenRouter API 안정화를 위한 호출 간 딜레이(초). 기본 1초.
# 필요하면 실행 시 `DELAY_SEC=0` 또는 `DELAY_SEC=2`처럼 조절.
DELAY_SEC="${DELAY_SEC:-1}"

sanitize_model_name() {
    echo "$1" | sed 's/openrouter\///' | sed 's/\//_/g' | sed 's/:/_/g'
}

is_run_complete() {
    # usage: is_run_complete <json_path> <num_trials>
    # returns 0 if complete, 1 otherwise
    local json_path="$1"
    local num_trials="$2"
    python3 - <<PY
import json, sys
from pathlib import Path
p = Path("$json_path")
if not p.exists():
    sys.exit(1)
try:
    data = json.loads(p.read_text(encoding="utf-8"))
except Exception:
    sys.exit(1)
tasks = data.get("tasks") or []
sims = data.get("simulations") or []
expected = len(tasks) * int("$num_trials")
done = len(sims)
sys.exit(0 if expected > 0 and done >= expected else 1)
PY
}

build_llm_args() {
    # shell vars -> json
    TEMP_ENV="$TEMP" MAX_TOKENS_ENV="$MAX_TOKENS" \
    python3 - <<'PY'
import json, os
args = {
    "temperature": float(os.environ["TEMP_ENV"]),
    "max_tokens": int(os.environ["MAX_TOKENS_ENV"]),
}
print(json.dumps(args))
PY
}

echo "Starting TAU2-Bench Evaluation..."
echo "Trials: $NUM_TRIALS | Temp: $TEMP | MaxTokens: $MAX_TOKENS | Resume: $RESUME | Force: $FORCE"

mkdir -p results/latest

for model in "${MODELS[@]}"; do
    sanitized=$(sanitize_model_name "$model")
    echo "------------------------------------------"
    echo "Model: ${model##*/}"
    
    for domain in "${DOMAINS[@]}"; do
        echo "  Domain: $domain"

        OUT_JSON="data/simulations/${sanitized}_${domain}.json"

        # FORCE=1이면 항상 새로 시작
        if [ "$FORCE" = "1" ]; then
            rm -f "$OUT_JSON" 2>/dev/null || true
        fi

        # 이미 완료된 결과면 스킵(RESUME=1일 때)
        if [ -f "$OUT_JSON" ] && [ "$RESUME" = "1" ] && is_run_complete "$OUT_JSON" "$NUM_TRIALS"; then
            echo "  [SKIP] already complete: $OUT_JSON"
            continue
        fi

        # 결과 파일이 있는데 RESUME=0이면 명시적으로 중단
        if [ -f "$OUT_JSON" ] && [ "$RESUME" != "1" ]; then
            echo "  [ERROR] result exists but RESUME=0: $OUT_JSON"
            echo "          Use RESUME=1 to continue from checkpoints, or FORCE=1 to overwrite."
            exit 1
        fi

        # LLM args 구성(temperature + max_tokens)
        AGENT_ARGS="$(build_llm_args)"
        USER_ARGS="$AGENT_ARGS"

        # 파일이 있으면 tau2가 resume 질문을 함 → 비대화형으로 자동 y 입력(2번 넣어서 2회 프롬프트까지 대비)
        if [ -f "$OUT_JSON" ]; then
            if ! printf "y\ny\n" | tau2 run \
                --domain "$domain" \
                --agent-llm "$model" \
                --agent-llm-args "$AGENT_ARGS" \
                --user-llm "$model" \
                --user-llm-args "$USER_ARGS" \
                --num-trials "$NUM_TRIALS" \
                --save-to "${sanitized}_${domain}" \
                --max-concurrency 3 \
                --log-level ERROR; then
                echo "  [WARN] tau2 run failed (model=$model domain=$domain). Continuing."
            fi
        else
            if ! tau2 run \
                --domain "$domain" \
                --agent-llm "$model" \
                --agent-llm-args "$AGENT_ARGS" \
                --user-llm "$model" \
                --user-llm-args "$USER_ARGS" \
                --num-trials "$NUM_TRIALS" \
                --save-to "${sanitized}_${domain}" \
                --max-concurrency 3 \
                --log-level ERROR; then
                echo "  [WARN] tau2 run failed (model=$model domain=$domain). Continuing."
            fi
        fi

        # provider rate-limit/용량 이슈 완화용
        if [ "$DELAY_SEC" != "0" ]; then
            sleep "$DELAY_SEC"
        fi
    done
    
    # 전체/모델별 리포트(경로 고정: results/latest)
    if ! python3 generate_reports.py --results-root results/latest --prune; then
        echo "  [WARN] generate_reports.py failed. Continuing."
    else
        echo "  Reports updated under: results/latest/"
    fi
done

echo "------------------------------------------"
echo "Evaluation Complete."
echo "Final Reports:"
echo "  - results/latest/전체_요약/TAU2_전체요약_latest.xlsx"
echo "  - results/latest/모델별/<모델라벨>/TAU2_<모델라벨>_latest.xlsx"
