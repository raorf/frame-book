#!/usr/bin/env python3
"""
帧卷 - 成就管理脚本
支持记录、查询、分析个人成就数据。

用法:
    python achievement.py record --title "完成项目汇报" --category "职场" --importance 4
    python achievement.py query --range week --limit 10
    python achievement.py analyze
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

DEFAULT_FILE = default_filepath("achievements.json")
MAX_TITLE_LENGTH = 200
MAX_EMOTION_LENGTH = 50
MAX_FRAME_LENGTH = 250
VALID_CATEGORIES = ["职场", "学习", "健康", "关系", "创作", "科研", "生产", "其他"]
VALID_LEVELS = ["regular", "daily", "weekly", "monthly", "yearly"]
VALID_RANGES = ["today", "week", "all"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ============================================================
# 工具函数
# ============================================================

def validate_date(date_str):
    """验证日期格式是否为 YYYY-MM-DD 且为有效日期。"""
    if not date_str:
        return True
    if not DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_week_range(base_date=None):
    """获取本周的起止日期（周一为一周开始）。"""
    if base_date is None:
        base_date = datetime.now()
    monday = base_date - timedelta(days=base_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date(), sunday.date()


# ============================================================
# 命令处理函数
# ============================================================

def cmd_record(args):
    """记录一条成就。"""
    # 验证标题
    title = args.title.strip()
    if not title:
        output_json({"status": "error", "message": "标题不能为空"})
        sys.exit(1)
    if len(title) > MAX_TITLE_LENGTH:
        output_json({"status": "error", "message": f"标题过长，最大{MAX_TITLE_LENGTH}字符"})
        sys.exit(1)

    # 验证分类
    category = args.category
    if category not in VALID_CATEGORIES:
        output_json({
            "status": "error",
            "message": f"分类不合法，可选: {'/'.join(VALID_CATEGORIES)}"
        })
        sys.exit(1)

    # 验证重要性
    importance = args.importance if args.importance is not None else 3
    if not (1 <= importance <= 5):
        output_json({"status": "error", "message": "重要性必须在1-5范围内"})
        sys.exit(1)

    # 验证情绪描述
    emotion = args.emotion or ""
    if len(emotion) > MAX_EMOTION_LENGTH:
        output_json({"status": "error", "message": f"情绪描述过长，最大{MAX_EMOTION_LENGTH}字符"})
        sys.exit(1)

    # 验证图片帧路径
    frame = args.frame or ""
    if frame:
        if len(frame) > MAX_FRAME_LENGTH:
            output_json({"status": "error", "message": f"图片路径过长，最大{MAX_FRAME_LENGTH}字符"})
            sys.exit(1)
        if not validate_filepath(frame):
            output_json({"status": "error", "message": "图片路径不合法"})
            sys.exit(1)

    # 验证等级
    level = args.level if args.level else "regular"
    if level not in VALID_LEVELS:
        output_json({
            "status": "error",
            "message": f"记录等级不合法，可选: {'/'.join(VALID_LEVELS)}"
        })
        sys.exit(1)

    # 验证日期
    date = args.date if args.date else datetime.now().strftime("%Y-%m-%d")
    if not validate_date(date):
        output_json({"status": "error", "message": "日期格式错误，应为YYYY-MM-DD"})
        sys.exit(1)

    # 构建记录
    record = {
        "date": date,
        "title": title,
        "category": category,
        "importance": importance,
        "emotion": emotion,
        "frame": frame,
        "level": level,
        "timestamp": datetime.now().isoformat()
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
        "message": f"成就已记录: {title}",
        "record": record,
        "total_count": len(data)
    })


def cmd_query(args):
    """查询成就列表。"""
    filepath = args.file if args.file else DEFAULT_FILE
    if args.file and not validate_filepath(filepath):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)

    data = load_data_list(filepath)

    # 范围筛选
    range_type = args.range if args.range else "today"
    if range_type not in VALID_RANGES:
        output_json({"status": "error", "message": f"范围不合法，可选: {'/'.join(VALID_RANGES)}"})
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
    else:  # all
        filtered = data

    # 按时间戳倒序排列
    filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    # 限制返回数量
    limit = args.limit if args.limit else 5
    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100
    filtered = filtered[:limit]

    output_json({
        "status": "success",
        "total": len(data),
        "filtered_count": len(filtered),
        "range": range_type,
        "records": filtered
    })


def cmd_analyze(args):
    """生成成长分析简报。"""
    filepath = args.file if args.file else DEFAULT_FILE
    if args.file and not validate_filepath(filepath):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)

    data = load_data_list(filepath)

    total = len(data)

    # 本周计数
    monday, sunday = get_week_range()
    week_count = 0
    for r in data:
        try:
            r_date = datetime.strptime(r.get("date", ""), "%Y-%m-%d").date()
            if monday <= r_date <= sunday:
                week_count += 1
        except ValueError:
            continue

    # 上周计数
    last_monday = monday - timedelta(days=7)
    last_sunday = monday - timedelta(days=1)
    last_week_count = 0
    for r in data:
        try:
            r_date = datetime.strptime(r.get("date", ""), "%Y-%m-%d").date()
            if last_monday <= r_date <= last_sunday:
                last_week_count += 1
        except ValueError:
            continue

    # 环比增长率
    if last_week_count > 0:
        growth_rate = round((week_count - last_week_count) / last_week_count, 2)
    elif week_count > 0:
        growth_rate = 1.0
    else:
        growth_rate = 0.0

    # 分类统计
    category_count = {cat: 0 for cat in VALID_CATEGORIES}
    for r in data:
        cat = r.get("category", "")
        if cat in category_count:
            category_count[cat] += 1

    # 高频分类
    top_category = max(category_count, key=category_count.get) if total > 0 else ""
    top_category_count = category_count.get(top_category, 0)

    # 情绪统计
    emotion_count = {}
    for r in data:
        emo = r.get("emotion", "")
        if emo:
            emotion_count[emo] = emotion_count.get(emo, 0) + 1
    top_emotion = max(emotion_count, key=emotion_count.get) if emotion_count else ""

    output_json({
        "status": "success",
        "total": total,
        "week_count": week_count,
        "last_week_count": last_week_count,
        "growth_rate": growth_rate,
        "top_category": top_category,
        "top_category_count": top_category_count,
        "top_emotion": top_emotion,
        "category": category_count
    })


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="帧卷 - 成就管理脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python achievement.py record --title "完成项目汇报" --category "职场" --importance 4
  python achievement.py query --range week --limit 10
  python achievement.py analyze
        """
    )
    parser.add_argument("--file", help="指定数据文件路径（默认: ./achievements.json）")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # record 子命令
    record_parser = subparsers.add_parser("record", help="记录一条成就")
    record_parser.add_argument("--title", required=True, help="成就标题（最大200字符）")
    record_parser.add_argument("--category", required=True, help=f"分类: {'/'.join(VALID_CATEGORIES)}")
    record_parser.add_argument("--importance", type=int, default=3, help="重要性 1-5（默认3）")
    record_parser.add_argument("--emotion", default="", help="情绪描述或emoji（最大50字符）")
    record_parser.add_argument("--frame", default="", help="图片帧路径（相对路径或文件名）")
    record_parser.add_argument("--level", default="regular", help=f"记录等级: {'/'.join(VALID_LEVELS)}")
    record_parser.add_argument("--date", default="", help="成就日期 YYYY-MM-DD（默认今天）")

    # query 子命令
    query_parser = subparsers.add_parser("query", help="查询成就列表")
    query_parser.add_argument("--range", default="today", help=f"查询范围: {'/'.join(VALID_RANGES)}")
    query_parser.add_argument("--limit", type=int, default=5, help="返回条数上限 1-100（默认5）")

    # analyze 子命令
    subparsers.add_parser("analyze", help="生成成长分析简报")

    args = parser.parse_args()

    if args.command == "record":
        cmd_record(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
