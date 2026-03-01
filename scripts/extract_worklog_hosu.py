#!/usr/bin/env python3
"""保守工数管理CSVからhelp-XXXXX案件の日別×担当者工数を抽出

列構造: 0=案件名(head1行), 3=担当者(line行), 4=合計, 5=マーカー, 6=行数, 7〜34=日別(1〜28日)
"""
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "sample" / "保守工数管理 - 人月契約範囲内.csv"
OUTPUT_PATH = PROJECT_ROOT / "sample" / "_worklog_hosu.json"

TARGET_CDS = [
    "help-12401", "help-12395", "help-12231", "help-12792", "help-12043",
    "help-12923", "help-12902", "help-13037", "help-13203", "help-13672",
    "help-13839", "help-14344", "help-14636", "help-14695", "help-14888",
    "help-15025", "help-15228", "help-15275", "help-15329",
    "help-14990", "help-15174", "help-15300",
]

# 日付マッピング: 列7=1日, 列8=2日, ..., 列34=28日
DATE_COLS = {7 + d: f"2026-02-{d+1:02d}" for d in range(28)}


def main():
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    result = []
    in_target = False
    current_cd = None
    current_entries = []

    for row in rows:
        marker = row[5].strip() if len(row) > 5 else ""

        if marker == "head1":
            if in_target and current_entries:
                result.append({"issue_cd": current_cd, "entries": current_entries})

            name = row[0].strip()
            cd = name.split()[0] if name else ""
            in_target = cd in TARGET_CDS
            current_cd = cd
            current_entries = []

        elif marker in ("line2", "line3") and in_target:
            member = row[3].strip() if len(row) > 3 else ""
            if not member:
                continue

            for col_idx, date_str in DATE_COLS.items():
                if col_idx < len(row):
                    val = row[col_idx].strip()
                    if val:
                        try:
                            hours = float(val)
                            if hours > 0:
                                current_entries.append({
                                    "user": member,
                                    "date": date_str,
                                    "hours": hours
                                })
                        except ValueError:
                            pass

        elif marker == "foot1" and in_target:
            if current_entries:
                result.append({"issue_cd": current_cd, "entries": current_entries})
            in_target = False
            current_cd = None
            current_entries = []

    if in_target and current_entries:
        result.append({"issue_cd": current_cd, "entries": current_entries})

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total_entries = sum(len(s["entries"]) for s in result)
    total_hours = sum(e["hours"] for s in result for e in s["entries"])
    print(f"help sections: {len(result)}")
    print(f"Total entries: {total_entries}")
    print(f"Total hours: {total_hours}")


if __name__ == "__main__":
    main()
