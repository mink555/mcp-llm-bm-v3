#!/usr/bin/env python3
"""
TAU2-Bench Evaluation Report Generator
Uses actual TAU2 Pass^k metrics with Excel formulas for all calculations.
"""
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import math
import subprocess
import platform

try:
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"])
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

def setup_styles():
    """가독성 중심(최소 색상, 엑셀 기본 톤) 스타일."""
    grid = "D9D9D9"
    header_fill = "F2F2F2"
    header_fill2 = "E7E6E6"
    pass_fill = "E2F0D9"   # 연한 초록
    fail_fill = "FCE4D6"   # 연한 빨강/주황
    return {
        'title': {
            'font': Font(bold=True, size=14, name="Malgun Gothic"),
            'align': Alignment(horizontal="center", vertical="center")
        },
        'section': {
            'font': Font(bold=True, size=12, name="Malgun Gothic", color="1F4E79"),
            'align': Alignment(horizontal="left", vertical="center")
        },
        'header': {
            'fill': PatternFill(start_color=header_fill, end_color=header_fill, fill_type="solid"),
            'font': Font(bold=True, size=10, name="Malgun Gothic"),
            'align': Alignment(horizontal="center", vertical="center", wrap_text=True),
            'border': Border(
                left=Side(style='thin', color=grid),
                right=Side(style='thin', color=grid),
                top=Side(style='thin', color=grid),
                bottom=Side(style='thin', color=grid)
            ),
        },
        'header2': {
            'fill': PatternFill(start_color=header_fill2, end_color=header_fill2, fill_type="solid"),
            'font': Font(bold=True, size=10, name="Malgun Gothic"),
            'align': Alignment(horizontal="center", vertical="center", wrap_text=True),
            'border': Border(
                left=Side(style='thin', color=grid),
                right=Side(style='thin', color=grid),
                top=Side(style='thin', color=grid),
                bottom=Side(style='thin', color=grid)
            ),
        },
        'data': {
            'font': Font(size=9, name="Malgun Gothic"),
            'align': Alignment(horizontal="left", vertical="top", wrap_text=True),
            'border': Border(
                left=Side(style='thin', color=grid),
                right=Side(style='thin', color=grid),
                top=Side(style='thin', color=grid),
                bottom=Side(style='thin', color=grid)
            )
        },
        'data_center': {
            'font': Font(size=9, name="Malgun Gothic"),
            'align': Alignment(horizontal="center", vertical="center"),
            'border': Border(
                left=Side(style='thin', color=grid),
                right=Side(style='thin', color=grid),
                top=Side(style='thin', color=grid),
                bottom=Side(style='thin', color=grid)
            )
        },
        'pass': {
            'fill': PatternFill(start_color=pass_fill, end_color=pass_fill, fill_type="solid"),
            'font': Font(size=9, name="Malgun Gothic", color="006100")
        },
        'fail': {
            'fill': PatternFill(start_color=fail_fill, end_color=fail_fill, fill_type="solid"),
            'font': Font(size=9, name="Malgun Gothic", color="9C0006")
        }
    }

def create_runs_raw_sheet(wb, runs, styles):
    """런 단위 원본 데이터(요청/GT/모델응답 포함). 모든 집계는 이 시트를 기반으로 파생."""
    ws = wb.create_sheet("런_원본", 0)
    
    # Headers
    headers = [
        "RunID",
        "모델",
        "LLM(Agent)",
        "도메인",
        "도메인 설명",
        "TaskID",
        "Trial",
        "결과",
        "성공(0/1)",
        "Reward",
        "RewardBreakdown(JSON)",
        "종료사유",
        "툴호출수",
        "툴목록(요약)",
        "툴호출(JSON 원본)",
        "툴응답(원본)",
        "요청(원본)",
        "GT(원본/필수액션)",
        "모델 최종응답(원본)",
    ]
    ws.append(headers)
    
    for col_idx, cell in enumerate(ws[1], 1):
        cell.font = styles['header']['font']
        cell.fill = styles['header']['fill']
        cell.alignment = styles['header']['align']
        cell.border = styles['header']['border']
    
    # Add all run data
    for run in runs:
        row_idx = ws.max_row + 1
        ws.append(
            [
                run["RunID"],
                run["ModelLabel"],
                run["AgentLLM"],
                run["Domain"],
                None,  # 도메인 설명(수식)
                run["TaskID"],
                run["Trial"],
                None,  # 결과(수식)
                run["Pass"],
                run["Reward"],
                run.get("RewardBreakdownJSON", ""),
                run.get("Termination", "N/A"),
                run.get("ToolCallCount", 0),
                run.get("ToolNames", ""),
                run.get("ToolCallsRaw", ""),
                run.get("ToolResultsRaw", ""),
                run.get("UserRequestRaw", ""),
                run.get("GTRaw", ""),
                run.get("AgentFinalRaw", ""),
            ]
        )
        # 도메인 설명 수식
        ws.cell(row=row_idx, column=5).value = f'=IFERROR(VLOOKUP(D{row_idx},도메인_설명!$A:$C,3,FALSE),"")'
        # 결과(PASS/FAIL)는 엑셀 수식으로
        ws.cell(row=row_idx, column=8).value = f'=IF(I{row_idx}=1,"PASS","FAIL")'
    
    # Style data rows
    for row_idx in range(2, ws.max_row + 1):
        # PASS/FAIL만 아주 옅게 강조 (결과 컬럼)
        result_cell = ws.cell(row=row_idx, column=8)
        pass_flag = ws.cell(row=row_idx, column=9).value
        if pass_flag == 1:
            result_cell.fill = styles["pass"]["fill"]
            result_cell.font = styles["pass"]["font"]
        else:
            result_cell.fill = styles["fail"]["fill"]
            result_cell.font = styles["fail"]["font"]

        for col_idx in range(1, 20):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = styles['data']['border']
            if col_idx in [6, 7, 9, 10, 13]:
                cell.alignment = styles['data_center']['align']
            elif col_idx == 8:
                cell.alignment = styles['data_center']['align']
            else:
                cell.alignment = styles['data']['align']
            
            if col_idx == 10:  # Reward column
                cell.number_format = '0.0000'
    
    # Freeze header and add filters
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    
    # Column widths
    ws.column_dimensions['A'].width = 34  # RunID
    ws.column_dimensions['B'].width = 28  # 모델
    ws.column_dimensions['C'].width = 28  # LLM
    ws.column_dimensions['D'].width = 10  # 도메인
    ws.column_dimensions['E'].width = 24  # 도메인 설명
    ws.column_dimensions['F'].width = 8   # TaskID
    ws.column_dimensions['G'].width = 6   # Trial
    ws.column_dimensions['H'].width = 8   # 결과
    ws.column_dimensions['I'].width = 9   # 성공
    ws.column_dimensions['J'].width = 9   # Reward
    ws.column_dimensions['K'].width = 28  # reward breakdown
    ws.column_dimensions['L'].width = 14  # 종료
    ws.column_dimensions['M'].width = 8   # tool count
    ws.column_dimensions['N'].width = 22  # tool names
    ws.column_dimensions['O'].width = 44  # tool calls raw
    ws.column_dimensions['P'].width = 44  # tool results raw
    ws.column_dimensions['Q'].width = 48  # request raw
    ws.column_dimensions['R'].width = 48  # GT raw
    ws.column_dimensions['S'].width = 48  # agent final

    # 보기 좋은 행높이
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = 60

def create_task_summary_sheet(wb, all_logs, models_mapping, domains, styles):
    """Create task-level summary with Pass^k calculations using Excel formulas."""
    ws = wb.create_sheet("Task별_집계", 1)
    
    # Title
    ws.append(["Task별 성공률 집계 (Pass^k 계산용)"])
    ws.merge_cells('A1:H1')
    ws['A1'].font = styles['title']['font']
    ws['A1'].alignment = styles['title']['align']
    ws.row_dimensions[1].height = 25
    
    ws.append([""])
    ws.append(["이 시트는 각 Task의 시행별 성공 횟수를 집계하여 Pass^k 메트릭을 계산합니다."])
    ws.merge_cells('A3:H3')
    ws.append(["Pass^k = COMBIN(성공횟수, k) / COMBIN(총시행횟수, k)"])
    ws.merge_cells('A4:H4')
    ws.append([""])
    
    # Headers (총시행/성공횟수 모두 런_원본 기반 수식)
    headers = ["모델", "도메인", "도메인 설명", "TaskID", "총시행", "성공횟수", "Pass@1", "Pass@2", "Pass@4"]
    ws.append(headers)
    header_row = ws.max_row
    
    for col_idx, cell in enumerate(ws[header_row], 1):
        cell.font = styles['header']['font']
        cell.fill = styles['header']['fill']
        cell.alignment = styles['header']['align']
        cell.border = styles['header']['border']
    
    # Group data by Model, Domain, TaskID (행 생성용 키만 파이썬으로 추출)
    task_groups = {}
    for log in all_logs:
        key = (log['Model'], log['Domain'], str(log['TaskID']))
        if key not in task_groups:
            task_groups[key] = []
        task_groups[key].append(log)
    
    # Add data rows
    for (model, domain, task_id), logs in sorted(task_groups.items()):
        row_num = ws.max_row + 1
        ws.append([model, domain, None, task_id, None, None, None, None, None])

        # 도메인 설명(도메인_설명 시트 참조)
        ws.cell(row=row_num, column=3).value = f'=IFERROR(VLOOKUP(B{row_num},도메인_설명!$A:$C,3,FALSE),"")'

        # 총시행/성공횟수: 런 시트 기반 (외부/연결 오탐 방지)
        # 런: B 모델, C 도메인, D TaskID, F 결과(PASS/FAIL)
        ws.cell(row=row_num, column=5).value = f'=COUNTIFS(런!$B:$B,$A{row_num},런!$C:$C,$B{row_num},런!$D:$D,$D{row_num})'
        ws.cell(row=row_num, column=6).value = f'=COUNTIFS(런!$B:$B,$A{row_num},런!$C:$C,$B{row_num},런!$D:$D,$D{row_num},런!$F:$F,\"PASS\")'
        
        # Pass@1 formula: COMBIN(E, 1) / COMBIN(D, 1) = E / D
        ws.cell(row=row_num, column=7).value = f"=IFERROR(F{row_num}/E{row_num}, 0)"
        ws.cell(row=row_num, column=7).number_format = '0.0%'
        
        # Pass@2 formula: COMBIN(E, 2) / COMBIN(D, 2)
        ws.cell(row=row_num, column=8).value = f"=IFERROR(COMBIN(F{row_num},2)/COMBIN(E{row_num},2), 0)"
        ws.cell(row=row_num, column=8).number_format = '0.0%'
        
        # Pass@4 formula: COMBIN(E, 4) / COMBIN(D, 4)
        ws.cell(row=row_num, column=9).value = f"=IFERROR(COMBIN(F{row_num},4)/COMBIN(E{row_num},4), 0)"
        ws.cell(row=row_num, column=9).number_format = '0.0%'
        
        # Apply styles
        for col_idx in range(1, 10):
            cell = ws.cell(row=row_num, column=col_idx)
            cell.border = styles['data']['border']
            if col_idx in [4, 5, 6]:
                cell.alignment = styles['data_center']['align']
            elif col_idx >= 7:
                cell.alignment = styles['data_center']['align']
            else:
                cell.alignment = styles['data']['align']
    
    # Freeze header and add filters
    ws.freeze_panes = f"A{header_row+1}"
    ws.auto_filter.ref = f"A{header_row}:I{ws.max_row}"
    
    # Column widths
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 28
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 10
    for col in ['G', 'H', 'I']:
        ws.column_dimensions[col].width = 12

def create_summary_sheet(wb, models_mapping, domains, styles):
    """요약 시트: Overall 랭킹 + 도메인별 Pass^k 매트릭스를 한 시트에 섹션으로 구성."""
    ws = wb.create_sheet("요약", 0)
    
    # Title
    ws.append(["TAU2-Bench 평가 요약"])
    ws.merge_cells('A1:O1')
    ws['A1'].font = styles['title']['font']
    ws['A1'].alignment = styles['title']['align']
    ws.row_dimensions[1].height = 25
    
    ws.append([""])
    
    # Description
    desc = "Pass^k = COMBIN(성공횟수, k) / COMBIN(총시행횟수, k) 의 Task 평균. 성공 기준: Reward가 1.0(±1e-6)에 해당."
    ws.append([desc])
    ws.merge_cells('A3:O3')
    ws['A3'].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[3].height = 30
    
    ws.append([""])
    
    # Section title
    ws.append(["Overall Pass^k 랭킹 (전 도메인 평균)"])
    ws.merge_cells('A5:F5')
    ws['A5'].font = styles['section']['font']
    ws.row_dimensions[5].height = 20
    
    # Headers
    headers = ["순위", "모델", "Pass@1", "Pass@2", "Pass@4", "RankKey(hidden)"]
    ws.append(headers)
    header_row = ws.max_row
    
    for col_idx, cell in enumerate(ws[header_row], 1):
        cell.font = styles['header']['font']
        cell.fill = styles['header']['fill']
        cell.alignment = styles['header']['align']
        cell.border = styles['header']['border']
    
    # Data rows with formulas (정렬은 엑셀에서 수행. 순위는 RANK 계열 대신 COUNTIF로 호환성 확보)
    first_data_row = ws.max_row + 1
    for _, (model_key, model_name) in enumerate(models_mapping.items(), 1):
        row_num = ws.max_row + 1
        ws.append([None, model_name, None, None, None, None])
        
        # Pass@1: Average of Pass@1 for this model from Task별_집계
        ws.cell(row=row_num, column=3).value = f'=IFERROR(AVERAGEIF(Task별_집계!A:A, B{row_num}, Task별_집계!F:F),0)'
        ws.cell(row=row_num, column=3).number_format = '0.00%'
        
        # Pass@2: Average of Pass@2 for this model
        ws.cell(row=row_num, column=4).value = f'=IFERROR(AVERAGEIF(Task별_집계!A:A, B{row_num}, Task별_집계!G:G),0)'
        ws.cell(row=row_num, column=4).number_format = '0.00%'
        
        # Pass@4: Average of Pass@4 for this model
        ws.cell(row=row_num, column=5).value = f'=IFERROR(AVERAGEIF(Task별_집계!A:A, B{row_num}, Task별_집계!H:H),0)'
        ws.cell(row=row_num, column=5).number_format = '0.00%'
        # RankKey: Pass@1 > Pass@2 > Pass@4 우선, 동점은 행번호로 안정화
        ws.cell(row=row_num, column=6).value = f"=C{row_num}*1000000 + D{row_num}*1000 + E{row_num} + ROW()/1000000000"

        # Apply styles (이 행 전체)
        for col_idx in range(1, 6 + 1):
            cell = ws.cell(row=row_num, column=col_idx)
            cell.border = styles['data']['border']
            if col_idx == 1 or col_idx >= 3:
                cell.alignment = styles['data_center']['align']
            else:
                cell.alignment = styles['data']['align']

    last_data_row = ws.max_row
    # 순위 수식 입력
    for r in range(first_data_row, last_data_row + 1):
        ws.cell(row=r, column=1).value = f"=1+COUNTIF($F${first_data_row}:$F${last_data_row},\">\"&F{r})"
        ws.cell(row=r, column=1).alignment = styles["data_center"]["align"]

    # RankKey 컬럼 숨김
    ws.column_dimensions["F"].hidden = True
    
    # Column widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14

    # ===== Domain matrix section =====
    ws.append([""])
    ws.append(["모델 × 도메인 Pass^k 매트릭스"])
    matrix_title_row = ws.max_row
    ws.merge_cells(f"A{matrix_title_row}:O{matrix_title_row}")
    ws.cell(row=matrix_title_row, column=1).font = styles["section"]["font"]

    ws.append([f"평가 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ts_row = ws.max_row
    ws.merge_cells(f"A{ts_row}:O{ts_row}")

    ws.append(["각 도메인별 Pass^k 값(= 각 Task의 Pass^k 평균)."])
    desc_row = ws.max_row
    ws.merge_cells(f"A{desc_row}:O{desc_row}")

    ws.append([""])
    header_row_1 = ["도메인"]
    for model_name in models_mapping.values():
        header_row_1.extend([model_name, "", ""])
    ws.append(header_row_1)
    h1 = ws.max_row
    header_row_2 = [""]
    for _ in models_mapping.values():
        header_row_2.extend(["P@1", "P@2", "P@4"])
    ws.append(header_row_2)
    h2 = ws.max_row

    # merge + style headers
    ws.merge_cells(start_row=h1, start_column=1, end_row=h2, end_column=1)
    for rr in [h1, h2]:
        for cc in range(1, 1 + len(header_row_2)):
            cell = ws.cell(rr, cc)
            cell.border = styles["header"]["border"]
            cell.alignment = styles["header"]["align"]
            if rr == h1:
                cell.fill = styles["header"]["fill"]
                cell.font = styles["header"]["font"]
            else:
                cell.fill = styles["header2"]["fill"]
                cell.font = styles["header2"]["font"]

    col = 2
    for _mn in models_mapping.values():
        ws.merge_cells(start_row=h1, start_column=col, end_row=h1, end_column=col + 2)
        col += 3

    domain_names = {"retail": "Retail", "airline": "Airline", "telecom": "Telecom"}
    data_start = ws.max_row + 1
    for d in domains:
        r = ws.max_row + 1
        ws.cell(r, 1).value = domain_names.get(d, d)
        ws.cell(r, 1).border = styles["data"]["border"]
        ws.cell(r, 1).alignment = styles["data"]["align"]
        col = 2
        for _k, model_name in models_mapping.items():
            ws.cell(r, col).value = f'=IFERROR(AVERAGEIFS(Task별_집계!F:F, Task별_집계!A:A, \"{models_mapping[_k]}\", Task별_집계!B:B, \"{d}\"),0)'
            ws.cell(r, col).number_format = "0.00%"
            ws.cell(r, col+1).value = f'=IFERROR(AVERAGEIFS(Task별_집계!G:G, Task별_집계!A:A, \"{models_mapping[_k]}\", Task별_집계!B:B, \"{d}\"),0)'
            ws.cell(r, col+1).number_format = "0.00%"
            ws.cell(r, col+2).value = f'=IFERROR(AVERAGEIFS(Task별_집계!H:H, Task별_집계!A:A, \"{models_mapping[_k]}\", Task별_집계!B:B, \"{d}\"),0)'
            ws.cell(r, col+2).number_format = "0.00%"
            for cc in [col, col+1, col+2]:
                c = ws.cell(r, cc)
                c.border = styles["data"]["border"]
                c.alignment = styles["data_center"]["align"]
            col += 3

    overall_r = ws.max_row + 1
    ws.cell(overall_r, 1).value = "Overall"
    ws.cell(overall_r, 1).font = Font(bold=True, size=10, name="Malgun Gothic")
    ws.cell(overall_r, 1).fill = styles["header2"]["fill"]
    ws.cell(overall_r, 1).alignment = styles["data_center"]["align"]
    ws.cell(overall_r, 1).border = styles["data"]["border"]
    data_end = overall_r - 1
    col = 2
    for _ in models_mapping.values():
        ws.cell(overall_r, col).value = f"=AVERAGE({get_column_letter(col)}{data_start}:{get_column_letter(col)}{data_end})"
        ws.cell(overall_r, col).number_format = "0.00%"
        ws.cell(overall_r, col+1).value = f"=AVERAGE({get_column_letter(col+1)}{data_start}:{get_column_letter(col+1)}{data_end})"
        ws.cell(overall_r, col+1).number_format = "0.00%"
        ws.cell(overall_r, col+2).value = f"=AVERAGE({get_column_letter(col+2)}{data_start}:{get_column_letter(col+2)}{data_end})"
        ws.cell(overall_r, col+2).number_format = "0.00%"
        for cc in [col, col+1, col+2]:
            c = ws.cell(overall_r, cc)
            c.font = Font(bold=True, size=10, name="Malgun Gothic")
            c.fill = styles["header2"]["fill"]
            c.border = styles["data"]["border"]
            c.alignment = styles["data_center"]["align"]
        col += 3

    # Freeze header for the sheet top (ranking)
    ws.freeze_panes = "A7"


def create_runs_sheet(wb, runs, styles):
    """
    런 시트(간결): 케이스_요약 + 런_원본을 합친 형태.
    - 기본은 간결한 컬럼만 노출
    - 원본/JSON/툴응답은 숨김 컬럼으로 유지(사용자가 필요시 펼치기)
    """
    ws = wb.create_sheet("런", 1)
    ws.append(["Run 단위 케이스 (요청/GT/툴/응답/판정근거)"])
    ws.merge_cells("A1:M1")
    ws["A1"].font = styles["title"]["font"]
    ws["A1"].alignment = styles["title"]["align"]
    ws.row_dimensions[1].height = 22

    ws.append(["필터로 PASS/FAIL, 모델, 도메인, TaskID를 좁혀서 보세요. 원본(JSON/툴응답)은 숨김 컬럼을 펼치면 확인 가능합니다."])
    ws.merge_cells("A2:M2")
    ws["A2"].alignment = styles["data"]["align"]
    ws.row_dimensions[2].height = 32

    headers = [
        "RunID", "모델", "도메인", "TaskID", "Trial",
        "결과", "Reward", "툴호출수", "툴목록",
        "요청(원문)", "GT 요약", "모델 최종응답(원문)", "왜 맞/틀"
    ]
    # 숨김(원본) 컬럼들(오른쪽)
    hidden_headers = ["툴호출(JSON 원문)", "툴응답(원문)", "GT(원문 JSON)", "RewardBreakdown(JSON)", "ActionChecks(JSON)"]
    ws.append(headers + hidden_headers)
    hrow = ws.max_row
    for c in ws[hrow]:
        c.font = styles["header"]["font"]
        c.fill = styles["header"]["fill"]
        c.alignment = styles["header"]["align"]
        c.border = styles["header"]["border"]

    for run in runs:
        rb = run.get("RewardBreakdown") or {}
        # 근거
        if run.get("Pass") == 1:
            why = "reward=1.0 (필수 액션/DB/커뮤니케이션 체크 통과)"
        else:
            parts = []
            term = str(run.get("Termination") or "")
            if "too_many_errors" in term:
                parts.append("too_many_errors(오류 누적 종료)")
            if run.get("MissingRequiredActions"):
                parts.append(f"필수 액션 미충족: {run['MissingRequiredActions']}")
            if run.get("ActionMismatchCount") is not None and run.get("ActionMismatchCount") > 0:
                parts.append(f"action_checks 불일치 {run['ActionMismatchCount']}건")
            if not parts:
                parts.append(f"breakdown={rb}")
            why = " / ".join(parts)

        row = [
            run.get("RunID",""),
            run.get("ModelLabel",""),
            run.get("Domain",""),
            run.get("TaskID",""),
            run.get("Trial",0),
            "PASS" if run.get("Pass")==1 else "FAIL",
            run.get("Reward",0.0),
            run.get("ToolCallCount",0),
            run.get("ToolNames",""),
            run.get("UserRequestRaw",""),
            run.get("GTSummary",""),
            run.get("AgentFinalRaw",""),
            why,
            # hidden originals
            run.get("ToolCallsRaw",""),
            run.get("ToolResultsRaw",""),
            run.get("GTRaw",""),
            run.get("RewardBreakdownJSON",""),
            run.get("ActionChecksRaw",""),
        ]
        ws.append(row)
        r = ws.max_row
        # 스타일
        for col_idx in range(1, len(headers) + len(hidden_headers) + 1):
            cell = ws.cell(r, col_idx)
            cell.border = styles["data"]["border"]
            if col_idx in [5,6,7,8]:
                cell.alignment = styles["data_center"]["align"]
            else:
                cell.alignment = styles["data"]["align"]
        # 결과 색
        rc = ws.cell(r, 6)
        if run.get("Pass")==1:
            rc.fill = styles["pass"]["fill"]; rc.font = styles["pass"]["font"]
        else:
            rc.fill = styles["fail"]["fill"]; rc.font = styles["fail"]["font"]
        ws.row_dimensions[r].height = 68

    ws.freeze_panes = f"A{hrow+1}"
    ws.auto_filter.ref = f"A{hrow}:{get_column_letter(len(headers)+len(hidden_headers))}{ws.max_row}"

    # Column widths (간결)
    widths = {
        "A":34, "B":26, "C":10, "D":8, "E":6,
        "F":7, "G":8, "H":8, "I":20,
        "J":50, "K":22, "L":50, "M":34,
        "N":44, "O":44, "P":44, "Q":26, "R":26
    }
    for k,v in widths.items():
        ws.column_dimensions[k].width = v
    # 숨김 컬럼
    for col_letter in ["N","O","P","Q","R"]:
        ws.column_dimensions[col_letter].hidden = True
    return ws


def create_turns_sheet(wb, turns_rows, styles):
    """턴 단위 원본(필요 시만 보는 디버깅 시트)."""
    ws = wb.create_sheet("턴", 2)
    headers = ["RunID", "모델", "도메인", "TaskID", "Trial", "TurnIdx", "Role", "Content(원문)", "ToolCalls(JSON)", "ToolResult(원문)"]
    ws.append(headers)
    for c in ws[1]:
        c.font = styles["header"]["font"]
        c.fill = styles["header"]["fill"]
        c.alignment = styles["header"]["align"]
        c.border = styles["header"]["border"]
    for row in turns_rows:
        ws.append(row)
    for r in range(2, ws.max_row + 1):
        for c in range(1, len(headers)+1):
            cell = ws.cell(r,c)
            cell.border = styles["data"]["border"]
            cell.alignment = styles["data_center"]["align"] if c in [5,6] else styles["data"]["align"]
        ws.row_dimensions[r].height = 44
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 8
    ws.column_dimensions["E"].width = 6
    ws.column_dimensions["F"].width = 7
    ws.column_dimensions["G"].width = 8
    ws.column_dimensions["H"].width = 70
    ws.column_dimensions["I"].width = 50
    ws.column_dimensions["J"].width = 50
    # JSON/툴결과는 기본 숨김(필요할 때만 펼치기)
    ws.column_dimensions["I"].hidden = True
    ws.column_dimensions["J"].hidden = True
    return ws
    
    # Title
    ws.append(["모델 × 도메인 Pass^k 매트릭스"])
    ws.merge_cells(f'A1:{get_column_letter(len(models_mapping) * 3 + 1)}1')
    ws['A1'].font = styles['title']['font']
    ws['A1'].alignment = styles['title']['align']
    ws.row_dimensions[1].height = 25
    
    ws.append([""])
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append([f"평가 일시: {timestamp}"])
    ws.merge_cells(f'A3:{get_column_letter(len(models_mapping) * 3 + 1)}3')
    
    # Description
    ws.append(["각 도메인별 Pass^k 값. Pass^k = 각 Task의 Pass^k를 평균한 값. (Task별_집계 시트 참조)"])
    ws.merge_cells(f'A4:{get_column_letter(len(models_mapping) * 3 + 1)}4')
    
    ws.append([""])
    
    # 2단 헤더: (모델명 merged) + (P@1/P@2/P@4)
    header_row_1 = ["도메인"]
    for model_name in models_mapping.values():
        header_row_1.extend([model_name, "", ""])
    ws.append(header_row_1)
    header_row_idx_1 = ws.max_row

    header_row_2 = [""]
    for _ in models_mapping.values():
        header_row_2.extend(["P@1", "P@2", "P@4"])
    ws.append(header_row_2)
    header_row_idx_2 = ws.max_row

    # 스타일 + merge
    ws.cell(row=header_row_idx_1, column=1).font = styles["header"]["font"]
    ws.cell(row=header_row_idx_1, column=1).fill = styles["header"]["fill"]
    ws.cell(row=header_row_idx_1, column=1).alignment = styles["header"]["align"]
    ws.cell(row=header_row_idx_1, column=1).border = styles["header"]["border"]
    ws.merge_cells(start_row=header_row_idx_1, start_column=1, end_row=header_row_idx_2, end_column=1)

    col = 2
    for _model_name in models_mapping.values():
        ws.merge_cells(start_row=header_row_idx_1, start_column=col, end_row=header_row_idx_1, end_column=col + 2)
        for c in range(col, col + 3):
            cell_top = ws.cell(row=header_row_idx_1, column=c)
            cell_top.font = styles["header"]["font"]
            cell_top.fill = styles["header"]["fill"]
            cell_top.alignment = styles["header"]["align"]
            cell_top.border = styles["header"]["border"]
        for c in range(col, col + 3):
            cell_sub = ws.cell(row=header_row_idx_2, column=c)
            cell_sub.value = header_row_2[c - 1]
            cell_sub.font = styles["header2"]["font"]
            cell_sub.fill = styles["header2"]["fill"]
            cell_sub.alignment = styles["header2"]["align"]
            cell_sub.border = styles["header2"]["border"]
        col += 3
    
    # Domain descriptions
    domain_names = {
        'retail': 'Retail',
        'airline': 'Airline',
        'telecom': 'Telecom'
    }
    
    # Data rows for each domain
    # data rows start
    data_start_row = ws.max_row + 1
    for domain_key in domains:
        row_num = ws.max_row + 1
        ws.cell(row=row_num, column=1).value = domain_names[domain_key]
        ws.cell(row=row_num, column=1).alignment = styles["data"]["align"]
        ws.cell(row=row_num, column=1).border = styles["data"]["border"]

        col = 2
        for _model_key, model_name in models_mapping.items():
            ws.cell(row=row_num, column=col).value = f'=IFERROR(AVERAGEIFS(Task별_집계!F:F, Task별_집계!A:A, "{model_name}", Task별_집계!B:B, "{domain_key}"),0)'
            ws.cell(row=row_num, column=col).number_format = '0.00%'
            ws.cell(row=row_num, column=col + 1).value = f'=IFERROR(AVERAGEIFS(Task별_집계!G:G, Task별_집계!A:A, "{model_name}", Task별_집계!B:B, "{domain_key}"),0)'
            ws.cell(row=row_num, column=col + 1).number_format = '0.00%'
            ws.cell(row=row_num, column=col + 2).value = f'=IFERROR(AVERAGEIFS(Task별_집계!H:H, Task별_집계!A:A, "{model_name}", Task별_집계!B:B, "{domain_key}"),0)'
            ws.cell(row=row_num, column=col + 2).number_format = '0.00%'

            for c in range(col, col + 3):
                cell = ws.cell(row=row_num, column=c)
                cell.alignment = styles["data_center"]["align"]
                cell.border = styles["data"]["border"]
            col += 3
    
    # Overall row
    overall_row = ws.max_row + 1
    ws.cell(row=overall_row, column=1).value = "Overall"
    ws.cell(row=overall_row, column=1).font = Font(bold=True, size=10, name="Malgun Gothic")
    ws.cell(row=overall_row, column=1).fill = styles["header2"]["fill"]
    ws.cell(row=overall_row, column=1).alignment = styles["data_center"]["align"]
    ws.cell(row=overall_row, column=1).border = styles["data"]["border"]

    # data rows range
    data_end_row = overall_row - 1
    col = 2
    for _model_key, _model_name in models_mapping.items():
        ws.cell(row=overall_row, column=col).value = f"=AVERAGE({get_column_letter(col)}{data_start_row}:{get_column_letter(col)}{data_end_row})"
        ws.cell(row=overall_row, column=col).number_format = '0.00%'
        ws.cell(row=overall_row, column=col + 1).value = f"=AVERAGE({get_column_letter(col+1)}{data_start_row}:{get_column_letter(col+1)}{data_end_row})"
        ws.cell(row=overall_row, column=col + 1).number_format = '0.00%'
        ws.cell(row=overall_row, column=col + 2).value = f"=AVERAGE({get_column_letter(col+2)}{data_start_row}:{get_column_letter(col+2)}{data_end_row})"
        ws.cell(row=overall_row, column=col + 2).number_format = '0.00%'
        for c in range(col, col + 3):
            cell = ws.cell(row=overall_row, column=c)
            cell.font = Font(bold=True, size=10, name="Malgun Gothic")
            cell.fill = styles["header2"]["fill"]
            cell.alignment = styles["data_center"]["align"]
            cell.border = styles["data"]["border"]
        col += 3

    # Freeze + filter
    ws.freeze_panes = "B" + str(data_start_row)
    last_col = 1 + (len(models_mapping) * 3)
    ws.auto_filter.ref = f"A{header_row_idx_2}:{get_column_letter(last_col)}{data_end_row}"

    # Column widths
    ws.column_dimensions["A"].width = 12
    for c in range(2, last_col + 1):
        ws.column_dimensions[get_column_letter(c)].width = 9

def create_detailed_run_log(wb, all_logs, all_turns, gt_map, styles):
    """(deprecated) kept for backward compatibility; no longer used when using 3-sheet layout."""
    ws = wb.create_sheet("상세_런_로그", 99)
    
    # Headers
    headers = [
        "결과", "모델", "도메인", "도메인 설명", "Query ID", "질문",
        "GT(원본/필수액션)", "툴호출수", "툴목록(원본)",
        "모델 최종응답(원본)", "실패분류(L1/L2)", "근거(원본)", "Reward"
    ]
    
    ws.append(headers)
    for col_idx, cell in enumerate(ws[1], 1):
        cell.font = styles['header']['font']
        cell.fill = styles['header']['fill']
        cell.alignment = styles['header']['align']
        cell.border = styles['header']['border']
    
    # Group turns by run_id
    turn_by_run = {}
    for turn in all_turns:
        run_id = turn['RunID']
        if run_id not in turn_by_run:
            turn_by_run[run_id] = []
        turn_by_run[run_id].append(turn)
    
    # 모든 run 포함 (FAIL 먼저 보고 싶으면 엑셀 필터/정렬)
    for log in all_logs:
        run_id = f"{log['Model']}_{log['Domain']}_T{log['TaskID']}_trial{log['Trial']}"
        turns = turn_by_run.get(run_id, [])
        
        user_question = ""
        for turn in turns:
            if turn['Speaker'] == 'user':
                user_question = turn['Message'][:100] + "..." if len(turn['Message']) > 100 else turn['Message']
                break
        
        # run 전체를 훑어서 tool_calls를 누적
        tool_names: list[str] = []
        tool_count = 0
        for turn in turns:
            tc = turn.get("Tool_Called") or ""
            if tc:
                chunks = [x.strip() for x in tc.split(";") if x.strip()]
                tool_count += len(chunks)
                for ch in chunks:
                    name = ch.split("(")[0].strip()
                    if name:
                        tool_names.append(name)

        # 모델 최종 응답(assistant 마지막 메시지 원본)
        agent_final = ""
        for turn in reversed(turns):
            if turn.get("Speaker") == "assistant":
                agent_final = turn.get("Message") or ""
                break
        
        term_reason = log['Termination']
        # 실패분류 개선(termination만이 아니라 action_checks/env/db/communicate 기반)
        fail_l1l2 = ""
        evidence = ""
        if log.get("Pass") == 1:
            result = "PASS"
            fail_l1l2 = "-"
            evidence = "reward=1.0"
        else:
            result = "FAIL"
            if 'too_many_errors' in (term_reason or ""):
                fail_l1l2 = "Infra/API / Too many errors"
                evidence = term_reason
            elif 'max_turns' in (term_reason or ""):
                fail_l1l2 = "Loop/timeout / Max turns"
                evidence = term_reason
            else:
                # reward breakdown 기반(없으면 termination)
                rb = log.get("RewardBreakdown") or {}
                if rb.get("ACTION") == 0.0:
                    fail_l1l2 = "Tool misuse / Missing required actions"
                    evidence = "ACTION=0"
                elif rb.get("DB") == 0.0:
                    fail_l1l2 = "Reasoning/Planning / DB mismatch"
                    evidence = "DB=0"
                elif rb.get("COMMUNICATE") == 0.0:
                    fail_l1l2 = "Missing info / Communication"
                    evidence = "COMMUNICATE=0"
                else:
                    fail_l1l2 = "Unknown"
                    evidence = term_reason or "n/a"

        gt = gt_map.get((log["Domain"], str(log["TaskID"])), "N/A")
        row_data = [
            result,
            log['Model'],
            log['Domain'],
            None,  # 도메인 설명(수식)
            f"{log['Domain']}_{log['TaskID']}",
            user_question,
            gt,
            tool_count,
            ", ".join(tool_names) if tool_names else "",
            agent_final,
            fail_l1l2,
            evidence,
            log.get("Reward", 0.0),
        ]

        ws.append(row_data)
        row_idx = ws.max_row

        # 도메인 설명 수식
        ws.cell(row=row_idx, column=4).value = f'=IFERROR(VLOOKUP(C{row_idx},도메인_설명!$A:$C,3,FALSE),"")'
        # Reward 표시 포맷
        ws.cell(row=row_idx, column=13).number_format = '0.0000'

        for col_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = styles['data']['border']
            if col_idx == 1:
                if result == "PASS":
                    cell.font = styles['pass']['font']
                    cell.fill = styles['pass']['fill']
                else:
                    cell.font = styles['fail']['font']
                    cell.fill = styles['fail']['fill']
                cell.alignment = styles['data_center']['align']
            elif col_idx in [3, 8, 13]:  # 도메인/툴호출수/Reward
                cell.alignment = styles['data_center']['align']
            else:
                cell.alignment = styles['data']['align']
    
    # Freeze and filter
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    
    # Column widths
    ws.column_dimensions['A'].width = 7   # 결과
    ws.column_dimensions['B'].width = 28  # 모델
    ws.column_dimensions['C'].width = 10  # 도메인
    ws.column_dimensions['D'].width = 24  # 도메인 설명
    ws.column_dimensions['E'].width = 12  # Query ID
    ws.column_dimensions['F'].width = 48  # 질문
    ws.column_dimensions['G'].width = 34  # GT
    ws.column_dimensions['H'].width = 8   # 툴호출수
    ws.column_dimensions['I'].width = 28  # 툴목록
    ws.column_dimensions['J'].width = 42  # 모델응답
    ws.column_dimensions['K'].width = 26  # 실패분류
    ws.column_dimensions['L'].width = 18  # 근거
    ws.column_dimensions['M'].width = 10  # reward

    ws.freeze_panes = "A2"

def create_turns_raw_sheet(wb, turns_rows, styles):
    """턴 단위 원본(요청/응답/툴콜/툴결과). 요약/짤림 없이 그대로 저장."""
    ws = wb.create_sheet("턴_원본", 5)
    headers = ["RunID", "모델", "도메인", "TaskID", "Trial", "TurnIdx", "Role", "Content(원본)", "ToolCalls(JSON 원본)", "ToolResult(원본)"]
    ws.append(headers)
    for c in ws[1]:
        c.font = styles["header"]["font"]
        c.fill = styles["header"]["fill"]
        c.alignment = styles["header"]["align"]
        c.border = styles["header"]["border"]
    for row in turns_rows:
        ws.append(row)
    for r in range(2, ws.max_row + 1):
        for c in range(1, len(headers) + 1):
            cell = ws.cell(r, c)
            cell.border = styles["data"]["border"]
            cell.alignment = styles["data"]["align"] if c not in [6] else styles["data_center"]["align"]
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 8
    ws.column_dimensions["E"].width = 6
    ws.column_dimensions["F"].width = 7
    ws.column_dimensions["G"].width = 8
    ws.column_dimensions["H"].width = 70
    ws.column_dimensions["I"].width = 60
    ws.column_dimensions["J"].width = 60
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = 60


def create_case_summary_sheet(wb, runs, styles):
    """
    사람이 바로 읽히는 '케이스_요약' 시트.
    - 요청/GT/모델응답/툴호출/판정근거(왜 맞음/왜 틀림)를 한 행에 배치
    """
    ws = wb.create_sheet("케이스_요약", 1)

    title = "케이스 요약 (요청/정답기준/모델행동/판정근거)"
    ws.append([title])
    ws.merge_cells("A1:N1")
    ws["A1"].font = styles["title"]["font"]
    ws["A1"].alignment = styles["title"]["align"]
    ws.row_dimensions[1].height = 22

    ws.append(
        [
            "읽는 법: TAU2의 '정답(GT)'은 단일 텍스트가 아니라, (1) 필수 툴 호출/절차(Action) (2) DB 상태 변화(ENV/DB) (3) 커뮤니케이션 요건을 만족했는지로 판정됩니다.",
        ]
    )
    ws.merge_cells("A2:N2")
    ws["A2"].alignment = styles["data"]["align"]
    ws.row_dimensions[2].height = 36

    headers = [
        "RunID",
        "모델",
        "도메인",
        "TaskID",
        "Trial",
        "요청(원문)",
        "GT 요약(필수액션)",
        "모델 툴호출(요약)",
        "모델 최종응답(원문)",
        "결과",
        "Reward",
        "Breakdown(DB/ACTION/COMM)",
        "왜 맞음/왜 틀림(근거)",
        "참고(턴_원본 RunID)",
    ]
    ws.append(headers)
    header_row = ws.max_row
    for c in ws[header_row]:
        c.font = styles["header"]["font"]
        c.fill = styles["header"]["fill"]
        c.alignment = styles["header"]["align"]
        c.border = styles["header"]["border"]

    for run in runs:
        rb = run.get("RewardBreakdown") or {}
        breakdown = f'DB={rb.get("DB","")}, ACTION={rb.get("ACTION","")}, COMM={rb.get("COMMUNICATE","")}'

        # 판정근거(사람용)
        if run.get("Pass") == 1:
            why = "reward=1.0. 필수 액션(action_checks)이 모두 충족되고 DB/커뮤니케이션 체크가 통과된 케이스입니다."
        else:
            why_parts = []
            if run.get("Termination") and "too_many_errors" in str(run.get("Termination")):
                why_parts.append("too_many_errors로 조기 종료(실행 중 오류 누적).")
            if run.get("MissingRequiredActions"):
                why_parts.append(f"필수 액션 미충족: {run['MissingRequiredActions']}")
            if run.get("ActionMismatchCount") is not None:
                why_parts.append(f"action_checks 불일치 {run['ActionMismatchCount']}건.")
            if not why_parts:
                why_parts.append("reward_info 기준 미충족(세부 근거는 런_원본의 RewardBreakdown/툴로그 확인).")
            why = " ".join(why_parts)

        row = [
            run.get("RunID", ""),
            run.get("ModelLabel", ""),
            run.get("Domain", ""),
            run.get("TaskID", ""),
            run.get("Trial", 0),
            run.get("UserRequestRaw", ""),
            run.get("GTSummary", ""),
            run.get("ToolNames", ""),
            run.get("AgentFinalRaw", ""),
            "PASS" if run.get("Pass") == 1 else "FAIL",
            run.get("Reward", 0.0),
            breakdown,
            why,
            run.get("RunID", ""),
        ]
        ws.append(row)
        r = ws.max_row

        # 도메인 설명은 다른 시트에 숨겨져 있으니 여기서는 직접 텍스트로 넣지 않고, 가독성 확보를 위해 폭/줄바꿈으로 처리
        # 스타일
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(r, col_idx)
            cell.border = styles["data"]["border"]
            if col_idx in [5, 10, 11]:
                cell.alignment = styles["data_center"]["align"]
            else:
                cell.alignment = styles["data"]["align"]
        # 결과 컬럼 색 약하게
        result_cell = ws.cell(r, 10)
        if run.get("Pass") == 1:
            result_cell.fill = styles["pass"]["fill"]
            result_cell.font = styles["pass"]["font"]
        else:
            result_cell.fill = styles["fail"]["fill"]
            result_cell.font = styles["fail"]["font"]

        ws.row_dimensions[r].height = 84

    ws.freeze_panes = f"A{header_row+1}"
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(len(headers))}{ws.max_row}"

    # Column widths (읽기 최적화)
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 8
    ws.column_dimensions["E"].width = 6
    ws.column_dimensions["F"].width = 52
    ws.column_dimensions["G"].width = 30
    ws.column_dimensions["H"].width = 26
    ws.column_dimensions["I"].width = 52
    ws.column_dimensions["J"].width = 7
    ws.column_dimensions["K"].width = 8
    ws.column_dimensions["L"].width = 20
    ws.column_dimensions["M"].width = 44
    ws.column_dimensions["N"].width = 26

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-filter', type=str, default=None)
    args = parser.parse_args()
    
    base_dirs = [Path("data/simulations"), Path("data/tau2/simulations")]
    base_dir = next((d for d in base_dirs if d.exists()), None)
    
    if not base_dir:
        print("Error: Results directory not found.")
        return

    # 평가 대상 모델(표 표시 순서 고정)
    llm_to_label = {
        "openrouter/meta-llama/llama-3.3-70b-instruct": "llama-3.3-70b-instruct-FC",
        "openrouter/mistralai/mistral-small-3.2-24b-instruct": "mistral-small-3.2-24b-instruct-FC",
        "openrouter/qwen/qwen3-32b": "qwen3-32b-FC",
        "openrouter/qwen/qwen3-14b": "qwen3-14b-FC",
        "openrouter/qwen/qwen3-next-80b-a3b-instruct": "qwen3-next-80b-a3b-instruct-FC",
    }
    # 모델 매핑은 {llm_string: label} 형태로 유지
    models_mapping = dict(llm_to_label)
    if args.model_filter:
        models_mapping = {k: v for k, v in models_mapping.items() if k == args.model_filter}

    domains = ["retail", "airline", "telecom"]
    all_logs = []
    all_turns = []

    # GT(정답) 성격: TAU2는 단일 정답 문자열이 아니라 "필수 액션/체크"의 집합
    gt_map: dict[tuple[str, str], str] = {}

    # 결과 JSON 파일 전체를 스캔해서 모델/도메인/시뮬레이션을 추출
    runs: list[dict] = []
    turns_rows: list[list] = []
    # task -> (user scenario raw, gt raw)
    task_meta: dict[tuple[str, str], dict] = {}

    for file_path in sorted(base_dir.glob("*.json")):
        try:
            data = json.loads(file_path.read_text())
        except Exception:
            continue

        info = data.get("info") or {}
        agent_llm = (((info.get("agent_info") or {}).get("llm")) or "").strip()
        domain = (((info.get("environment_info") or {}).get("domain_name")) or "").strip()
        if not agent_llm or not domain:
            continue

        # 관심 모델만 포함 (그 외는 제외)
        if agent_llm not in models_mapping:
            continue
        display_name = models_mapping[agent_llm]

        # GT 맵 구성 (task_id -> required action tool names)
        for t in data.get("tasks", []) or []:
            tid = str(t.get("id"))
            crit = (t.get("evaluation_criteria") or {})
            actions = crit.get("actions") or []
            # 원본 GT: actions 전체(이름+args 포함)
            gt_raw = json.dumps(actions, ensure_ascii=False)
            req_tools = [a.get("name") for a in actions if a.get("name")]
            if req_tools:
                gt_map[(domain, tid)] = "required_tools: " + ", ".join(req_tools)
            task_meta[(domain, tid)] = {
                "gt_raw": gt_raw,
                "user_scenario_raw": json.dumps(((t.get("user_scenario") or {}).get("instructions") or {}), ensure_ascii=False),
            }

        for sim in data.get("simulations", []) or []:
            task_id = str(sim.get("task_id", "N/A"))
            trial = sim.get("trial")
            if trial is None:
                trial = sim.get("info_trial_num")
            if trial is None:
                trial = 0

            reward = sim.get("reward")
            if reward is None:
                reward = ((sim.get("reward_info") or {}).get("reward"))
            if reward is None:
                reward = 0.0

            reward_info = sim.get("reward_info") or {}
            reward_breakdown = reward_info.get("reward_breakdown") or {}
            action_checks = reward_info.get("action_checks") or []

            # TAU2 success 기준: reward가 1.0(±1e-6)
            is_pass = 1 if abs(float(reward) - 1.0) <= 1e-6 else 0

            run_id = f"{display_name}_{domain}_T{task_id}_trial{trial}"

            all_logs.append(
                {
                    "Model": display_name,
                    "Domain": domain,
                    "TaskID": task_id,
                    "Trial": int(trial),
                    "Pass": is_pass,
                    "Reward": float(reward),
                    "RewardBreakdown": reward_breakdown,
                    "Termination": sim.get("termination_reason", "N/A"),
                }
            )

            messages = sim.get("messages", []) or []
            # run-level aggregation for tool count/names + raw request/gt/agent final
            tool_names: list[str] = []
            tool_count = 0
            first_user = ""
            agent_final = ""
            tool_calls_raw_all: list[dict] = []
            tool_results_raw_all: list[str] = []
            for idx, msg in enumerate(messages):
                role = msg.get("role", "")
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls", []) or []
                tool_info = ""
                if tool_calls:
                    tool_info = "; ".join(
                        [
                            f"{tc.get('name')}({json.dumps(tc.get('arguments', {}), ensure_ascii=False)})"
                            for tc in tool_calls
                            if tc.get("name")
                        ]
                    )
                    tool_count += len(tool_calls)
                    for tc in tool_calls:
                        n = tc.get("name")
                        if n:
                            tool_names.append(n)
                        tool_calls_raw_all.append(tc)

                if not first_user and role == "user":
                    first_user = content or ""
                if role == "assistant":
                    # 마지막 assistant 원본: 텍스트가 없고 tool_calls만 있으면 tool_calls를 텍스트로 표시
                    if content:
                        agent_final = content
                    elif tool_calls:
                        agent_final = json.dumps(tool_calls, ensure_ascii=False)
                    else:
                        agent_final = agent_final
                if role == "tool" and content:
                    tool_results_raw_all.append(content)

                all_turns.append(
                    {
                        "RunID": run_id,
                        "Turn": idx,
                        "Speaker": role,
                        "Message": content,
                        "Tool_Called": tool_info,
                        "Tool_Response": content[:200] + "..." if role == "tool" and len(content) > 200 else (content if role == "tool" else ""),
                    }
                )

                # 턴 원본 시트 row
                turns_rows.append(
                    [
                        run_id,
                        display_name,
                        domain,
                        task_id,
                        int(trial),
                        idx,
                        role,
                        content,
                        json.dumps(tool_calls, ensure_ascii=False) if tool_calls else "",
                        content if role == "tool" else "",
                    ]
                )

            meta = task_meta.get((domain, str(task_id)), {})
            user_request_raw = first_user or meta.get("user_scenario_raw", "")
            gt_raw = meta.get("gt_raw", "")
            gt_summary = gt_map.get((domain, str(task_id)), "N/A")

            # 실패 근거(필수 액션 미충족 등) 계산
            mismatches = [a for a in action_checks if a and (a.get("action_match") is False)]
            mismatch_count = len(mismatches)
            missing_actions = []
            for a in mismatches[:8]:
                act = (a.get("action") or {})
                name = act.get("name")
                if name:
                    missing_actions.append(name)
            missing_actions_str = ", ".join(missing_actions)

            runs.append(
                {
                    "RunID": run_id,
                    "ModelLabel": display_name,
                    "AgentLLM": agent_llm,
                    "Domain": domain,
                    "TaskID": task_id,
                    "Trial": int(trial),
                    "Pass": is_pass,
                    "Reward": float(reward),
                    "RewardBreakdownJSON": json.dumps(reward_breakdown, ensure_ascii=False),
                    "RewardBreakdown": reward_breakdown,
                    "Termination": sim.get("termination_reason", "N/A"),
                    "ToolCallCount": tool_count,
                    "ToolNames": ", ".join(tool_names),
                    "ToolCallsRaw": json.dumps(tool_calls_raw_all, ensure_ascii=False),
                    "ToolResultsRaw": "\n\n---\n\n".join(tool_results_raw_all),
                    "UserRequestRaw": user_request_raw,
                    "GTRaw": gt_raw,
                    "GTSummary": gt_summary,
                    "AgentFinalRaw": agent_final,
                    "ActionChecksRaw": json.dumps(action_checks, ensure_ascii=False),
                    "ActionMismatchCount": mismatch_count,
                    "MissingRequiredActions": missing_actions_str,
                }
            )

    wb = Workbook()
    wb.remove(wb.active)
    styles = setup_styles()
    # 엑셀 열 때 수식 재계산(캐시값 NULL 방지)
    try:
        wb.calculation.fullCalcOnLoad = True
        wb.calculation.calcMode = "auto"
    except Exception:
        pass
    
    # 도메인 설명 시트(다른 시트에서 VLOOKUP으로 참조)
    ws_dom = wb.create_sheet("도메인_설명", 0)
    ws_dom.append(["domain", "표시명", "설명"])
    for c in ws_dom[1]:
        c.font = styles["header"]["font"]
        c.fill = styles["header"]["fill"]
        c.alignment = styles["header"]["align"]
        c.border = styles["header"]["border"]
    rows = [
        ["retail", "Retail", "온라인 쇼핑 주문/반품/교환/배송지/결제 변경 등 고객센터 시나리오"],
        ["airline", "Airline", "항공 예약/변경/좌석/마일리지 등 고객센터 시나리오"],
        ["telecom", "Telecom", "요금제/장애/청구/개통 등 통신 고객센터 시나리오"],
    ]
    for r in rows:
        ws_dom.append(r)
    ws_dom.column_dimensions["A"].width = 10
    ws_dom.column_dimensions["B"].width = 10
    ws_dom.column_dimensions["C"].width = 60

    # ===== 3-sheet layout (visible) =====
    create_summary_sheet(wb, models_mapping, domains, styles)     # 요약(랭킹+매트릭스)
    create_runs_sheet(wb, runs, styles)                           # 런(케이스 단위)
    create_turns_sheet(wb, turns_rows, styles)                    # 턴(디버깅)

    # ===== helper sheets (hidden) =====
    create_task_summary_sheet(wb, all_logs, models_mapping, domains, styles)  # Pass^k 계산용

    # 시트 수 줄이기: helper 시트 숨김
    for name in ["Task별_집계", "도메인_설명"]:
        if name in wb.sheetnames:
            wb[name].sheet_state = "hidden"
    
    output_path = Path("tau2_evaluation_report.xlsx")
    wb.save(output_path)
    # macOS Excel 경고(외부 데이터 연결/신뢰) 오탐을 줄이기 위해 xattr 제거
    # - 실제로 외부 연결은 포함되어 있지 않음(패키지 검사 기준).
    try:
        if platform.system().lower() == "darwin":
            # 가장 확실: 모든 xattr 제거
            subprocess.run(["xattr", "-c", str(output_path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    print(f"\nReport generated: {output_path}")
    print(f"  - Sheet 1: 전체 모델 평가 요약 (Overall ranking)")
    print(f"  - Sheet 2: 모델 × 도메인 Pass^k 매트릭스")
    print(f"  - Sheet 3: 상세 런 로그 (PASS/FAIL 모두 포함)")
    print(f"  - Sheet 4: 원본 데이터 (Raw trial data)")
    print(f"  - Sheet 5: Task별 집계 (Task-level Pass^k calculations)")
    print(f"  - Data: {len(all_logs)} runs")
    print(f"  - All metrics calculated using Excel formulas (COMBIN, AVERAGEIF, etc.)\n")

if __name__ == "__main__":
    main()
