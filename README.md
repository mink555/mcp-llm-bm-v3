# mcp-llm-bm-v3

이 저장소는 `tau2-bench`(업스트림)를 포함하고, OpenRouter를 통해 5개 LLM 모델을 평가하는 실행/리포트 파이프라인을 제공합니다.

## 구성

- **업스트림 벤치마크 코드**: `tau2-bench/` (원본 README 및 코드 유지)
- **실행 스크립트**: `tau2-bench/run_evaluation.sh`
- **리포트 생성기**: `tau2-bench/generate_excel_report.py`

## TAU2 평가 의도(무엇을 측정하나)

τ²-bench는 “정답 텍스트 한 줄”을 맞히는 벤치마크가 아니라, **고객센터 시나리오에서 에이전트가 정책을 지키며 도구를 사용해 상태(DB)를 올바르게 바꾸고, 사용자에게 필요한 정보를 전달하는지**를 측정합니다. 오케스트레이터가 Agent ↔ UserSimulator ↔ Environment(툴/DB)를 중재하며 여러 턴의 대화를 시뮬레이션합니다(업스트림 `tau2-bench/README.md`의 Orchestration Sequence Diagram 참고).

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

## OpenRouter 설정

OpenRouter는 LiteLLM provider로 호출됩니다.

- **모델 표기 규칙**: `openrouter/<provider>/<model>` 형태
- **API 키 설정(환경변수 권장)**:

```bash
export OPENROUTER_API_KEY="YOUR_KEY"
```

키는 절대 커밋하지 마세요. (업스트림 `tau2-bench/.env.example`은 참고용 템플릿입니다.)

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
