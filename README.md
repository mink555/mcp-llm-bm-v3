# 🚀 mcp-llm-bm-v3

> **τ²-bench 기반 LLM 에이전트 벤치마크** - OpenRouter를 통한 5개 모델 평가 파이프라인

---

## 📋 TL;DR (3분 요약)

```
1. API 키 설정     →  cp .env.example .env && 키 입력
2. 450회 평가 실행  →  cd tau2-bench && ./run_quick_450.sh
3. 결과 확인       →  results/latest/전체_요약/TAU2_전체요약_latest.xlsx
```

---

## 🎯 τ²-bench란?

### 벤치마크 유형

| 특성 | 해당 | 설명 |
|------|:----:|------|
| **Multi-Turn Conversation** | ✅ | 평균 **19턴**/대화 |
| **Tool-Use / Function Calling** | ✅ | 평균 **6회**/대화 tool 호출 |
| **Task-Oriented Dialogue** | ✅ | 고객센터 과업 수행 |
| **3-Party Conversation** | ✅ | Agent ↔ User ↔ Tool |
| **Simulated User** | ✅ | LLM이 User 역할 수행 |
| Single-Turn QA | ❌ | 단일 턴 아님 |
| Text Generation Only | ❌ | 도구 사용이 핵심 |

### 핵심 철학

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ❌ "정답 텍스트를 맞히는가?"                                       │
│                                                                     │
│   ✅ "에이전트가 도구를 사용해 DB를 변경하고 과업을 완수하는가?"      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3자 대화 구조

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Agent     │◀─────▶│    User     │       │    Tool     │
│   (LLM)     │       │ (Simulator) │       │    (API)    │
└──────┬──────┘       └─────────────┘       └──────▲──────┘
       │                                           │
       │            tool_call 요청                 │
       └───────────────────────────────────────────┘
```

| 참여자 | 역할 | 구현 |
|--------|------|------|
| **Agent** | 고객센터 상담원 | 평가 대상 LLM |
| **User** | 고객 (시뮬레이션) | User Simulator LLM |
| **Tool** | API/DB | Environment (Python) |

### 대화 흐름 예시

```
Turn 1  🤖 Agent  : "안녕하세요, 무엇을 도와드릴까요?"
        ↓
Turn 2  👤 User   : "주문 W2378156 반품하고 싶어요"
        ↓
Turn 3  🤖 Agent  : [TOOL_CALL: get_order_details]
        ↓
Turn 4  🔧 Tool   : {order_id: "#W2378156", status: "delivered"}
        ↓
Turn 5  🤖 Agent  : [TOOL_CALL: process_return]
        ↓
Turn 6  🔧 Tool   : {success: true, refund: 150.00}
        ↓
Turn 7  🤖 Agent  : "반품 완료! $150 환불됩니다."
        ↓
Turn 8  👤 User   : "감사합니다!" → [STOP]
```

### 대화 통계 (실제 데이터)

| 항목 | 평균값 |
|------|--------|
| 총 턴 수 | **19.4** 턴/대화 |
| User 발화 | **4.6** 회/대화 |
| Assistant 발화 | **8.3** 회/대화 |
| Tool Call | **6.2** 회/대화 |

### 다른 벤치마크와 비교

| 벤치마크 | 턴 | Tool | User Sim | 평가 대상 |
|----------|:--:|:----:|:--------:|-----------|
| **τ²-bench** | **Multi** | **✅** | **✅** | **Agent 행동** |
| MMLU | Single | ❌ | ❌ | 지식 |
| HumanEval | Single | ❌ | ❌ | 코드 생성 |
| MT-Bench | Multi | ❌ | ❌ | 대화 품질 |
| ToolBench | Multi | ✅ | ❌ | 도구 사용 |

---

## 📁 프로젝트 구조

```
mcp-llm-bm-v3/
├── README.md                    ← 이 파일
├── .env                         ← API 키 (gitignore)
│
└── tau2-bench/                  ← 업스트림 벤치마크
    ├── README.md                ← 공식 문서 (영어)
    ├── EXCEL_GUIDE.md           ← 엑셀 보고서 가이드
    │
    ├── run_quick_450.sh         ← ⭐ 450회 평가 스크립트
    ├── generate_excel_report.py ← 엑셀 생성기
    │
    └── results/latest/          ← 결과 (gitignore)
        ├── 전체_요약/
        └── 모델별/
```

---

## ⚡ 빠른 시작

### Step 1: API 키 설정

```bash
cp .env.example .env
# .env 파일 열고 OPENROUTER_API_KEY 입력
```

### Step 2: 450회 Quick 평가

```bash
cd tau2-bench
./run_quick_450.sh
```

| 항목 | 값 |
|------|-----|
| 실행 횟수 | 450회 (3 도메인 × 30 태스크 × 5 모델) |
| 예상 시간 | ~30분 |

### Step 3: 결과 확인

| 파일 | 경로 |
|------|------|
| 전체 요약 | `results/latest/전체_요약/TAU2_전체요약_latest.xlsx` |
| 모델별 | `results/latest/모델별/<모델>/TAU2_<모델>_latest.xlsx` |

---

## 📊 평가 도메인

| 도메인 | 설명 | 주요 태스크 |
|--------|------|-------------|
| **Retail** | 전자상거래 고객센터 | 주문 조회, 반품, 교환 |
| **Airline** | 항공 고객센터 | 예약, 변경, 좌석 |
| **Telecom** | 통신 고객센터 | 요금제, 장애, 청구 |

---

## 📈 평가 지표 (Reward Breakdown)

| RB 항목 | 평가 내용 | PASS 조건 |
|---------|----------|-----------|
| **RB_DB** | DB 상태가 정답과 같은가? | Hash 일치 |
| **RB_COMMUNICATE** | 필수 정보를 전달했는가? | 모든 GT 값 언급 |
| **RB_ACTION** | 필수 액션을 수행했는가? | 모든 GT Action 매칭 |
| **RB_ENV_ASSERTION** | 환경 조건을 만족하는가? | 모든 Assertion 통과 |

### 점수 계산

```
Reward = RB_DB × RB_COMMUNICATE × RB_ACTION × RB_ENV_ASSERTION
PASS: Reward == 1.0  |  FAIL: Reward < 1.0
```

---

## 🔧 평가 대상 모델 (5개)

| # | 모델 | Provider |
|---|------|----------|
| 1 | `llama-3.3-70b-instruct` | Meta |
| 2 | `mistral-small-3.2-24b-instruct` | Mistral |
| 3 | `qwen3-32b` | Qwen |
| 4 | `qwen3-14b` | Qwen |
| 5 | `qwen3-next-80b-a3b-instruct` | Qwen |

---

## 📈 실행 옵션

| 목적 | 명령어 | 설명 |
|------|--------|------|
| Quick (450회) | `./run_quick_450.sh` | P@1 중심 |
| Full 평가 | `./run_evaluation.sh` | P@k 전체 |
| 1개 테스트 | `tau2 run --num-tasks 1` | 연결 확인 |

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NUM_TASKS` | 30 | 도메인당 태스크 수 |
| `NUM_TRIALS` | 1 | 태스크당 반복 수 |
| `MAX_CONCURRENCY` | 3 | 동시 실행 수 |
| `FORCE` | 0 | 1이면 기존 결과 삭제 |

---

## 🛠️ 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| HTTP 503 | Provider 가용성 | 재시도, 시간대 변경 |
| HTTP 422 | Tool schema 오류 | LiteLLM 업데이트 |
| RB_ACTION=0 | 툴 호출 실패 | 툴 args 확인 |

---

## 📝 코드 실행 경로

```
tau2 run (CLI)
    ↓
src/tau2/run.py → Orchestrator.run()
    ↓
┌─────────────────────────────────────────┐
│           Orchestrator                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  Agent  │←→│  User   │←→│   Env   │ │
│  │  (LLM)  │  │  (LLM)  │  │ (Tools) │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────┘
    ↓
src/tau2/utils/llm_utils.py → litellm.completion()
    ↓
OpenRouter API
```

---

## ✅ 빠른 점검

- [ ] `echo $OPENROUTER_API_KEY` → 키 출력 확인
- [ ] `tau2 check-data` → 데이터 경로 확인
- [ ] `tau2 run --num-tasks 1` → 1개 태스크 성공

---

## 📚 참고 문서

| 문서 | 위치 | 내용 |
|------|------|------|
| 공식 README | `tau2-bench/README.md` | 설치/CLI |
| 엑셀 가이드 | `tau2-bench/EXCEL_GUIDE.md` | 보고서 해석 |

---

<div align="center">

**[📖 공식 문서](tau2-bench/README.md)** · **[📊 엑셀 가이드](tau2-bench/EXCEL_GUIDE.md)** · **[🏆 Leaderboard](https://taubench.com)**

</div>
