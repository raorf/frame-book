# 帧卷 · 快速入门

> 瞬间一帧，终成长卷。

## 这是什么

帧卷是一个个人成长导航 Skill，以**成就记录为核心主干**：

- **通用成长能力**（模块 1-7）：适用于所有人——拆任务、治拖延、破卡顿、记成就、看数据、生成视频
- **学习子分支**（模块 8-14）：成就体系下的 K-12 学习分类——作业自查雷达、明日课表解析、情感伴学陪练、教材进度追踪、学习工具箱、动态学习规划、城市考情适配

学习分支是成就总模块的子分支：学习进步自动写入成就库（category="学习"），与通用成就统一存储。

## 30 秒上手

安装完成后，在任意对话中直接说：

### 通用能力模块

| 你说什么 | 会发生什么 |
|---------|----------|
| **"帧卷"** | 弹出自适应功能菜单（根据身份和数据动态显示） |
| **"帮我拆解任务"** | 把目标变成可执行清单 |
| **"不想动 / 想刷视频"** | 来一针防拖延免疫 |
| **"卡住了 / 不会写"** | 识别卡点，帮你突破 |
| **"今天完成了 XX"** | 记录一条成就 |
| **"看看成就"** | 查询成就列表 |
| **"分析一下"** | 生成成长数据简报 |
| **"生成成长视频"** | 把成就帧连成视频或 HTML 时间线 |

### 学习分支模块

| 你说什么 | 会发生什么 |
|---------|----------|
| **"明天有什么课"** | 生成明日一课一清单 |
| **"学到哪了"** | 展示教材学情地图 |
| **"作业错题 / 这道题不会"** | 录入错题，生成知识缺口地图 |
| **"陪我背 / 背单词 / 听写 / 口算"** | 虚拟家长/宠物陪练，即时反馈进步点 |
| **"压力大 / 心情不好 / 抱抱"** | 情绪疏导：先共情，再给具体小步骤 |
| **"费曼 / 番茄钟 / 导图 / 记忆复习"** | 调用学习工具箱的 5 大方法工具 |
| **"下周计划"** | 生成自适应学习规划 |
| **"本地考情"** | 本地考情分析和真题推荐 |
| **"设置课表"** | 配置学习档案（首次使用必做，智能补全城市/教材/学校，班级从课表提取） |

## 功能菜单

> 菜单是**三维自适应**的，根据三项检测结果动态显示：
> - **K-12 相关性**：非 K-12 用户不显示学习分支模块 8-14（完全移除）
> - **成就数据**：无成就时模块 5-7 显示为灰色 🔒
> - **城市本地化**：无城市时模块 8、9、13、10、11、12 灰色 🔒，模块 14 作为配置入口显示
>
> 详细菜单场景见 [references/menu-rules.md](file:///e:/ZJ/skill/trae/frame-book/references/menu-rules.md)

**完整菜单**（K-12 + 有成就 + 有城市，全模块 1-14 展开）：

```
【通用能力】
1 导航任务集 — 帮你拆解目标，生成执行清单
2 防拖延免疫针 — 又不想动了？来一针
3 心流破壁机 — 卡住了？帮你突破
4 成就记录器 — 今天完成了什么？记下来
5 成就快速查询 — 看看你做过的事
6 成长分析简报 — 数据说话
7 成长卷轴 — 把成就帧连成视频

【学习分支】
8 作业自查雷达 — 拍题诊断错题，找到你的知识漏洞
9 明日课表解析 — 明天怎么听课？帮你准备好
10 学习工具箱 — 费曼讲解/记忆复习/番茄钟/思维导图
11 教材学情追踪 — 学到哪了？下一步该学什么？
12 动态学习规划 — 自适应学习计划
13 情感伴学陪练 — 虚拟家长/宠物陪你学：辅导·陪练·抱一抱
14 城市本地化适配 — 本地考情分析与真题推荐
```

首次呼叫时，帧卷会先说一句"我是帧卷——你的个人成长导航"，再给出菜单。后续对话中提及学校/课表/考试等关键词时，自动切换为 K-12 模式。

### 模块 1-3：通用能力

- **导航任务集**（触发：不知干什么 / 没效率 / 拆解任务）→ 匹配领域模板，拆目标为 3-5 步行动清单
- **防拖延免疫针**（触发：刷视频 / 不想动 / 歇会儿）→ 用"未来闪回"技术让你看见选择的结果
- **心流破壁机**（触发：卡住了 / 不会写 / 好难）→ 识别卡点类型（开头难/数据缺/情绪性卡顿），针对性突破

### 模块 4：成就记录器

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

### 模块 5-6：查询与分析

- **成就快速查询**（触发：我的成就 / 看看成就）→ 参数 `--range today|week|all`、`--limit 1-100`，查完提供导出、分享、生成视频等选项
- **成长分析简报**（触发：成长分析 / 成长报告）→ 输出总成就数、本周计数、环比增长率、高频领域、50 字以内客观洞察

### 模块 7：成长卷轴

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

## 学习分支模块（8-14）

> 学习分支是成就总模块的 K-12 子分类。首次使用需要先设置学习档案。
> 详细功能说明见 [references/learning-modules.md](file:///e:/ZJ/skill/trae/frame-book/references/learning-modules.md)

### 首次设置：学习档案

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

### 模块 8-9：作业雷达 + 明日课表

- **作业自查雷达**（触发：作业错题 / 这道题不会 / 拍题）→ 错题录入 → 知识缺口地图 → 动态补学
- **明日课表解析**（触发：明天有什么课 / 课前准备）→ 一课一清单：预习建议 + 听课问题 + 物品提醒

### 模块 8：作业自查雷达

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

### 模块 10：学习工具箱

方法增强插件集。所有交互通过对话触发，无需跳转独立界面。

#### 🧠 记忆编织器（艾宾浩斯遗忘曲线）

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

#### ⏱️ 番茄计时器

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

#### 其他 3 大工具（LLM 处理）

| 工具 | 触发词 | 做什么 |
|------|-------|--------|
| 🗣️ 费曼讲解员 | "讲一遍浮力原理" | 引导你语音讲解，检测卡壳点 |
| 🗺️ 思维导图师 | "构建二次函数导图" | 骨架填空 + 知识图谱诊断 |
| 🌱 成长激励官 | （自动触发） | 消灭错题/连续打卡等里程碑自动反馈 |

**启停命令**：
- "打开工具箱的全部功能" / "关闭番茄计时器"
- 默认：记忆编织器自动开启，其余手动激活

### 模块 11-14：学情追踪 + 规划 + 陪练 + 城市

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
├── growth_timeline_*.html   # 生成的 HTML 时间线（降级方案）
```

所有数据存在本地，不联网，不上传。文件不存在时自动创建，格式损坏时自动降级。

---

## 文件结构

```
frame-book/
├── SKILL.md                          # 主入口（frontmatter + 核心路由 + 模块摘要）
├── QUICKSTART.md                     # 本文件
├── scripts/
│   ├── achievement.py                # 成就管理（record/query/analyze）
│   ├── learning_manager.py           # 学习数据底座（7 个子命令）
│   ├── radar_manager.py              # 错题雷达（add/review/analyze/resolve）
│   ├── emotional_companion.py        # 情感伴学陪练（虚拟家长/宠物：陪练/辅导/疏导/预警）
│   ├── toolbox_manager.py            # 学习工具箱（记忆复习 + 番茄钟）
│   └── growth_video.py               # 成长视频生成（auto/video/html）
└── references/
    ├── menu-rules.md                 # 自适应菜单规则 + 6 种场景模板
    ├── learning-modules.md           # 模块 8-14 详细功能说明
    ├── templates-index.md            # 模板索引（37 套模板速查）
    ├── templates-work.md             # 职场模板
    ├── templates-study.md            # 学习模板
    ├── templates-education.md        # 教育模板
    ├── templates-health.md            # 健康模板
    ├── templates-creative.md          # 创作模板
    ├── templates-life.md              # 生活模板
    └── templates-learning.md         # 学习管理模板
```

---

## 常见问题

### Q: 不是学生，学习分支模块有用吗？

学习分支模块 8-14 是成就总模块的 K-12 子分类，专为中小学生设计。非 K-12 用户的菜单会自动移除模块 8-14，只显示通用能力模块 1-7。完全不影响体验。

### Q: 学习分支需要单独安装吗？

不需要。学习分支是帧卷内置的子分类，无第三方依赖，装好帧卷即可使用。只需首次使用时设置学习档案（城市和教材版本会自动智能补全）。

### Q: 成就数据会被上传吗？

不会。所有数据存在本地 JSON 文件，不联网，不上传。

### Q: 模块 7 视频功能不装依赖能用吗？

能用。auto 模式（默认）会自动尝试安装依赖，安装失败自动降级为 HTML 时间线（零依赖，浏览器打开）。也可以直接用 `--format html` 强制生成 HTML。

### Q: 模板匹配不到怎么办？

不会报错。帧卷会先用通用拆解框架（目标→拆分→行动→时间预估）生成清单，然后告诉你"有更具体的场景可以告诉我，我能匹配更精准的模板"。

### Q: 换了城市、学校或年级怎么办？

对话中说"更新学习档案"或"设置课表"，帧卷会智能检测变化范围，按需更新对应字段。已有数据不会丢失。

### Q: 不会写代码也能用吗？

能。帧卷的所有操作通过对话完成，脚本调用由帧卷在后台自动处理。

---

## 下一步

- **开始记录成就** → 对话说"今天完成了 XX"
- **设置学习档案** → 对话说"设置课表"（城市、教材、学校智能补全，班级从课表提取）
- **生成第一支成长卷轴** → 记录几条成就后，说"生成成长视频"（零依赖也能用）
- **探索模板** → 说说你的领域，帧卷会匹配对应模板
