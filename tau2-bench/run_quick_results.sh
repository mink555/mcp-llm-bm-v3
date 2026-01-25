#!/bin/bash
# 퀵 검증: 5개 모델을 아주 작게(도메인 1개, task 1개, trial 1개) 돌리고
# "기존 누적 결과"는 포함하지 않고, 방금 퀵으로 생성된 JSON만 모아서
# results/ 아래에 모델별/전체_요약 리포트를 자동 생성한다.

set -e

# .env 로드(옵션)
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
  echo "[ERROR] OPENROUTER_API_KEY가 없습니다. (.env 또는 환경변수로 설정)"
  exit 1
fi

MODELS=(
  "openrouter/meta-llama/llama-3.3-70b-instruct"
  "openrouter/mistralai/mistral-small-3.2-24b-instruct"
  "openrouter/qwen/qwen3-32b"
  "openrouter/qwen/qwen3-14b"
  "openrouter/qwen/qwen3-next-80b-a3b-instruct"
)

# 비용/속도 때문에 1개 모델만 돌리고 싶으면:
#   ONLY_MODEL="openrouter/mistralai/mistral-small-3.2-24b-instruct" ./run_quick_results.sh
if [ -n "${ONLY_MODEL:-}" ]; then
  MODELS=("$ONLY_MODEL")
fi

# 기본은 telecom_small 1 task/1 trial (가장 빨리 확인 가능)
DOMAIN="${DOMAIN:-telecom}"
TASK_SET="${TASK_SET:-telecom_small}"
NUM_TASKS="${NUM_TASKS:-1}"
NUM_TRIALS="${NUM_TRIALS:-1}"
MAX_CONCURRENCY="${MAX_CONCURRENCY:-1}"
TEMP="${TEMP:-0.0}"
MAX_TOKENS="${MAX_TOKENS:-2048}"
DELAY_SEC="${DELAY_SEC:-0}"
FORCE="${FORCE:-1}"

sanitize_model_name() {
  echo "$1" | sed 's/openrouter\///' | sed 's/\//_/g' | sed 's/:/_/g'
}

build_llm_args() {
  TEMP_ENV="$TEMP" MAX_TOKENS_ENV="$MAX_TOKENS" \
  python3 - <<'PY'
import json, os
print(json.dumps({"temperature": float(os.environ["TEMP_ENV"]), "max_tokens": int(os.environ["MAX_TOKENS_ENV"])}))
PY
}

echo "[START] QUICK | domain=$DOMAIN task_set=$TASK_SET tasks=$NUM_TASKS trials=$NUM_TRIALS max_tokens=$MAX_TOKENS"

mkdir -p data/simulations

# 이번 퀵 런 전용 결과 폴더(누적 결과와 분리)
# - 기본은 항상 latest로 덮어쓰기(경로 난립 방지)
# - 히스토리가 필요하면 RUN_TAG를 직접 지정: RUN_TAG=20260126_010101 ./run_quick_results.sh
RUN_TAG="${RUN_TAG:-latest}"
RESULTS_ROOT="${RESULTS_ROOT:-results/quick/${RUN_TAG}}"
RUN_SIM_DIR="${RESULTS_ROOT}/simulations"
mkdir -p "${RUN_SIM_DIR}"

# latest 모드에서는 이전 퀵 JSON을 정리(이번 런만 남기기)
if [ "$RUN_TAG" = "latest" ]; then
  rm -f "${RUN_SIM_DIR}"/*.json 2>/dev/null || true
fi

for model in "${MODELS[@]}"; do
  sanitized=$(sanitize_model_name "$model")
  save_to="${sanitized}_${DOMAIN}_quick"
  out_json="data/simulations/${save_to}.json"

  if [ "$FORCE" = "1" ]; then
    rm -f "$out_json" 2>/dev/null || true
  fi

  AGENT_ARGS="$(build_llm_args)"
  USER_ARGS="$AGENT_ARGS"

  echo "------------------------------------------"
  echo "[MODEL] $model"
  if ! tau2 run \
    --domain "$DOMAIN" \
    --task-set-name "$TASK_SET" \
    --num-tasks "$NUM_TASKS" \
    --num-trials "$NUM_TRIALS" \
    --max-concurrency "$MAX_CONCURRENCY" \
    --agent-llm "$model" \
    --agent-llm-args "$AGENT_ARGS" \
    --user-llm "$model" \
    --user-llm-args "$USER_ARGS" \
    --save-to "$save_to" \
    --log-level ERROR; then
    echo "  [WARN] tau2 run failed: $model (계속 진행)"
  fi

  # 방금 퀵으로 생성된 JSON만 전용 폴더로 복사(리포트 입력을 이 폴더로 제한)
  if [ -f "$out_json" ]; then
    cp -f "$out_json" "${RUN_SIM_DIR}/"
  fi

  if [ "$DELAY_SEC" != "0" ]; then
    sleep "$DELAY_SEC"
  fi
done

echo "------------------------------------------"
echo "[REPORT] (누적 제외) ${RESULTS_ROOT} 아래에 전체/모델별 엑셀 생성 (latest만)"
python3 generate_reports.py --results-root "${RESULTS_ROOT}" --input-dir "${RUN_SIM_DIR}" --prune
echo "[DONE] ${RESULTS_ROOT} 확인"

