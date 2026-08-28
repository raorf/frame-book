#!/usr/bin/env python3
"""
帧卷 - 学习数据底座管理脚本
管理学生学习档案：年级、学期、城市、课表、教材版本、学习进度、薄弱点。
支持生成明日课程准备清单（一课一清单）。

用法:
    python learning_manager.py setup --grade "八年级上" --city "南昌"
    python learning_manager.py show
    python learning_manager.py schedule --day monday --data '[{"period":1,"subject":"数学","time":"08:00-08:45"}]'
    python learning_manager.py textbook --subject "数学" --version "人教版A版"
    python learning_manager.py progress --subject "数学" --chapter "一元二次方程" --page 34
    python learning_manager.py weakness --subject "数学" --items '["配方法","几何证明"]'
    python learning_manager.py tomorrow
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
    load_json,
    save_json,
    default_filepath,
)

# ============================================================
# 常量定义
# ============================================================

DEFAULT_FILE = default_filepath("learning_profile.json")
MAX_GRADE_LENGTH = 20
MAX_CITY_LENGTH = 20
MAX_SUBJECT_LENGTH = 20
MAX_VERSION_LENGTH = 50
MAX_CHAPTER_LENGTH = 100
MAX_SECTION_LENGTH = 100
MAX_UNIT_LENGTH = 50
VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday",
              "friday", "saturday", "sunday"]
WEEKDAY_MAP = {
    0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
    4: "friday", 5: "saturday", 6: "sunday"
}
REQUIRED_SCHEDULE_FIELDS = ["period", "subject", "time"]


# ============================================================
# 工具函数
# ============================================================

def validate_input(value, max_length, field_name):
    """验证输入字符串：非空、长度限制。"""
    if not value or not value.strip():
        output_json({"status": "error", "message": f"{field_name}不能为空"})
        sys.exit(1)
    value = value.strip()
    if len(value) > max_length:
        output_json({"status": "error",
                     "message": f"{field_name}过长，最大{max_length}字符"})
        sys.exit(1)
    return value


def create_empty_profile():
    """创建空的学习档案结构。"""
    now = datetime.now().isoformat()
    return {
        "grade": "",
        "semester": "",
        "city": "",
        "school": "",
        "class": "",
        "schedule": {day: [] for day in VALID_DAYS},
        "textbooks": {},
        "progress": {},
        "weakness": {},
        "created_at": now,
        "updated_at": now
    }


def load_data(filepath):
    """加载学习档案，补齐缺失字段（静默降级）。"""
    empty = create_empty_profile()
    data = load_json(filepath, default=None)
    if not isinstance(data, dict):
        return empty
    for key in ["grade", "semester", "city", "school", "class"]:
        if key not in data or not isinstance(data[key], str):
            data[key] = ""
    if "schedule" not in data or not isinstance(data["schedule"], dict):
        data["schedule"] = {day: [] for day in VALID_DAYS}
    else:
        for day in VALID_DAYS:
            if day not in data["schedule"] or \
               not isinstance(data["schedule"][day], list):
                data["schedule"][day] = []
    for key in ["textbooks", "progress", "weakness"]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
    if "created_at" not in data:
        data["created_at"] = empty["created_at"]
    if "updated_at" not in data:
        data["updated_at"] = empty["updated_at"]
    return data


def save_data(filepath, data):
    """保存学习档案，自动刷新 updated_at。"""
    data["updated_at"] = datetime.now().isoformat()
    save_json(filepath, data)


def parse_json_string(json_str, field_name):
    """安全解析 JSON 字符串。"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        output_json({"status": "error",
                     "message": f"{field_name} JSON 解析失败: {e}"})
        sys.exit(1)


def get_filepath(args):
    """从参数获取文件路径并验证安全性。"""
    filepath = args.file if args.file else DEFAULT_FILE
    if not validate_filepath(filepath):
        output_json({"status": "error", "message": "文件路径不合法"})
        sys.exit(1)
    return filepath


# ============================================================
# 命令处理函数
# ============================================================

def cmd_setup(args):
    """初始化或更新学习档案。"""
    grade = validate_input(args.grade, MAX_GRADE_LENGTH, "年级")
    city = validate_input(args.city, MAX_CITY_LENGTH, "城市")

    semester = ""
    if args.semester:
        semester = args.semester.strip()
        if len(semester) > MAX_GRADE_LENGTH:
            output_json({"status": "error",
                         "message": f"学期过长，最大{MAX_GRADE_LENGTH}字符"})
            sys.exit(1)

    school = ""
    if args.school:
        school = args.school.strip()
        if len(school) > MAX_CITY_LENGTH:
            output_json({"status": "error",
                         "message": f"学校名过长，最大{MAX_CITY_LENGTH}字符"})
            sys.exit(1)

    class_name = ""
    if args.class_name:
        class_name = args.class_name.strip()
        if len(class_name) > MAX_GRADE_LENGTH:
            output_json({"status": "error",
                         "message": f"班级过长，最大{MAX_GRADE_LENGTH}字符"})
            sys.exit(1)

    filepath = get_filepath(args)
    file_exists = os.path.exists(filepath)
    data = load_data(filepath)

    data["grade"] = grade
    data["city"] = city
    if semester:
        data["semester"] = semester
    if school:
        data["school"] = school
    if class_name:
        data["class"] = class_name
    if not file_exists:
        data["created_at"] = datetime.now().isoformat()

    save_data(filepath, data)

    output_json({
        "status": "success",
        "message": f"学习档案已{'更新' if file_exists else '创建'}",
        "profile": data
    })


def cmd_show(args):
    """显示当前学习档案。"""
    filepath = get_filepath(args)
    data = load_data(filepath)
    output_json(data)


def cmd_schedule(args):
    """设置某天的课表。"""
    day = args.day.lower()
    if day not in VALID_DAYS:
        output_json({"status": "error",
                     "message": f"星期不合法，可选: {'/'.join(VALID_DAYS)}"})
        sys.exit(1)

    schedule_data = parse_json_string(args.data, "课表数据")
    if not isinstance(schedule_data, list):
        output_json({"status": "error", "message": "课表数据必须是JSON数组"})
        sys.exit(1)

    # 验证每条课表记录
    for i, entry in enumerate(schedule_data):
        if not isinstance(entry, dict):
            output_json({"status": "error",
                         "message": f"第{i + 1}条课表记录格式错误，应为JSON对象"})
            sys.exit(1)
        for field in REQUIRED_SCHEDULE_FIELDS:
            if field not in entry:
                output_json({"status": "error",
                             "message": f"第{i + 1}条课表记录缺少字段: {field}"})
                sys.exit(1)
        # 验证 period 为正整数
        if not isinstance(entry["period"], int) or entry["period"] < 1:
            output_json({"status": "error",
                         "message": f"第{i + 1}条课表记录的period必须为正整数"})
            sys.exit(1)
        # 验证 subject
        if not isinstance(entry["subject"], str) or not entry["subject"].strip():
            output_json({"status": "error",
                         "message": f"第{i + 1}条课表记录的subject不能为空"})
            sys.exit(1)
        if len(entry["subject"]) > MAX_SUBJECT_LENGTH:
            output_json({"status": "error",
                         "message": f"第{i + 1}条课表记录的subject过长"})
            sys.exit(1)
        # 验证 time
        if not isinstance(entry["time"], str) or not entry["time"].strip():
            output_json({"status": "error",
                         "message": f"第{i + 1}条课表记录的time不能为空"})
            sys.exit(1)

    filepath = get_filepath(args)
    data = load_data(filepath)
    data["schedule"][day] = schedule_data
    save_data(filepath, data)

    output_json({
        "status": "success",
        "message": f"{day}课表已设置（{len(schedule_data)}节课）",
        "day": day,
        "schedule": schedule_data
    })


def cmd_textbook(args):
    """设置教材版本。"""
    subject = validate_input(args.subject, MAX_SUBJECT_LENGTH, "科目")
    version = validate_input(args.version, MAX_VERSION_LENGTH, "教材版本")

    filepath = get_filepath(args)
    data = load_data(filepath)
    data["textbooks"][subject] = version
    save_data(filepath, data)

    output_json({
        "status": "success",
        "message": f"{subject}教材已设置为: {version}",
        "subject": subject,
        "version": version
    })


def cmd_progress(args):
    """更新学习进度。"""
    subject = validate_input(args.subject, MAX_SUBJECT_LENGTH, "科目")
    chapter = validate_input(args.chapter, MAX_CHAPTER_LENGTH, "章节")

    section = ""
    if args.section:
        section = args.section.strip()
        if len(section) > MAX_SECTION_LENGTH:
            output_json({"status": "error",
                         "message": f"小节过长，最大{MAX_SECTION_LENGTH}字符"})
            sys.exit(1)

    unit = ""
    if args.unit:
        unit = args.unit.strip()
        if len(unit) > MAX_UNIT_LENGTH:
            output_json({"status": "error",
                         "message": f"单元过长，最大{MAX_UNIT_LENGTH}字符"})
            sys.exit(1)

    page = args.page if args.page is not None else None

    filepath = get_filepath(args)
    data = load_data(filepath)
    data["progress"][subject] = {
        "unit": unit,
        "chapter": chapter,
        "section": section,
        "page": page
    }
    save_data(filepath, data)

    output_json({
        "status": "success",
        "message": f"{subject}学习进度已更新",
        "subject": subject,
        "progress": data["progress"][subject]
    })


def cmd_weakness(args):
    """设置科目薄弱点。"""
    subject = validate_input(args.subject, MAX_SUBJECT_LENGTH, "科目")

    items = parse_json_string(args.items, "薄弱点")
    if not isinstance(items, list):
        output_json({"status": "error", "message": "薄弱点数据必须是JSON数组"})
        sys.exit(1)

    # 验证每个薄弱点
    validated_items = []
    for i, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            output_json({"status": "error",
                         "message": f"第{i + 1}个薄弱点必须为非空字符串"})
            sys.exit(1)
        if len(item) > MAX_CHAPTER_LENGTH:
            output_json({"status": "error",
                         "message": f"第{i + 1}个薄弱点过长，"
                                    f"最大{MAX_CHAPTER_LENGTH}字符"})
            sys.exit(1)
        validated_items.append(item.strip())

    filepath = get_filepath(args)
    data = load_data(filepath)
    data["weakness"][subject] = validated_items
    save_data(filepath, data)

    output_json({
        "status": "success",
        "message": f"{subject}薄弱点已设置（{len(validated_items)}项）",
        "subject": subject,
        "weakness": validated_items
    })


def cmd_tomorrow(args):
    """生成明日课程准备清单（一课一清单）。"""
    filepath = get_filepath(args)
    data = load_data(filepath)

    # 计算明天的日期和星期
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date = tomorrow.strftime("%Y-%m-%d")
    tomorrow_weekday_num = tomorrow.weekday()
    tomorrow_weekday = WEEKDAY_MAP[tomorrow_weekday_num]
    is_weekend = tomorrow_weekday_num >= 5

    # 获取明天的课表
    schedule = data.get("schedule", {})
    classes = schedule.get(tomorrow_weekday, [])

    if not classes:
        status = "weekend" if is_weekend else "no_classes"
        message = "明天是周末，无需上课" if is_weekend else "明天没有课程安排"
        output_json({
            "status": status,
            "date": tomorrow_date,
            "weekday": tomorrow_weekday,
            "message": message,
            "classes": [],
            "items_to_bring": []
        })
        return

    textbooks = data.get("textbooks", {})
    progress = data.get("progress", {})
    weakness = data.get("weakness", {})

    class_list = []
    items_to_bring = set()

    for entry in classes:
        subject = entry.get("subject", "")
        period = entry.get("period", 0)
        time = entry.get("time", "")

        # 交叉引用教材版本
        textbook = textbooks.get(subject, "未设置")

        # 交叉引用学习进度
        subj_progress = progress.get(subject, {})
        current_chapter = subj_progress.get("chapter", "")
        current_section = subj_progress.get("section", "")
        current_page = subj_progress.get("page")

        # 交叉引用薄弱点
        weak_points = weakness.get(subject, [])

        # 生成预测主题
        if current_chapter and current_section:
            predicted_topic = f"{current_chapter}—{current_section}"
        elif current_chapter:
            predicted_topic = current_chapter
        elif current_section:
            predicted_topic = current_section
        else:
            predicted_topic = "待定"

        # 生成预习建议
        if current_page and weak_points:
            weak_str = "、".join(weak_points)
            preparation = f"建议今晚重点看课本P{current_page}，复习{weak_str}"
        elif current_page:
            preparation = (f"建议今晚预习课本P{current_page}，"
                           f"了解{current_chapter or '明日内容'}")
        elif weak_points:
            weak_str = "、".join(weak_points)
            preparation = f"建议今晚复习{weak_str}相关内容"
        else:
            preparation = f"建议今晚预习{current_chapter or subject}相关内容"

        # 生成建议带的问题
        questions = []
        for wp in weak_points:
            questions.append(f"关于{wp}，还有哪些不清楚的地方？")
        if not questions:
            if current_chapter:
                questions.append(f"{current_chapter}的重点和难点是什么？")
            questions.append(f"明天{subject}课需要重点听什么？")

        # 收集携带物品
        items_to_bring.add(f"{subject}课本")
        items_to_bring.add(f"{subject}练习册")

        class_list.append({
            "period": period,
            "subject": subject,
            "time": time,
            "textbook": textbook,
            "current_chapter": current_chapter,
            "current_section": current_section,
            "predicted_topic": predicted_topic,
            "weak_points": weak_points,
            "preparation": preparation,
            "questions_to_bring": questions
        })

    # 添加通用物品
    items_to_bring.add("笔记本")
    items_to_bring.add("草稿纸")

    output_json({
        "status": "success",
        "date": tomorrow_date,
        "weekday": tomorrow_weekday,
        "classes": class_list,
        "items_to_bring": list(items_to_bring)
    })


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="帧卷 - 学习数据底座管理脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python learning_manager.py setup --grade "八年级上" --city "南昌"
  python learning_manager.py show
  python learning_manager.py schedule --day monday --data '[{"period":1,"subject":"数学","time":"08:00-08:45"}]'
  python learning_manager.py textbook --subject "数学" --version "人教版A版"
  python learning_manager.py progress --subject "数学" --chapter "一元二次方程" --page 34
  python learning_manager.py weakness --subject "数学" --items '["配方法"]'
  python learning_manager.py tomorrow
        """
    )
    parser.add_argument("--file",
                        help="指定数据文件路径（默认: ./learning_profile.json）")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # setup 子命令
    setup_parser = subparsers.add_parser("setup", help="初始化或更新学习档案")
    setup_parser.add_argument("--grade", required=True,
                              help=f"年级（最大{MAX_GRADE_LENGTH}字符）")
    setup_parser.add_argument("--city", required=True,
                              help=f"城市（最大{MAX_CITY_LENGTH}字符）")
    setup_parser.add_argument("--semester", default="",
                              help="学期，如 2026春（可选）")
    setup_parser.add_argument("--school", default="",
                              help="学校名（可选，最大{MAX_CITY_LENGTH}字符）")
    setup_parser.add_argument("--class-name", default="",
                              dest="class_name",
                              help="班级（可选，最大{MAX_GRADE_LENGTH}字符）")

    # show 子命令
    subparsers.add_parser("show", help="显示当前学习档案")

    # schedule 子命令
    schedule_parser = subparsers.add_parser("schedule", help="设置某天的课表")
    schedule_parser.add_argument("--day", required=True,
                                 help=f"星期: {'/'.join(VALID_DAYS)}")
    schedule_parser.add_argument("--data", required=True,
                                 help="课表JSON数组字符串")

    # textbook 子命令
    textbook_parser = subparsers.add_parser("textbook", help="设置教材版本")
    textbook_parser.add_argument("--subject", required=True,
                                 help=f"科目（最大{MAX_SUBJECT_LENGTH}字符）")
    textbook_parser.add_argument("--version", required=True,
                                 help=f"教材版本（最大{MAX_VERSION_LENGTH}字符）")

    # progress 子命令
    progress_parser = subparsers.add_parser("progress", help="更新学习进度")
    progress_parser.add_argument("--subject", required=True,
                                help=f"科目（最大{MAX_SUBJECT_LENGTH}字符）")
    progress_parser.add_argument("--chapter", required=True,
                                help=f"章节（最大{MAX_CHAPTER_LENGTH}字符）")
    progress_parser.add_argument("--section", default="",
                                help=f"小节（可选，最大{MAX_SECTION_LENGTH}字符）")
    progress_parser.add_argument("--page", type=int, default=None,
                                help="页码（可选，整数）")
    progress_parser.add_argument("--unit", default="",
                                help=f"单元（可选，最大{MAX_UNIT_LENGTH}字符）")

    # weakness 子命令
    weakness_parser = subparsers.add_parser("weakness", help="设置科目薄弱点")
    weakness_parser.add_argument("--subject", required=True,
                                help=f"科目（最大{MAX_SUBJECT_LENGTH}字符）")
    weakness_parser.add_argument("--items", required=True,
                                help="薄弱点JSON数组字符串")

    # tomorrow 子命令
    subparsers.add_parser("tomorrow", help="生成明日课程准备清单")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "textbook":
        cmd_textbook(args)
    elif args.command == "progress":
        cmd_progress(args)
    elif args.command == "weakness":
        cmd_weakness(args)
    elif args.command == "tomorrow":
        cmd_tomorrow(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
