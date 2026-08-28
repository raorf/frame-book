#!/usr/bin/env python3
"""
帧卷 - 公共工具模块
提供 5 个脚本共享的 JSON 读写、路径安全校验、输出函数。
"""

import json
import os
import sys


def output_json(data):
    """统一 JSON 输出到 stdout。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def validate_filepath(filepath):
    """
    验证文件路径安全性，防止路径遍历攻击。
    空路径返回 True（调用方决定用哪个默认文件）。
    禁止: '..' 遍历、绝对路径。
    """
    if not filepath:
        return True
    if ".." in filepath:
        return False
    if os.path.isabs(filepath):
        return False
    return True


def load_json(filepath, default=None):
    """
    加载 JSON 文件。
    文件不存在或格式损坏时返回 default。
    """
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return default


def load_data_list(filepath):
    """加载数组型 JSON 文件，返回 list。"""
    data = load_json(filepath, default=[])
    if not isinstance(data, list):
        return []
    return data


def load_data_dict(filepath, default_factory):
    """加载对象型 JSON 文件，用 default_factory 生成默认值。"""
    data = load_json(filepath, default=None)
    if not isinstance(data, dict):
        return default_factory()
    return data


def save_json(filepath, data):
    """保存 JSON 数据到文件。IOError 时报错 exit(1)。"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (IOError, OSError) as e:
        output_json({"status": "error", "message": f"保存失败: {e}"})
        sys.exit(1)


def default_filepath(filename):
    """构造当前工作目录下的默认路径。"""
    return os.path.join(os.getcwd(), filename)
