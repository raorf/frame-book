# 帧卷（frame-book）详细设计文档

> **生成方式**：逆向工程，以源码为准
> **基准版本**：SKILL.md v1.0.0 / 5 个 Python 脚本
> **生成日期**：2026-08-07

---

## 1. 系统概述

帧卷是一个运行在 Agent 对话环境中的个人成长导航 Skill。核心架构为 **LLM 对话层 + 本地 JSON 数据层 + Python CLI 执行层**。

### 1.1 三层架构

```
┌──────────────────────────────────────────────────────┐
│  LLM 对话层（SKILL.md 描述）                           │
│  - 意图路由 / 人格系统 / 自适应菜单                      │
│  - 编排脚本调用 / 合成输出                              │
│  - 不持久化任何数据                                     │
├──────────────────────────────────────────────────────┤
│  本地 JSON 数据层（5 个文件）                           │
│  - achievements.json        成就记录                    │
│  - learning_profile.json   学习档案                    │
│  - radar_data.json         错题雷达                     │
│  - toolbox_state.json      学习工具箱状态               │
│  - SKILL.md 不读写，仅描述                             │
├──────────────────────────────────────────────────────┤
│  Python CLI 执行层（5 个脚本）                          │
│  - 纯 argparse + json 标准库                            │
│  - 所有脚本只做 JSON CRUD + 少量计算                     │
│  - LLM 负责"智能"部分（OCR/知识图谱/预测等）             │
└──────────────────────────────────────────────────────┘
```

### 1.2 设计原则（代码体现）

| 原则 | 代码证据 |
|------|---------|
| **静默降级** | 所有 `load_data()` 在文件不存在或 JSON 损坏时返回空结构 |
| **路径安全** | `validate_filepath()` 禁止 `..` 遍历和绝对路径 |
| **统一 JSON 输出** | 所有脚本 stdout 只输出 JSON，`status` 取值 `success` / `warning` / `error` / `info` 四种 |
| **字段白名单** | `load_data()` 强制补齐缺失字段，防止 KeyError |
| **LLM 智能/脚本存储分离** | 脚本不做任何 AI 逻辑（知识图谱、OCR、预测等全由 LLM 处理） |

---

## 2. 数据契约（JSON Schema）

### 2.1 achievements.json

**类型**：`Array<Record>`
**消费方**：`achievement.py`（全读写）、`growth_video.py`（只读）

```json
[
  {
    "date": "2026-08-07",
    "title": "完成项目汇报",
    "category": "职场",
    "importance": 4,
    "emotion": "😤",
    "frame": "screenshot.png",
    "level": "regular",
    "timestamp": "2026-08-07T10:30:00.000000"
  }
]
```

**字段消费面**（`achievement.py` 代码实际读取）：

| 字段 | 类型 | 必填 | 代码验证 | 最大长度 | 枚举值 |
|------|------|------|---------|---------|--------|
| `title` | string | ✅ | 非空 + `<=200` | 200 | — |
| `category` | string | ✅ | 必须在 `VALID_CATEGORIES` 内 | — | 职场/学习/健康/关系/创作/科研/生产/其他 |
| `importance` | int | ❌ (默认3) | `1 <= n <= 5` | — | 1-5 |
| `emotion` | string | ❌ | `<=50` | 50 | — |
| `frame` | string | ❌ | 非空时 `<=250` + 路径安全校验（禁止 `..` 和绝对路径） | 250 | — |
| `level` | string | ❌ (默认"regular") | 必须在 `VALID_LEVELS` 内 | — | regular/daily/weekly/monthly/yearly |
| `date` | string (date) | ❌ (默认今天) | `^\d{4}-\d{2}-\d{2}$` 正则 + `datetime.strptime` 校验 | — | YYYY-MM-DD |
| `timestamp` | string (iso) | 自动 | `datetime.now().isoformat()` | — | — |

**growth_video.py 额外消费**：所有上述字段（按 `--range` 筛选后读取）

### 2.2 learning_profile.json

**类型**：`Object`
**消费方**：`learning_manager.py`（全读写）

```json
{
  "grade": "八年级上",
  "semester": "2026春",
  "city": "南昌",
  "school": "南昌三中",
  "class": "八(3)班",
  "schedule": {
    "monday": [
      {"period": 1, "subject": "数学", "time": "08:00-08:45"},
      {"period": 2, "subject": "语文", "time": "08:55-09:40"}
    ],
    "tuesday": [], "wednesday": [], "thursday": [],
    "friday": [], "saturday": [], "sunday": []
  },
  "textbooks": {
    "数学": "人教版A版",
    "语文": "部编版"
  },
  "progress": {
    "数学": {
      "unit": "第二十一章",
      "chapter": "一元二次方程",
      "section": "解法(2)",
      "page": 34
    }
  },
  "weakness": {
    "数学": ["配方法", "几何证明"],
    "物理": ["受力分析"]
  },
  "created_at": "2026-08-07T10:30:00",
  "updated_at": "2026-08-07T10:30:00"
}
```

**顶层字段消费面**（`create_empty_profile()` + `load_data()` 强制补齐）：

| 字段 | 类型 | 必填 | 最大长度 | 说明 |
|------|------|------|---------|------|
| `grade` | string | ✅ | 20 | 年级（八年级上、高一上） |
| `city` | string | ✅ | 20 | 所在城市 |
| `semester` | string | ❌ | 20 | 学期（2026春） |
| `school` | string | ❌ | 20 | 学校名 |
| `class` | string | ❌ | 20 | 班级名（JSON key 为 `class`） |
| `schedule` | Object | ✅ 结构固定 | — | 7 个 day key 固定存在，空数组兜底 |
| `textbooks` | Object | ✅ 结构固定 | — | subject → version 映射 |
| `progress` | Object | ✅ 结构固定 | — | subject → progress 对象 |
| `weakness` | Object | ✅ 结构固定 | — | subject → string[] |
| `created_at` | string (iso) | 自动 | — | 首次创建时写入 |
| `updated_at` | string (iso) | 自动 | — | 每次 save 时刷新 |

**schedule 条目内部字段**（`cmd_schedule()` 验证）：

| 字段 | 类型 | 必填 | 代码验证 |
|------|------|------|---------|
| `period` | int | ✅ | 正整数 `>= 1` |
| `subject` | string | ✅ | 非空 + `<=20` 字符 |
| `time` | string | ✅ | 非空（无格式正则） |

**progress 条目内部字段**（`cmd_progress()` 写入）：

| 字段 | 类型 | 必填 | 最大长度 |
|------|------|------|---------|
| `chapter` | string | ✅ | 100 |
| `section` | string | ❌ | 100 |
| `unit` | string | ❌ | 50 |
| `page` | int | ❌ | — |

**weekday key 枚举**：monday / tuesday / wednesday / thursday / friday / saturday / sunday

### 2.3 radar_data.json

**类型**：`Array<Record>`
**消费方**：`radar_manager.py`（全读写）、`toolbox_manager.py` 只读（读取未消灭错题做记忆复习）

```json
[
  {
    "date": "2026-08-07",
    "timestamp": "2026-08-07T10:20:31",
    "subject": "数学",
    "chapter": "二次函数",
    "knowledge_point": "配方法",
    "error_type": "计算错",
    "note": "配方步骤漏了常数项",
    "source": "作业",
    "exercise_id": "P58第3题",
    "error_count": 1,
    "resolved": false,
    "resolved_at": null,
    "local_weight": ""
  }
]
```

**字段消费面**（`cmd_add()` 构建 + 各命令读取）：

| 字段 | 类型 | 必填 | 代码验证 | 最大长度 | 枚举值 |
|------|------|------|---------|---------|--------|
| `subject` | string | ✅ | 非空 + `<=20` | 20 | — |
| `chapter` | string | ❌ | 非空时 `<=100` | 100 | — |
| `knowledge_point` | string | ❌ | 非空时 `<=100` | 100 | — |
| `error_type` | string | ❌ (默认"其他") | 必须在 `VALID_ERROR_TYPES` | — | 计算错/概念不清/完全没思路/审题错/粗心/方法不当/知识盲点/其他 |
| `note` | string | ❌ | 非空时 `<=500` | 500 | — |
| `source` | string | ❌ (默认"作业") | 必须在 `VALID_SOURCES` | — | 作业/考试/练习册/真题/学伴互查/其他 |
| `exercise_id` | string | ❌ | 非空时 `<=200` | 200 | — |
| `local_weight` | string | ❌ | 非空时 `<=100` | 100 | — |
| `date` | string (date) | 自动 | `datetime.now().strftime("%Y-%m-%d")` | — | — |
| `timestamp` | string (iso) | 自动 | `datetime.now().isoformat()` | — | — |
| `error_count` | int | 自动 | 固定初始值 1 | — | — |
| `resolved` | bool | 自动 | 初始 false，`resolve` 后置 true | — | — |
| `resolved_at` | string/null | 自动 | resolve 时写入 iso 时间 | — | — |

### 2.4 toolbox_state.json

**类型**：`Object`
**消费方**：`toolbox_manager.py`（全读写）

```json
{
  "tomato": {
    "active": true,
    "started_at": "2026-08-07T10:21:21",
    "task": "复习数学错题",
    "duration_minutes": 25,
    "interrupted": false
  },
  "pomodoro_log": [
    {
      "date": "2026-08-07",
      "started_at": "2026-08-07T10:21:21",
      "task": "复习数学错题",
      "duration_minutes": 25,
      "actual_minutes": 0.1,
      "completed": true,
      "interrupted": false
    }
  ],
  "review_schedule": {
    "0": {
      "last_review_date": "2026-08-07",
      "next_review_date": "2026-08-09",
      "box": 1,
      "rating": "easy"
    }
  }
}
```

**顶层字段消费面**（`load_state()` 构建）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tomato` | Object | 当前番茄钟状态 |
| `pomodoro_log` | Array | 历史番茄钟记录 |
| `review_schedule` | Object | 记忆复习进度：key 为 radar_data 中的数组下标字符串 |

**tomato 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `active` | bool | 是否进行中 |
| `started_at` | string (iso) | 开始时间 |
| `task` | string | 任务描述 |
| `duration_minutes` | int | 设定时长（默认 25） |
| `interrupted` | bool | 是否被取消 |

**pomodoro_log 条目**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string (date) | 日期 |
| `started_at` | string (iso) | 开始时间 |
| `task` | string | 任务描述 |
| `duration_minutes` | int | 设定时长 |
| `actual_minutes` | float | 实际用时 |
| `completed` | bool | 是否完成 |
| `interrupted` | bool | 是否中断 |

**review_schedule 条目**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `box` | int | 艾宾浩斯箱位 0-5 |
| `last_review_date` | string (date) | 上次复习日期 |
| `next_review_date` | string (date) | 下次复习日期 |
| `rating` | string | easy / medium / hard |

---

## 3. CLI 接口规范

### 3.1 achievement.py

```
achievement.py <subcommand> [--file PATH] [flags...]
```

| 子命令 | 必填参数 | 可选参数 | 输出结构 |
|--------|---------|---------|---------|
| `record` | `--title`, `--category` | `--importance`(1-5, 默认3), `--emotion`(≤50), `--frame`(≤250,路径安全), `--level`(regular/daily/weekly/monthly/yearly), `--date`(YYYY-MM-DD,默认今天) | `{status, message, record, total_count}` |
| `query` | — | `--range`(today/week/all, 默认today), `--limit`(1-100, 默认5) | `{status, total, filtered_count, range, records[]}` |
| `analyze` | — | — | `{status, total, week_count, last_week_count, growth_rate, top_category, top_category_count, top_emotion, category{}}` |

### 3.2 learning_manager.py

```
learning_manager.py <subcommand> [--file PATH] [flags...]
```

| 子命令 | 必填参数 | 可选参数 | 输出结构 |
|--------|---------|---------|---------|
| `setup` | `--grade`(≤20), `--city`(≤20) | `--semester`(≤20), `--school`(≤20), `--class-name`(≤20) | `{status, message, profile{}}` |
| `show` | — | — | 完整 profile object |
| `schedule` | `--day`(monday-sunday), `--data`(JSON数组字符串) | — | `{status, message, day, schedule[]}` |
| `textbook` | `--subject`(≤20), `--version`(≤50) | — | `{status, message, subject, version}` |
| `progress` | `--subject`(≤20), `--chapter`(≤100) | `--section`(≤100), `--unit`(≤50), `--page`(int) | `{status, message, subject, progress{unit,chapter,section,page}}` |
| `weakness` | `--subject`(≤20), `--items`(JSON数组字符串) | — | `{status, message, subject, weakness[]}` |
| `tomorrow` | — | — | 成功:`{status,date,weekday,classes[],items_to_bring[]}` / 空:`{status:"weekend|no_classes",date,weekday,message,classes:[],items_to_bring:[]}` |

### 3.3 radar_manager.py

```
radar_manager.py <subcommand> [--file PATH] [flags...]
```

| 子命令 | 必填参数 | 可选参数 | 输出结构 |
|--------|---------|---------|---------|
| `add` | `--subject`(≤20) | `--chapter`(≤100), `--knowledge-point`(≤100), `--error-type`(枚举), `--note`(≤500), `--source`(枚举), `--exercise-id`(≤200), `--local-weight`(≤100) | `{status, message, record, total_count}` |
| `review` | — | `--range`(today/week/month/all, 默认week), `--limit`(1-200, 默认50), `--subject`, `--unresolved`(flag) | `{status, total, filtered_count, range, subject, unresolved_only, records[]}` |
| `analyze` | — | — | `{status, total, unresolved_count, resolve_rate, week_count, week_unresolved, subject_stats[], hot_chapters[], error_type_dist{}, hot_knowledge_points[], local_weighted_count}` |
| `resolve` | `--index`(int) | — | `{status, message, record}` |

### 3.4 toolbox_manager.py

```
toolbox_manager.py <subcommand> [flags...]
```

| 子命令 | 必填参数 | 可选参数 | 输出结构 |
|--------|---------|---------|---------|
| `review` | — | `--count`(默认10) | `{status, date, total_due, items[], hint}` |
| `mark` | `--index`(int) | `--rating`(easy/medium/hard, 默认medium) | `{status, message, subject, chapter, next_review_date, next_box}` |
| `tomato_start` | — | `--task`(默认"专注任务"), `--minutes`(默认25) | `{status, message, task, ends_at, duration_minutes, command_to_end, command_to_cancel}` |
| `tomato_status` | — | — | `{status:"running|idle", task?, started_at?, duration_minutes?, elapsed_seconds?, remaining_seconds?, remaining_text?, progress_percent?, interrupted?}` |
| `tomato_done` | — | — | `{status, message, task, actual_minutes, completed}` |
| `tomato_cancel` | — | — | `{status, message, task, actual_minutes}` |
| `tomato_stats` | — | `--range`(today/week/month/all, 默认week) | `{status, range, total_sessions, completed, interrupted, completion_rate, total_minutes, task_distribution{}}` |

### 3.5 growth_video.py

```
growth_video.py [flags...]
```

**不使用子命令模式**，直接参数驱动。

| 参数 | 类型 | 默认 | 可选值 | 说明 |
|------|------|------|--------|------|
| `--range` | string | month | today/week/month/year/all | 成就时间范围 |
| `--duration` | int | 4 | 2-10 | 每帧秒数 |
| `--quality` | string | 720p | 480p/720p/1080p | 分辨率（仅 video 模式） |
| `--music` | string | 空 | — | 背景音乐路径 |
| `--format` | string | auto | auto/video/html | 输出模式 |
| `--output` | string | 自动 | — | 输出文件名 |

**三种模式行为**：

| 模式 | 依赖 | 降级行为 | 输出 |
|------|------|---------|------|
| auto（默认） | moviepy + Pillow + ffmpeg | ① 自动 pip install moviepy/Pillow（ffmpeg 无法 pip，只能系统安装）<br>② 检查三者是否全就绪<br>③ 全部就绪 → 生成 MP4<br>④ 仍有缺失 → 降级为 HTML | MP4 或 HTML |
| video（强制） | 必须全部就绪 | 不自动安装；有缺失 → 报错 + 提示各平台安装命令 | MP4 |
| html（强制） | 无 | — | HTML（图片 base64 内联 + 键盘导航 + CSS 自动播放） |

**视频生成内部细节**（代码实际）：
- 帧过渡：CrossFadeIn 0.5 秒（兼容 moviepy 1.x 的 `crossfadein` 方法和 2.x 的 `with_effects([vfx.CrossFadeIn(...)])`）
- 字幕叠加：半透明黑色条（bar_h = height × 0.18），位于画面 72% 处（SUBTITLE_Y_RATIO = 0.72）
- 输出编码：libx264 + AAC（仅当 --music 提供时），30fps
- 背景音不足时自动 subloop 至视频时长
- 图片帧安全处理：`os.path.basename(frame_path)` 只取文件名，防止路径遍历
- HTML 键盘导航：← 上一帧 / → 下一帧 / 空格 暂停播放
- HTML 图片帧：支持 png/jpg/jpeg/webp/gif 五种 MIME 类型，base64 内联

---

## 4. 数据流图

### 4.1 数据生产 → 消费关系

```
                    ┌─────────────────────┐
                    │  achievements.json  │
                    └─────────┬───────────┘
                              │
          achievement.py 读写  │  growth_video.py 只读
                              │
    ┌─────────────────────────┼─────────────────────────┐
    ▼                         ▼                         ▼
  record                   query/analyze            视频/HTML生成


┌─────────────────────────────────────────────────────────────────────────┐
│                         learning_profile.json                           │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌─────────────┐ │
│  │ schedule │  │textbooks│  │ progress  │  │weakness │  │ grade/city/ │ │
│  └────┬────┘  └────┬────┘  └─────┬─────┘  └────┬────┘  │ semester/...│ │
│       │            │             │               │      └──────┬──────┘ │
│       └────────────┼─────────────┼───────────────┼──────────────┘       │
│                    ▼             ▼               ▼                        │
│              cmd_tomorrow 交叉引用四者 → 生成一课一清单                      │
└─────────────────────────────────────────────────────────────────────────┘


┌──────────────────┐
│  radar_data.json  │
└────────┬─────────┘
         │
    toolbox_manager.py 只读 (review 子命令)
         │
         ▼
    今日应复习条目（过滤 resolved=false 的条目 → 艾宾浩斯计算 next_review_date）


┌──────────────────┐    ┌───────────────────┐
│  radar_data.json  │    │ toolbox_state.json │
└────────┬─────────┘    └────────┬──────────┘
         │                         │
         └─────────┬───────────────┘
                   ▼
          toolbox_manager.py mark 子命令
          → 读取 radar_data[index] → 更新 state.review_schedule[index]
          → 写回 toolbox_state.json
```

### 4.2 脚本间交叉引用矩阵

| 脚本 | 读取 | 写入 |
|------|------|------|
| `achievement.py` | — | `achievements.json` |
| `learning_manager.py` | — | `learning_profile.json` |
| `radar_manager.py` | — | `radar_data.json` |
| `toolbox_manager.py` | `radar_data.json`（review 子命令，读未消灭错题） | `toolbox_state.json` |
| `growth_video.py` | `achievements.json` | MP4 / HTML 文件（不写回 JSON） |

**关键发现**：脚本间无直接写入依赖。唯一跨脚本读取是 `toolbox_manager.py → radar_data.json`（只读）。所有跨模块的"智能联动"（如"作业雷达根据课表调整优先级"）由 LLM 在对话层编排，不在脚本中实现。

### 4.3 艾宾浩斯遗忘曲线算法

```python
EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]  # 天

def mark_rating(rating, current_box):
    if rating == "easy":
        new_box = min(current_box + 1, 5)      # 升级，间隔拉长
    elif rating == "medium":
        new_box = current_box                   # 保持当前级别
    elif rating == "hard":
        new_box = max(current_box - 1, 0)      # 降级，间隔缩短

    next_date = today + timedelta(days=EBBINGHAUS_INTERVALS[new_box])
    return next_date, new_box
```

**review 子命令筛选逻辑**：
- 条件 1：`state.review_schedule[index].next_review_date <= today` （已到期）
- 条件 2：或者 index 不在 review_schedule 中（从未安排过复习，今日优先处理）
- 条件 3：radar_data[index].resolved == false （未消灭的错题才需要复习）

---

## 5. 通用工具函数库

5 个脚本共享一套相同的辅助函数模式：

| 函数 | 所在脚本 | 功能 | 安全校验 |
|------|---------|------|---------|
| `load_data(filepath)` | 全部 5 个 | 文件不存在返回空列表/空对象；JSON 损坏返回空结构 | try/except 静默降级 |
| `save_data(filepath, data)` | 全部 5 个 | 写 JSON 到文件 | try/except 报错退出 |
| `output_json(data)` | 全部 5 个 | 统一 JSON stdout 输出 | — |
| `validate_filepath(filepath)` | achievement, learning_manager | 禁止 `..` 路径遍历 + 绝对路径（radar_manager/toolbox_manager/growth_video 缺失此校验） | ✅ 安全关键 |
| `validate_input(value, max_len, field_name)` | learning_manager | 非空 + 长度限制 | — |
| `get_week_range(base_date)` | achievement | 周一为起始的本周起止日期 | — |
| `parse_json_string(json_str, field_name)` | learning_manager | 安全 JSON 字符串解析 | — |

---

## 6. 常量白名单（代码硬编码）

| 常量 | 位置 | 值 |
|------|------|-----|
| `VALID_CATEGORIES` | achievement.py | `["职场","学习","健康","关系","创作","科研","生产","其他"]` |
| `VALID_LEVELS` | achievement.py | `["regular","daily","weekly","monthly","yearly"]` |
| `VALID_RANGES` | achievement.py | `["today","week","all"]` |
| `VALID_RANGES` | growth_video.py | `["today","week","month","year","all"]` |
| `VALID_RANGES` | radar_manager.py | `["today","week","month","all"]` |
| `VALID_RANGES` | toolbox_manager.py | `["today","week","month","all"]` |
| `VALID_DAYS` | learning_manager.py | `["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]` |
| `VALID_ERROR_TYPES` | radar_manager.py | `["计算错","概念不清","完全没思路","审题错","粗心","方法不当","知识盲点","其他"]` |
| `VALID_SOURCES` | radar_manager.py | `["作业","考试","练习册","真题","学伴互查","其他"]` |
| `EBBINGHAUS_INTERVALS` | toolbox_manager.py | `[1, 2, 4, 7, 15, 30]` |
| `DEFAULT_DURATION` | growth_video.py | `4`（秒/帧） |
| `QUALITY_MAP` | growth_video.py | `{"480p":(854,480),"720p":(1280,720),"1080p":(1920,1080)}` |

---

## 7. 静默降级矩阵

| 场景 | 脚本 | 降级行为 |
|------|------|---------|
| 数据文件不存在 | 全部 | 返回空结构（`[]` / 空 profile），不报错 |
| JSON 文件格式损坏 | 全部 | try/except 捕获，返回空结构 |
| `--file` 路径含 `..` | achievement, learning_manager | 报错退出 |
| `--file` 为绝对路径 | achievement | 报错退出 |
| moviepy 未安装 | growth_video auto 模式 | 自动 pip install（失败则计入 missing） |
| Pillow 未安装 | growth_video auto 模式 | 自动 pip install（失败则计入 missing） |
| ffmpeg 未安装 | growth_video 所有模式 | **无法 pip 安装**，计入 missing；auto 模式降级 HTML，video 模式报错 |
| 三者任一缺失（auto 模式经自动尝试后仍有 missing） | growth_video auto 模式 | 降级为 HTML 模式，输出 `status: "warning"` + missing 列表 |
| 三者任一缺失（video 模式不自动安装） | growth_video video 模式 | 报错 + 各平台安装命令（Windows: winget/choco, macOS: brew, Linux: apt/yum） |
| tomorrow 明日无课 | learning_manager | 返回 `status: "weekend"|"no_classes"` + 空列表 |
| 番茄钟已活跃时再 start | toolbox_manager | 返回 `status: "warning"` + 当前状态 |
| tomato_status 无活跃番茄钟 | toolbox_manager | 返回 `status: "idle"` |
| review 无待复习条目 | toolbox_manager | 返回空 items 数组 |
| analyze 无数据 | achievement, radar | 返回 0 值统计，不报错 |

---

## 8. 约束与限制

| 约束 | 具体值 | 来源 |
|------|--------|------|
| achievement title 最大长度 | 200 | `MAX_TITLE_LENGTH` |
| achievement emotion 最大长度 | 50 | `MAX_EMOTION_LENGTH` |
| achievement frame 路径最大长度 | 250 | `MAX_FRAME_LENGTH` |
| learning grade 最大长度 | 20 | `MAX_GRADE_LENGTH` |
| learning city/school 最大长度 | 20 | `MAX_CITY_LENGTH` |
| learning subject 最大长度 | 20 | `MAX_SUBJECT_LENGTH` |
| learning version 最大长度 | 50 | `MAX_VERSION_LENGTH` |
| learning chapter 最大长度 | 100 | `MAX_CHAPTER_LENGTH` |
| learning section 最大长度 | 100 | `MAX_SECTION_LENGTH` |
| learning unit 最大长度 | 50 | `MAX_UNIT_LENGTH` |
| schedule entries 每节课 subject 最大 | 20 | `MAX_SUBJECT_LENGTH` |
| radar subject 最大长度 | 20 | `MAX_SUBJECT_LENGTH` |
| radar chapter/note/knowledge 最大 | 100 / 500 / 100 | 各自常量 |
| radar review limit 上限 | 200 | 硬编码 |
| achievement query limit 上限 | 100 | 硬编码 |
| importance 取值范围 | 1-5 | 硬编码 |
| tomato 默认时长 | 25 分钟 | 硬编码 |
| growth_video 默认每帧 | 4 秒 | 硬编码 |

---

## 9. 模块 8-14 代码→LLM 分工

**关键发现**：SKILL.md 描述中提到的复杂能力（OCR、知识图谱、薄弱点热力图等）**全部不在脚本中实现**，脚本只做数据存储和检索：

| 模块 | 脚本实现 | LLM 负责 |
|------|---------|---------|
| 8 明日课表解析 | 读取 schedule + textbooks + progress + weakness，交叉引用生成 class_list JSON | 播报渲染（人格化输出） |
| 9 教材学情追踪 | `show` 输出完整 profile JSON | 渲染成树形学情地图格式 |
| 10 作业自查雷达 | JSON CRUD + 统计（add/review/analyze/resolve） | OCR 识别题干、知识图谱定位、错因智能分类、热力图可视化、变形题关联、考前押题卷生成 |
| 11 动态学习规划 | **无独立脚本**（LLM 消费 learning_profile.json + radar_data.json 综合生成） | 周计划生成、自适应难度调节、请假补课流程 |
| 12 学习工具箱 | 记忆复习 CRUD（review/mark）、番茄钟生命周期管理（start/status/done/cancel/stats） | 费曼讲解引导、思维导图骨架生成、成长激励话术 |
| 13 城市本地化适配 | **无独立脚本**（LLM 消费 learning_profile.json） | 智能补全（城市/教材/学校）、本地考情权重标注、真题推送、考试节点提醒、学期变更/转学的变化检测 |

**设计含义**：模块 11 和 13 没有专门的脚本文件，完全由 LLM 在对话层消费已有的 `learning_profile.json` 和 `radar_data.json` 做智能编排。如果后续要给 11/13 加脚本，需要明确哪些计算要下沉到代码层（例如"下周日程规划"可以由脚本计算每周日的 task slots，LLM 负责填充内容）。

---

## 10. 依赖清单

| 依赖 | 使用位置 | 必要性 | 安装方式 |
|------|---------|--------|---------|
| Python 3.8+ | 全部脚本 | ✅ 必须 | 系统自带 |
| moviepy | growth_video.py video 模式 | ⚠️ 可选 | `pip install moviepy Pillow`（auto 模式自动安装） |
| Pillow | growth_video.py video 模式 | ⚠️ 可选 | 同上 |
| ffmpeg | growth_video.py video 模式 | ⚠️ 可选 | Windows: `winget install ffmpeg` |

**零依赖路径**：growth_video.py 的 html 模式（标准库 `base64` + `html.escape` 即可运行）。

---

## 11. 文件结构（代码实际）

```
frame-book/
├── SKILL.md                          # LLM 行为描述（不被脚本读取）
├── QUICKSTART.md                     # 用户文档（不被脚本读取）
├── scripts/
│   ├── achievement.py                # 成就管理（record/query/analyze）
│   ├── learning_manager.py           # 学习数据底座（7 个子命令）
│   ├── radar_manager.py              # 错题雷达（add/review/analyze/resolve）
│   ├── toolbox_manager.py            # 学习工具箱（记忆复习 + 番茄钟）
│   └── growth_video.py               # 成长卷轴（auto/video/html）
├── references/
│   ├── menu-rules.md                 # 自适应菜单规则（不被脚本读取）
│   ├── learning-modules.md           # 模块 8-14 详细说明（不被脚本读取）
│   ├── templates-index.md            # 模板索引（不被脚本读取）
│   └── templates-*.md (7 个)         # 模板文件（不被脚本读取）
└── [运行时生成]
    ├── achievements.json
    ├── learning_profile.json
    ├── radar_data.json
    ├── toolbox_state.json
    ├── growth_video_*.mp4
    └── growth_timeline_*.html
```

---

## 12. 架构不一致修复记录（2026-08-14 修复）

逆向分析发现的 5 类架构不一致问题，已全部修复。

### 12.1 ✅ 数据文件路径处理方式分裂

**修复前**：radar_manager 缺安全校验、toolbox_manager/growth_video 硬编码路径
**修复后**：

| 脚本 | 数据路径方式 | 安全校验 |
|------|-------------|---------|
| `achievement.py` | `--file PATH` | ✅ `validate_filepath()` |
| `learning_manager.py` | `--file PATH` | ✅ `validate_filepath()` |
| `radar_manager.py` | `--file PATH` | ✅ `validate_filepath()`（**新增**） |
| `toolbox_manager.py` | `--file`（state）+ `--radar-file`（radar） | ✅ `validate_filepath()`（**新增两个参数 + 校验**） |
| `growth_video.py` | `--file PATH` | ✅ `validate_filepath()`（**新增**） |

**额外改动**：
- 统一用 `common.default_filepath(filename)` 构造默认路径，消除所有 `os.path.join(os.getcwd(), ...)` 硬编码
- 删除 toolbox_manager.py 中定义了但从未使用的 `LEARNING_PROFILE_FILE`（死代码）
- 删除 growth_video.py 中硬编码的 `ACHIEVEMENTS_FILE` 常量

### 12.2 frame 字段路径安全策略不一致

**状态**：保留现状，不属于架构缺陷
- achievement.py 对用户录入 frame 路径做严格校验（报错更显式）
- growth_video.py 运行时对已存储 frame 做 basename 兜底读取
- 两者安全结果一致（都能防止路径遍历），只是行为风格不同

### 12.3 growth_video.py 的"非子命令"风格

**状态**：设计选择，不修改
- 5 个脚本中有 4 个是子命令架构，growth_video.py 直接参数驱动
- growth_video.py 的所有功能通过一个 `cmd_generate()` 完成（视频和 HTML 只是 --format 模式），不需要拆子命令

### 12.4 ✅ 错误输出格式文档化

**修复前**：文档中 status 只记录了 success/error 两种值
**修复后**：
- 已在 DESIGN.md 1.2 节补充：status 取值 `success` / `warning` / `error` / `info` 四种
- 已在 growth_video.py 的 auto 模式降级、tomato 已活跃等场景中确认 warning/info 状态正常工作

### 12.5 ✅ 共享函数抽成公共模块

**修复前**：5 个脚本各自复制实现 `output_json` / `load_json` / `save_json` / `validate_filepath`
**修复后**：创建 [common.py](file:///e:/ZJ/skill/trae/frame-book/scripts/common.py)，提供统一的公共 API

| common.py 函数 | 用途 | 使用脚本 |
|---------------|------|---------|
| `output_json(data)` | 统一 JSON stdout | 全部 5 个 |
| `validate_filepath(filepath)` | 路径安全校验（禁止 `..` + 绝对路径） | 全部 5 个 |
| `load_json(filepath, default)` | 底层 JSON 读取 | achievement / learning_manager / radar / toolbox / growth_video |
| `load_data_list(filepath)` | 加载数组型 JSON | achievement / radar |
| `save_json(filepath, data)` | 底层 JSON 写入 | 全部 5 个 |
| `default_filepath(filename)` | 构造 cwd 下默认路径 | 全部 5 个 |

**保留的脚本特有函数**（与通用版有差异）：
- `learning_manager.load_data()` — 有字段补齐逻辑（grade/city/schedule/weekdays 等）
- `learning_manager.save_data()` — 保存前自动刷新 `updated_at`
- `toolbox_manager.load_state(filepath)` / `save_state(filepath, state)` — 封装了 toolbox_state.json 的默认值结构（tomato/pomodoro_log/review_schedule）
