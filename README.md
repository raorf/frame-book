# 帧卷 Frame Book

> 瞬间一帧，终成长卷。

**帧卷** 是一个个人成长导航 Skill，以**成就记录为核心主干**，通过对话驱动，帮你拆任务、治拖延、破卡顿、记成就、看数据、生成成长视频。K-12 学生额外解锁课表解析、教材追踪、错题诊断、学习工具箱、城市考情适配、动态学习规划和情感伴学陪练。

- **零依赖启动**：所有脚本纯 Python 标准库，视频功能自动降级 HTML 时间线
- **本地存储**：所有数据存在本地 JSON 文件，不联网，不上传
- **三维自适应菜单**：根据 K-12 身份、成就数据、城市本地化动态显示
- **对话驱动**：不用学命令，说句话就行

---

## 目录

- [快速开始](#快速开始)
- [功能概述](#功能概述)
- [功能详解](#功能详解)
- [脚本速查表](#脚本速查表)
- [数据存储](#数据存储)
- [项目结构](#项目结构)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 快速开始

### 安装

```bash
git clone https://github.com/your-username/frame-book.git
cd frame-book
```

无需 `pip install`，所有脚本基于 Python 3.8+ 标准库运行。

---

## 功能概述

### 通用成长能力（模块 1-7）

适用于所有人。

| 模块 | 名称 | 触发词 | 做什么 |
|------|------|--------|--------|
| 1 | 导航任务集 | "拆解任务" / "不知干什么" | 匹配领域模板，拆目标为 3-5 步行动清单 |
| 2 | 防拖延免疫针 | "不想动" / "刷视频" | 用"未来闪回"技术让你看见选择的结果 |
| 3 | 心流破壁机 | "卡住了" / "好难" | 识别卡点类型（开头难/数据缺/情绪性），针对性突破 |
| 4 | 成就记录器 | "今天完成了" | 每条记录就是一"帧"，所有帧连起来就是成长"卷" |
| 5 | 成就快速查询 | "看看成就" | 按时间/领域/重要性筛选，支持导出和分享 |
| 6 | 成长分析简报 | "成长分析" | 总成就数、环比增长率、高频领域、客观洞察 |
| 7 | 成长卷轴 | "生成成长视频" | 把成就帧编排成 MP4 视频或 HTML 时间线动画 |

### 学习子分支（模块 8-14）

成就体系下的 K-12 学习分类，专为中小学生设计。学习进步自动写入成就库（`category="学习"`），与通用成就统一存储。

| 模块 | 名称 | 核心脚本 | 核心功能 |
|------|------|---------|---------|
| 8 | 作业自查雷达 | `radar_manager.py` | 错题录入 → 知识缺口地图 → 动态补学 |
| 9 | 明日课表解析 | `learning_manager.py` | 一课一清单：预习建议 + 听课问题 + 物品提醒 |
| 10 | 学习工具箱 | `toolbox_manager.py` | 记忆复习 + 番茄钟 + 费曼讲解 + 思维导图 + 成长激励 |
| 11 | 教材学情追踪 | `learning_manager.py` | 私人教材学情地图，精准到每一节 |
| 12 | 动态学习规划 | （LLM 综合生成） | 自适应活计划，数据驱动的时间分配 |
| 13 | 情感伴学陪练 | `emotional_companion.py` | 虚拟家长/宠物：辅导引导 + 陪练互动 + 情绪疏导 + 安全预警 |
| 14 | 城市本地化适配 | `learning_manager.py` | 本地考情权重 + 真题推送 + 考试节点提醒 |

## 功能详解

> 详细菜单场景见 [references/menu-rules.md](references/menu-rules.md)

### 通用成长能力（模块 1-7）

#### 模块 1-3：通用能力

- **导航任务集**（触发：不知干什么 / 没效率 / 拆解任务）→ 匹配领域模板，拆目标为 3-5 步行动清单
- **防拖延免疫针**（触发：刷视频 / 不想动 / 歇会儿）→ 用"未来闪回"技术让你看见选择的结果
- **心流破壁机**（触发：卡住了 / 不会写 / 好难）→ 识别卡点类型（开头难/数据缺/情绪性卡顿），针对性突破

#### 模块 4：成就记录器

每条记录就是一"帧"，所有帧连起来就是成长"卷"。

**字段速查**：

| 字段 | 必填 | 取值 | 默认 |
|------|------|------|------|
| title | ✅ | 最大 200 字符 | — |
| category | ✅ | 职场/学习/健康/关系/创作/科研/生产/其他 | — |
| importance | ❌ | 1-5 | 3 |
| emotion | ❌ | emoji 或文字 | 空 |
| frame | ❌ | 图片文件名或路径 | 空 |
| level | ❌ | regular/daily/weekly/monthly/yearly | regular |

#### 模块 5-6：查询与分析

- **成就快速查询**（触发：我的成就 / 看看成就）→ 参数 `--range today|week|all`、`--limit 1-100`，查完提供导出、分享、生成视频等选项
- **成长分析简报**（触发：成长分析 / 成长报告）→ 输出总成就数、本周计数、环比增长率、高频领域、50 字以内客观洞察

#### 模块 7：成长卷轴

把成就记录按时间线编排成视频或 HTML 动画。**零依赖也能用**。

**三种模式**：

| 模式 | 命令 | 依赖 | 输出 |
|------|------|------|------|
| auto（默认） | `--format auto` | 自动检测 + 安装 | 优先 MP4，降级 HTML |
| html | `--format html` | 无 | HTML 时间线，浏览器打开 |
| video | `--format video` | moviepy + ffmpeg | MP4 视频 |

```bash
# 新手直接用（auto 模式，零配置）
python scripts/growth_video.py --range month

# 想秒出结果？强制 HTML 模式
python scripts/growth_video.py --range month --format html
```

| 参数 | 默认 | 说明 |
|------|------|------|
| --range | month | 成就时间范围 |
| --duration | 4 秒 | 每帧持续时长 |
| --quality | 720p | 分辨率（仅视频模式） |
| --music | 无 | 背景音乐（仅视频模式） |
| --format | auto | auto/video/html |
| --output | 自动 | 输出文件名 |

---

### 学习分支模块（8-14）

> 学习分支是成就总模块的 K-12 子分类。首次使用需要先设置学习档案。
> 详细功能说明见 [references/learning-modules.md](references/learning-modules.md)

#### 首次设置：学习档案

对话中说"设置课表"或"学习档案"，帧卷会引导你完成。**城市、教材版本、学校会自动智能补全，班级从课表提取**，你确认即可：

```bash
# 1. 创建档案（城市/教材版本自动补全，学校/班级可选）
python scripts/learning_manager.py setup \
  --grade "八年级上" --city "南昌" \
  --semester "2026春" \
  --school "南昌三中" --class-name "八(3)班"

# 2. 设置课表（每天单独设置）
python scripts/learning_manager.py schedule --day monday \
  --data '[{"period":1,"subject":"数学","time":"08:00-08:45"}]'

# 3. 设置教材版本（说"设置教材"即可，会自动推荐本地主流版本）
python scripts/learning_manager.py textbook --subject "数学" --version "人教版A版"

# 4. 更新学习进度（学到哪了）
python scripts/learning_manager.py progress --subject "数学" \
  --chapter "一元二次方程" --section "解法(2)" --page 34

# 5. 设置薄弱点
python scripts/learning_manager.py weakness --subject "数学" \
  --items '["配方法","几何证明"]'
```

设置完成后，直接对话触发即可，帧卷后台自动调用脚本。

#### 模块 8-9：作业雷达 + 明日课表

- **作业自查雷达**（触发：作业错题 / 这道题不会 / 拍题）→ 错题录入 → 知识缺口地图 → 动态补学
- **明日课表解析**（触发：明天有什么课 / 课前准备）→ 一课一清单：预习建议 + 听课问题 + 物品提醒

#### 模块 8：作业自查雷达

通过日常作业诊断，构建个人专属的"知识缺口地图"。

```bash
# 录入一道错题（全参数）
python scripts/radar_manager.py add \
  --subject "数学" \
  --chapter "二次函数" \
  --knowledge-point "配方法" \
  --error-type "计算错" \
  --note "配方步骤漏了常数项" \
  --source "作业" \
  --exercise-id "P58第3题"

# 查看错题列表（按时间/科目筛选）
python scripts/radar_manager.py review --range week
python scripts/radar_manager.py review --range month --subject 数学 --unresolved

# 生成学情诊断报告
python scripts/radar_manager.py analyze

# 消灭一道错题（标记为已解决）
python scripts/radar_manager.py resolve --index 3
```

**错因类型**：计算错 / 概念不清 / 完全没思路 / 审题错 / 粗心 / 方法不当 / 知识盲点 / 其他
**来源**：作业 / 考试 / 练习册 / 真题 / 学伴互查 / 其他
**查询范围**：today / week / month / all

#### 模块 10：学习工具箱

方法增强插件集。所有交互通过对话触发，无需跳转独立界面。

##### 🧠 记忆编织器（艾宾浩斯遗忘曲线）

```bash
# 获取今日应复习的错题卡片
python scripts/toolbox_manager.py review --count 10

# 标记某条错题复习完成
python scripts/toolbox_manager.py mark --index 2 --rating easy
```

**复习评级**：
- **easy**（轻松答对）→ 自动升级，间隔拉长到下一级
- **medium**（有些吃力）→ 保持当前间隔
- **hard**（卡壳了）→ 自动降级，间隔缩短

**遗忘曲线间隔（天）**：1, 2, 4, 7, 15, 30（6 级）

##### ⏱️ 番茄计时器

```bash
# 开始一个番茄钟（默认 25 分钟）
python scripts/toolbox_manager.py tomato_start --task "复习数学错题"

# 查看当前状态
python scripts/toolbox_manager.py tomato_status

# 正常结束并记录
python scripts/toolbox_manager.py tomato_done

# 中途取消（标记为中断）
python scripts/toolbox_manager.py tomato_cancel

# 番茄钟统计
python scripts/toolbox_manager.py tomato_stats --range week
```

| 参数 | 可选值 | 默认 |
|------|--------|------|
| --range | today / week / month / all | week |

##### 其他 3 大工具（LLM 处理）

| 工具 | 触发词 | 做什么 |
|------|-------|--------|
| 🗣️ 费曼讲解员 | "讲一遍浮力原理" | 引导你语音讲解，检测卡壳点 |
| 🗺️ 思维导图师 | "构建二次函数导图" | 骨架填空 + 知识图谱诊断 |
| 🌱 成长激励官 | （自动触发） | 消灭错题/连续打卡等里程碑自动反馈 |

**启停命令**：
- "打开工具箱的全部功能" / "关闭番茄计时器"
- 默认：记忆编织器自动开启，其余手动激活

#### 模块 11-14：学情追踪 + 规划 + 陪练 + 城市

- **教材学情追踪**（触发：学到哪了 / 教材进度）→ 私人教材学情地图，精准到每一节
- **动态学习规划**（触发：下周计划 / 学习规划 / 请假补课）→ 自适应活计划，数据驱动的时间分配
- **情感伴学陪练**（触发：陪我背 / 背单词 / 听写 / 口算；压力大 / 心情不好；这道题不会 + 知识点）→ 虚拟家长/宠物：辅导引导 + 陪练互动 + 情绪疏导 + 安全预警
- **城市本地化适配**（触发：本地考情 / 中考真题；上传课表自动触发；学期变更/转学/课堂学习条件触发）→ 本地考情权重 + 真题推送 + 考试节点提醒

---

## 脚本速查表

| 脚本 | 子命令 | 功能 | 数据文件 |
|------|--------|------|---------|
| `scripts/achievement.py` | record / query / analyze | 成就管理 | `achievements.json` |
| `scripts/learning_manager.py` | setup / show / schedule / textbook / progress / weakness / tomorrow | 学习数据底座 | `learning_profile.json` |
| `scripts/radar_manager.py` | add / review / analyze / resolve | 错题雷达 | `radar_data.json` |
| `scripts/emotional_companion.py` | setup / get_profile / start_practice / practice_feedback / emotion_check / check_risk / log_session / stats | 情感伴学陪练（虚拟家长/宠物） | `companion_profile.json` / `companion_sessions.json` |
| `scripts/toolbox_manager.py` | review / mark / tomato_start / tomato_status / tomato_cancel / tomato_done / tomato_stats | 学习工具箱 | `toolbox_state.json` |
| `scripts/growth_video.py` | （直接执行） | 成长视频生成（auto/video/html） | 读取 achievements.json |

**所有脚本输出 JSON 到 stdout，静默降级处理文件不存在或格式损坏。**

---

## 数据存储

```
你的工作目录/
├── achievements.json        # 成就数据（通用模块 + 学习分支共享）
├── learning_profile.json    # 学习档案（年级/学期/课表/教材/城市/学校/班级）
├── radar_data.json          # 错题雷达数据
├── companion_profile.json   # 情感伴学陪练档案（角色/昵称/头像/语气）
├── companion_sessions.json  # 情感伴学陪练会话记录（陪练/疏导/风险日志）
├── toolbox_state.json       # 学习工具箱状态（番茄钟 + 记忆复习进度）
├── growth_video_*.mp4       # 生成的成长视频
└── growth_timeline_*.html   # 生成的 HTML 时间线（降级方案）
```

所有数据存在本地，不联网，不上传。文件不存在时自动创建，格式损坏时自动降级。

---

## 项目结构

```
frame-book/
├── SKILL.md                          # 主入口（frontmatter + 核心路由 + 模块摘要）
├── QUICKSTART.md                     # 快速入门文档
├── DESIGN.md                         # 架构设计文档
├── README.md                         # 本文件
├── scripts/
│   ├── achievement.py                # 成就管理（record/query/analyze）
│   ├── learning_manager.py          # 学习数据底座（7 个子命令）
│   ├── radar_manager.py             # 错题雷达（add/review/analyze/resolve）
│   ├── emotional_companion.py       # 情感伴学陪练（陪练/辅导/疏导/预警）
│   ├── toolbox_manager.py           # 学习工具箱（记忆复习 + 番茄钟）
│   └── growth_video.py              # 成长视频生成（auto/video/html）
└── references/
    ├── menu-rules.md                 # 自适应菜单规则 + 6 种场景模板
    ├── learning-modules.md          # 模块 8-14 详细功能说明
    ├── templates-index.md           # 模板索引（37 套模板速查）
    ├── templates-work.md           # 职场模板
    ├── templates-study.md           # 学习模板
    ├── templates-education.md       # 教育模板
    ├── templates-health.md          # 健康模板
    ├── templates-creative.md        # 创作模板
    ├── templates-life.md            # 生活模板
    └── templates-learning.md        # 学习管理模板
```

---

## 贡献

欢迎提交 Issue 和 Pull Request。

- 模块详细说明见 [references/learning-modules.md](references/learning-modules.md)
- 菜单规则见 [references/menu-rules.md](references/menu-rules.md)
- 架构设计见 [DESIGN.md](DESIGN.md)
- 快速入门见 [QUICKSTART.md](QUICKSTART.md)

---

## 许可证

[MIT](LICENSE) - (c) frame-book contributors
