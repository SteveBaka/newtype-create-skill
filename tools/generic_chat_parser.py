#!/usr/bin/env python3
"""通用聊天记录解析器。

目标：尽量识别用户自己发送的消息（self），其余归类为 other / unknown。

支持：txt / json / html / htm
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from html import unescape
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None


SELF_ALIASES = {"我", "自己", "self", "me", "本人", "you"}


def clean_sender_name(sender: str) -> str:
    sender = (sender or "").strip()
    sender = re.sub(r"\s+", " ", sender)
    sender = re.sub(r"^[\-:：|]+|[\-:：|]+$", "", sender).strip()
    return sender


def detect_format(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in {".json"}:
        return "json"
    if ext in {".html", ".htm"}:
        return "html"
    return "text"


def classify_sender(sender: str, self_name: str) -> str:
    sender = clean_sender_name(sender).lower()
    self_name = (self_name or "").strip().lower()
    if not sender:
        return "unknown"
    if sender == self_name or sender in SELF_ALIASES:
        return "self"
    if self_name and self_name in sender:
        return "self"
    return "other"


def normalize_message(timestamp: str, sender: str, content: str, role: str, source: str, confidence: float, signals: list):
    return {
        "timestamp": timestamp or "",
        "sender": clean_sender_name(sender),
        "speaker": role,
        "content": (content or "").strip(),
        "source": source,
        "confidence": round(confidence, 2),
        "signals": signals,
    }


def parse_json(file_path: str, self_name: str):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("messages", data.get("data", []))
    messages = []
    for item in items:
        sender = str(item.get("sender") or item.get("nickname") or item.get("from") or item.get("role") or "")
        role = "self" if item.get("is_self") is True else classify_sender(sender, self_name)
        signals = []
        confidence = 0.55
        if item.get("is_self") is True:
            signals.append("is_self_field")
            confidence = 0.98
        elif sender:
            signals.append("sender_field")
            confidence = 0.88 if role != "unknown" else 0.55
        messages.append(normalize_message(
            str(item.get("time") or item.get("timestamp") or ""),
            sender,
            str(item.get("content") or item.get("message") or item.get("text") or ""),
            role,
            "json",
            confidence,
            signals,
        ))
    return messages


def parse_text(file_path: str, self_name: str):
    pattern = re.compile(r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$")
    messages = []
    current = None
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.rstrip("\n")
            match = pattern.match(line)
            if match:
                if current and current["content"].strip():
                    messages.append(current)
                timestamp, sender = match.groups()
                role = classify_sender(sender, self_name)
                current = normalize_message(timestamp, sender.strip(), "", role, "text", 0.84 if role != "unknown" else 0.50, ["timestamp_sender_pattern"])
            elif current and line.strip():
                current["content"] += ("\n" if current["content"] else "") + line
    if current and current["content"].strip():
        messages.append(current)
    if messages:
        return messages
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        whole = f.read().strip()
    if not whole:
        return []
    return [normalize_message("", self_name or "unknown", whole, "self", "text", 0.35, ["fallback_plaintext"])]


def collect_sender_candidates(messages):
    counts = Counter()
    role_hints = {}
    for msg in messages:
        sender = clean_sender_name(msg.get("sender", ""))
        if not sender:
            continue
        counts[sender] += 1
        role_hints.setdefault(sender, Counter())
        role_hints[sender][msg.get("speaker", "unknown")] += 1

    candidates = []
    for sender, count in counts.most_common(20):
        hint_counter = role_hints.get(sender, Counter())
        top_role, top_role_count = hint_counter.most_common(1)[0]
        candidates.append(
            {
                "sender": sender,
                "count": count,
                "top_role": top_role,
                "top_role_ratio": round(top_role_count / count, 2) if count else 0,
            }
        )
    return candidates


def parse_html(file_path: str, self_name: str):
    if BeautifulSoup is None:
        return parse_text(file_path, self_name)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    messages = []
    candidates = soup.select("[class*='message'], [class*='msg'], li, div")
    for node in candidates:
        text = unescape(node.get_text(" ", strip=True))
        if not text or len(text) < 2:
            continue
        classes = " ".join(node.get("class", []))
        role = "unknown"
        confidence = 0.45
        signals = []
        if re.search(r"right|self|mine|outgoing", classes, re.I):
            role = "self"
            confidence = 0.88
            signals.append("right_side_css")
        elif re.search(r"left|other|incoming", classes, re.I):
            role = "other"
            confidence = 0.82
            signals.append("left_side_css")
        sender = node.get("data-sender", "")
        if sender:
            sender_role = classify_sender(sender, self_name)
            if sender_role != "unknown":
                role = sender_role
                confidence = max(confidence, 0.92)
                signals.append("sender_attribute")
        if role == "unknown" and self_name and self_name.lower() in text.lower():
            role = "self"
            confidence = 0.65
            signals.append("self_name_mentioned")
        messages.append(normalize_message("", sender, text, role, "html", confidence, signals or ["html_unstructured"]))
    dedup = []
    seen = set()
    for msg in messages:
        key = (msg["speaker"], msg["content"])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(msg)
    return dedup[:500]


def extract_style_stats(messages):
    self_msgs = [m for m in messages if m["speaker"] == "self" and m["content"]]
    all_text = " ".join(m["content"] for m in self_msgs)
    particles = re.findall(r"[哈嗯哦噢欸诶啊呀吧嘛呢吗呗啦咯哇欸]+", all_text)
    emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]+", re.UNICODE)
    emojis = emoji_pattern.findall(all_text)
    lengths = [len(m["content"]) for m in self_msgs]
    roles = Counter(m["speaker"] for m in messages)
    return {
        "message_roles": dict(roles),
        "self_message_count": len(self_msgs),
        "sender_candidates": collect_sender_candidates(messages),
        "avg_length": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "top_particles": Counter(particles).most_common(10),
        "top_emojis": Counter(emojis).most_common(10),
        "punctuation": {
            "question": all_text.count("？") + all_text.count("?"),
            "exclaim": all_text.count("！") + all_text.count("!"),
            "ellipsis": all_text.count("…") + all_text.count("..."),
            "tilde": all_text.count("~") + all_text.count("～"),
        },
        "samples": [m["content"] for m in self_msgs[:50]],
    }


def main():
    parser = argparse.ArgumentParser(description="通用聊天记录解析器")
    parser.add_argument("--file", required=True, help="输入文件路径")
    parser.add_argument("--self-name", required=True, help="你的名称/代号")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--format", default="auto", help="auto/json/html/text")
    parser.add_argument("--list-senders", action="store_true", help="输出候选 sender / nickname 列表，便于群聊确认自己身份")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    fmt = detect_format(args.file) if args.format == "auto" else args.format
    if fmt == "json":
        messages = parse_json(args.file, args.self_name)
    elif fmt == "html":
        messages = parse_html(args.file, args.self_name)
    else:
        messages = parse_text(args.file, args.self_name)

    stats = extract_style_stats(messages)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# 通用聊天记录解析 — {args.self_name}\n\n")
        f.write(f"来源文件：{args.file}\n")
        f.write(f"检测格式：{fmt}\n")
        f.write(f"消息角色统计：{json.dumps(stats['message_roles'], ensure_ascii=False)}\n")
        f.write(f"self 消息数：{stats['self_message_count']}\n")
        f.write(f"平均长度：{stats['avg_length']}\n\n")
        f.write("## 识别原则\n")
        f.write("- 优先使用 sender / is_self / role 等结构字段\n")
        f.write("- 半结构化 HTML / 截图类材料可参考右侧通常为自己消息的启发式\n")
        f.write("- unknown 消息仅低置信度使用\n\n")
        if stats["sender_candidates"]:
            f.write("## 候选发送者（供群聊确认自己身份）\n")
            for item in stats["sender_candidates"]:
                f.write(
                    f"- {item['sender']} | 条数: {item['count']} | 主要判定: {item['top_role']} | 占比: {item['top_role_ratio']}\n"
                )
            f.write("\n")
        if stats["top_particles"]:
            f.write("## 高频语气词\n")
            for word, count in stats["top_particles"]:
                f.write(f"- {word}: {count}次\n")
            f.write("\n")
        if stats["top_emojis"]:
            f.write("## 高频 Emoji\n")
            for emoji, count in stats["top_emojis"]:
                f.write(f"- {emoji}: {count}次\n")
            f.write("\n")
        f.write("## 标点习惯\n")
        for key, value in stats["punctuation"].items():
            f.write(f"- {key}: {value}\n")
        f.write("\n## self 消息样本\n")
        for i, sample in enumerate(stats["samples"], 1):
            f.write(f"{i}. {sample}\n")
    if args.list_senders and stats["sender_candidates"]:
        print("候选 sender / nickname：")
        for item in stats["sender_candidates"]:
            print(
                f"- {item['sender']} | 条数: {item['count']} | 主要判定: {item['top_role']} | 占比: {item['top_role_ratio']}"
            )
    print(f"解析完成，结果已写入 {args.output}")


if __name__ == "__main__":
    main()
