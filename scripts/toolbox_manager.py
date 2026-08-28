#!/usr/bin/env python3
"""
帧卷 - 学习工具箱脚本
记忆复习（按遗忘曲线）、番茄计时器管理。

用法:
    python toolbox_manager.py review --count 10          # 获取今日应复习条目
    python toolbox_manager.py mark --index 2 --rating easy    # 标记复习完成
    python toolbox_manager.py tomato_start --task "复习数学错题"
    python toolbox_manager.py tomato_status              # 查看当前番茄钟
    python toolbox_manager.py tomato_cancel              # 取消当前番茄钟
    python toolbox_manager.py tomato_done                # 结束当前番茄钟并记录
    python toolbox_manager.py tomato_stats --range week  # 番茄钟统计
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

from common import (
    output_json,
    validate_filepath,
    load_json,
    save_json,
    default_filepath,
)

# ============================================================
# 常量定义
# ============================================================

DEFAULT_STATE_FILE = default_filepath("toolbox_state.json")
DEFAULT_RADAR_FILE = default_filepath("radar_data.json")

DEFAULT_TOMATO_MINUTES = 25
BREAK_MINUTES = 5

VALID_RATINGS = ["easy", "medium", "hard"]
VALID_RANGES = ["today", "week", "month", "all"]

EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]


# ============================================================
# 工具函数
# ============================================================

def load_state(state_filepath):
    """加载工具箱状态。"""
    state = load_json(state_filepath, default=None)
    if state is None:
        state = {
            "tomato": {
                "active": False,
                "started_at": None,
                "task": "",
                "duration_minutes": DEFAULT_TOMATO_MINUTES,
                "interrupted": False,
            },
            "pomodoro_log": [],
            "review_schedule": {},
        }
    return state


def save_state(state_filepath, state):
    """保存工具箱状态。"""
    save_json(state_filepath, state)


def load_radar(radar_filepath):
    """加载错题雷达数据。"""
    data = load_json(radar_filepath, default=None)
    if not isinstance(data, list):
        return []
    return data


def ebbinghaus_next_review(last_review_date, box):
    """根据艾宾浩斯曲线计算下一次复习日期。"""
    interval = EBBINGHAUS_INTERVALS[min(box, len(EBBINGHAUS_INTERVALS) - 1)]
    next_date = last_review_date + timedelta(days=interval)
    return next_date.strftime("%Y-%m-%d"), min(box + 1, len(EBBINGHAUS_INTERVALS) - 1)


def get_week_range(base_date=None):
    """获取本周的起止日期（周一为一周开始）。"""
    if base_date is None:
        base_date = datetime.now()
    monday = base_date - timedelta(days=base_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date(), sunday.date()


# ============================================================
# 记忆复习功能
# ============================================================

def cmd_review(args):
    """按遗忘曲线筛选今日应复习的条目。"""
    state = load_state(args.state_file)
    radar_data = load_radar(args.radar_file)

    today = datetime.now().strftime("%Y-%m-%d")
    items_due = []

    # 从错题库中筛选：有复习计划且到期的
    review_schedule = state.get("review_schedule", {})
    for idx, record in enumerate(radar_data):
        if record.get("resolved", False):
            continue

        record_id = str(idx)
        schedule = review_schedule.get(record_id, {})
        next_date = schedule.get("next_review_date")

        if next_date and next_date <= today:
            items_due.append({
                "source": "错题",
                "index": idx,
                "subject": record.get("subject", ""),
                "chapter": record.get("chapter", ""),
                "knowledge_point": record.get("knowledge_point", ""),
                "error_type": record.get("error_type", ""),
                "note": record.get("note", ""),
                "box": schedule.get("box", 0),
                "days_overdue": (datetime.strptime(today, "%Y-%m-%d")
                                 - datetime.strptime(next_date, "%Y-%m-%d")).days,
                "needs_review": True,
            })
        elif not next_date:
            # 从未安排过复习 → 今日优先处理
            items_due.append({
                "source": "错题",
                "index": idx,
                "subject": record.get("subject", ""),
                "chapter": record.get("chapter", ""),
                "knowledge_point": record.get("knowledge_point", ""),
                "error_type": record.get("error_type", ""),
                "note": record.get("note", ""),
                "box": 0,
                "days_overdue": 0,
                "needs_review": True,
            })

    items_due.sort(key=lambda x: x.get("days_overdue", 0), reverse=True)

    count = args.count if args.count else 10
    items_due = items_due[:count]

    output_json({
        "status": "success",
        "date": today,
        "total_due": len(items_due),
        "items": items_due,
        "hint": "使用 'mark --index N --rating easy|medium|hard' 标记完成",
    })


def cmd_mark(args):
    """标记某个复习条目的完成情况，更新遗忘曲线。"""
    state = load_state(args.state_file)
    radar_data = load_radar(args.radar_file)

    index = args.index
    rating = args.rating if args.rating in VALID_RATINGS else "medium"

    if index < 0 or index >= len(radar_data):
        output_json({"status": "error",
                     "message": f"索引越界，有效范围 0-{len(radar_data) - 1}"})
        sys.exit(1)

    today = datetime.now()
    record_id = str(index)
    review_schedule = state.get("review_schedule", {})

    current_box = review_schedule.get(record_id, {}).get("box", 0)

    if rating == "easy":
        # 轻松答对 → 升级
        next_date, new_box = ebbinghaus_next_review(today, current_box)
    elif rating == "medium":
        # 有些吃力 → 保持当前级别
        interval = EBBINGHAUS_INTERVALS[current_box]
        next_date = (today + timedelta(days=interval)).strftime("%Y-%m-%d")
        new_box = current_box
    else:  # hard
        # 卡壳了 → 降级
        new_box = max(current_box - 1, 0)
        interval = EBBINGHAUS_INTERVALS[new_box]
        next_date = (today + timedelta(days=interval)).strftime("%Y-%m-%d")

    review_schedule[record_id] = {
        "last_review_date": today.strftime("%Y-%m-%d"),
        "next_review_date": next_date,
        "box": new_box,
        "rating": rating,
    }
    state["review_schedule"] = review_schedule
    save_state(args.state_file, state)

    output_json({
        "status": "success",
        "message": f"复习已标记 [{rating}]，下次复习: {next_date}（箱 {new_box + 1}）",
        "subject": radar_data[index].get("subject", ""),
        "chapter": radar_data[index].get("chapter", ""),
        "next_review_date": next_date,
        "next_box": new_box,
    })


# ============================================================
# 番茄钟功能
# ============================================================

def cmd_tomato_start(args):
    """开始一个番茄钟。"""
    state = load_state(args.state_file)

    if state["tomato"]["active"]:
        output_json({
            "status": "warning",
            "message": "已有进行中的番茄钟",
            "current": state["tomato"],
        })
        sys.exit(0)

    task = args.task if args.task else "专注任务"
    minutes = args.minutes if args.minutes else DEFAULT_TOMATO_MINUTES

    state["tomato"] = {
        "active": True,
        "started_at": datetime.now().isoformat(),
        "task": task,
        "duration_minutes": minutes,
        "interrupted": False,
    }
    save_state(args.state_file, state)

    end_time = datetime.now() + timedelta(minutes=minutes)
    output_json({
        "status": "success",
        "message": f"🍅 番茄钟开始！{minutes}分钟后结束",
        "task": task,
        "ends_at": end_time.strftime("%H:%M"),
        "duration_minutes": minutes,
        "command_to_end": "tomato_done",
        "command_to_cancel": "tomato_cancel",
    })


def cmd_tomato_status(args):
    """查看当前番茄钟状态。"""
    state = load_state(args.state_file)

    if not state["tomato"]["active"]:
        output_json({
            "status": "idle",
            "message": "当前没有进行中的番茄钟",
        })
        return

    started = datetime.fromisoformat(state["tomato"]["started_at"])
    duration_minutes = state["tomato"]["duration_minutes"]
    elapsed = (datetime.now() - started).total_seconds()
    total_seconds = duration_minutes * 60
    remaining = max(0, int(total_seconds - elapsed))
    progress = min(100, int(elapsed / total_seconds * 100))

    output_json({
        "status": "running",
        "task": state["tomato"]["task"],
        "started_at": state["tomato"]["started_at"],
        "duration_minutes": duration_minutes,
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": remaining,
        "remaining_text": f"{remaining // 60}:{remaining % 60:02d}",
        "progress_percent": progress,
        "interrupted": state["tomato"]["interrupted"],
    })


def cmd_tomato_cancel(args):
    """取消当前番茄钟（中断）。"""
    state = load_state(args.state_file)

    if not state["tomato"]["active"]:
        output_json({"status": "idle", "message": "当前没有进行中的番茄钟"})
        return

    task = state["tomato"]["task"]
    started = datetime.fromisoformat(state["tomato"]["started_at"])
    elapsed_minutes = round((datetime.now() - started).total_seconds() / 60, 1)

    # 记录到日志
    state["pomodoro_log"].append({
        "date": started.strftime("%Y-%m-%d"),
        "started_at": started.isoformat(),
        "task": task,
        "duration_minutes": state["tomato"]["duration_minutes"],
        "actual_minutes": elapsed_minutes,
        "completed": False,
        "interrupted": True,
    })

    state["tomato"] = {
        "active": False,
        "started_at": None,
        "task": "",
        "duration_minutes": DEFAULT_TOMATO_MINUTES,
        "interrupted": False,
    }
    save_state(args.state_file, state)

    output_json({
        "status": "success",
        "message": f"番茄钟已取消（{task}，进行了 {elapsed_minutes} 分钟）",
        "task": task,
        "actual_minutes": elapsed_minutes,
    })


def cmd_tomato_done(args):
    """结束当前番茄钟并记录完成。"""
    state = load_state(args.state_file)

    if not state["tomato"]["active"]:
        output_json({"status": "idle", "message": "当前没有进行中的番茄钟"})
        return

    task = state["tomato"]["task"]
    started = datetime.fromisoformat(state["tomato"]["started_at"])
    elapsed_minutes = round((datetime.now() - started).total_seconds() / 60, 1)

    state["pomodoro_log"].append({
        "date": started.strftime("%Y-%m-%d"),
        "started_at": started.isoformat(),
        "task": task,
        "duration_minutes": state["tomato"]["duration_minutes"],
        "actual_minutes": elapsed_minutes,
        "completed": True,
        "interrupted": False,
    })

    state["tomato"] = {
        "active": False,
        "started_at": None,
        "task": "",
        "duration_minutes": DEFAULT_TOMATO_MINUTES,
        "interrupted": False,
    }
    save_state(args.state_file, state)

    output_json({
        "status": "success",
        "message": f"🎉 番茄钟完成！{task}，实际用时 {elapsed_minutes} 分钟",
        "task": task,
        "actual_minutes": elapsed_minutes,
        "completed": True,
    })


def cmd_tomato_stats(args):
    """番茄钟统计。"""
    state = load_state(args.state_file)
    log = state.get("pomodoro_log", [])

    range_type = args.range if args.range else "week"
    if range_type not in VALID_RANGES:
        output_json({"status": "error",
                     "message": f"范围不合法，可选: {'/'.join(VALID_RANGES)}"})
        sys.exit(1)

    today = datetime.now().date()
    filtered = []

    if range_type == "today":
        today_str = today.strftime("%Y-%m-%d")
        filtered = [e for e in log if e.get("date") == today_str]
    elif range_type == "week":
        monday, sunday = get_week_range()
        for e in log:
            try:
                e_date = datetime.strptime(e.get("date", ""), "%Y-%m-%d").date()
                if monday <= e_date <= sunday:
                    filtered.append(e)
            except ValueError:
                continue
    elif range_type == "month":
        filtered = [e for e in log
                    if datetime.strptime(e.get("date", ""), "%Y-%m-%d").date().month == today.month]
    else:  # all
        filtered = log

    completed = [e for e in filtered if e.get("completed")]
    interrupted = [e for e in filtered if e.get("interrupted")]
    total_minutes = round(sum(e.get("actual_minutes", 0) for e in completed), 1)
    completion_rate = round(len(completed) / len(filtered) * 100, 1) if filtered else 0.0

    # 按任务统计
    task_count = {}
    for e in completed:
        t = e.get("task", "")
        task_count[t] = task_count.get(t, 0) + 1

    output_json({
        "status": "success",
        "range": range_type,
        "total_sessions": len(filtered),
        "completed": len(completed),
        "interrupted": len(interrupted),
        "completion_rate": completion_rate,
        "total_minutes": total_minutes,
        "task_distribution": task_count,
    })


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="帧卷 - 学习工具箱（记忆复习 + 番茄钟）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python toolbox_manager.py --file custom_state.json review --count 10
  python toolbox_manager.py --radar-file my_radar.json mark --index 2 --rating easy
  python toolbox_manager.py tomato_start --task "复习数学错题"
  python toolbox_manager.py tomato_status
  python toolbox_manager.py tomato_stats --range week
        """
    )
    parser.add_argument("--file", dest="state_file_arg",
                        help=f"工具箱状态文件路径（默认: {os.path.basename(DEFAULT_STATE_FILE)}）")
    parser.add_argument("--radar-file", dest="radar_file_arg",
                        help=f"错题雷达文件路径（默认: {os.path.basename(DEFAULT_RADAR_FILE)}）")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # review 子命令
    review_parser = subparsers.add_parser("review", help="获取今日应复习的条目（艾宾浩斯曲线）")
    review_parser.add_argument("--count", type=int, default=10,
                              help="返回条目数量上限（默认10）")

    # mark 子命令
    mark_parser = subparsers.add_parser("mark", help="标记复习完成，更新遗忘曲线")
    mark_parser.add_argument("--index", type=int, required=True,
                             help="条目索引（review 输出的 items 数组下标）")
    mark_parser.add_argument("--rating", default="medium",
                             help=f"自评: {'/'.join(VALID_RATINGS)}（默认: medium）")

    # tomato_start 子命令
    tomato_start_parser = subparsers.add_parser("tomato_start", help="开始番茄钟")
    tomato_start_parser.add_argument("--task", default="专注任务", help="任务描述")
    tomato_start_parser.add_argument("--minutes", type=int, default=DEFAULT_TOMATO_MINUTES,
                                     help=f"时长（分钟，默认{DEFAULT_TOMATO_MINUTES}）")

    # tomato_status 子命令
    subparsers.add_parser("tomato_status", help="查看当前番茄钟状态")

    # tomato_cancel 子命令
    subparsers.add_parser("tomato_cancel", help="取消当前番茄钟（中断）")

    # tomato_done 子命令
    subparsers.add_parser("tomato_done", help="结束当前番茄钟并记录完成")

    # tomato_stats 子命令
    tomato_stats_parser = subparsers.add_parser("tomato_stats", help="番茄钟统计")
    tomato_stats_parser.add_argument("--range", default="week",
                                     help=f"统计范围: {'/'.join(VALID_RANGES)}（默认: week）")

    args = parser.parse_args()

    # 解析并验证文件路径
    state_file = args.state_file_arg if args.state_file_arg else DEFAULT_STATE_FILE
    radar_file = args.radar_file_arg if args.radar_file_arg else DEFAULT_RADAR_FILE
    if args.state_file_arg and not validate_filepath(state_file):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    if args.radar_file_arg and not validate_filepath(radar_file):
        output_json({"status": "error", "message": "--radar-file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    args.state_file = state_file
    args.radar_file = radar_file

    if args.command == "review":
        cmd_review(args)
    elif args.command == "mark":
        cmd_mark(args)
    elif args.command == "tomato_start":
        cmd_tomato_start(args)
    elif args.command == "tomato_status":
        cmd_tomato_status(args)
    elif args.command == "tomato_cancel":
        cmd_tomato_cancel(args)
    elif args.command == "tomato_done":
        cmd_tomato_done(args)
    elif args.command == "tomato_stats":
        cmd_tomato_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
