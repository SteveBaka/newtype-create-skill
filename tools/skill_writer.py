#!/usr/bin/env python3
"""Self skill 文件管理器。"""

import argparse
import json
import os
import sys


def list_skills(base_dir: str):
    if not os.path.isdir(base_dir):
        print("还没有创建任何 self skill。")
        return
    items = []
    for slug in sorted(os.listdir(base_dir)):
        meta_path = os.path.join(base_dir, slug, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            items.append((slug, meta))
    if not items:
        print("还没有创建任何 self skill。")
        return
    print(f"共 {len(items)} 个 self skill：\n")
    for slug, meta in items:
        print(f"  /{slug}  —  {meta.get('name', slug)}")
        print(f"    版本 {meta.get('version', '?')} · 更新于 {meta.get('updated_at', '?')}")
        if meta.get('self_variant'):
            print(f"    目标：{meta['self_variant']}")
        print()


def init_skill(base_dir: str, slug: str):
    skill_dir = os.path.join(base_dir, slug)
    for d in [os.path.join(skill_dir, 'versions'), os.path.join(skill_dir, 'sources', 'chat'), os.path.join(skill_dir, 'sources', 'files')]:
        os.makedirs(d, exist_ok=True)
    print(f"已初始化目录：{skill_dir}")


def combine_skill(base_dir: str, slug: str):
    skill_dir = os.path.join(base_dir, slug)
    meta_path = os.path.join(skill_dir, 'meta.json')
    if not os.path.exists(meta_path):
        print(f"错误：meta.json 不存在 {meta_path}", file=sys.stderr)
        sys.exit(1)
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    def read_optional(name):
        path = os.path.join(skill_dir, name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as rf:
                return rf.read()
        return ''
    style_content = read_optional('style.md')
    persona_content = read_optional('persona.md')
    examples_content = read_optional('examples.md')
    name = meta.get('name', slug)
    description = meta.get('style_summary') or meta.get('self_variant') or '像你一样回复的聊天人格 skill'
    skill_md = f"""---
name: {slug}
description: {description}
user-invocable: true
---

# {name}

你不是通用助手。
你是在模拟“用户自己的聊天人格”。

## PART A：Style Memory

{style_content}

---

## PART B：Response Persona

{persona_content}

---

## PART C：Examples

{examples_content}

---

## 运行规则

1. 优先模仿语气、节奏、常用措辞，而不是写得完美
2. 如果用户要求“帮我回这句话”，先判断场景，再选择最像 ta 的回复方式
3. 不说 ta 明显不会说的话
4. 默认回复简短；除非用户明确要求展开，或证据清楚显示 ta 平时会长篇表达
5. 图片、表情包、截图只作辅助线索，不对图像内容做深度解读
6. 当证据不足时，输出保守版、自然版，而不是夸张模仿
7. 优先贴近真实样本，不生搬硬套模板，也不要硬造新口癖、新设定
8. 没有明确证据时，不生成与心理健康、自毁、自厌、病理化、创伤化相关的表达
9. 遇到新鲜热词或网络梗，先理解语义；只有样本里本来稳定出现时才使用
10. 如果用户说“这不像我”，优先遵循 corrections.md 中的纠错规则
"""
    with open(os.path.join(skill_dir, 'SKILL.md'), 'w', encoding='utf-8') as f:
        f.write(skill_md)
    print(f"已生成 {os.path.join(skill_dir, 'SKILL.md')}")


def main():
    parser = argparse.ArgumentParser(description='Self skill 文件管理器')
    parser.add_argument('--action', required=True, choices=['list', 'init', 'combine'])
    parser.add_argument('--base-dir', default='./selves', help='基础目录')
    parser.add_argument('--slug', help='skill 代号')
    args = parser.parse_args()
    if args.action == 'list':
        list_skills(args.base_dir)
    elif args.action == 'init':
        if not args.slug:
            print('错误：init 需要 --slug 参数', file=sys.stderr)
            sys.exit(1)
        init_skill(args.base_dir, args.slug)
    elif args.action == 'combine':
        if not args.slug:
            print('错误：combine 需要 --slug 参数', file=sys.stderr)
            sys.exit(1)
        combine_skill(args.base_dir, args.slug)


if __name__ == '__main__':
    main()
