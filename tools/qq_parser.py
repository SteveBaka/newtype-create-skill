#!/usr/bin/env python3
"""QQ 聊天记录解析器（复用通用 parser）。"""

from generic_chat_parser import detect_format, parse_text, parse_html, extract_style_stats
import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description='QQ 聊天记录解析器')
    parser.add_argument('--file', required=True, help='输入文件路径')
    parser.add_argument('--self-name', required=True, help='你的名字/昵称')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--format', default='auto', help='auto/html/text')
    parser.add_argument('--list-senders', action='store_true', help='输出候选 sender / nickname 列表')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    fmt = detect_format(args.file) if args.format == 'auto' else args.format
    messages = parse_html(args.file, args.self_name) if fmt == 'html' else parse_text(args.file, args.self_name)
    stats = extract_style_stats(messages)
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# QQ 聊天记录分析 — {args.self_name}\n\n")
        f.write(f"来源文件：{args.file}\n")
        f.write(f"检测格式：{fmt}\n")
        f.write(f"消息角色统计：{json.dumps(stats['message_roles'], ensure_ascii=False)}\n")
        f.write(f"self 消息数：{stats['self_message_count']}\n\n")
        f.write("## 识别说明\n")
        f.write("- 优先使用昵称、时间戳、结构标签判断\n")
        f.write("- 对布局型材料，右侧气泡优先视为自己消息\n")
        f.write("- 群聊建议先查看候选发送者，再确认哪个名字是你自己\n\n")
        if stats['sender_candidates']:
            f.write("## 候选发送者\n")
            for item in stats['sender_candidates']:
                f.write(
                    f"- {item['sender']} | 条数: {item['count']} | 主要判定: {item['top_role']} | 占比: {item['top_role_ratio']}\n"
                )
            f.write("\n")
        f.write("## 样本\n")
        for i, sample in enumerate(stats['samples'], 1):
            f.write(f"{i}. {sample}\n")
    if args.list_senders and stats['sender_candidates']:
        print('候选 sender / nickname：')
        for item in stats['sender_candidates']:
            print(
                f"- {item['sender']} | 条数: {item['count']} | 主要判定: {item['top_role']} | 占比: {item['top_role_ratio']}"
            )
    print(f"分析完成，结果已写入 {args.output}")


if __name__ == '__main__':
    main()
