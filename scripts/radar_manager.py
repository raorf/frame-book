#!/usr/bin/env python3
"""
帧卷 - 作业自查雷达脚本
管理错题数据：录入、查询、学情分析。

用法:
    python radar_manager.py add --subject "数学" --chapter "二次函数" --knowledge-point "配方法" --error-type "计算错" --note "配方步骤漏了常数项"
    python radar_manager.py add --subject "物理" --chapter "压强" --knowledge-point "液体压强" --error-type "概念不清"
    python radar_manager.py review --range week --limit 20
    python radar_manager.py analyze
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta

from common import (
    output_json,
    validate_filepath,
    load_data_list,
    save_json,
    default_filepath,
)

# ============================================================
# 常量定义
# ============================================================

DEFAULT_FILE = default_filepath("radar_data.json")
MAX_NOTE_LENGTH = 500
MAX_SOURCE_LENGTH = 200
VALID_ERROR_TYPES = ["计算错", "概念不清", "完全没思路", "审题错", "粗心", "方法不当", "知识盲点", "其他"]
VALID_SOURCES = ["作业", "考试", "练习册", "真题", "学伴互查", "其他"]
VALID_RANGES = ["today", "week", "month", "all"]
VALID_SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "科学"]


# ============================================================
# 工具函数
# ============================================================


def get_week_range(base_date=None):
    """获取本周的起止日期（周一为一周开始）。"""
    if base_date is None:
        base_date = datetime.now()
    monday = base_date - timedelta(days=base_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date(), sunday.date()


def get_month_range(base_date=None):
    """获取本月的起止日期。"""
    if base_date is None:
        base_date = datetime.now()
    first_day = base_date.replace(day=1).date()
    if base_date.month == 12:
        last_day = base_date.replace(year=base_date.year + 1, month=1, day=1).date() - timedelta(days=1)
    else:
        last_day = base_date.replace(month=base_date.month + 1, day=1).date() - timedelta(days=1)
    return first_day, last_day


def validate_input(value, field_name, max_length=100, allow_empty=False):
    """验证输入字符串：非空（可选）、长度限制。"""
    if not value or not value.strip():
        if allow_empty:
            return ""
        output_json({"status": "error", "message": f"{field_name}不能为空"})
        sys.exit(1)
    value = value.strip()
    if len(value) > max_length:
        output_json({"status": "error",
                     "message": f"{field_name}过长，最大{max_length}字符"})
        sys.exit(1)
    return value


# ============================================================
# 命令处理函数
# ============================================================

def cmd_add(args):
    """录入一道错题。"""
    subject = validate_input(args.subject, "科目", max_length=20)
    chapter = validate_input(args.chapter, "章节", max_length=100) if args.chapter else ""
    knowledge_point = validate_input(args.knowledge_point, "知识点", max_length=100) if args.knowledge_point else ""
    error_type = args.error_type if args.error_type in VALID_ERROR_TYPES else "其他"
    note = validate_input(args.note, "备注", max_length=MAX_NOTE_LENGTH, allow_empty=True)
    source = args.source if args.source in VALID_SOURCES else "作业"
    exercise_id = validate_input(args.exercise_id, "题目标识", max_length=MAX_SOURCE_LENGTH, allow_empty=True)
    local_weight = validate_input(args.local_weight, "本地权重", max_length=100, allow_empty=True)

    record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "subject": subject,
        "chapter": chapter,
        "knowledge_point": knowledge_point,
        "error_type": error_type,
        "note": note,
        "source": source,
        "exercise_id": exercise_id,
        "error_count": 1,
        "resolved": False,
        "resolved_at": None,
        "local_weight": local_weight,
    }

    filepath = args.file if args.file else DEFAULT_FILE
    if args.file and not validate_filepath(filepath):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    data = load_data_list(filepath)
    data.append(record)
    save_json(filepath, data)

    output_json({
        "status": "success",
        "message": f"错题已记录: {subject}·{chapter}·{knowledge_point}",
        "record": record,
        "total_count": len(data),
    })


def cmd_review(args):
    """查询错题列表。"""
    filepath = args.file if args.file else DEFAULT_FILE
    if args.file and not validate_filepath(filepath):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    data = load_data_list(filepath)

    range_type = args.range if args.range else "week"
    if range_type not in VALID_RANGES:
        output_json({"status": "error",
                     "message": f"范围不合法，可选: {'/'.join(VALID_RANGES)}"})
        sys.exit(1)

    today = datetime.now().date()
    filtered = []

    if range_type == "today":
        today_str = today.strftime("%Y-%m-%d")
        filtered = [r for r in data if r.get("date") == today_str]
    elif range_type == "week":
        monday, sunday = get_week_range()
        for r in data:
            try:
                r_date = datetime.strptime(r.get("date", ""), "%Y-%m-%d").date()
                if monday <= r_date <= sunday:
                    filtered.append(r)
            except ValueError:
                continue
    elif range_type == "month":
        month_start, month_end = get_month_range()
        for r in data:
            try:
                r_date = datetime.strptime(r.get("date", ""), "%Y-%m-%d").date()
                if month_start <= r_date <= month_end:
                    filtered.append(r)
            except ValueError:
                continue
    else:  # all
        filtered = data

    subject_filter = args.subject
    if subject_filter:
        filtered = [r for r in filtered if r.get("subject") == subject_filter]

    unresolved_only = args.unresolved
    if unresolved_only:
        filtered = [r for r in filtered if not r.get("resolved", False)]

    filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    limit = args.limit if args.limit else 50
    if limit < 1:
        limit = 1
    elif limit > 200:
        limit = 200
    filtered = filtered[:limit]

    output_json({
        "status": "success",
        "total": len(data),
        "filtered_count": len(filtered),
        "range": range_type,
        "subject": subject_filter or "全部",
        "unresolved_only": unresolved_only,
        "records": filtered,
    })


def cmd_analyze(args):
    """生成错题学情分析报告。"""
    filepath = args.file if args.file else DEFAULT_FILE
    if args.file and not validate_filepath(filepath):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    data = load_data_list(filepath)

    total = len(data)
    unresolved = [r for r in data if not r.get("resolved", False)]
    unresolved_count = len(unresolved)

    # 本周错题数
    monday, sunday = get_week_range()
    week_count = 0
    week_unresolved = 0
    for r in data:
        try:
            r_date = datetime.strptime(r.get("date", ""), "%Y-%m-%d").date()
            if monday <= r_date <= sunday:
                week_count += 1
                if not r.get("resolved", False):
                    week_unresolved += 1
        except ValueError:
            continue

    # 按科目统计
    subject_count = {}
    subject_unresolved = {}
    for r in data:
        subj = r.get("subject", "未知")
        subject_count[subj] = subject_count.get(subj, 0) + 1
        if not r.get("resolved", False):
            subject_unresolved[subj] = subject_unresolved.get(subj, 0) + 1

    # 按章节统计
    chapter_count = {}
    for r in data:
        ch = f"{r.get('subject', '')}·{r.get('chapter', '')}"
        if ch.strip() and ch != "·":
            chapter_count[ch] = chapter_count.get(ch, 0) + 1

    sorted_chapters = sorted(chapter_count.items(), key=lambda x: x[1], reverse=True)

    # 按错因统计
    error_type_count = {}
    for r in data:
        et = r.get("error_type", "其他")
        error_type_count[et] = error_type_count.get(et, 0) + 1

    # 高频薄弱知识点
    kp_count = {}
    for r in data:
        kp = r.get("knowledge_point", "")
        if kp:
            kp_count[kp] = kp_count.get(kp, 0) + 1
    sorted_kp = sorted(kp_count.items(), key=lambda x: x[1], reverse=True)[:10]

    # 消灭率
    resolve_rate = round((total - unresolved_count) / total * 100, 1) if total > 0 else 0.0

    # 本地权重标记
    local_weighted = [r for r in unresolved if r.get("local_weight")]
    local_weighted_count = len(local_weighted)

    output_json({
        "status": "success",
        "total": total,
        "unresolved_count": unresolved_count,
        "resolve_rate": resolve_rate,
        "week_count": week_count,
        "week_unresolved": week_unresolved,
        "subject_stats": [
            {"subject": s, "total": subject_count[s],
             "unresolved": subject_unresolved.get(s, 0)}
            for s in sorted(subject_count.keys())
        ],
        "hot_chapters": sorted_chapters[:15],
        "error_type_dist": error_type_count,
        "hot_knowledge_points": sorted_kp,
        "local_weighted_count": local_weighted_count,
    })


def cmd_resolve(args):
    """消灭一道错题（标记为已解决）。"""
    filepath = args.file if args.file else DEFAULT_FILE
    if args.file and not validate_filepath(filepath):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    data = load_data_list(filepath)

    if not data:
        output_json({"status": "error", "message": "暂无错题记录"})
        sys.exit(1)

    index = args.index
    if index < 0 or index >= len(data):
        output_json({"status": "error",
                     "message": f"索引越界，有效范围 0-{len(data) - 1}"})
        sys.exit(1)

    data[index]["resolved"] = True
    data[index]["resolved_at"] = datetime.now().isoformat()
    save_json(filepath, data)

    output_json({
        "status": "success",
        "message": "错题已消灭",
        "record": data[index],
    })


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="帧卷 - 作业自查雷达（错题管理）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python radar_manager.py add --subject "数学" --chapter "二次函数" --knowledge-point "配方法" --error-type "计算错"
  python radar_manager.py review --range week --limit 20
  python radar_manager.py review --range month --subject 数学 --unresolved
  python radar_manager.py analyze
  python radar_manager.py resolve --index 3
        """
    )
    parser.add_argument("--file",
                        help=f"指定数据文件路径（默认: ./{os.path.basename(DEFAULT_FILE)}）")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # add 子命令
    add_parser = subparsers.add_parser("add", help="录入一道错题")
    add_parser.add_argument("--subject", required=True, help="科目")
    add_parser.add_argument("--chapter", default="", help="章节（可选）")
    add_parser.add_argument("--knowledge-point", default="", help="知识点（可选）")
    add_parser.add_argument("--error-type", default="其他",
                            help=f"错因类型: {'/'.join(VALID_ERROR_TYPES)}")
    add_parser.add_argument("--note", default="", help="备注（可选）")
    add_parser.add_argument("--source", default="作业",
                            help=f"来源: {'/'.join(VALID_SOURCES)}")
    add_parser.add_argument("--exercise-id", default="", help="题目标识（可选，如'P58第3题'）")
    add_parser.add_argument("--local-weight", default="", help="本地权重标注（可选）")

    # review 子命令
    review_parser = subparsers.add_parser("review", help="查询错题列表")
    review_parser.add_argument("--range", default="week",
                               help=f"查询范围: {'/'.join(VALID_RANGES)}（默认: week）")
    review_parser.add_argument("--limit", type=int, default=50,
                               help="返回条数上限 1-200（默认50）")
    review_parser.add_argument("--subject", default="", help="按科目筛选（可选）")
    review_parser.add_argument("--unresolved", action="store_true",
                               help="仅显示未消灭的错题")

    # analyze 子命令
    subparsers.add_parser("analyze", help="生成学情分析报告")

    # resolve 子命令
    resolve_parser = subparsers.add_parser("resolve", help="消灭一道错题")
    resolve_parser.add_argument("--index", type=int, required=True,
                                help="错题索引（review 输出的 records 数组下标）")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "review":
        cmd_review(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "resolve":
        cmd_resolve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
