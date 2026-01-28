# 📊 TAU2 엑셀 보고서 사용 가이드

## 🎯 결론: 이렇게 보세요!

### 1️⃣ FAIL 케이스를 찾았다면:

**Step 1: RewardBasis (F열) 확인**
```
[DB, COMMUNICATE]       → airline/retail 문제
[ENV_ASSERTION]         → telecom 문제
```

**Step 2-A: airline/retail인 경우**
- ✅ **깨진 Actions (N열)** 확인 → 어떤 툴을 안 불렀는지
- ✅ **DB 불일치 (P열)** 확인 → 불일치면 DB가 다름
- ✅ **MissingTools (L열)** 확인 → 누락된 필수 툴

**Step 2-B: telecom인 경우**
- ✅ **깨진 env_assertions (O열)** 확인 → 어떤 조건 실패
- ✅ **RB_ENV_ASSERTION (T열)** 확인 → 0이면 실패

**Step 3: Model 최종응답 (M열) 읽기**
- 모델이 사용자에게 뭐라고 말했는지 확인

### 2️⃣ GT vs 모델 비교:

| 평가 항목 | GT 컬럼 | 모델 컬럼 | 실패 원인 컬럼 |
|-----------|---------|-----------|----------------|
| **툴 호출** | G (GT Actions) | K (CalledTools) | N (깨진 Actions) |
| **환경 조건** | I (GT env_assertions) | - | O (깨진 env_assertions) |
| **사용자 안내** | J (GT NL Assertions) | M (Model 최종응답) | - |
| **DB 상태** | - | - | P (DB 불일치) |

### 3️⃣ 빠른 디버깅:

```
FAIL → RewardBasis 보기 → 해당 축의 "깨진" 컬럼 확인!

- DB 실패 → 깨진 Actions (N) + DB 불일치 (P)
- ENV 실패 → 깨진 env_assertions (O)
- COMMUNICATE 실패 → Model 최종응답 (M) 확인
```

✅ **모든 정보가 한 행에 있습니다! 스크롤만 하면 됩니다!**

---

## 📋 전체 컬럼 구조

### ✅ 결과 확인
- **A. Result** - PASS/FAIL
- **E. Reward** - 점수 (1.0이면 PASS)

### 📋 무엇이 정답인가 (GT)
- **F. RewardBasis** - 뭘 채점하는가? `[DB, COMMUNICATE]` 또는 `[ENV_ASSERTION]`
- **G. GT Actions (상세)** - 어떤 툴을 호출해야 하는가
- **H. GT 필수툴** - 간단 요약
- **I. GT env_assertions** - 환경 조건 (telecom)
- **J. GT NL Assertions** - 해야 할 행동 (자연어)

### 🤖 모델이 뭘 했는가
- **K. CalledTools** - 실제로 호출한 툴
- **L. MissingTools** - 누락된 툴
- **M. Model 최종응답** - 사용자에게 한 말

### ⚠️ 왜 실패했는가
- **N. 깨진 Actions** - GT Actions 중 안 한 것
- **O. 깨진 env_assertions** - 실패한 환경 조건
- **P. DB 불일치** - Golden DB와 다른가?

### 📊 세부 점수
- **Q. RB_DB** - DB 점수 (0 또는 1)
- **R. RB_COMMUNICATE** - 안내 점수 (0 또는 1)
- **S. RB_ACTION** - 액션 점수 (0 또는 1)
- **T. RB_ENV_ASSERTION** - 환경 점수 (0 또는 1)

---

## 💡 실전 예시

### Airline FAIL 케이스

| 컬럼 | 값 | 의미 |
|------|-----|------|
| **A** | FAIL | 실패 |
| **F** | ["DB", "COMMUNICATE"] | DB와 안내를 채점 |
| **G** | get_user_details(...)<br>cancel_reservation(...) | 이 툴들을 호출해야 함 |
| **K** | get_user_details, transfer_to_human_agents | 실제로 이것만 호출함 |
| **N** | cancel_reservation(...) 불일치 | 취소를 안 했음! |
| **P** | 불일치 | DB가 Golden과 다름 |

**💡 실패 원인**: 취소를 안 해서 DB 불일치!

### Telecom FAIL 케이스

| 컬럼 | 값 | 의미 |
|------|-----|------|
| **A** | FAIL | 실패 |
| **F** | ["ENV_ASSERTION"] | 환경 조건을 채점 |
| **I** | assert_internet_speed(expected_speed=200) | 속도가 200이어야 함 |
| **O** | assert_internet_speed(...) 미충족 | 속도가 200 안 나옴! |
| **T** | 0 | 환경 조건 실패 |

**💡 실패 원인**: 네트워크 속도가 기준 미달!

---

## 🔑 핵심 개념

### DB 불일치 (P열)

**전체 DB를 해시로 비교합니다:**

```
Golden DB (GT Actions 실행 후):
  reservations["Q69X3R"].status = "CANCELLED"
  → Hash: abc123...

모델 DB:
  reservations["Q69X3R"].status = "CONFIRMED"
  → Hash: xyz789...

비교: abc123... != xyz789... → "불일치"
```

**중요**: 필드 하나만 달라도 불일치!

### COMMUNICATE (R열)

**특정 문자열이 응답에 있는가?**

```
GT: communicate_info = ["1628"]

✅ PASS: "You'll receive $1628."
❌ FAIL: "You'll receive a refund." (숫자 없음)
```

### ENV_ASSERTION (T열)

**환경 조건을 만족하는가?**

```
GT: assert_internet_speed(expected_speed=200)

✅ PASS: 실제 속도 >= 200
❌ FAIL: 실제 속도 < 200
```

---

## ⚡ 자주 묻는 질문

### Q: ACTION은 왜 채점 안 하나요?

**A**: 현재 데이터셋은 "How가 아닌 What" 평가
- 어떤 툴을 호출했는지보다 → 최종 결과(DB)만 중요
- 다른 방법으로 같은 결과 만들어도 OK

### Q: 툴을 다르게 호출해도 PASS 가능?

**A**: 가능합니다!
```
GT: get_user(id=123) → cancel(id=456)
모델: find_user(name="John") → cancel(id=456)
→ 최종 DB가 같으면 PASS!
```

### Q: NL Assertions는 채점에 반영?

**A**: 대부분 반영 안 됨
- reward_basis에서 제외됨
- 참고용으로만 사용

---

## 📝 빠른 참조

```
FAIL 발견
    ↓
RewardBasis (F열) 확인
    ↓
┌─────────────────┬─────────────────┐
│ [DB, COMMUNICATE] │ [ENV_ASSERTION]    │
└─────────────────┴─────────────────┘
         ↓                    ↓
  airline/retail         telecom
         ↓                    ↓
   깨진 Actions (N)    깨진 env_assertions (O)
   DB 불일치 (P)        RB_ENV_ASSERTION (T)
   MissingTools (L)
```

✅ **스크롤만 하면 모든 정보를 볼 수 있습니다!** 🚀
