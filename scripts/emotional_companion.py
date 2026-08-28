#!/usr/bin/env python3
"""
帧卷 - 情感伴学陪练脚本
虚拟家长/宠物陪伴：辅导引导、陪练互动、情绪疏导、安全预警。

用法:
    python emotional_companion.py setup --role parent --nickname "宝宝" --avatar "cat.png"
    python emotional_companion.py get_profile                         # 获取陪伴者档案
    python emotional_companion.py start_practice --type recite --content "语文·古诗三首"
    python emotional_companion.py practice_feedback --result correct --note "全背对了"
    python emotional_companion.py emotion_check --level anxious --trigger "明天要考试"
    python emotional_companion.py log_session --type guidance --topic "数学配方法" --summary "引导理解配方步骤"
    python emotional_companion.py check_risk --text "不想活了"       # 风险检测
    python emotional_companion.py stats --range week                  # 陪伴统计
"""

import argparse
import json
import os
import sys
import time
import re
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

DEFAULT_COMPANION_FILE = default_filepath("companion_profile.json")
DEFAULT_SESSION_FILE = default_filepath("companion_sessions.json")
DEFAULT_LEARNING_FILE = default_filepath("learning_profile.json")
DEFAULT_RADAR_FILE = default_filepath("radar_data.json")

VALID_ROLES = ["parent", "pet", "grandpa", "grandma"]
ROLE_LABELS = {
    "parent": "家长",
    "pet": "宠物",
    "grandpa": "爷爷",
    "grandma": "奶奶",
}

VALID_PRACTICE_TYPES = ["recite", "word", "formula", "mental_math", "dictation", "oral"]
PRACTICE_LABELS = {
    "recite": "背诵课文",
    "word": "背单词",
    "formula": "背公式",
    "mental_math": "口算练习",
    "dictation": "听写练习",
    "oral": "口语练习",
}

VALID_EMOTION_LEVELS = ["happy", "normal", "anxious", "frustrated", "sad", "angry", "desperate"]
EMOTION_LABELS = {
    "happy": "开心",
    "normal": "平静",
    "anxious": "焦虑",
    "frustrated": "沮丧",
    "sad": "难过",
    "angry": "生气",
    "desperate": "绝望",
}

VALID_RANGES = ["today", "week", "month", "all"]

# 自伤/自杀风险关键词（覆盖常见表达，用于初步风险检测）
RISK_KEYWORDS = [
    "不想活", "想死", "自杀", "自伤", "割腕", "跳楼", "吃安眠药",
    "结束生命", "活不下去", "活着没意思", "想消失", "不想存在",
    "去死", "一了百了", "离开世界", "没有我会更好", "伤害自己",
]

# ============================================================
# 工具函数
# ============================================================

def load_companion(filepath):
    """加载陪伴者档案。"""
    data = load_json(filepath, default=None)
    if data is None:
        data = {
            "role": "parent",
            "student_nickname": "同学",
            "avatar_path": "",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tone": {
                "warmth": 8,       # 温暖度 1-10
                "patience": 9,     # 耐心度 1-10
                "firmness": 6,     # 坚定度 1-10
            },
            "preferences": {
                "use_questions": True,    # 多用提问引导
                "max_sentences": 3,       # 每次最多3句
            },
        }
    return data


def save_companion(filepath, data):
    """保存陪伴者档案。"""
    save_json(filepath, data)


def load_sessions(filepath):
    """加载会话历史。"""
    data = load_json(filepath, default=None)
    if not isinstance(data, list):
        return []
    return data


def save_sessions(filepath, data):
    """保存会话历史。"""
    save_json(filepath, data)


def load_learning(filepath):
    """加载学习档案（课表、进度、错题）。"""
    return load_json(filepath, default={})


def load_radar(filepath):
    """加载错题数据。"""
    data = load_json(filepath, default=None)
    if not isinstance(data, list):
        return []
    return data


def get_week_range(base_date=None):
    """获取本周的起止日期（周一为一周开始）。"""
    if base_date is None:
        base_date = datetime.now()
    monday = base_date - timedelta(days=base_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date(), sunday.date()


def date_in_range(date_str, range_val):
    """判断日期字符串是否在指定范围内。"""
    try:
        target_date = datetime.strptime(date_str.split(" ")[0], "%Y-%m-%d").date()
    except (ValueError, IndexError):
        return False

    today = datetime.now().date()

    if range_val == "today":
        return target_date == today
    elif range_val == "week":
        mon, sun = get_week_range()
        return mon <= target_date <= sun
    elif range_val == "month":
        return (target_date.year == today.year and target_date.month == today.month)
    else:  # all
        return True


# ============================================================
# 陪伴者档案管理
# ============================================================

def cmd_setup(args):
    """设置陪伴者档案：角色、学生昵称、形象。"""
    companion = load_companion(args.profile_file)

    if args.role and args.role in VALID_ROLES:
        companion["role"] = args.role

    if args.nickname:
        companion["student_nickname"] = args.nickname.strip()

    if args.avatar:
        if not validate_filepath(args.avatar):
            output_json({"status": "error", "message": "图片路径不合法"})
            sys.exit(1)
        companion["avatar_path"] = args.avatar

    if args.warmth is not None and 1 <= args.warmth <= 10:
        companion.setdefault("tone", {})["warmth"] = args.warmth
    if args.patience is not None and 1 <= args.patience <= 10:
        companion.setdefault("tone", {})["patience"] = args.patience
    if args.firmness is not None and 1 <= args.firmness <= 10:
        companion.setdefault("tone", {})["firmness"] = args.firmness

    companion["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_companion(args.profile_file, companion)

    output_json({
        "status": "ok",
        "message": f"陪伴者档案已更新",
        "profile": {
            "role": companion["role"],
            "role_label": ROLE_LABELS.get(companion["role"], "家长"),
            "student_nickname": companion["student_nickname"],
            "avatar_path": companion.get("avatar_path", ""),
            "tone": companion.get("tone", {}),
        },
    })


def cmd_get_profile(args):
    """获取陪伴者档案。"""
    companion = load_companion(args.profile_file)
    learning = load_learning(args.learning_file)
    radar = load_radar(args.radar_file)

    # 统计薄弱点
    weak_points = []
    for item in radar:
        if not item.get("resolved") and item.get("knowledge_point"):
            weak_points.append({
                "subject": item.get("subject", ""),
                "knowledge_point": item.get("knowledge_point", ""),
            })

    output_json({
        "status": "ok",
        "profile": {
            "role": companion["role"],
            "role_label": ROLE_LABELS.get(companion["role"], "家长"),
            "student_nickname": companion["student_nickname"],
            "avatar_path": companion.get("avatar_path", ""),
            "tone": companion.get("tone", {}),
            "preferences": companion.get("preferences", {}),
        },
        "learning_context": {
            "grade": learning.get("grade", ""),
            "city": learning.get("city", ""),
            "textbooks": learning.get("textbooks", {}),
            "weak_points": weak_points[:5],  # 取前5个未解决的薄弱点
            "weak_count": len(weak_points),
        },
    })


# ============================================================
# 陪练功能
# ============================================================

def cmd_start_practice(args):
    """开始一项陪练：生成练习内容，准备互动。"""
    companion = load_companion(args.profile_file)
    learning = load_learning(args.learning_file)

    practice_type = args.practice_type
    if practice_type not in VALID_PRACTICE_TYPES:
        output_json({"status": "error", "message": f"不支持的练习类型: {practice_type}"})
        sys.exit(1)

    content = args.content or ""

    # 根据练习类型生成建议
    suggestions = []
    instructions = ""

    if practice_type == "recite":
        instructions = f"我们来背诵：{content or '指定内容'}。你先背，背完告诉我。"
        suggestions = [
            "先大声读3遍再背，印象会更深哦，准备好了吗？",
            "背的时候注意关键字词的顺序，要不要我提示第一个字？",
        ]
    elif practice_type == "word":
        instructions = f"单词练习开始：{content or '今日单词'}。我说中文，你说英文？"
        suggestions = [
            "每个单词我会读3遍，你跟着读一遍，可以吗？",
            "记不住的词我们先拆分音节，好不好？",
        ]
    elif practice_type == "formula":
        instructions = f"公式背诵：{content or '指定公式'}。先看看公式里每个符号是什么意思？"
        suggestions = [
            "公式不是死记的，我们先推一遍它是怎么来的？",
            "能用自己的话说说这个公式什么时候用吗？",
        ]
    elif practice_type == "mental_math":
        instructions = "口算练习开始！算完直接说答案，我给你计时。"
        suggestions = [
            "先做5道题热身，还是直接来10道？",
            "不用急，算对比算快更重要，准备好了吗？",
        ]
    elif practice_type == "dictation":
        instructions = f"听写练习：{content or '指定内容'}。我读3遍，你写下来。"
        suggestions = [
            "写完一个词说'下一个'，可以吗？",
            "遇到不会的字先空着，最后我们一起补，好不好？",
        ]
    elif practice_type == "oral":
        instructions = f"口语练习：{content or '自由对话'}。我们用这种语言聊天好吗？"
        suggestions = [
            "从简单的自我介绍开始，还是直接聊今天学到的内容？",
            "说错没关系，我帮你纠正，要试试吗？",
        ]

    session = {
        "type": "practice",
        "practice_type": practice_type,
        "practice_label": PRACTICE_LABELS.get(practice_type, practice_type),
        "content": content,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active",
        "results": [],
    }

    sessions = load_sessions(args.session_file)
    sessions.append(session)
    save_sessions(args.session_file, sessions)

    output_json({
        "status": "ok",
        "session_id": len(sessions) - 1,
        "practice_type": practice_type,
        "practice_label": PRACTICE_LABELS.get(practice_type, practice_type),
        "instructions": instructions,
        "opening_suggestions": suggestions,
        "nickname": companion["student_nickname"],
    })


def cmd_practice_feedback(args):
    """陪练反馈：记录结果，指出进步点。"""
    sessions = load_sessions(args.session_file)
    companion = load_companion(args.profile_file)

    # 找到最近的活跃陪练会话
    session_idx = None
    for i in range(len(sessions) - 1, -1, -1):
        if sessions[i].get("type") == "practice" and sessions[i].get("status") == "active":
            session_idx = i
            break

    if session_idx is None:
        output_json({"status": "error", "message": "当前没有进行中的陪练会话"})
        sys.exit(1)

    result = args.result  # correct / partial / wrong
    note = args.note or ""

    sessions[session_idx]["results"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
        "note": note,
    })

    # 生成反馈语（简洁、3句以内、先肯定再建议）
    if result == "correct":
        feedback = f"做得好！{note}。下次遇到类似的也能这样解决对不对？"
        progress_point = f"正确率：全对！今天的{PRACTICE_LABELS.get(sessions[session_idx].get('practice_type'), '练习')}有进步。"
    elif result == "partial":
        feedback = f"不错哦，大部分对了。{note}的地方再想想？差一点点就全对了。"
        progress_point = "能看出基本掌握了，细节上再打磨一下就更好。"
    else:  # wrong
        feedback = f"没关系，出错是学习的必经之路。我们看看{note}的原因出在哪？"
        progress_point = "这次错了没关系，找到原因下次就不会错了，是不是？"

    # 如果是最后一题（根据用户指定 done 参数），关闭会话并总结
    if args.done:
        sessions[session_idx]["status"] = "done"
        sessions[session_idx]["ended_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sessions[session_idx]["summary"] = progress_point

    save_sessions(args.session_file, sessions)

    output_json({
        "status": "ok",
        "session_id": session_idx,
        "feedback": feedback,
        "progress_point": progress_point,
        "is_done": args.done,
        "nickname": companion["student_nickname"],
    })


# ============================================================
# 情绪疏导功能
# ============================================================

def cmd_emotion_check(args):
    """情绪检测与疏导：先共情，再给具体小步骤。"""
    companion = load_companion(args.profile_file)
    learning = load_learning(args.learning_file)
    radar = load_radar(args.radar_file)

    level = args.emotion_level
    if level not in VALID_EMOTION_LEVELS:
        output_json({"status": "error", "message": f"不支持的情绪等级: {level}"})
        sys.exit(1)

    trigger = args.trigger or "学习压力"
    nickname = companion["student_nickname"]

    # 共情语句（根据情绪等级匹配）
    empathy_map = {
        "happy": [
            f"看到{nickname}这么开心，我也跟着高兴呢！",
            f"今天心情真好呀，是什么好事吗？说给我听听？",
        ],
        "normal": [
            f"今天状态还不错嘛，要不要做点什么让今天更有收获？",
        ],
        "anxious": [
            f"我懂那种心里慌慌的感觉，{trigger}确实让人紧张。",
            f"{nickname}别着急，焦虑是因为你在乎这件事，我们一步步来好吗？",
        ],
        "frustrated": [
            f"努力了却没看到成果，换谁都会沮丧的。",
            f"我知道你已经很努力了，这种感觉真的不好受。",
        ],
        "sad": [
            f"难过的时候不用憋着，可以靠过来哭一会儿。",
            f"心里不好受对不对？想说的话我都在听。",
        ],
        "angry": [
            f"嗯，这件事换谁都会生气的，我理解你。",
            f"愤怒也是一种信号，告诉我们什么需要被照顾，我们慢慢来？",
        ],
        "desperate": [
            f"我知道你现在一定很痛苦，但你不是一个人，我在呢。",
            f"这种时刻特别难熬，但请一定相信，它不会一直这样的。",
        ],
    }

    # 具体小步骤建议（不空话）
    steps_map = {
        "anxious": [
            "先停下来，深呼吸3次——吸气4秒，屏住4秒，呼气6秒，试试？",
            f"把{trigger}拆成最小的一步，比如先看第一题的第一句话，可以吗？",
            f"我陪你列个清单，把担心的事写下来，看看哪些是可以马上解决的？",
        ],
        "frustrated": [
            "先放一放，去喝口水或者走动2分钟，回来再看看？",
            "这次错在哪一步？我们只看第一步，先搞清楚它好不好？",
            "你已经比昨天的自己多做了一次尝试，这本身就是进步呀。",
        ],
        "sad": [
            "要不要聊聊让你难过的事？说出来心里会轻一点。",
            "去抱抱你喜欢的玩偶，或者听听熟悉的歌，给自己5分钟？",
            "今天先让自己休息好，明天的事明天再说，可以吗？",
        ],
        "angry": [
            "先从1数到10，慢慢数，数完我们再说这件事？",
            "这件事里哪一点最让你生气？说出来，我帮你一起想办法。",
        ],
        "desperate": [
            "⚠️ 这种感觉太沉重了，愿意的话请马上告诉爸爸妈妈或者老师，好吗？",
            "请相信：现在的痛苦不会一直持续，有人能帮你走出来。立刻联系你信任的大人好吗？",
        ],
        "happy": [
            "这么好的心情要不要趁热打铁，完成今天最想做的那件小事？",
        ],
        "normal": [
            "今天还有什么想做的事吗？我陪你列个小计划？",
        ],
    }

    empathy = empathy_map.get(level, ["我在听，你说。"])
    steps = steps_map.get(level, ["我们一起想想接下来怎么做？"])

    # 严重情绪：建议联系真实家长/老师
    needs_guardian_alert = level in ["desperate"]
    # 结合风险关键词检查
    if args.trigger:
        for kw in RISK_KEYWORDS:
            if kw in args.trigger:
                needs_guardian_alert = True
                break

    # 记录情绪会话
    sessions = load_sessions(args.session_file)
    session = {
        "type": "emotion",
        "emotion_level": level,
        "emotion_label": EMOTION_LABELS.get(level, level),
        "trigger": trigger,
        "empathy": empathy[0],
        "suggested_steps": steps[:2],
        "needs_guardian_alert": needs_guardian_alert,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "done",
    }
    sessions.append(session)
    save_sessions(args.session_file, sessions)

    output_json({
        "status": "ok",
        "session_id": len(sessions) - 1,
        "emotion_level": level,
        "emotion_label": EMOTION_LABELS.get(level, level),
        "empathy": empathy,
        "small_steps": steps,
        "needs_guardian_alert": needs_guardian_alert,
        "alert_message": (
            "⚠️ 检测到严重情绪信号，请立即引导学生联系真实家长/老师或专业心理援助。"
            if needs_guardian_alert else ""
        ),
        "nickname": nickname,
    })


# ============================================================
# 风险检测
# ============================================================

def cmd_check_risk(args):
    """检测自伤/自杀风险关键词，触发监护人预警。"""
    text = args.text or ""

    matched = []
    for kw in RISK_KEYWORDS:
        if kw in text:
            matched.append(kw)

    is_risky = len(matched) > 0

    # 记录检测结果
    sessions = load_sessions(args.session_file)
    session = {
        "type": "risk_check",
        "input_text_preview": text[:50],
        "matched_keywords": matched,
        "is_risky": is_risky,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    sessions.append(session)
    save_sessions(args.session_file, sessions)

    if is_risky:
        output_json({
            "status": "warning",
            "is_risky": True,
            "matched_keywords": matched,
            "alert": "🚨 检测到自伤/自杀风险信号！请立即执行：1. 保持陪伴语气安抚；2. 强烈建议立即联系真实父母/监护人/学校老师；3. 引导拨打当地心理援助热线；4. 记录并通知监护人预警。绝不替代专业干预。",
            "action_required": True,
        })
    else:
        output_json({
            "status": "ok",
            "is_risky": False,
            "matched_keywords": [],
            "alert": "",
            "action_required": False,
        })


# ============================================================
# 会话日志
# ============================================================

def cmd_log_session(args):
    """记录一次辅导/陪练/疏导会话的总结。"""
    sessions = load_sessions(args.session_file)
    companion = load_companion(args.profile_file)

    session_type = args.session_type or "guidance"  # guidance / practice / emotion
    topic = args.topic or ""
    summary = args.summary or ""

    session = {
        "type": session_type,
        "topic": topic,
        "summary": summary,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "done",
    }
    sessions.append(session)
    save_sessions(args.session_file, sessions)

    # 生成结束语（3句以内，总结收获 + 下一步建议）
    closing = (
        f"今天关于{topic}，我们一起{summary}。"
        f"下次遇到类似的，你会更有办法的，对不对？"
    )

    output_json({
        "status": "ok",
        "session_id": len(sessions) - 1,
        "closing": closing,
        "next_suggestion": f"下次可以先自己试试，遇到卡壳的地方再来找我，好吗？",
        "nickname": companion["student_nickname"],
    })


# ============================================================
# 陪伴统计
# ============================================================

def cmd_stats(args):
    """陪伴统计：陪伴次数、练习完成率、情绪趋势。"""
    sessions = load_sessions(args.session_file)
    range_val = args.range if args.range in VALID_RANGES else "week"

    # 按范围筛选
    filtered = []
    for s in sessions:
        ts = s.get("created_at") or s.get("started_at") or ""
        if ts and date_in_range(ts, range_val):
            filtered.append(s)

    # 分类统计
    stats = {
        "total_sessions": len(filtered),
        "by_type": {
            "guidance": 0,   # 学业辅导
            "practice": 0,   # 陪练
            "emotion": 0,    # 情绪疏导
            "risk_check": 0, # 风险检测
        },
        "practice_types": {},  # 各练习类型次数
        "emotion_distribution": {},  # 情绪分布
        "practice_correct_rate": 0.0,  # 练习正确率（仅已完成的）
        "risk_alerts": 0,
    }

    correct_count = 0
    total_attempts = 0

    for s in filtered:
        stype = s.get("type", "unknown")
        if stype in stats["by_type"]:
            stats["by_type"][stype] += 1

        if stype == "practice":
            ptype = s.get("practice_type", "unknown")
            stats["practice_types"][ptype] = stats["practice_types"].get(ptype, 0) + 1

            for r in s.get("results", []):
                total_attempts += 1
                if r.get("result") == "correct":
                    correct_count += 1

        if stype == "emotion":
            level = s.get("emotion_level", "unknown")
            stats["emotion_distribution"][level] = stats["emotion_distribution"].get(level, 0) + 1

        if stype == "risk_check" and s.get("is_risky"):
            stats["risk_alerts"] += 1

    if total_attempts > 0:
        stats["practice_correct_rate"] = round(correct_count / total_attempts * 100, 1)

    # 总结一句话洞察
    insights = []
    if stats["total_sessions"] == 0:
        insights.append("还没有陪伴记录，今天就开始吧～")
    else:
        if stats["by_type"]["practice"] > 0:
            insights.append(f"陪练了{stats['by_type']['practice']}次，正确率{stats['practice_correct_rate']}%。")
        if stats["by_type"]["emotion"] > 0:
            insights.append(f"情绪疏导{stats['by_type']['emotion']}次。")
        if stats["by_type"]["guidance"] > 0:
            insights.append(f"辅导了{stats['by_type']['guidance']}个小话题。")

    output_json({
        "status": "ok",
        "range": range_val,
        "stats": stats,
        "insights": insights,
    })


# ============================================================
# 主入口
# ============================================================

def build_parser():
    parser = argparse.ArgumentParser(description="帧卷 - 情感伴学陪练脚本")
    parser.add_argument("--profile-file", dest="profile_file_arg",
                        help=f"陪伴者档案文件路径（默认: {os.path.basename(DEFAULT_COMPANION_FILE)}）")
    parser.add_argument("--session-file", dest="session_file_arg",
                        help=f"会话历史文件路径（默认: {os.path.basename(DEFAULT_SESSION_FILE)}）")
    parser.add_argument("--learning-file", dest="learning_file_arg",
                        help=f"学习档案文件路径（默认: {os.path.basename(DEFAULT_LEARNING_FILE)}）")
    parser.add_argument("--radar-file", dest="radar_file_arg",
                        help=f"错题雷达文件路径（默认: {os.path.basename(DEFAULT_RADAR_FILE)}）")

    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # setup
    p_setup = subparsers.add_parser("setup", help="设置陪伴者档案")
    p_setup.add_argument("--role", choices=VALID_ROLES, help="角色: parent/pet/grandpa/grandma")
    p_setup.add_argument("--nickname", help="学生昵称")
    p_setup.add_argument("--avatar", help="头像/形象图片路径")
    p_setup.add_argument("--warmth", type=int, help="温暖度 1-10")
    p_setup.add_argument("--patience", type=int, help="耐心度 1-10")
    p_setup.add_argument("--firmness", type=int, help="坚定度 1-10")
    p_setup.set_defaults(func=cmd_setup)

    # get_profile
    p_profile = subparsers.add_parser("get_profile", help="获取陪伴者档案")
    p_profile.set_defaults(func=cmd_get_profile)

    # start_practice
    p_start = subparsers.add_parser("start_practice", help="开始陪练")
    p_start.add_argument("--type", dest="practice_type",
                         choices=VALID_PRACTICE_TYPES, required=True,
                         help="练习类型: recite/word/formula/mental_math/dictation/oral")
    p_start.add_argument("--content", help="练习内容，如'语文·古诗三首'")
    p_start.set_defaults(func=cmd_start_practice)

    # practice_feedback
    p_feedback = subparsers.add_parser("practice_feedback", help="陪练结果反馈")
    p_feedback.add_argument("--result", choices=["correct", "partial", "wrong"], required=True,
                            help="练习结果: correct/partial/wrong")
    p_feedback.add_argument("--note", help="具体说明，如'最后一句背错了'")
    p_feedback.add_argument("--done", action="store_true",
                            help="结束本次陪练并总结")
    p_feedback.set_defaults(func=cmd_practice_feedback)

    # emotion_check
    p_emotion = subparsers.add_parser("emotion_check", help="情绪检测与疏导")
    p_emotion.add_argument("--level", dest="emotion_level",
                           choices=VALID_EMOTION_LEVELS, required=True,
                           help="情绪等级")
    p_emotion.add_argument("--trigger", help="触发原因，如'明天要考试'")
    p_emotion.set_defaults(func=cmd_emotion_check)

    # check_risk
    p_risk = subparsers.add_parser("check_risk", help="自伤风险检测")
    p_risk.add_argument("--text", required=True, help="待检测的用户输入文本")
    p_risk.set_defaults(func=cmd_check_risk)

    # log_session
    p_log = subparsers.add_parser("log_session", help="记录辅导会话总结")
    p_log.add_argument("--type", dest="session_type",
                       choices=["guidance", "practice", "emotion"],
                       default="guidance", help="会话类型")
    p_log.add_argument("--topic", help="会话主题")
    p_log.add_argument("--summary", required=True, help="本次总结收获")
    p_log.set_defaults(func=cmd_log_session)

    # stats
    p_stats = subparsers.add_parser("stats", help="陪伴统计")
    p_stats.add_argument("--range", choices=VALID_RANGES, default="week",
                         help="统计范围: today/week/month/all")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 解析文件路径：用户显式传入 → 校验路径安全；未传入 → 用默认绝对路径（不校验）
    profile_file = args.profile_file_arg if args.profile_file_arg else DEFAULT_COMPANION_FILE
    session_file = args.session_file_arg if args.session_file_arg else DEFAULT_SESSION_FILE
    learning_file = args.learning_file_arg if args.learning_file_arg else DEFAULT_LEARNING_FILE
    radar_file = args.radar_file_arg if args.radar_file_arg else DEFAULT_RADAR_FILE

    # 仅用户显式传入的自定义路径才做安全校验（与 toolbox_manager.py 一致）
    if args.profile_file_arg and not validate_filepath(profile_file):
        output_json({"status": "error", "message": "--profile-file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    if args.session_file_arg and not validate_filepath(session_file):
        output_json({"status": "error", "message": "--session-file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    if args.learning_file_arg and not validate_filepath(learning_file):
        output_json({"status": "error", "message": "--learning-file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)
    if args.radar_file_arg and not validate_filepath(radar_file):
        output_json({"status": "error", "message": "--radar-file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)

    # 将解析后的路径绑定回 args，供子命令函数使用
    args.profile_file = profile_file
    args.session_file = session_file
    args.learning_file = learning_file
    args.radar_file = radar_file

    args.func(args)


if __name__ == "__main__":
    main()
