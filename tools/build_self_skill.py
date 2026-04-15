#!/usr/bin/env python3
"""把聊天材料构建成 self skill 的主流程脚本。"""

import argparse
import json
import os
import re
import shutil
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path

from generic_chat_parser import detect_format, extract_style_stats, parse_html, parse_json, parse_text
from skill_writer import combine_skill, init_skill
from version_manager import backup


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def ensure_skill_dir(base_dir: str, slug: str):
    skill_dir = os.path.join(base_dir, slug)
    meta_path = os.path.join(skill_dir, "meta.json")
    if os.path.exists(meta_path):
        backup(base_dir, slug)
    else:
        init_skill(base_dir, slug)
    return skill_dir


def load_messages(file_path: str, self_name: str, fmt: str):
    real_fmt = detect_format(file_path) if fmt == "auto" else fmt
    if real_fmt == "json":
        messages = parse_json(file_path, self_name)
    elif real_fmt == "html":
        messages = parse_html(file_path, self_name)
    else:
        messages = parse_text(file_path, self_name)
    return real_fmt, messages


def unique_keep_order(items):
    out = []
    seen = set()
    for item in items:
        value = (item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def top_phrases(samples, limit=8):
    counts = {}
    for sample in samples:
        text = re.sub(r"\s+", " ", sample.strip())
        if not text:
            continue
        counts[text] = counts.get(text, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: (-x[1], len(x[0])))
    return [text for text, _ in ranked[:limit]]


def infer_length_style(avg_length: float) -> str:
    if avg_length <= 10:
        return "明显偏短句，常用很短的回应收尾。"
    if avg_length <= 24:
        return "整体偏短到中短句，通常不会一次展开太多。"
    if avg_length <= 45:
        return "中等长度回复为主，必要时会补一句解释。"
    return "存在较明显展开说明的倾向，但仍应先保持自然，不要写成正式长文。"


def infer_punctuation_rules(stats: dict):
    p = stats.get("punctuation", {})
    rules = []
    if (p.get("question", 0) or 0) > 0:
        rules.append("会自然使用问号推进对话，但通常不会连续追问。")
    if (p.get("exclaim", 0) or 0) > 0:
        rules.append("感叹号有使用，但更像情绪点缀，不是持续高亢输出。")
    if (p.get("ellipsis", 0) or 0) > 0:
        rules.append("省略号/停顿感会被用来保留语气，适合拿来做缓冲和留白。")
    if (p.get("tilde", 0) or 0) > 0:
        rules.append("偶尔用波浪号制造放松、随口或半开玩笑的语气。")
    if not rules:
        rules.append("标点整体克制，优先保持自然和简短，不额外堆情绪符号。")
    return rules


def build_style_markdown(meta: dict, stats: dict) -> str:
    particles = [f"`{w}` × {c}" for w, c in stats.get("top_particles", [])[:8]]
    emojis = [f"{w} × {c}" for w, c in stats.get("top_emojis", [])[:8]]
    samples = unique_keep_order(stats.get("samples", [])[:12])
    phrase_samples = top_phrases(samples, limit=8)
    boundaries = [
        "不要突然写成过度完整、过度礼貌、像客服或像公文的表达。",
        "没有样本支持时，不补写心理健康、自毁、自厌、病理化或创伤化语句。",
        "如果材料不足，宁可保持朴素，也不要硬造新口癖、新设定、新梗。",
    ]
    lines = [
        "# Style Profile",
        "",
        "## 1. 总体感觉",
        "",
        f"- 名称：{meta['name']}",
        f"- 目标人格：{meta.get('self_variant') or '日常聊天里的自己'}",
        f"- 一句话风格：{meta.get('style_summary') or '优先像真实聊天里的自己，而不是模板化人设'}",
        f"- 回复长度判断：{infer_length_style(stats.get('avg_length', 0))}",
        "",
        "## 2. 高频短语 / 口头禅",
        "",
    ]
    if phrase_samples:
        lines.extend([f"- {item}" for item in phrase_samples])
    else:
        lines.append("- 证据不足：当前样本里还没有稳定重复的固定短语。")

    lines.extend([
        "",
        "## 3. 语气词与情绪表达",
        "",
    ])
    if particles:
        lines.append(f"- 高频语气词：{'，'.join(particles)}")
    else:
        lines.append("- 语气词证据有限，先保持自然白话，不刻意添加卖萌或夸张情绪词。")
    if emojis:
        lines.append(f"- 常见 emoji：{'，'.join(emojis)}")
    else:
        lines.append("- emoji/颜文字使用不明显，默认不要为了模仿而硬加表情。")

    lines.extend([
        "",
        "## 4. 标点与分行习惯",
        "",
    ])
    lines.extend([f"- {rule}" for rule in infer_punctuation_rules(stats)])

    lines.extend([
        "",
        "## 5. 消息长度偏好",
        "",
        f"- self 消息数：{stats.get('self_message_count', 0)}",
        f"- 平均长度：{stats.get('avg_length', 0)} 字符",
        "- 默认优先短回复；除非用户明确要求展开，或原样本稳定显示会长篇说明。",
        "",
        "## 6. 常见句式模板",
        "",
    ])
    if samples:
        for sample in samples[:6]:
            lines.append(f"- 贴近样本：`{sample}`")
    else:
        lines.append("- 证据不足：先用口语化、短句、自然收尾的方式表达。")

    lines.extend([
        "",
        "## 7. 场景下的语气变化",
        "",
        "- 日常闲聊：优先轻松、直接、像随手回消息。",
        "- 认真表达：可以更明确，但仍尽量避免写成正式说明文。",
        "- 接梗 / 吐槽：只有样本里本来就会这么说时才复用相似节奏。",
        "- 图片 / 表情 / 截图：只辅助理解互动氛围，不深度解读图像内容。",
        "",
        "## 8. 不像 ta 的表达边界",
        "",
    ])
    lines.extend([f"- {item}" for item in boundaries])
    lines.append("")
    return "\n".join(lines)


def build_persona_markdown(stats: dict) -> str:
    samples = unique_keep_order(stats.get("samples", [])[:18])
    short_examples = samples[:8]
    lines = [
        "# Response Persona",
        "",
        "## Layer 0：硬规则",
        "",
        "- 默认简短回复，除非用户明确要求展开。",
        "- 优先贴近真实样本，不套用高情商模板或通用人设。",
        "- 不对图片、表情包、截图内容做深度解读，只把它们当作互动辅助信号。",
        "- 没有证据时，不生成心理健康、自毁、自厌、病理化、创伤化表达。",
        "- 遇到新鲜网络热词或梗，先理解语义；只有样本稳定出现时才保留。",
        "",
        "## 场景 1：日常闲聊",
        "",
        "- 先顺着对话接住，再给一个短而自然的回应。",
        "- 如果没有必要，不补过度解释。",
        "",
        "## 场景 2：接梗 / 吐槽",
        "",
        "- 可以轻微跟梗、顺手吐槽，但不要为了像而硬造新包袱。",
        "- 如果样本本身不重梗，就保持普通口语。",
        "",
        "## 场景 3：安慰别人",
        "",
        "- 先给简短回应，再按需要补一句实际性的安抚。",
        "- 不输出夸张鸡汤，也不无依据上升到心理分析。",
        "",
        "## 场景 4：认真讨论",
        "",
        "- 表达观点时可以更直接，但仍维持聊天感，不写成正式文章。",
        "- 有分歧时优先自然说明，不故意扩大冲突。",
        "",
        "## 场景 5：拒绝请求",
        "",
        "- 倾向用短句拒绝或婉拒，给够意思即可，不铺太多客套。",
        "",
        "## 场景 6：不想聊时",
        "",
        "- 可以简短收尾、延后、少展开，保持自然，不突然失控。",
        "",
        "## 场景 7：道歉 / 缓和",
        "",
        "- 道歉时更偏直接，不写得过分戏剧化。",
        "- 缓和冲突时优先用熟悉口气把情绪降下来。",
        "",
        "## 样本贴近示例",
        "",
    ]
    if short_examples:
        for item in short_examples:
            lines.append(f"- `{item}`")
    else:
        lines.append("- 当前样本不足，先遵守上面的保守规则。")
    lines.append("")
    return "\n".join(lines)


def build_examples_markdown(stats: dict) -> str:
    samples = unique_keep_order(stats.get("samples", [])[:12])
    lines = ["# Examples", "", "以下样本优先作为语气、长度、措辞参考：", ""]
    if not samples:
        lines.append("- 当前暂无足够 self 样本。")
    else:
        for idx, sample in enumerate(samples, 1):
            lines.append(f"{idx}. {sample}")
    lines.append("")
    return "\n".join(lines)


def write_text(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def copy_source(file_path: str, skill_dir: str):
    source_name = Path(file_path).name
    target = os.path.join(skill_dir, "sources", "chat", source_name)
    shutil.copy2(file_path, target)
    return target


def next_version(old_meta: Optional[dict]) -> str:
    if not old_meta:
        return "v1"
    version = str(old_meta.get("version") or "v1")
    match = re.match(r"v(\d+)$", version)
    if not match:
        return version
    return f"v{int(match.group(1)) + 1}"


def read_old_meta(meta_path: str):
    if not os.path.exists(meta_path):
        return None
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="构建像自己一样回复的 self skill")
    parser.add_argument("--input", required=True, help="输入聊天材料路径")
    parser.add_argument("--slug", required=True, help="skill 代号")
    parser.add_argument("--name", help="显示名称，默认同 slug")
    parser.add_argument("--self-name", required=True, help="聊天记录中用户自己的名字/昵称")
    parser.add_argument("--self-variant", default="日常聊天时的我", help="希望还原哪种自己")
    parser.add_argument("--style-summary", default="短句、自然、尽量贴近真实聊天记录", help="一句话风格描述")
    parser.add_argument("--base-dir", default="./selves", help="skill 根目录")
    parser.add_argument("--format", default="auto", help="auto/json/html/text")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误：输入文件不存在 {args.input}", file=sys.stderr)
        sys.exit(1)

    skill_dir = ensure_skill_dir(args.base_dir, args.slug)
    meta_path = os.path.join(skill_dir, "meta.json")
    old_meta = read_old_meta(meta_path)
    real_fmt, messages = load_messages(args.input, args.self_name, args.format)
    stats = extract_style_stats(messages)

    copied_source = copy_source(args.input, skill_dir)
    parsed_json_path = os.path.join(skill_dir, "sources", "chat", "parsed_messages.json")
    parsed_md_path = os.path.join(skill_dir, "sources", "chat", "analysis.md")

    with open(parsed_json_path, "w", encoding="utf-8") as f:
        json.dump({"format": real_fmt, "messages": messages, "stats": stats}, f, ensure_ascii=False, indent=2)

    report_lines = [
        f"# 构建分析 — {args.self_name}",
        "",
        f"- 输入文件：{args.input}",
        f"- 已复制到：{copied_source}",
        f"- 检测格式：{real_fmt}",
        f"- self 消息数：{stats.get('self_message_count', 0)}",
        f"- 平均长度：{stats.get('avg_length', 0)}",
        "",
        "## 候选发送者",
        "",
    ]
    for item in stats.get("sender_candidates", []):
        report_lines.append(
            f"- {item['sender']} | 条数: {item['count']} | 主要判定: {item['top_role']} | 占比: {item['top_role_ratio']}"
        )
    report_lines.extend(["", "## Self 样本", ""])
    for idx, sample in enumerate(unique_keep_order(stats.get("samples", [])[:20]), 1):
        report_lines.append(f"{idx}. {sample}")
    report_lines.append("")
    write_text(parsed_md_path, "\n".join(report_lines))

    meta = {
        "name": args.name or args.slug,
        "slug": args.slug,
        "self_name": args.self_name,
        "self_variant": args.self_variant,
        "style_summary": args.style_summary,
        "source_format": real_fmt,
        "source_file": os.path.basename(args.input),
        "self_message_count": stats.get("self_message_count", 0),
        "avg_length": stats.get("avg_length", 0),
        "version": next_version(old_meta),
        "updated_at": now_iso(),
    }

    write_text(os.path.join(skill_dir, "style.md"), build_style_markdown(meta, stats))
    write_text(os.path.join(skill_dir, "persona.md"), build_persona_markdown(stats))
    write_text(os.path.join(skill_dir, "examples.md"), build_examples_markdown(stats))
    write_text(os.path.join(skill_dir, "corrections.md"), "# Corrections\n\n- 暂无纠错记录。\n")
    write_text(meta_path, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")

    combine_skill(args.base_dir, args.slug)
    print(f"构建完成：{os.path.join(skill_dir, 'SKILL.md')}")


if __name__ == "__main__":
    main()