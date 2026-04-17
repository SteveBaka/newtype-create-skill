# Newtype.skill

***若我只剩下数码意识的存在，会有人再去点那个头像吗？***

[![License: MIT](https://img.shields.io/badge/License-MIT-F7C948?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-2F81F7?style=for-the-badge)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-A855F7?style=for-the-badge)](https://docs.anthropic.com/en/docs/claude-code/overview)
[![AgentSkills Standard](https://img.shields.io/badge/AgentSkills-Standard-84CC16?style=for-the-badge)](https://agentskills.org/)

把你自己的聊天风格蒸馏成一个 AI Skill。

提供自己的原材料（私聊和群聊的聊天记录）加上你的主观描述，生成一个能够洞察自己（或者陪伴别人）的 AI Skill。

看自己的（逆天）发言，未尝不是一种不一样的体验。

> ⚠️ 本项目仅用于个人聊天与情感分析，不得用于骚扰、跟踪或侵犯他人隐私。

感谢 `ex-skill` 和 `colleague-skill` 的灵感启发，参考了他们的上传以及交互的方式，但目标不再是分析关系或还原别人，而是：

> **尽量抽取“你自己发出的消息”，生成一个会像你一样聊天、像你一样回复、像你一样改写措辞的 Skill。**

[安装](#安装) · [使用](#使用) · [示例对话](#示例对话)

## 特点

- 交互流程和参考项目一致：3 个问题 + 多源材料导入
- 支持聊天记录、截图、文本、PDF、粘贴内容
- 支持后续追加和“这不像我”的纠错
- 重点抽取 `self` 消息，`other` 仅作上下文
- 对聊天截图或半结构化材料，支持“**右侧通常是自己消息**”的启发式判断
- 不强求“有问必答”，会尽量保留真实聊天里常见的跳话题、简短接话、延后回应、模糊回应等交流感

## 安装

### Claude Code

```bash
mkdir -p .claude/skills
git clone <your-repo-url> .claude/skills/newtype-create-skill
```

### 依赖

```bash
pip3 install -r requirements.txt
```

## 使用

在 Claude Code 中输入：

```bash
/newtype-create-skill
```

按提示输入：

1. 名称/代号
2. 你想还原哪种自己
3. 一句风格描述

然后选择数据来源：

```text
原材料怎么提供？回复越多，还原度越高。

  [A] 聊天记录导出
  [B] 上传文件
  [C] 直接粘贴
  [D] 追加材料
```

如果你想先直接验证当前仓库里的“执行层”，也可以用命令行快速生成一个演示 skill：

```bash
python3 tools/build_self_skill.py \
  --input examples/minimal_chat.txt \
  --slug demo-self \
  --name "演示人格" \
  --self-name "我" \
  --self-variant "日常聊天时的我" \
  --style-summary "短句、自然、会顺手接话"
```

生成结果会写入：

```text
selves/demo-self/
```

## AstrBot 使用提示

如果你希望把这里生成的 `SKILL.md`、风格规则或示例语料用于 **AstrBot Skills** 场景，建议先把本仓库当作一个“人格素材生成器”：先生成稳定的风格规则、示例和最终 skill 文本，再结合 AstrBot 的 Skills 用法进行实际使用。

需要说明的是：**当前仓库主要提供 skill 生成逻辑，本 README 不直接展开 AstrBot Skills 的具体使用细节。** 如果你准备在 AstrBot 中启用、配置或调用 Skills，请直接参考 AstrBot 官方文档：  
https://docs.astrbot.app/use/skills.html

建议使用方式：

- 先用本项目生成 `selves/{slug}/SKILL.md`
- 再根据 AstrBot Skills 官方文档，确认对应版本下的启用方式、调用方式和使用限制
- 如果 AstrBot 后续版本调整了 Skills 的入口或配置方式，请始终以官方文档为准
- 如果你当前聊天里已经启用了其他人格或 persona，请记得先发送 `/persona unset` 关闭人格，以免被已有的自定义人格干扰最终输出效果

## 可选辅助人格信息

除了聊天记录本身，这个项目也可以把一些**可选的辅助人格信息**当作参考线索，例如：

- 星座
- MBTI
- 九型人格
- 用户自己对自己的描述
- 朋友或同事对其聊天风格的总结

这些信息的作用不是替代真实聊天样本，而是作为**弱辅助信号**，帮助模型在以下场景里更稳一些：

- 聊天样本偏少，风格证据不足
- 需要补充“这个人平时更直接还是更委婉”之类的倾向
- 需要帮助判断更适合鼓励式、理性式、冷淡式还是轻松式回复

但需要注意：

- **聊天记录仍然是最高优先级证据**
- 星座、MBTI 这类信息只能辅助理解，不能直接当作最终人格结论
- 如果辅助信息和真实聊天样本冲突，应优先以真实表达习惯为准
- 不应因为星座或 MBTI 标签，生硬生成用户平时并不会说的话

更合适的使用方式是：

- 用聊天记录决定“这个人实际上怎么说话”
- 用星座 / MBTI / 自述信息辅助理解“为什么会偏向这样说”
- 最终仍以生成更像本人、而不是更像标签描述，为目标

## 更真实的交流感

这个项目的目标，不只是把回复写得“像回答”，而是尽量还原真实聊天里那种**不总是正面回答、也不总是把每句话都接满**的交流感觉。

这类真实感通常可能表现为：

- 不一定逐条回应对方每一个问题
- 有时只接情绪，不接事实细节
- 有时会顺手换话题，或者只回应其中一部分
- 会出现“晚点说”“再看”“都行”“别提了哈哈”这种非完整回答
- 某些场景下会故意留白，而不是解释得很满

如果聊天样本里本来就存在这些特征，生成出来的 skill 也应该允许：

- 适度不把话说满
- 适度模糊回应
- 适度延后回答
- 适度把重点放在语气和关系感，而不是信息完整度上

当然，这里的“更真实”不等于故意敷衍。更准确地说，是：**优先模拟真实说话习惯，而不是强行做一个每问必答、次次都很标准的客服式回复器。**

## 支持的数据源

| 来源 | 格式 | 说明 |
|------|------|------|
| 微信聊天记录 | txt / json | 优先按结构字段识别自己消息 |
| QQ 聊天记录 | txt / mht | 提取说话风格与样本 |
| 通用聊天记录 | txt / html / json | 用统一 parser 归一化 |
| 图片截图 | png / jpg | 可结合左右布局做自己消息启发式识别 |
| PDF / Markdown / TXT | 文本型文件 | 提取常见表达和语料样本 |
| 直接粘贴 | 纯文本 | 适合临时补料 |

## 自己消息识别策略

为了避免把别人的说话方式误学成“你”，项目使用多信号识别：

### 优先级高的信号
- `sender` / `from` / `nickname` / `is_self`
- 导出 JSON 中的角色字段
- HTML 中明确的自己消息 class

### 启发式信号
- 右侧气泡 / 右侧头像
- 连续右侧消息簇
- 聊天 UI 常见配色或布局

最终每条消息会尽量归类为：
- `self`
- `other`
- `unknown`

其中：
- `self` 是人格蒸馏主语料
- `other` 仅作上下文
- `unknown` 低置信度使用

## 项目结构

本项目尽量按照 **AgentSkills 开放标准** 的思路组织内容：把可复用的提示词、构建脚本、样例数据和最终生成产物分开存放，方便迁移、调试、二次接入和后续扩展。

当前仓库结构大致如下：

```text
newtype-create-skill/
├── README.md
├── SKILL.md
├── requirements.txt
├── docs/
│   └── PRD.md
├── examples/
│   └── minimal_chat.txt
├── prompts/
│   ├── intake.md
│   ├── style_analyzer.md
│   ├── style_builder.md
│   ├── persona_builder.md
│   ├── response_analyzer.md
│   ├── correction_handler.md
│   ├── merger.md
│   └── session_summary.md
├── tools/
│   ├── build_self_skill.py
│   ├── skill_writer.py
│   ├── version_manager.py
│   ├── generic_chat_parser.py
│   ├── wechat_parser.py
│   └── qq_parser.py
└── selves/
    └── {slug}/
        ├── style.md
        ├── persona.md
        ├── examples.md
        ├── corrections.md
        ├── meta.json
        ├── SKILL.md
        ├── sources/
        └── versions/
```

各目录职责可以简单理解为：

- `prompts/`：放人格分析、风格提取、纠错合并等提示词模板
- `tools/`：放解析、构建、合并、版本管理等执行层脚本
- `examples/`：放最小样例输入，便于验证端到端流程
- `docs/`：放产品说明、范围定义和设计文档
- `selves/{slug}/`：放某一次实际生成出来的人格 skill 结果

这种组织方式的好处是：

- 既方便把“生成逻辑”和“生成结果”分开管理
- 也方便后续把产物接到 Claude Code、AstrBot Skills 或其他 Agent/Skill 系统里
- 同时更适合做版本备份、纠错追加和样本回溯

## 输出结构

```text
selves/{slug}/
├── style.md
├── persona.md
├── examples.md
├── corrections.md
├── meta.json
├── SKILL.md
└── versions/
```

另外，主流程脚本还会额外保留原始与中间产物，便于检查：

```text
selves/{slug}/sources/chat/
├── 原始输入文件
├── analysis.md
└── parsed_messages.json
```

## 命令行构建示例

主流程脚本：

```bash
python3 tools/build_self_skill.py \
  --input <聊天记录文件> \
  --slug <skill-slug> \
  --name "显示名称" \
  --self-name "你在记录里的名字" \
  --self-variant "你想还原哪种自己" \
  --style-summary "一句话风格描述"
```

常用参数说明：

- `--input`：输入聊天材料，当前支持 txt / html / json
- `--slug`：生成后的 skill 目录名
- `--name`：最终 skill 标题
- `--self-name`：记录里代表“你自己”的 sender / 昵称
- `--self-variant`：要还原的版本，例如“日常聊天时的我”
- `--style-summary`：一句话风格总结，会进入 `meta.json` 与最终 `SKILL.md`
- `--format`：可选，默认 `auto`
- `--base-dir`：可选，默认输出到 `./selves`

如果是重复生成同一个 slug，脚本会先调用版本备份，再覆盖写入最新结果。

## 示例对话

示例输入文件见：`examples/minimal_chat.txt`

内容示例：

```text
2026-04-01 09:00 阿明
中午吃啥
2026-04-01 09:01 我
都行啊
2026-04-01 09:02 阿明
那火锅？
2026-04-01 09:03 我
也不是不行
2026-04-01 09:10 小周
晚上还来吗
2026-04-01 09:11 我
看情况，晚点说
```

基于这份样例，当前仓库已经生成了演示产物：`selves/demo-self/SKILL.md`

对应的人格效果会更接近这种短回复：

```text
对方：中午吃啥
你式回复：都行啊

对方：那今天去不去？
你式回复：也不是不行

对方：晚上还来吗
你式回复：看情况，晚点说
```

这类示例的目的不是“创造新人格”，而是验证：

- 能不能从记录里识别 `self` 消息
- 能不能提取短句、自然收尾、顺手接话的风格
- 能不能把这些证据合成为最终可调用的 `SKILL.md`

## 常见用法

生成完成后，你可以继续这样用：

- `/{slug}` → 直接像你一样聊天
- `/{slug} 帮我回这句话`
- `/{slug} 用我平时的语气改写`
- `/{slug} 这句太不像我了，改得更像我一点`

## 相关项目

| 项目 | 仓库地址 | 说明 |
|------|----------|------|
| ex-skill | https://github.com/therealXiaomanChu/ex-skill | 提供了本项目在上传流程与交互方式上的重要灵感参考 |
| colleague-skill | https://github.com/titanwings/colleague-skill | 提供了本项目在材料组织与交互体验上的参考启发 |

再次感谢 `ex-skill` 和 `colleague-skill` 带来的灵感启发。这个项目沿用了它们部分清晰、自然的上传与交互思路，但最终希望把重点放在“更贴近自己真实聊天方式的人格蒸馏”这件事上。

## 最后

<div style="display: inline-block; padding: 10px 14px; background: #f3f4f6; color: #6b7280; border-radius: 8px;">
  <strong><em>不论生活怎样不如意，请不要放弃自己，因为数字意识没法替你感受任何美好。</em></strong><br />
  <strong><em>No matter how disappointing life feels, please do not give up on yourself, because digital consciousness cannot feel any of the beauty in your place.</em></strong>
</div>
