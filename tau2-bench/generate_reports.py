#!/usr/bin/env python3
"""
results/ 폴더 아래에
- 전체_요약/ (전체 모델 종합 리포트)
- 모델별/<모델폴더>/ (각 모델 단독 리포트)
구조로 엑셀을 생성한다.
"""

import argparse
from pathlib import Path
from datetime import datetime

from generate_excel_report import generate_report, LLM_TO_LABEL


def sanitize_folder_name(s: str) -> str:
    # 폴더명 안전화: 공백/슬래시/콜론 등 제거
    return (
        s.replace("openrouter/", "")
        .replace("/", "_")
        .replace(":", "_")
        .replace(" ", "_")
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", type=str, default="results", help="결과 폴더 루트(기본: results)")
    ap.add_argument("--input-dir", type=str, default=None, help="시뮬레이션 json 폴더(기본: data/simulations 자동 탐색)")
    ap.add_argument("--timestamp", action="store_true", help="파일명에 타임스탬프를 붙임")
    args = ap.parse_args()

    results_root = Path(args.results_root)
    base_dir = Path(args.input_dir) if args.input_dir else None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S") if args.timestamp else "latest"

    # 1) 전체 요약
    overall_dir = results_root / "전체_요약"
    overall_dir.mkdir(parents=True, exist_ok=True)
    overall_path = overall_dir / f"TAU2_전체요약_{ts}.xlsx"
    generate_report(output_path=overall_path, model_filter=None, base_dir=base_dir)

    # 2) 모델별
    by_model_root = results_root / "모델별"
    by_model_root.mkdir(parents=True, exist_ok=True)
    for llm, label in LLM_TO_LABEL.items():
        folder = by_model_root / sanitize_folder_name(label)
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / f"TAU2_{sanitize_folder_name(label)}_{ts}.xlsx"
        generate_report(output_path=out, model_filter=llm, base_dir=base_dir)

    # 안내 파일
    (results_root / "README.txt").write_text(
        "\n".join(
            [
                "이 폴더는 TAU2-Bench 평가 결과 엑셀을 자동 생성한 산출물입니다.",
                "- 전체_요약/: 전체 모델 종합 리포트",
                "- 모델별/: 모델별 단독 리포트",
                "",
                "엑셀 가독성 팁:",
                "- '런' 시트에서 PASS/FAIL, 도메인, TaskID로 필터링",
                "- tool_calls / tool 결과는 숨김 컬럼을 펼쳐서 확인",
                "",
                f"생성 키워드: {ts}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"[OK] 전체 요약: {overall_path}")
    print(f"[OK] 모델별 폴더: {by_model_root}")


if __name__ == "__main__":
    main()

