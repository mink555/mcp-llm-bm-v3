# mcp-llm-bm-v3

이 저장소는 `tau2-bench`(업스트림)를 포함하고, OpenRouter를 통해 5개 LLM 모델을 평가하는 실행/리포트 파이프라인을 제공합니다.

## 구성

- **업스트림 벤치마크 코드**: `tau2-bench/` (원본 README 및 코드 유지)
- **실행 스크립트**: `tau2-bench/run_evaluation.sh`
- **리포트 생성기**: `tau2-bench/generate_excel_report.py`

## TAU2 평가 의도(무엇을 측정하나)

τ²-bench는 “정답 텍스트 한 줄”을 맞히는 벤치마크가 아니라, **고객센터 시나리오에서 에이전트가 정책을 지키며 도구를 사용해 상태(DB)를 올바르게 바꾸고, 사용자에게 필요한 정보를 전달하는지**를 측정합니다. 오케스트레이터가 Agent ↔ UserSimulator ↔ Environment(툴/DB)를 중재하며 여러 턴의 대화를 시뮬레이션합니다(업스트림 `tau2-bench/README.md`의 Orchestration Sequence Diagram 참고).

## TAU2 벤치마크의 철학과 “검증 방식” 요약

TAU2는 **텍스트 정답형 QA가 아니라 행동 기반(agentic) 평가**입니다.  
즉, 모델이 “말만 잘하는지”가 아니라 **정책을 지키며 도구를 호출해 실제 상태를 바꾸고, 그 결과를 사용자에게 전달하는지**를 봅니다.

### 무엇을 입력으로 받고, 무엇을 비교하나
- **입력(요청)**: `task.user_scenario.instructions`의 *상황/제약/요구사항*
- **기대값(GT)**: `task.evaluation_criteria`의 *필수 액션 + 상태 검증*
- **모델 응답**: 
  - `tool_calls`(구조화된 툴 호출) **또는**
  - `content`(자연어 답변)  
  단, **둘 중 하나만** 있어야 합니다.

### 왜 “툴콜”이 핵심인가
툴 호출이 **구조화된 `tool_calls`로 들어와야** 실제 환경(툴/DB)이 바뀝니다.  
- 텍스트로 “[TOOL_CALLS ...]”처럼 흉내를 내도 **평가에서는 툴 호출이 없는 것으로 처리**됩니다.

---

## 샘플: Telecom 태스크 1개(요청 → 기대 행동 → 성공 조건)

아래는 telecom 태스크에서 흔히 나오는 흐름을 **요약 샘플**로 정리한 것입니다.

**요청(발췌)**  
- 해외에서 데이터가 느리거나 끊김  
- 반드시 “excellent” 속도가 나와야 해결 인정  
- Wi‑Fi 없음, 요금제 변경 원치 않음

**기대 행동(예시)**  
- `toggle_airplane_mode`  
- `toggle_roaming`

**성공 조건(예시)**  
- `assert_mobile_data_status == true`  
- `assert_internet_speed == excellent(200)`

**성공 흐름(이상적인 모델 행동)**  
- 툴을 **구조화 `tool_calls`로 호출**  
- 도구 결과로 상태가 **기대값과 일치**  
- 마지막에 사용자에게 **결과/안내를 자연어로 전달**

**실패 흐름(대표 케이스)**  
- 자연어로만 해결책을 설명하고 **툴 호출 없음**  
- 툴 호출이 누락되거나 잘못됨  
- 상태가 기대값에 도달하지 못함

---

## 실제 JSON 샘플 (telecom 1회 실행 발췌)

아래는 `data/simulations/mistral_small_telecom_one.json`에서 **요청/GT/모델 응답을 그대로** 추출한 예시입니다.

```json
{
  "task_id": "[mobile_data_issue]airplane_mode_on|user_abroad_roaming_enabled_off[PERSONA:None]",
  "request": {
    "reason_for_call": "You mobile data is not working properly. It either stops working or is very slow. You want to fix it and absolutely want to get excellent internet speed on your phone. You are not willing to accept any other internet speed (poor, fair or good). You do not have access to wifi.",
    "known_info": "You are John Smith with phone number 555-123-2002. You are currently abroad in France.",
    "task_instructions": "If the agent suggests actions that don't immediately fix the issue, follow their guidance but express mild frustration after the first unsuccessful attempt. You will consider the issue resolved only when speed test returns excellent internet speed and nothing else. If it returns poor, fair or good, you will not consider the issue resolved. You are willing to refuel 2.0 GB of data if necessary, but you do not want to change your mobile data plan. If the tool call does not return updated status information, you might need to perform another tool call to get the updated status. \nWhenever the agent asks you about your device, always ground your responses on the results of tool calls. \nFor example: If the agent asks what the status bar shows, always ground your response on the results of the `get_status_bar` tool call. If the agent asks if you are able to send an MMS message, always ground your response on the results of the `can_send_mms` tool call.\nNever make up the results of tool calls, always ground your responses on the results of tool calls.\nIf you are unsure about whether an action is necessary, always ask the agent for clarification.\n"
  },
  "gt": {
    "actions": [
      {
        "action_id": "toggle_airplane_mode_0",
        "requestor": "user",
        "name": "toggle_airplane_mode",
        "arguments": {},
        "info": null,
        "compare_args": null
      },
      {
        "action_id": "toggle_roaming_1",
        "requestor": "user",
        "name": "toggle_roaming",
        "arguments": {},
        "info": null,
        "compare_args": null
      }
    ],
    "env_assertions": [
      {
        "env_type": "user",
        "func_name": "assert_mobile_data_status",
        "arguments": {
          "expected_status": true
        },
        "assert_value": true,
        "message": null
      },
      {
        "env_type": "user",
        "func_name": "assert_internet_speed",
        "arguments": {
          "expected_speed": 200,
          "expected_desc": "excellent"
        },
        "assert_value": true,
        "message": null
      }
    ]
  },
  "model_response": "[TOOL_CALLStransfer_to_human_agents[ARGS{\"summary\": \"User is experiencing slow mobile data speeds while abroad in France. They have a 10.0 GB data plan and are not interested in changing it. Basic troubleshooting steps have been attempted without success. The user requires excellent internet speed for their needs.\"}",
  "model_tool_calls": null
}
```

**이 샘플에서의 판단 포인트**
- `model_tool_calls`가 **null**이면 실제 툴 호출이 발생하지 않습니다.  
- 평가 기준(`gt.actions`, `gt.env_assertions`)은 **툴 호출/상태 변화가 전제**이므로, 이 경우 **FAIL**로 처리됩니다.

---

## 모델별 툴콜/검증 결과 비교표 (telecom 1회 샘플)

아래는 telecom 결과 JSON의 첫 번째 trial 기준 요약입니다.  
`assistant tool_calls 수`가 0이면 **모델이 구조화된 툴 호출을 내지 못한 것**을 의미합니다.

| 모델 | assistant tool_calls 수 | user tool_calls 수 | Action Checks(성공/전체) | Env Assertions(성공/전체) | Reward |
|---|---:|---:|---|---|---:|
| openrouter/meta-llama/llama-3.3-70b-instruct | 0 | 5 | 2/2 | 2/2 | 1.0 |
| openrouter/mistralai/mistral-small-3.2-24b-instruct | 0 | 0 | 0/2 | 0/2 | 0.0 |
| openrouter/qwen/qwen3-32b | 실행 결과 없음 | - | - | - | - |
| openrouter/qwen/qwen3-14b | 실행 결과 없음 | - | - | - | - |
| openrouter/qwen/qwen3-next-80b-a3b-instruct | 실행 결과 없음 | - | - | - | - |

**해석 팁**
- `Action Checks`는 **requestor가 user/assistant인지**에 따라 실행 주체가 달라질 수 있습니다.  
- 이 표는 “툴콜이 실제로 들어왔는지(assistant tool_calls 수)”와 “평가 기준이 충족됐는지”를 분리해서 보여줍니다.

## 평가 카테고리(도메인)

- **Retail**: 주문 조회/반품/교환/주소·결제 변경 등 전자상거래 고객센터 업무
- **Airline**: 항공 예약/변경/좌석/마일리지 등 여행 고객센터 업무
- **Telecom**: 요금제/장애/청구/개통 등 통신 고객센터 업무

## 평가 지표(스코어)와 산식

- **Success(성공/실패)**: 한 trial의 최종 성공 여부. τ²-bench 코드 기준으로 **`reward == 1.0(±1e-6)`이면 성공**입니다(`tau2-bench/src/tau2/metrics/agent_metrics.py:is_successful`).
- **Reward (0~1)**: `reward_info.reward`로 기록됩니다. 실전적으로는 성공이면 1.0, 아니면 0.0에 가깝게 나오는 경우가 많습니다(도메인별 체크가 모두 충족되어야 1.0).
- **Pass^k (k=1..n)**: 같은 Task를 `n`번(trials) 실행했을 때, **그 중 k개를 동시에 성공할 확률 기반**으로 계산합니다.
  - 산식(코드): \( \mathrm{Pass}^k = \binom{c}{k} / \binom{n}{k} \)  (n=총 시행 수, c=성공 횟수)
  - 집계: Task별 Pass^k를 평균내어 도메인 점수로 보고, 도메인 점수들을 평균(매크로 평균)해 전체 요약을 만듭니다.

## 지표별로 “어떤 실력”을 보는가 (해석 가이드)

| 지표 | 정의(무엇을 측정) | 주로 보는 모델 실력 | 높으면 좋은데, 주의할 점 |
|---|---|---|---|
| **Pass(0/1)** | 해당 trial이 **최종 성공**(최종 assertion/DB check 통과)하면 1 | **엔드투엔드 과업 완수 능력**(정책 준수 + 올바른 툴 사용 + 상태변경 + 마무리 커뮤니케이션) | 말만 그럴듯해도 **DB/액션이 안 맞으면 0** |
| **Reward (0~1)** | `reward_info.reward` (대개 성공=1, 실패=0에 가까움) | **부분 점수까지 포함한 수행 품질**(도메인별 communicate/action/DB 등 구성) | 도메인/설정에 따라 **부분점수 비중**이 달라 단순 비교 시 주의 |
| **DB Check (0~1)** | DB 상태가 GT와 일치하는지 | **정확한 상태 갱신/검증 능력**(툴 결과를 반영해 “실제로” 처리) | 텍스트로 “처리 완료”라고 해도 DB가 안 바뀌면 0 |
| **Action Checks (각 step별 0/1)** | 요구되는 액션(핵심 툴 호출/행동)을 했는지 | **툴 선택/계획/절차 준수 능력**(올바른 툴을 올바른 순서·인자로 호출) | 툴 args 누락/깨짐은 여기서 크게 감점 |
| **COMMUNICATE (0~1)** | 사용자에게 필요한 정보 전달/형식 준수(가능한 경우) | **대화 품질 + 정책 기반 커뮤니케이션**(설명, 확인질문, 안내문) | 로그에 `No communicate_info to evaluate`면 이 축이 사실상 평가에 안 걸린 것(태스크/설정 영향) |
| **Termination Reason** | 왜 종료됐는지(USER_STOP, MAX_TURNS, ERROR 등) | **수렴/종료 능력**(불필요 루프 없이 목표 달성 후 종료) | USER_STOP이 빠르다고 좋은 게 아니라 **Pass/DB와 같이** 봐야 함 |
| **Duration (sec)** | 한 trial 수행 시간 | **효율/지연**(빠르게 수렴하는지) | 네트워크/공급자(503 등) 영향 큼 → 성능지표로 단독 비교 금지 |
| **Agent Cost / User Cost** | LLM 호출 비용(가능한 경우) | **비용 효율성**(같은 성공률 대비 비용) | LiteLLM 가격 매핑 누락이면 0으로 찍힐 수 있어 “0=무료”가 아님 |
| **Pass^k (k=1..4)** | 같은 Task를 n번 돌릴 때 \( \binom{c}{k}/\binom{n}{k} \) | **안정성/재현성**(운 좋게 1번 성공이 아니라 반복 성공) | k가 클수록 **일관성**을 강하게 봄(권장 n≥k) |
| **Overall (macro avg)** | 도메인별 Pass^k 평균을 다시 평균 | **범용성/도메인 일반화** | 특정 도메인 강점/약점이 평균에 가려질 수 있어 도메인별도 같이 확인 권장 |

## 모델은 “무엇을 해야” 점수가 나오나 (벤치 동작 관점)

τ²-bench에서 모델은 “정답 문장”을 맞히는 게 아니라, **정책을 지키면서 도구(tool)를 올바르게 호출해 상태(DB)를 바꾸고, 그 결과를 사용자에게 커뮤니케이션**해야 합니다.

- **공통(모든 도메인)**:
  - **요구사항 파악**: 사용자가 원하는 최종 목표/제약(날짜, 계정, 주문번호 등)을 확인
  - **정책 준수**: 도메인 정책에 따라 가능한 행동/불가능한 행동 구분
  - **툴 사용**: 적절한 툴을 선택하고, **스키마에 맞는 arguments(JSON)**로 호출
  - **상태 추적**: 툴 응답을 근거로 다음 행동을 결정(추측 금지)
  - **종료**: 목표 달성 후 사용자에게 결과(변경 내역/환불/다음 단계)를 정리하고 종료

- **Retail 예시**:
  - **주문/상품 조회 → 조건 확인 → 교환/반품 실행 → 결과 안내** 같은 “조회-실행-확인” 흐름이 핵심
- **Airline 예시**:
  - **예약/항공편 조회 → 변경 가능 조건 확인 → 변경 실행 → 최종 일정/비용 안내**
- **Telecom 예시**:
  - **본인확인/계정 조회 → 요금제/장애/청구 등 워크플로우 수행 → 조치/티켓/가이드 제공**

## OpenRouter 사용 시 코드 실행 경로(어떤 .py를 거치나)

OpenRouter는 “별도 구현”이 아니라 **LiteLLM provider로 호출**됩니다. 핵심 흐름은 아래입니다.

- **CLI 진입**: `tau2-bench/src/tau2/cli.py`
  - `tau2 run ...` 인자 파싱 → `run_domain(RunConfig(...))` 호출
- **실행 루프**: `tau2-bench/src/tau2/run.py`
  - `run_domain()` → `run_tasks()` → `run_task()` → `Orchestrator.run()`
- **대화 오케스트레이션**: `tau2-bench/src/tau2/orchestrator/orchestrator.py`
  - Agent ↔ UserSimulator ↔ Environment를 번갈아 호출
- **에이전트 LLM 호출**: `tau2-bench/src/tau2/agent/llm_agent.py`
  - `generate_next_message()`에서 LLM 응답 생성
- **LiteLLM(OpenRouter) 호출**: `tau2-bench/src/tau2/utils/llm_utils.py`
  - `generate()` → `litellm.completion(model="openrouter/...")`
  - tools/tool_choice가 포함되면 모델이 tool call을 반환하고, 오케스트레이터가 환경 툴을 실행

## “오류 없이 잘 하고 있는지” 빠른 점검 체크리스트

- **키 로딩 확인**:
  - 쉘에서 `echo $OPENROUTER_API_KEY`가 비어있지 않은지 확인
- **저장 경로 확인**:
  - 이 repo 기준으로 결과는 기본적으로 `tau2-bench/data/simulations/*.json`에 쌓입니다(`tau2-bench/src/tau2/cli.py` help 기준).
- **툴이 실제로 호출되는지**:
  - `tau2 run` 출력에서 Action Checks가 전부 ❌이고 DB가 0이면, 대개 “툴 호출을 못 했거나(포맷/args 문제)”, “호출했지만 실패”입니다.
- **OpenRouter 일시 오류(503/429) 구분**:
  - 모델 실력 문제가 아니라 provider 가용성/레이트리밋일 수 있으니 `--max-concurrency`를 줄이거나 `DELAY_SEC`를 늘려 재시도합니다.
- **리포트 생성 확인**:
  - `python3 tau2-bench/generate_excel_report.py` 실행 후 `tau2_evaluation_report.xlsx`가 생성되는지 확인

## OpenRouter 설정

OpenRouter는 LiteLLM provider로 호출됩니다.

- **모델 표기 규칙**: `openrouter/<provider>/<model>` 형태
- **API 키 설정(.env 권장)**:

가장 간단한 방식은 `.env.example`을 복사해서 `.env`를 만들고, 쉘에 로드하는 것입니다.

```bash
cp .env.example .env
# .env에 OPENROUTER_API_KEY를 채운 뒤
set -a
source .env
set +a
```

```bash
export OPENROUTER_API_KEY="YOUR_KEY"
```

키는 절대 커밋하지 마세요. (`.gitignore`에 `.env`가 포함되어 있습니다.)

## OpenRouter로 모델 실력 검증: 빠른 사용법(테이블)

아래 표는 “어떻게 실행하면 무엇을 확인할 수 있는지”를 한눈에 정리한 것입니다.

| 목적 | 실행 명령 | 무엇을 확인하나 |
|---|---|---|
| **연결/키 확인** | `cd tau2-bench`<br>`tau2 check-data` | 데이터 경로/환경 설정이 정상인지 |
| **초고속 1개 테스트(telecom)** | `cd tau2-bench`<br>`export OPENROUTER_API_KEY="YOUR_KEY"`<br>`tau2 run --domain telecom --agent-llm openrouter/mistralai/mistral-small-3.2-24b-instruct --user-llm openrouter/mistralai/mistral-small-3.2-24b-instruct --num-trials 1 --num-tasks 1 --max-concurrency 1 --log-level ERROR` | 1개 태스크에서 **툴 호출이 실제로 나오는지**, 통신이 되는지 |
| **엑셀 리포트 생성** | `cd tau2-bench`<br>`python3 generate_excel_report.py` | 요청/GT/모델 응답/FAIL 원인을 리포트로 확인 |
| **5개 모델 × 3도메인 전체 평가** | `cd tau2-bench`<br>`./run_evaluation.sh` | 전체 Pass^k/도메인 성능 비교 |
| **OpenRouter 기본 라우팅 사용** | `cd tau2-bench`<br>`./run_evaluation.sh` | OpenRouter 기본 라우팅으로 실행 |

### 짧은 해석 포인트
- **툴콜이 실제로 들어오면** `Action Checks`가 ✅로 올라가기 시작합니다.  
- **툴콜이 text로만 나오면** `tool_calls`가 비어 있어 **FAIL**로 찍히는 게 정상입니다.  
- 따라서 **OpenRouter provider 라우팅이 툴콜 품질에 큰 영향**을 줍니다.

### 참고
- OpenRouter는 기본적으로 provider를 자동 라우팅합니다.

## 평가 대상 모델(요청하신 5개)

- `openrouter/meta-llama/llama-3.3-70b-instruct`
- `openrouter/mistralai/mistral-small-3.2-24b-instruct`
- `openrouter/qwen/qwen3-32b`
- `openrouter/qwen/qwen3-14b`
- `openrouter/qwen/qwen3-next-80b-a3b-instruct`

## Quick 평가 CLI(연결/포맷/리포트 확인용)

```bash
cd tau2-bench
export OPENROUTER_API_KEY="YOUR_KEY"

tau2 run \
  --domain retail \
  --agent-llm openrouter/qwen/qwen3-32b \
  --user-llm openrouter/qwen/qwen3-32b \
  --num-trials 1 \
  --num-tasks 1 \
  --max-concurrency 3 \
  --log-level ERROR

python3 generate_excel_report.py
```

## Full 평가(5개 모델 자동 실행)

아래 스크립트가 5개 모델 × 3개 도메인을 순차 실행하고, 실행 후 엑셀 리포트를 갱신합니다.

```bash
cd tau2-bench
export OPENROUTER_API_KEY="YOUR_KEY"
./run_evaluation.sh
```

OpenRouter에서 503/429 같은 일시 오류가 잦으면, 호출 간 딜레이를 줄 수 있습니다(기본 1초).

```bash
cd tau2-bench
export OPENROUTER_API_KEY="YOUR_KEY"
DELAY_SEC=1 ./run_evaluation.sh
```

## 엑셀 리포트(요약)

`tau2-bench/generate_excel_report.py`는 결과 JSON을 읽어 `tau2_evaluation_report.xlsx`를 생성합니다.

- **요약**: 모델 랭킹 + 모델×도메인 Pass^k 매트릭스
- **런**: Run 단위(요청/GT/툴/최종응답/결과/근거). 원본(JSON/툴응답)은 숨김 컬럼을 펼쳐 확인
- **턴**: 턴 단위 원문(디버깅용). ToolCalls/ToolResult는 기본 숨김

## OpenRouter로 평가할 때 자주 겪는 이슈

- **HTTP 503 (No instances available)**: 해당 시점에 provider 쪽 가용 인스턴스가 부족한 상황입니다. 모델 성능 문제가 아니라 **호스팅 수용량 이슈**일 가능성이 큽니다.
  - 대응: 재시도, `--max-concurrency` 감소, 시간대 변경
- **HTTP 422 (요청 포맷 거부)**: 특정 provider 조합에서 tool calling 스키마 검증이 엄격해 요청이 차단될 수 있습니다.
  - 대응: LiteLLM/tau2 최신화, provider/route 변경(가능한 경우), 재시도
- **LiteLLM cost mapping 경고**: 일부 모델은 비용 테이블에 매핑이 없어서 cost 계산이 0이거나 경고가 날 수 있습니다. 평가 자체(성공/실패, Pass^k)와는 별개지만 로그 노이즈가 될 수 있습니다.

## 참고

- 업스트림 공식 문서: `tau2-bench/README.md`
