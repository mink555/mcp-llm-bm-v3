# 📊 TAU2 엑셀 보고서 사용 가이드

## 🎯 결론: 이렇게 보세요!

### 1️⃣ FAIL 케이스를 찾았다면:

**Step 1: RewardBasis (F열) 확인**
```
[DB, COMMUNICATE]       → airline/retail 문제
[ENV_ASSERTION]         → telecom 문제
```

**Step 2-A: airline/retail인 경우**
- ✅ **DB 매칭 상세 (P열)** 확인 → ✅/❌ 표시로 DB 일치 여부
- ✅ **ACTION 매칭 상세 (Q열)** 확인 → 각 GT Action별 ✅/❌
- ✅ **깨진 Actions (S열)** 확인 → 어떤 툴을 안 불렀는지
- ✅ **MissingTools (M열)** 확인 → 누락된 필수 툴

**Step 2-B: telecom인 경우**
- ✅ **ENV_ASSERTION 매칭 상세 (R열)** 확인 → 각 assertion별 ✅/❌
- ✅ **깨진 env_assertions (T열)** 확인 → 어떤 조건 실패
- ✅ **RB_ENV_ASSERTION (Y열)** 확인 → 0이면 실패

**Step 3: Model 최종응답 (N열) 읽기**
- 모델이 사용자에게 뭐라고 말했는지 확인

### 2️⃣ GT vs 모델 비교 (tau2 철학):

| 평가 항목 | GT 컬럼 | 증거/상세 컬럼 | 결과 컬럼 | PASS 조건 |
|-----------|---------|----------------|-----------|-----------|
| **COMMUNICATE** | K (GT Communicate) | O (관련 응답) | W (RB_COMMUNICATE) | 모든 GT 값이 응답에 있음 |
| **DB** | (암시적: GT Actions 실행 후) | P (DB 매칭 상세) | V (RB_DB) | ✅ DB 일치 |
| **ACTION** | G (GT Actions) | Q (ACTION 매칭 상세) | X (RB_ACTION) | 모든 action이 ✅ |
| **ENV_ASSERTION** | I (GT env_assertions) | R (ENV 매칭 상세) | Y (RB_ENV_ASSERTION) | 모든 assertion이 ✅ |

### 3️⃣ 빠른 디버깅:

```
FAIL → RewardBasis 보기 → 해당 축의 "매칭 상세" 컬럼 확인!

- DB 실패 → P열 (DB 매칭 상세) 확인
- ACTION 실패 → Q열 (ACTION 매칭 상세) 확인  
- ENV 실패 → R열 (ENV_ASSERTION 매칭 상세) 확인
- COMMUNICATE 실패 → K열과 O열 비교
```

✅ **모든 정보가 한 행에 있습니다! 스크롤만 하면 됩니다!**

---

## 📋 전체 컬럼 구조 (2026-01 최신)

### 1️⃣ 결과/식별 (A~E)
| 컬럼 | 이름 | 설명 |
|------|------|------|
| **A** | Result | PASS/FAIL |
| **B** | Model | 모델 라벨 |
| **C** | Domain | 도메인 (retail/airline/telecom) |
| **D** | TaskIdx | 태스크셋 내 순번 |
| **E** | Reward | 점수 (1.0이면 PASS) |

### 2️⃣ 정답(GT) - 무엇이 정답인가 (F~K)
| 컬럼 | 이름 | 설명 |
|------|------|------|
| **F** | RewardBasis | 뭘 채점하는가? `[DB, COMMUNICATE]` 또는 `[ENV_ASSERTION]` |
| **G** | GT Actions (상세) | 어떤 툴을 호출해야 하는가 (정답 레시피) |
| **H** | GT 필수툴 | 간단 요약 (툴 이름만) |
| **I** | GT env_assertions | 환경 조건 (telecom) |
| **J** | GT NL Assertions | 해야 할 행동 (자연어, 참고용) |
| **K** | GT Communicate | 모델이 반드시 말해야 하는 값들 |

### 3️⃣ 모델 행동 - 모델이 뭘 했는가 (L~O)
| 컬럼 | 이름 | 설명 |
|------|------|------|
| **L** | CalledTools | 실제로 호출한 툴 목록 |
| **M** | MissingTools | 누락된 필수 툴 |
| **N** | Model 최종응답 | 사용자에게 한 마지막 말 |
| **O** | COMMUNICATE 관련 응답 | GT Communicate 값이 포함된 메시지 (`[포함: 'val']` 형식) |

### 4️⃣ 평가 상세 - GT vs 모델 매칭 결과 (P~R) ⭐NEW
| 컬럼 | 이름 | 설명 |
|------|------|------|
| **P** | DB 매칭 상세 | ✅ DB 일치 / ❌ DB 불일치 |
| **Q** | ACTION 매칭 상세 | 각 GT Action별 ✅/❌ 표시 |
| **R** | ENV_ASSERTION 매칭 상세 | 각 assertion별 ✅/❌ 표시 |

### 5️⃣ 실패 원인 요약 (S~U)
| 컬럼 | 이름 | 설명 |
|------|------|------|
| **S** | 깨진 Actions | GT Actions 중 매칭 안 된 것 |
| **T** | 깨진 env_assertions | 실패한 환경 조건 목록 |
| **U** | DB 불일치 | Golden DB와 다른가? (일치/불일치/N/A) |

### 6️⃣ 세부 점수 (V~Y)
| 컬럼 | 이름 | 설명 |
|------|------|------|
| **V** | RB_DB | DB 점수 (0 또는 1) |
| **W** | RB_COMMUNICATE | 안내 점수 (0 또는 1) |
| **X** | RB_ACTION | 액션 점수 (0 또는 1) |
| **Y** | RB_ENV_ASSERTION | 환경 점수 (0 또는 1) |

### 7️⃣ 종료 (Z)
| 컬럼 | 이름 | 설명 |
|------|------|------|
| **Z** | Termination | 종료 사유 (user_stop, max_turns 등) |

---

## 🔑 tau2 평가 철학 (핵심!)

### COMMUNICATE 평가
```
GT Communicate (K열): ['327', '1000', '44']
           ↓
전체 대화에서 검색 (substring 매칭, 대소문자 무시, 쉼표 제거)
           ↓
COMMUNICATE 관련 응답 (O열): [포함: '327', '1000'] ...
           ↓
모든 값이 있으면 → RB_COMMUNICATE (W열) = 1 (PASS)
하나라도 없으면 → RB_COMMUNICATE (W열) = 0 (FAIL)
```

### DB 평가
```
GT Actions (G열) 실행 → Golden DB Hash 생성
모델 tool_calls 실행 → Predicted DB Hash 생성
           ↓
두 Hash 비교 (agent_db + user_db 둘 다)
           ↓
일치 → DB 매칭 상세 (P열) = "✅ DB 일치", RB_DB (V열) = 1
불일치 → DB 매칭 상세 (P열) = "❌ DB 불일치", RB_DB (V열) = 0
```

### ACTION 평가
```
GT Actions (G열): [get_user_details(...), cancel_reservation(...)]
           ↓
모델 tool_calls와 비교
           ↓
ACTION 매칭 상세 (Q열):
  ✅ get_user_details(user_id=xxx)
  ❌ cancel_reservation(id=yyy)
           ↓
모든 action이 ✅ → RB_ACTION (X열) = 1 (PASS)
하나라도 ❌ → RB_ACTION (X열) = 0 (FAIL)
```

### ENV_ASSERTION 평가
```
GT env_assertions (I열): [assert_mobile_data_status(...), assert_internet_speed(...)]
           ↓
Predicted Environment에서 각 assertion 실행
           ↓
ENV_ASSERTION 매칭 상세 (R열):
  ✅ assert_mobile_data_status(expected_status=True)
  ❌ assert_internet_speed(expected_speed=200)
           ↓
모든 assertion이 ✅ → RB_ENV_ASSERTION (Y열) = 1 (PASS)
하나라도 ❌ → RB_ENV_ASSERTION (Y열) = 0 (FAIL)
```

---

## 💡 실전 예시

### Airline FAIL 케이스

| 컬럼 | 값 | 의미 |
|------|-----|------|
| **A** | FAIL | 실패 |
| **F** | ["DB", "COMMUNICATE"] | DB와 안내를 채점 |
| **G** | get_user_details(...)<br>cancel_reservation(...) | 이 툴들을 호출해야 함 |
| **L** | get_user_details, transfer_to_human_agents | 실제로 이것만 호출함 |
| **P** | ❌ DB 불일치 | DB가 Golden과 다름 |
| **Q** | ✅ get_user_details(...)<br>❌ cancel_reservation(...) | 취소를 안 했음! |

**💡 실패 원인**: cancel_reservation을 안 해서 DB 불일치!

### Telecom FAIL 케이스

| 컬럼 | 값 | 의미 |
|------|-----|------|
| **A** | FAIL | 실패 |
| **F** | ["ENV_ASSERTION"] | 환경 조건을 채점 |
| **I** | assert_internet_speed(expected_speed=200) | 속도가 200이어야 함 |
| **R** | ✅ assert_mobile_data_status(...)<br>❌ assert_internet_speed(...) | 속도 미달! |
| **Y** | 0 | 환경 조건 실패 |

**💡 실패 원인**: 네트워크 속도가 기준 미달!

---

## ⚡ 자주 묻는 질문

### Q: GT Communicate가 null인데 RB_COMMUNICATE=1인 이유?

**A**: tau2 철학 - "정답이 없으면 틀릴 수 없다"
```python
if not communicate_info:  # null이거나 빈 리스트
    return reward=1.0  # 자동 PASS
```
→ 평가할 GT가 없으므로 자동 통과!

### Q: ACTION은 왜 채점 안 하나요?

**A**: 현재 데이터셋은 "How가 아닌 What" 평가
- 어떤 툴을 호출했는지보다 → 최종 결과(DB)만 중요
- RewardBasis에 ACTION이 없으면 채점 안 됨

### Q: 다른 툴로 같은 결과 만들어도 PASS?

**A**: 가능합니다!
```
GT: get_user(id=123) → cancel(id=456)
모델: find_user(name="John") → cancel(id=456)
→ 최종 DB Hash가 같으면 PASS!
```

---

## 📝 빠른 참조

```
FAIL 발견
    ↓
RewardBasis (F열) 확인
    ↓
┌─────────────────────┬─────────────────────┐
│ [DB, COMMUNICATE]   │ [ENV_ASSERTION]     │
└─────────────────────┴─────────────────────┘
         ↓                      ↓
   airline/retail            telecom
         ↓                      ↓
   P열: DB 매칭 상세       R열: ENV 매칭 상세
   Q열: ACTION 매칭 상세   Y열: RB_ENV_ASSERTION
   V열: RB_DB
   W열: RB_COMMUNICATE
```

✅ **매칭 상세 컬럼(P/Q/R)을 보면 왜 실패했는지 한눈에 알 수 있습니다!** 🚀
