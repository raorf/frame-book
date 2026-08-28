#!/usr/bin/env python3
"""
帧卷 - 成长卷轴（成长视频/时间线生成器）
将成就记录按时间线编排成 MP4 视频或 HTML 动画时间线。

依赖:
    视频模式: pip install moviepy Pillow + 系统安装 ffmpeg
    HTML模式: 无依赖（纯标准库生成）

用法:
    # 自动模式（优先视频，依赖缺失自动降级为HTML）
    python growth_video.py --range month

    # 强制视频模式
    python growth_video.py --range month --format video

    # 强制HTML模式（零依赖，浏览器打开）
    python growth_video.py --range month --format html

    # 带背景音乐
    python growth_video.py --range week --music bgm.mp3
"""

import argparse
import base64
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timedelta
from html import escape as html_escape

from common import (
    output_json,
    validate_filepath,
    load_json,
    default_filepath,
)

# ============================================================
# 常量定义
# ============================================================

DEFAULT_ACHIEVEMENTS_FILE = default_filepath("achievements.json")

DEFAULT_VIDEO_OUTPUT = "growth_video_{}.mp4"
DEFAULT_HTML_OUTPUT = "growth_timeline_{}.html"
DEFAULT_DURATION = 4       # 每帧持续秒数
DEFAULT_QUALITY = "720p"
QUALITY_MAP = {
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}
TRANSITION_DURATION = 0.5   # 转场持续秒数
BG_COLOR = (30, 30, 40)     # 文字帧背景色（深蓝灰）
BG_COLOR_HEX = "#1e1e28"
TEXT_COLOR = (255, 255, 255)
TEXT_COLOR_HEX = "#ffffff"
SUBTITLE_COLOR = (200, 200, 210)
SUBTITLE_COLOR_HEX = "#c8c8d2"
ACCENT_COLOR_HEX = "#6c8ce2"
VALID_RANGES = ["today", "week", "month", "year", "all"]
VALID_FORMATS = ["auto", "video", "html"]

SUBTITLE_Y_RATIO = 0.72

# Windows 字体路径候选
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",      # 黑体
    "C:/Windows/Fonts/simsun.ttc",      # 宋体
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑 (Linux)
    "/System/Library/Fonts/PingFang.ttc",               # 苹方 (macOS)
    "/Library/Fonts/Arial Unicode.ttf",
]


# ============================================================
# 依赖检查与自动安装
# ============================================================

def try_install_package(package_name):
    """尝试用 pip 安装指定包，返回是否成功。"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return False


def check_package_available(package_name):
    """检查某个 Python 包是否已安装。"""
    try:
        if package_name == "moviepy":
            import moviepy  # noqa: F401
        elif package_name == "Pillow":
            import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def check_ffmpeg_available():
    """检查 ffmpeg 是否可用。"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def get_ffmpeg_install_hint():
    """返回当前操作系统的 ffmpeg 安装命令。"""
    system = platform.system()
    if system == "Windows":
        return "winget install ffmpeg  或  choco install ffmpeg  或  从 https://ffmpeg.org 下载"
    elif system == "Darwin":
        return "brew install ffmpeg"
    else:
        return "sudo apt install ffmpeg  或  sudo yum install ffmpeg"


def check_and_install_deps(auto_install=True):
    """
    检查视频依赖，尝试自动安装。
    返回 (missing_list, install_log)。
    """
    missing = []
    install_log = []

    # 检查 moviepy
    if not check_package_available("moviepy"):
        if auto_install:
            install_log.append("正在自动安装 moviepy...")
            if try_install_package("moviepy"):
                install_log.append("moviepy 安装成功")
                if check_package_available("moviepy"):
                    pass
                else:
                    missing.append("moviepy")
            else:
                missing.append("moviepy")
                install_log.append("moviepy 自动安装失败")
        else:
            missing.append("moviepy")

    # 检查 Pillow
    if not check_package_available("Pillow"):
        if auto_install:
            install_log.append("正在自动安装 Pillow...")
            if try_install_package("Pillow"):
                install_log.append("Pillow 安装成功")
                if not check_package_available("Pillow"):
                    missing.append("Pillow")
            else:
                missing.append("Pillow")
                install_log.append("Pillow 自动安装失败")
        else:
            missing.append("Pillow")

    # 检查 ffmpeg（系统命令，不能 pip 安装）
    if not check_ffmpeg_available():
        missing.append("ffmpeg")
        install_log.append(f"ffmpeg 未安装，安装方法: {get_ffmpeg_install_hint()}")

    return missing, install_log


def get_font_path():
    """查找可用的中文字体路径。"""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


# ============================================================
# 数据加载
# ============================================================

def load_achievements(filepath, range_type):
    """加载并按日期范围筛选成就数据，按时间戳升序排列。"""
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
    except (json.JSONDecodeError, IOError, OSError):
        return []

    now = datetime.now()
    filtered = []

    for record in data:
        date_str = record.get("date", "")
        try:
            r_date = datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            continue

        if range_type == "today":
            if r_date.date() != now.date():
                continue
        elif range_type == "week":
            monday = now - timedelta(days=now.weekday())
            sunday = monday + timedelta(days=6)
            if not (monday.date() <= r_date.date() <= sunday.date()):
                continue
        elif range_type == "month":
            if r_date.year != now.year or r_date.month != now.month:
                continue
        elif range_type == "year":
            if r_date.year != now.year:
                continue
        # all: 不筛选

        filtered.append(record)

    # 按时间戳升序排列（时间线顺序）
    filtered.sort(key=lambda x: x.get("timestamp", ""))

    return filtered


# ============================================================
# HTML 时间线生成（零依赖降级方案）
# ============================================================

def generate_html_timeline(records, output_file, range_type, duration_per_slide):
    """
    生成 HTML 成长时间线文件。
    零依赖，浏览器打开即可查看。
    包含 CSS 动画自动播放、手动导航、图片展示。
    """
    # 计算日期范围
    dates = [r.get("date", "") for r in records if r.get("date")]
    date_range = f"{min(dates)} ~ {max(dates)}" if dates else ""

    # 构建幻灯片 HTML
    slides_html = []
    image_count = 0
    text_count = 0

    for i, record in enumerate(records):
        title = html_escape(record.get("title", "未知成就"))
        date_str = html_escape(record.get("date", ""))
        emotion = html_escape(record.get("emotion", ""))
        category = html_escape(record.get("category", "其他"))
        frame_path = record.get("frame", "")

        # 尝试加载图片（base64 内联）
        img_tag = ""
        safe_name = os.path.basename(frame_path) if frame_path else ""
        if safe_name and os.path.exists(safe_name):
            try:
                with open(safe_name, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("ascii")
                ext = os.path.splitext(safe_name)[1].lower()
                mime = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".webp": "image/webp",
                    ".gif": "image/gif",
                }.get(ext, "image/png")
                img_tag = f'<img src="data:{mime};base64,{img_data}" alt="{title}" loading="lazy">'
                image_count += 1
            except (IOError, OSError, MemoryError):
                text_count += 1
        else:
            text_count += 1

        emotion_html = f'<span class="emotion">{emotion}</span>' if emotion else ""

        slide = f"""
        <div class="slide" data-index="{i}">
          <div class="slide-content">
            {img_tag if img_tag else '<div class="text-card"><div class="text-card-icon">★</div></div>'}
            <div class="overlay">
              <div class="slide-title">{title} {emotion_html}</div>
              <div class="slide-meta">{date_str} · {category}</div>
            </div>
          </div>
        </div>"""
        slides_html.append(slide)

    slides_html_str = "\n".join(slides_html)
    total_slides = len(records)

    # 构建 HTML 文档
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>成长卷轴 · {date_range}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: {BG_COLOR_HEX};
      color: {TEXT_COLOR_HEX};
      font-family: -apple-system, "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
      overflow: hidden;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .header {{
      text-align: center;
      padding: 20px;
      flex-shrink: 0;
    }}
    .header h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 4px; }}
    .header .date-range {{ font-size: 14px; color: {SUBTITLE_COLOR_HEX}; }}

    .slideshow {{
      flex: 1;
      position: relative;
      overflow: hidden;
    }}
    .slide {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      opacity: 0;
      transition: opacity 0.8s ease-in-out;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .slide.active {{ opacity: 1; }}
    .slide-content {{
      position: relative;
      width: 100%; height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .slide-content img {{
      max-width: 90%;
      max-height: 85%;
      object-fit: contain;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }}
    .text-card {{
      width: 60%; height: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid rgba(108,140,226,0.2);
      border-radius: 12px;
      background: rgba(255,255,255,0.02);
    }}
    .text-card-icon {{
      font-size: 48px;
      color: {ACCENT_COLOR_HEX};
      opacity: 0.4;
    }}
    .overlay {{
      position: absolute;
      bottom: 0; left: 0; right: 0;
      background: linear-gradient(transparent, rgba(0,0,0,0.7));
      padding: 30px 40px 24px;
    }}
    .slide-title {{
      font-size: 22px;
      font-weight: 600;
      margin-bottom: 6px;
      text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }}
    .slide-meta {{
      font-size: 14px;
      color: {SUBTITLE_COLOR_HEX};
    }}
    .emotion {{ font-size: 1.2em; }}

    .controls {{
      flex-shrink: 0;
      padding: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
    }}
    .btn {{
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.15);
      color: {TEXT_COLOR_HEX};
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.2s;
    }}
    .btn:hover {{ background: rgba(255,255,255,0.2); }}
    .btn-play {{ min-width: 80px; }}

    .dots {{
      display: flex;
      gap: 6px;
      align-items: center;
    }}
    .dot {{
      width: 8px; height: 8px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      cursor: pointer;
      transition: background 0.2s;
    }}
    .dot.active {{ background: {ACCENT_COLOR_HEX}; }}

    .counter {{
      font-size: 13px;
      color: {SUBTITLE_COLOR_HEX};
      min-width: 60px;
      text-align: center;
    }}

    .footer-info {{
      text-align: center;
      padding: 8px;
      font-size: 12px;
      color: rgba(200,200,210,0.4);
      flex-shrink: 0;
    }}

    @media (max-width: 768px) {{
      .slide-title {{ font-size: 16px; }}
      .overlay {{ padding: 20px; }}
      .text-card {{ width: 80%; }}
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>成长卷轴</h1>
    <div class="date-range">{date_range} · {total_slides} 帧成就</div>
  </div>

  <div class="slideshow" id="slideshow">
    {slides_html_str}
  </div>

  <div class="controls">
    <button class="btn" id="prevBtn">&larr; 上一帧</button>
    <button class="btn btn-play" id="playBtn">暂停</button>
    <button class="btn" id="nextBtn">下一帧 &rarr;</button>
    <div class="dots" id="dots"></div>
    <div class="counter" id="counter">1 / {total_slides}</div>
  </div>

  <div class="footer-info">
    帧卷 · 瞬间一帧，终成长卷 · 图片帧 {image_count} · 文字帧 {text_count}
  </div>

  <script>
    (function() {{
      var slides = document.querySelectorAll('.slide');
      var total = slides.length;
      var current = 0;
      var playing = true;
      var duration = {duration_per_slide * 1000};
      var timer = null;

      var dotsContainer = document.getElementById('dots');
      var counter = document.getElementById('counter');

      // 创建圆点导航
      for (var i = 0; i < total; i++) {{
        (function(idx) {{
          var dot = document.createElement('div');
          dot.className = 'dot' + (idx === 0 ? ' active' : '');
          dot.onclick = function() {{ goTo(idx); resetTimer(); }};
          dotsContainer.appendChild(dot);
        }})(i);
      }}

      var dots = document.querySelectorAll('.dot');

      function goTo(index) {{
        slides[current].classList.remove('active');
        dots[current].classList.remove('active');
        current = (index + total) % total;
        slides[current].classList.add('active');
        dots[current].classList.add('active');
        counter.textContent = (current + 1) + ' / ' + total;
      }}

      function next() {{ goTo(current + 1); }}
      function prev() {{ goTo(current - 1); }}

      function startTimer() {{
        if (timer) clearInterval(timer);
        timer = setInterval(next, duration);
      }}

      function stopTimer() {{
        if (timer) {{ clearInterval(timer); timer = null; }}
      }}

      function resetTimer() {{
        if (playing) startTimer();
      }}

      document.getElementById('prevBtn').onclick = function() {{ prev(); resetTimer(); }};
      document.getElementById('nextBtn').onclick = function() {{ next(); resetTimer(); }};

      document.getElementById('playBtn').onclick = function() {{
        playing = !playing;
        this.textContent = playing ? '暂停' : '播放';
        if (playing) startTimer(); else stopTimer();
      }};

      // 键盘导航
      document.onkeydown = function(e) {{
        if (e.key === 'ArrowLeft') {{ prev(); resetTimer(); }}
        else if (e.key === 'ArrowRight') {{ next(); resetTimer(); }}
        else if (e.key === ' ') {{
          e.preventDefault();
          document.getElementById('playBtn').click();
        }}
      }};

      // 初始化
      slides[0].classList.add('active');
      startTimer();
    }})();
  </script>
</body>
</html>"""

    # 写入文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_doc)
        return True
    except (IOError, OSError) as e:
        output_json({"status": "error", "message": f"HTML文件写入失败: {e}"})
        return False


# ============================================================
# 帧创建（视频模式）
# ============================================================

def create_text_frame(title, date_str, emotion, category, width, height):
    """
    用 Pillow 生成纯色底 + 文字的图片帧。
    返回 PIL.Image 对象。
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_path = get_font_path()
    title_font_size = max(24, int(height * 0.06))
    subtitle_font_size = max(16, int(height * 0.035))

    try:
        title_font = ImageFont.truetype(font_path, title_font_size) if font_path else ImageFont.load_default()
        subtitle_font = ImageFont.truetype(font_path, subtitle_font_size) if font_path else ImageFont.load_default()
    except (IOError, OSError):
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # 标题居中
    title_y = int(height * 0.35)
    _draw_centered_text(draw, title, title_font, width, title_y, TEXT_COLOR)

    # 日期 + 分类
    subtitle = f"{date_str}  [{category}]"
    _draw_centered_text(draw, subtitle, subtitle_font, width, title_y + title_font_size + 20, SUBTITLE_COLOR)

    # 情绪 emoji
    if emotion:
        emoji_y = int(height * 0.55)
        _draw_centered_text(draw, emotion, title_font, width, emoji_y, TEXT_COLOR)

    return img


def _draw_centered_text(draw, text, font, canvas_width, y, color):
    """在画布上居中绘制文本。"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (canvas_width - text_width) // 2
    draw.text((x, y), text, fill=color, font=font)


def create_image_clip(record, width, height, duration):
    """
    从图片帧创建视频片段。
    如果图片文件不存在，降级为文字帧。
    返回 moviepy ImageClip。
    """
    from moviepy import ImageClip
    import tempfile
    from PIL import Image

    frame_path = record.get("frame", "")
    title = record.get("title", "未知成就")
    date_str = record.get("date", "")
    emotion = record.get("emotion", "")
    category = record.get("category", "其他")

    # 判定帧类型
    use_image = False
    if frame_path:
        # 安全路径处理：仅使用文件名，防止路径遍历
        safe_name = os.path.basename(frame_path)
        if safe_name and os.path.exists(safe_name):
            try:
                img = Image.open(safe_name)
                # 按比例缩放裁剪到目标尺寸
                img = _resize_crop(img, width, height)
                # 转为临时文件供 moviepy 读取
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                img.save(tmp.name, "PNG")
                clip = ImageClip(tmp.name, duration=duration)
                clip = clip.resized((width, height))
                use_image = True
            except (IOError, OSError, ValueError):
                pass

    if not use_image:
        # 降级为文字帧
        img = create_text_frame(title, date_str, emotion, category, width, height)
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name, "PNG")
        clip = ImageClip(tmp.name, duration=duration)

    # 叠加字幕
    clip = _add_text_overlay(clip, title, date_str, emotion, category, width, height)

    return clip


def _resize_crop(img, target_w, target_h):
    """按比例缩放并裁剪图片到目标尺寸。"""
    from PIL import Image as PILImage

    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), PILImage.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    return img


def _add_text_overlay(clip, title, date_str, emotion, category, width, height):
    """为视频片段叠加字幕（标题 + 日期 + 分类）。"""
    import tempfile
    from PIL import Image, ImageDraw, ImageFont

    # 使用 Pillow 生成字幕条图片，再叠加到视频上
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_path = get_font_path()
    font_size = max(20, int(height * 0.04))
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except (IOError, OSError):
        font = ImageFont.load_default()

    # 半透明字幕背景条
    bar_h = int(height * 0.18)
    bar_y = int(height * SUBTITLE_Y_RATIO)
    draw.rectangle([0, bar_y, width, bar_y + bar_h], fill=(0, 0, 0, 160))

    # 标题文字
    subtitle_text = f"{title}"
    if emotion:
        subtitle_text += f"  {emotion}"
    _draw_centered_text(draw, subtitle_text, font, width, bar_y + 15, (255, 255, 255, 255))

    # 日期 + 分类
    meta_font_size = max(14, int(height * 0.025))
    try:
        meta_font = ImageFont.truetype(font_path, meta_font_size) if font_path else ImageFont.load_default()
    except (IOError, OSError):
        meta_font = ImageFont.load_default()
    meta_text = f"{date_str}  [{category}]"
    _draw_centered_text(draw, meta_text, meta_font, width, bar_y + font_size + 25, (200, 200, 210, 230))

    # 保存叠加层并应用
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    overlay.save(tmp.name, "PNG")

    from moviepy import ImageClip
    overlay_clip = ImageClip(tmp.name, duration=clip.duration).with_position(("center", "center"))
    clip = _composite(clip, overlay_clip)

    return clip


def _composite(base_clip, overlay_clip):
    """合成两个片段。"""
    try:
        from moviepy import CompositeVideoClip
        return CompositeVideoClip([base_clip, overlay_clip])
    except ImportError:
        # 兼容 moviepy 1.x
        from moviepy.editor import CompositeVideoClip
        return CompositeVideoClip([base_clip, overlay_clip])


# ============================================================
# 视频生成主流程
# ============================================================

def cmd_generate_video(records, args, range_type):
    """视频生成主流程（已确认依赖可用）。"""
    try:
        from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
    except ImportError:
        from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

    # 参数
    width, height = QUALITY_MAP.get(args.quality, QUALITY_MAP[DEFAULT_QUALITY])
    duration = args.duration if args.duration else DEFAULT_DURATION
    if not (2 <= duration <= 10):
        output_json({"status": "error", "message": "每帧时长必须在2-10秒范围内"})
        sys.exit(1)

    # 输出文件名
    if args.output and not args.output.endswith(".html"):
        output_file = args.output
    else:
        output_file = DEFAULT_VIDEO_OUTPUT.format(datetime.now().strftime("%Y%m%d"))

    # 记录降级计数
    degraded_count = 0

    # 创建视频片段
    clips = []
    for record in records:
        frame_path = record.get("frame", "")
        if not frame_path or not os.path.exists(os.path.basename(frame_path)):
            degraded_count += 1

        clip = create_image_clip(record, width, height, duration)
        clips.append(clip)

    # 添加转场（交叉淡入淡出）
    if len(clips) > 1:
        try:
            from moviepy import vfx
            faded_clips = []
            for i, clip in enumerate(clips):
                if i > 0:
                    clip = clip.with_effects([vfx.CrossFadeIn(TRANSITION_DURATION)])
                faded_clips.append(clip)
            clips = faded_clips
        except (ImportError, AttributeError):
            faded_clips = []
            for i, clip in enumerate(clips):
                if i > 0:
                    clip = clip.crossfadein(TRANSITION_DURATION)
                faded_clips.append(clip)
            clips = faded_clips

    # 拼接
    method = "compose"
    final = concatenate_videoclips(clips, method=method)

    # 可选：添加背景音乐
    music_added = False
    if args.music:
        if os.path.exists(args.music):
            try:
                audio = AudioFileClip(args.music)
                if audio.duration < final.duration:
                    audio = audio.subloop(duration=final.duration)
                final = final.with_audio(audio)
                music_added = True
            except (IOError, OSError, ValueError):
                pass

    # 渲染输出
    try:
        codec = "libx264"
        fps = 30
        audio_codec = "aac" if music_added else None

        render_kwargs = {
            "codec": codec,
            "fps": fps,
        }
        if music_added:
            render_kwargs["audio_codec"] = audio_codec

        final.write_videofile(
            output_file,
            **render_kwargs,
            verbose=False,
            logger=None
        )
    except Exception as e:
        output_json({"status": "error", "message": f"视频渲染失败: {e}"})
        sys.exit(1)

    # 计算日期范围
    dates = [r.get("date", "") for r in records if r.get("date")]
    date_range = f"{min(dates)} ~ {max(dates)}" if dates else ""

    output_json({
        "status": "success",
        "message": "成长视频已生成",
        "format": "video",
        "video_path": output_file,
        "frame_count": len(records),
        "degraded_count": degraded_count,
        "duration_seconds": round(final.duration, 1),
        "resolution": f"{width}x{height}",
        "date_range": date_range,
        "music": music_added
    })


def cmd_generate_html(records, args, range_type):
    """HTML 时间线生成（零依赖降级方案）。"""
    duration = args.duration if args.duration else DEFAULT_DURATION

    if args.output and args.output.endswith(".html"):
        output_file = args.output
    else:
        output_file = DEFAULT_HTML_OUTPUT.format(datetime.now().strftime("%Y%m%d"))

    success = generate_html_timeline(records, output_file, range_type, duration)

    if success:
        # 统计图片/文字帧
        image_count = 0
        text_count = 0
        for record in records:
            frame_path = record.get("frame", "")
            safe_name = os.path.basename(frame_path) if frame_path else ""
            if safe_name and os.path.exists(safe_name):
                image_count += 1
            else:
                text_count += 1

        dates = [r.get("date", "") for r in records if r.get("date")]
        date_range = f"{min(dates)} ~ {max(dates)}" if dates else ""

        output_json({
            "status": "success",
            "message": "成长时间线已生成（HTML模式）",
            "format": "html",
            "html_path": output_file,
            "frame_count": len(records),
            "image_frames": image_count,
            "text_frames": text_count,
            "date_range": date_range,
            "hint": "用浏览器打开即可查看，支持自动播放和键盘导航"
        })


def cmd_generate(args):
    """主生成流程：根据 --format 决定走视频还是 HTML。"""
    range_type = args.range if args.range else "month"
    if range_type not in VALID_RANGES:
        output_json({"status": "error", "message": f"范围不合法，可选: {'/'.join(VALID_RANGES)}"})
        sys.exit(1)

    achievements_file = args.file if args.file else DEFAULT_ACHIEVEMENTS_FILE
    if args.file and not validate_filepath(achievements_file):
        output_json({"status": "error", "message": "--file 路径不合法，禁止 '..' 和绝对路径"})
        sys.exit(1)

    records = load_achievements(achievements_file, range_type)

    if not records:
        output_json({"status": "error", "message": "该时间段内暂无成就记录，无法生成"})
        sys.exit(1)

    fmt = args.format if args.format else "auto"

    # auto 模式：先尝试视频，依赖不可用则降级为 HTML
    if fmt == "html":
        cmd_generate_html(records, args, range_type)
        return

    if fmt == "video":
        # 强制视频模式，检查依赖
        missing, install_log = check_and_install_deps(auto_install=False)
        if missing:
            output_json({
                "status": "error",
                "message": f"视频模式缺少依赖: {' + '.join(missing)}",
                "install_log": install_log,
                "ffmpeg_hint": get_ffmpeg_install_hint() if "ffmpeg" in missing else None,
                "hint": "使用 --format auto 可自动安装并降级，或 --format html 生成零依赖时间线"
            })
            sys.exit(1)
        cmd_generate_video(records, args, range_type)
        return

    # auto 模式（默认）
    missing, install_log = check_and_install_deps(auto_install=True)

    if not missing:
        # 依赖齐全，生成视频
        if install_log:
            output_json({
                "status": "info",
                "message": "依赖已就绪: " + "; ".join(install_log),
                "next": "开始生成视频..."
            })
        cmd_generate_video(records, args, range_type)
    else:
        # 依赖仍缺失，降级为 HTML
        if install_log:
            output_json({
                "status": "warning",
                "message": "视频依赖不可用，自动降级为 HTML 时间线",
                "missing": missing,
                "install_log": install_log,
                "ffmpeg_hint": get_ffmpeg_install_hint() if "ffmpeg" in missing else None,
                "hint": "安装依赖后可使用 --format video 生成视频"
            })
        cmd_generate_html(records, args, range_type)


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="帧卷 - 成长卷轴（成长视频/时间线生成器）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python growth_video.py --range month                    # 自动模式（优先视频，降级HTML）
  python growth_video.py --range week --format html       # 强制HTML时间线（零依赖）
  python growth_video.py --range month --format video      # 强制视频模式
  python growth_video.py --range all --duration 5 --music bgm.mp3
  python growth_video.py --range year --output my_growth.mp4 --quality 1080p
        """
    )

    parser.add_argument("--range", default="month",
                        help=f"成就时间范围: {'/'.join(VALID_RANGES)}（默认: month）")
    parser.add_argument("--output", default="",
                        help="输出文件名（默认: growth_video_YYYYMMDD.mp4 或 .html）")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION,
                        help="每帧持续秒数 2-10（默认: 4）")
    parser.add_argument("--quality", default=DEFAULT_QUALITY,
                        help=f"视频分辨率: {'/'.join(QUALITY_MAP.keys())}（默认: {DEFAULT_QUALITY}）")
    parser.add_argument("--music", default="",
                        help="背景音乐文件路径（可选，仅视频模式）")
    parser.add_argument("--format", default="auto",
                        help=f"输出格式: {'/'.join(VALID_FORMATS)}（默认: auto）"
                             "auto=优先视频自动降级HTML, video=仅视频, html=仅HTML")
    parser.add_argument("--file", default="",
                        help=f"成就数据文件路径（默认: {os.path.basename(DEFAULT_ACHIEVEMENTS_FILE)}）")

    args = parser.parse_args()
    cmd_generate(args)


if __name__ == "__main__":
    main()
