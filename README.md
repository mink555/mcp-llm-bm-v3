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

## 📁 프로젝트 구조

```
mcp-llm-bm-v3/
├── README.md                    ← 이 파일 (프로젝트 가이드)
├── .env                         ← API 키 (gitignore)
│
└── tau2-bench/                  ← 업스트림 벤치마크 코드
    ├── README.md                ← 공식 문서 (영어)
    ├── EXCEL_GUIDE.md           ← 엑셀 보고서 가이드
    │
    ├── run_quick_450.sh         ← ⭐ 450회 평가 스크립트
    ├── run_evaluation.sh        ← Full 평가 스크립트
    │
    ├── generate_excel_report.py ← 엑셀 생성기
    ├── generate_reports.py      ← 리포트 엔트리
    │
    ├── results/latest/          ← 결과 (gitignore)
    │   ├── 전체_요약/
    │   └── 모델별/
    │
    └── src/tau2/                 ← 핵심 코드
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
| **실행 횟수** | 450회 (3 도메인 × 30 태스크 × 5 모델 × 1 trial) |
| **예상 시간** | ~30분 |
| **비용** | OpenRouter 요금 기준 |

### Step 3: 결과 확인

| 파일 | 경로 |
|------|------|
| **전체 요약** | `results/latest/전체_요약/TAU2_전체요약_latest.xlsx` |
| **모델별** | `results/latest/모델별/<모델>/TAU2_<모델>_latest.xlsx` |

---

## 🎯 τ²-bench란?

```
┌─────────────────────────────────────────────────────────────────┐
│                    τ²-bench 평가 철학                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ❌ "정답 텍스트를 맞히는가?"                                   │
│                                                                 │
│   ✅ "에이전트가 정책을 지키며 도구를 사용해                     │
│       DB를 올바르게 변경하고, 사용자에게 정보를 전달하는가?"     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 평가 도메인

| 도메인 | 설명 | 주요 태스크 |
|--------|------|-------------|
| **Retail** | 전자상거래 고객센터 | 주문 조회, 반품, 교환, 결제 변경 |
| **Airline** | 항공 고객센터 | 예약, 변경, 좌석, 마일리지 |
| **Telecom** | 통신 고객센터 | 요금제, 장애, 청구, 개통 |

---

## 📊 평가 지표

### Reward Breakdown (RB) - 점수 구성

| RB 항목 | 평가 내용 | PASS 조건 |
|---------|----------|-----------|
| **RB_DB** | DB 상태가 정답과 같은가? | Hash 일치 |
| **RB_COMMUNICATE** | 필수 정보를 전달했는가? | 모든 GT 값 언급 |
| **RB_ACTION** | 필수 액션을 수행했는가? | 모든 GT Action 매칭 |
| **RB_ENV_ASSERTION** | 환경 조건을 만족하는가? | 모든 Assertion 통과 |

### 최종 점수 계산

```
Reward = RB_DB × RB_COMMUNICATE × RB_ACTION × RB_ENV_ASSERTION
       = (RewardBasis에 포함된 항목들만 곱셈)

PASS: Reward == 1.0
FAIL: Reward < 1.0
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
| **Quick (450회)** | `./run_quick_450.sh` | P@1 중심, 비용 절감 |
| **Full 평가** | `./run_evaluation.sh` | num_trials=4, P@k 전체 |
| **1개 테스트** | `tau2 run --num-tasks 1` | 연결/설정 확인용 |

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NUM_TASKS` | 30 | 도메인당 태스크 수 |
| `NUM_TRIALS` | 1 | 태스크당 반복 수 |
| `MAX_CONCURRENCY` | 3 | 동시 실행 수 |
| `DELAY_SEC` | 1 | 호출 간 딜레이 |
| `FORCE` | 0 | 1이면 기존 결과 삭제 |

---

## 🛠️ 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `HTTP 503` | Provider 가용성 부족 | 재시도, 시간대 변경 |
| `HTTP 422` | Tool calling 스키마 오류 | LiteLLM/tau2 업데이트 |
| `RB_ACTION=0` | 툴 호출 실패 | 툴 args 확인, 포맷 검증 |
| `cost=0` | LiteLLM 매핑 없음 | 무시 (평가에 영향 없음) |

---

## 📚 참고 문서

| 문서 | 위치 | 내용 |
|------|------|------|
| **공식 README** | `tau2-bench/README.md` | 영어 원본, 설치/CLI |
| **엑셀 가이드** | `tau2-bench/EXCEL_GUIDE.md` | 보고서 해석 방법 |
| **도메인 문서** | `tau2-bench/src/tau2/domains/README.md` | 도메인별 상세 |

---

## 📝 코드 실행 경로

```
tau2 run (CLI)
    ↓
src/tau2/cli.py → run_domain()
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

## ✅ 빠른 점검 체크리스트

- [ ] `echo $OPENROUTER_API_KEY` → 키가 출력되는가?
- [ ] `tau2 check-data` → 데이터 경로 정상인가?
- [ ] `tau2 run --num-tasks 1` → 1개 태스크 성공하는가?
- [ ] `results/latest/simulations/*.json` → 결과 파일 생성되는가?

---

<div align="center">

**[📖 공식 문서](tau2-bench/README.md)** · **[📊 엑셀 가이드](tau2-bench/EXCEL_GUIDE.md)** · **[🏆 Leaderboard](https://taubench.com)**

</div>
