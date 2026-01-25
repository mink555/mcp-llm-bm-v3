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

import json

from generate_excel_report import generate_report, LLM_TO_LABEL


def sanitize_folder_name(s: str) -> str:
    # 폴더명 안전화: 공백/슬래시/콜론 등 제거
    return (
        s.replace("openrouter/", "")
        .replace("/", "_")
        .replace(":", "_")
        .replace(" ", "_")
    )


def detect_llms_in_input_dir(input_dir: Path) -> set[str]:
    llms: set[str] = set()
    for fp in sorted(input_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        info = data.get("info") or {}
        agent_llm = (((info.get("agent_info") or {}).get("llm")) or "").strip()
        if agent_llm:
            llms.add(agent_llm)
    return llms


def prune_old_reports(results_root: Path) -> None:
    """
    results_root 하위에서 *_latest.xlsx를 제외한 TAU2_*.xlsx(타임스탬프 산출물)을 정리.
    - 사용자가 경로 난립을 싫어할 때 기본으로 깔끔하게 유지하기 위한 유틸
    """
    for fp in results_root.rglob("TAU2_*.xlsx"):
        name = fp.name
        if name.endswith("_latest.xlsx"):
            continue
        # 안전: TAU2_ 접두어 + xlsx만 정리
        try:
            fp.unlink()
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", type=str, default="results", help="결과 폴더 루트(기본: results)")
    ap.add_argument("--input-dir", type=str, default=None, help="시뮬레이션 json 폴더(기본: data/simulations 자동 탐색)")
    ap.add_argument("--timestamp", action="store_true", help="추가로 타임스탬프 파일도 생성(기본은 latest만 생성)")
    ap.add_argument(
        "--all-models",
        action="store_true",
        help="입력에 없는 모델도 포함해(빈 리포트라도) 5개 모델 전부 생성",
    )
    ap.add_argument(
        "--prune",
        action="store_true",
        help="results-root 하위의 타임스탬프 엑셀(TAU2_*.xlsx, *_latest.xlsx 제외)을 정리",
    )
    args = ap.parse_args()

    results_root = Path(args.results_root)
    base_dir = Path(args.input_dir) if args.input_dir else None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 기본: 입력 폴더에 실제로 존재하는 모델만 리포트 생성(불필요한 빈 파일 생성 방지)
    models_mapping = dict(LLM_TO_LABEL)
    if base_dir and base_dir.exists() and not args.all_models:
        present = detect_llms_in_input_dir(base_dir)
        models_mapping = {k: v for k, v in models_mapping.items() if k in present}

    # 1) 전체 요약
    overall_dir = results_root / "전체_요약"
    overall_dir.mkdir(parents=True, exist_ok=True)
    overall_latest = overall_dir / "TAU2_전체요약_latest.xlsx"
    generate_report(output_path=overall_latest, model_filter=None, base_dir=base_dir, models_mapping_override=models_mapping)
    if args.timestamp:
        overall_ts = overall_dir / f"TAU2_전체요약_{ts}.xlsx"
        try:
            import shutil
            shutil.copy2(overall_latest, overall_ts)
        except Exception:
            pass

    # 2) 모델별
    by_model_root = results_root / "모델별"
    by_model_root.mkdir(parents=True, exist_ok=True)

    # prune: 이번 입력에 없는 모델 폴더는 제거(누적/잔존 폴더로 인한 혼란 방지)
    if base_dir and base_dir.exists() and not args.all_models:
        keep = {sanitize_folder_name(v) for v in models_mapping.values()}
        for child in by_model_root.iterdir():
            if child.is_dir() and child.name not in keep:
                try:
                    # 파이썬 3.13+ Path.unlink/mkdir만으로는 재귀삭제가 번거로워서 rmtree 사용
                    import shutil

                    shutil.rmtree(child)
                except Exception:
                    pass

    for llm, label in models_mapping.items():
        folder = by_model_root / sanitize_folder_name(label)
        folder.mkdir(parents=True, exist_ok=True)
        out_latest = folder / f"TAU2_{sanitize_folder_name(label)}_latest.xlsx"
        generate_report(output_path=out_latest, model_filter=llm, base_dir=base_dir, models_mapping_override=models_mapping)
        if args.timestamp:
            out_ts = folder / f"TAU2_{sanitize_folder_name(label)}_{ts}.xlsx"
            try:
                import shutil
                shutil.copy2(out_latest, out_ts)
            except Exception:
                pass

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

    if args.prune:
        prune_old_reports(results_root)

    print(f"[OK] 전체 요약(latest): {overall_latest}")
    if args.timestamp:
        print(f"[OK] 전체 요약(timestamp): {overall_dir / f'TAU2_전체요약_{ts}.xlsx'}")
    print(f"[OK] 모델별 폴더: {by_model_root}")


if __name__ == "__main__":
    main()

