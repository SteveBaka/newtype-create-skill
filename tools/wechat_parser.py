#!/usr/bin/env python3
"""微信聊天记录解析器（self 风格提取版）。"""

from generic_chat_parser import detect_format, parse_json, parse_text, parse_html, extract_style_stats
import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description='微信聊天记录解析器')
    parser.add_argument('--file', required=True, help='输入文件路径')
    parser.add_argument('--self-name', required=True, help='你的名字/昵称')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--format', default='auto', help='auto/json/html/text')
    parser.add_argument('--list-senders', action='store_true', help='输出候选 sender / nickname 列表')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误：文件不存在 {args.file}", file=sys.stderr)
        sys.exit(1)

    fmt = detect_format(args.file) if args.format == 'auto' else args.format
    if fmt == 'json':
        messages = parse_json(args.file, args.self_name)
    elif fmt == 'html':
        messages = parse_html(args.file, args.self_name)
    else:
        messages = parse_text(args.file, args.self_name)

    stats = extract_style_stats(messages)
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# 微信聊天记录分析 — {args.self_name}\n\n")
        f.write(f"来源文件：{args.file}\n")
        f.write(f"检测格式：{fmt}\n")
        f.write(f"消息角色统计：{json.dumps(stats['message_roles'], ensure_ascii=False)}\n")
        f.write(f"self 消息数：{stats['self_message_count']}\n\n")
        f.write("## 识别说明\n")
        f.write("- 优先使用 sender / role / is_self 等结构字段\n")
        f.write("- 对 HTML / 截图导出的半结构化材料，可结合右侧通常为自己消息的规则辅助判断\n\n")
        if stats['sender_candidates']:
            f.write("## 候选发送者\n")
            for item in stats['sender_candidates']:
                f.write(
                    f"- {item['sender']} | 条数: {item['count']} | 主要判定: {item['top_role']} | 占比: {item['top_role_ratio']}\n"
                )
            f.write("\n")
        f.write("## 风格摘要\n")
        f.write(f"- 平均消息长度：{stats['avg_length']}\n")
        for name, value in stats['punctuation'].items():
            f.write(f"- {name}: {value}\n")
        f.write("\n## 样本\n")
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
