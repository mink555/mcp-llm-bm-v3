#!/bin/bash
# 3(도메인) x 30(tasks) x 5(models) x 1(trial) = 450 runs
#
# NOTE:
# - 유저 요청에 "Retail, Retail, Telecom (small)"로 적혀있지만, 통상 3도메인은 Retail/Airline/Telecom이므로
#   여기서는 Retail + Airline + Telecom(30 tasks) 조합으로 실행합니다.
# - Telecom(small)은 공식 telecom_small이 20 tasks 뿐이라, "telecom_full에서 앞 30개 TaskID"를 고정 서브셋으로 사용합니다.
#
# 결과는 무조건 tau2-bench/results/latest/ 아래에만 생성(기존 결과 전부 삭제 후 새로 생성)

set -euo pipefail

# 로그 노이즈/경고 최소화(평가 결과에는 영향 없음)
: "${LITELLM_LOG:=ERROR}"
export LITELLM_LOG
: "${PYTHONWARNINGS:=ignore:resource_tracker}"
export PYTHONWARNINGS
export LITELLM_DISABLE_TELEMETRY="${LITELLM_DISABLE_TELEMETRY:-1}"

# tau2 실행기 선택:
# - PATH에 tau2가 있으면 그대로 사용
# - 없으면 (python3.13 -> python3 -> python) 중 tau2 import 가능한 인터프리터로 `python -m tau2.cli` 사용
TAU2=()
if command -v tau2 >/dev/null 2>&1 && tau2 --help >/dev/null 2>&1; then
  TAU2=(tau2)
else
  for PY in python3.13 python3 python; do
    if command -v "$PY" >/dev/null 2>&1; then
      if "$PY" - <<'PY' >/dev/null 2>&1; then
import tau2  # noqa: F401
PY
        TAU2=("$PY" -m tau2.cli)
        break
      fi
    fi
  done
fi
if [ "${#TAU2[@]}" -eq 0 ]; then
  echo "[ERROR] tau2 실행기를 찾지 못했습니다."
  echo "  - 해결1) pyenv를 쓰는 경우: tau2가 설치된 버전으로 전환 (예: pyenv shell 3.13.6/envs/mcp-llm-bm-v3)"
  echo "  - 해결2) tau2-bench 설치: cd tau2-bench && python -m pip install -e ."
  exit 1
fi

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

NUM_TASKS="${NUM_TASKS:-30}"
NUM_TRIALS="${NUM_TRIALS:-1}"
MAX_CONCURRENCY="${MAX_CONCURRENCY:-3}"
TEMP="${TEMP:-0.0}"
MAX_TOKENS="${MAX_TOKENS:-2048}"
MAX_STEPS="${MAX_STEPS:-200}"
MAX_ERRORS="${MAX_ERRORS:-10}"
MAX_ERRORS_SINGLE="${MAX_ERRORS_SINGLE:-3}"
RETRIES_PER_TASK="${RETRIES_PER_TASK:-4}"
SINGLE_MAX_CONCURRENCY="${SINGLE_MAX_CONCURRENCY:-1}"
DELAY_SEC="${DELAY_SEC:-1}"
# FORCE=1이면 기존 결과를 삭제하고 처음부터 다시 실행
FORCE="${FORCE:-0}"

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

if [ "$FORCE" = "1" ]; then
  echo "[CLEAN] FORCE=1: 기존 결과 삭제"
  rm -rf results/latest 2>/dev/null || true
  rm -f data/simulations/*.json 2>/dev/null || true
else
  echo "[RESUME] FORCE=0: 기존 결과가 있으면 완료된 런은 스킵하고 이어서 실행"
fi
mkdir -p results/latest/simulations

is_complete() {
  # usage: is_complete data/simulations/<save_to>.json
  local path="$1"
  python3 - <<PY
import json, sys
from pathlib import Path
p=Path("$path")
if not p.exists():
    sys.exit(1)
try:
    data=json.loads(p.read_text(encoding="utf-8"))
except Exception:
    sys.exit(1)
sims=data.get("simulations") or []
expected=int("${NUM_TASKS}") * int("${NUM_TRIALS}")
sys.exit(0 if expected>0 and len(sims)>=expected else 1)
PY
}

echo "[PICK] 각 도메인에서 앞 ${NUM_TASKS}개 TaskID 고정 선택"
python3 - <<PY
import json
from pathlib import Path
n = int("${NUM_TASKS}")

def dump(path_in: str, path_out: str):
    data = json.loads(Path(path_in).read_text(encoding="utf-8"))
    assert isinstance(data, list), f"expected list: {path_in}"
    ids = [t["id"] for t in data if isinstance(t, dict) and t.get("id")]
    Path(path_out).write_text("\\n".join(ids[:n]) + "\\n", encoding="utf-8")

Path("results/latest").mkdir(parents=True, exist_ok=True)
dump("data/tau2/domains/retail/tasks.json", "results/latest/task_ids_retail.txt")
dump("data/tau2/domains/airline/tasks.json", "results/latest/task_ids_airline.txt")
dump("data/tau2/domains/telecom/tasks_full.json", "results/latest/task_ids_telecom_small30.txt")
print("[OK] wrote task id lists under results/latest/")
PY

RETAIL_IDS=()
AIRLINE_IDS=()
TELECOM_IDS=()
while IFS= read -r line; do
  [ -n "$line" ] && RETAIL_IDS+=("$line")
done < results/latest/task_ids_retail.txt
while IFS= read -r line; do
  [ -n "$line" ] && AIRLINE_IDS+=("$line")
done < results/latest/task_ids_airline.txt
while IFS= read -r line; do
  [ -n "$line" ] && TELECOM_IDS+=("$line")
done < results/latest/task_ids_telecom_small30.txt

if [ "${#RETAIL_IDS[@]}" -lt "$NUM_TASKS" ] || [ "${#AIRLINE_IDS[@]}" -lt "$NUM_TASKS" ] || [ "${#TELECOM_IDS[@]}" -lt "$NUM_TASKS" ]; then
  echo "[ERROR] task id가 부족합니다. (retail=${#RETAIL_IDS[@]}, airline=${#AIRLINE_IDS[@]}, telecom_full=${#TELECOM_IDS[@]})"
  exit 1
fi

run_one() {
  local domain="$1"
  local task_set="$2"
  local model="$3"
  local save_to="$4"
  shift 4
  local -a task_ids=("$@")

  local agent_args user_args
  agent_args="$(build_llm_args)"
  user_args="$agent_args"

  local out_json="data/simulations/${save_to}.json"
  local expected="${NUM_TASKS}"
  if [ "$FORCE" != "1" ] && is_complete "$out_json"; then
    echo "  [SKIP] already complete: $out_json"
    # 결과 폴더에 복사 보장
    cp -f "$out_json" "results/latest/simulations/" 2>/dev/null || true
    return 0
  fi

  # 1) 먼저 "일괄 실행"으로 최대한 채워보기(파일이 없을 때만)
  if [ ! -f "$out_json" ]; then
    echo "  - domain=${domain} task_set=${task_set} model=${model##*/} tasks=${NUM_TASKS} trials=${NUM_TRIALS}"
    if ! "${TAU2[@]}" run \
      --domain "$domain" \
      --task-set-name "$task_set" \
      --task-ids "${task_ids[@]}" \
      --num-tasks "$NUM_TASKS" \
      --num-trials "$NUM_TRIALS" \
      --max-steps "$MAX_STEPS" \
      --max-errors "$MAX_ERRORS" \
      --max-concurrency "$MAX_CONCURRENCY" \
      --agent-llm "$model" \
      --agent-llm-args "$agent_args" \
      --user-llm "$model" \
      --user-llm-args "$user_args" \
      --save-to "$save_to" \
      --log-level ERROR; then
      echo "  [WARN] tau2 run failed (domain=$domain model=$model). 누락분은 개별 재시도로 채웁니다."
    fi
  fi

  if [ -f "$out_json" ]; then
    cp -f "$out_json" "results/latest/simulations/"
    echo "    -> saved: results/latest/simulations/$(basename "$out_json")"
  fi

  # 2) 누락 TaskID만 1개씩 재시도해서 "완주" 보장
  # expected list -> temp file
  local exp_file
  exp_file="$(mktemp)"
  printf "%s\n" "${task_ids[@]}" > "$exp_file"
  # compute missing via python (based on existing simulations.task_id)
  local missing
  missing="$(python3 - <<PY
import json, sys
from pathlib import Path
out_json=Path("$out_json")
exp=Path("$exp_file").read_text(encoding="utf-8").splitlines()
exp=[x.strip() for x in exp if x.strip()]
done=set()
if out_json.exists():
    try:
        data=json.loads(out_json.read_text(encoding="utf-8"))
        for s in (data.get("simulations") or []):
            if isinstance(s, dict) and s.get("task_id"):
                done.add(str(s["task_id"]))
    except Exception:
        pass
missing=[x for x in exp if x not in done]
print("\\n".join(missing))
PY
)"
  rm -f "$exp_file" 2>/dev/null || true
  if [ -n "$missing" ]; then
    local missing_count
    missing_count="$(echo "$missing" | wc -l | tr -d ' ')"
    echo "  [FILL] missing tasks=${missing_count} -> 개별 실행/병합로 채움"
    while IFS= read -r tid; do
      [ -z "$tid" ] && continue
      local ok=0
      local attempt=1
      while [ "$attempt" -le "$RETRIES_PER_TASK" ]; do
        # task_id가 길 수 있어 파일명은 해시 대신 안전한 단축
        local tid_s
        tid_s="$(echo "$tid" | sed 's/[^A-Za-z0-9]/_/g' | cut -c1-80)"
        local tmp_save="${save_to}__fill_${tid_s}__a${attempt}"
        local tmp_json="data/simulations/${tmp_save}.json"
        echo "    - [TRY] (${attempt}/${RETRIES_PER_TASK}) task_id=${tid}"
        if "${TAU2[@]}" run \
          --domain "$domain" \
          --task-set-name "$task_set" \
          --task-ids "$tid" \
          --num-tasks 1 \
          --num-trials "$NUM_TRIALS" \
          --max-steps "$MAX_STEPS" \
          --max-errors "$MAX_ERRORS_SINGLE" \
          --max-concurrency "$SINGLE_MAX_CONCURRENCY" \
          --agent-llm "$model" \
          --agent-llm-args "$agent_args" \
          --user-llm "$model" \
          --user-llm-args "$user_args" \
          --save-to "$tmp_save" \
          --log-level ERROR; then
          :
        fi
        # tmp_json이 생성되고 simulations가 1개 이상이면 병합
        if [ -f "$tmp_json" ]; then
          python3 merge_simulations.py --base "$out_json" --add "$tmp_json" --out "$out_json" || true
          rm -f "$tmp_json" 2>/dev/null || true
          cp -f "$out_json" "results/latest/simulations/" 2>/dev/null || true
          ok=1
          break
        fi
        attempt=$((attempt+1))
        if [ "$DELAY_SEC" != "0" ]; then
          sleep "$DELAY_SEC"
        fi
      done
      if [ "$ok" -ne 1 ]; then
        echo "    [WARN] task_id=${tid} 를 ${RETRIES_PER_TASK}회 시도했지만 실패(나중에 다시 시도 가능)"
      fi
    done <<< "$missing"
  fi

  if [ "$DELAY_SEC" != "0" ]; then
    sleep "$DELAY_SEC"
  fi
}

echo "[RUN] 총 runs 예상: $((3 * NUM_TASKS * ${#MODELS[@]})) (=${NUM_TASKS} tasks * 3 domains * ${#MODELS[@]} models * ${NUM_TRIALS} trial)"
echo "[RUN] MAX_CONCURRENCY=${MAX_CONCURRENCY} MAX_TOKENS=${MAX_TOKENS} MAX_STEPS=${MAX_STEPS}"

for model in "${MODELS[@]}"; do
  sanitized="$(sanitize_model_name "$model")"
  echo "=========================================="
  echo "[MODEL] $model"

  run_one "retail"  "retail"      "$model" "${sanitized}_retail_30" "${RETAIL_IDS[@]}"
  run_one "airline" "airline"     "$model" "${sanitized}_airline_30" "${AIRLINE_IDS[@]}"
  run_one "telecom" "telecom_full" "$model" "${sanitized}_telecom_small30" "${TELECOM_IDS[@]}"
done

echo "------------------------------------------"
echo "[REPORT] results/latest/simulations만 입력으로 최종 엑셀 생성"
python3 generate_reports.py --results-root results/latest --input-dir results/latest/simulations --prune

echo "[DONE] 결과 위치:"
echo "  - results/latest/전체_요약/TAU2_전체요약_latest.xlsx"
echo "  - results/latest/모델별/<모델라벨>/TAU2_<모델라벨>_latest.xlsx"

