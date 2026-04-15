# QROS Global Codex Skill Install Design

**Date:** 2026-03-26  
**Status:** Approved for implementation  
**Scope:** `Codex-only`, `global install`, `skill-first entry`, `no backward compatibility`

## Goal

把 QROS 从“源码仓驱动的安装/运行模型”收敛成更接近 `gstack` 的体验：

- QROS 继续作为独立工具仓存在
- 用户通过 `pipx` 或 `uv tool` 全局安装一次
- 用户在任意研究仓里以 Codex skill 名称作为第一入口
- skills 背后调用稳定的全局 `qros` 命令
- 研究产物始终写当前研究仓，而不是写回 QROS 工具安装目录

目标不是保留旧 `./setup` 方式再包一层，而是直接切换到新的全局模型。

## Product Principle

这次改造优先解决的是边界清晰，而不是再加功能。

新的边界应当是：

- 对用户：QROS 是一个全局安装的研究工作流工具
- 对 Codex：QROS 暴露为一组全局可发现的 `qros-*` skills
- 对执行层：所有 skills 统一调用 `qros ...`
- 对研究仓：只负责承载 `outputs/` 和研究上下文

换句话说，QROS 不再要求用户记住“先切回工具仓，再运行某个脚本”。

## Current Problem

当前系统虽然已经支持 `user-global`，但产品体验仍然像“源码仓里的脚本集合”：

- 安装入口依赖当前源码仓的 `./setup`
- 更新依赖回到源码仓 `git pull` 再 `./setup --refresh`
- skill 文本里仍然引用 `python scripts/run_research_session.py ...` 这类相对路径
- runtime 资产和用户日常入口之间没有一个稳定的全局命令层

这会造成双仓使用时的混乱：

- 一个仓库放 QROS 工具
- 另一个仓库放研究内容
- 但真实执行时用户很难分清“当前应该站在哪个目录里”

## Reference Pattern From gstack

参考 `gstack`，本次只借鉴这几个核心原则：

- 工具仓只负责安装、升级和提供全局运行资产
- 日常工作发生在业务仓
- 用户的第一入口是全局注册的 skill 名称
- skill 依赖稳定的全局运行时，而不是业务仓内的相对脚本
- 尽量暴露最小运行时边界，而不是要求用户理解整个工具仓

QROS 不需要逐字复刻 `gstack` 的实现细节，但要对齐这套体验模型。

## Approaches Considered

### Approach A: Package-Only Runtime

把 runtime、模板、文档、skill 模板全部作为 Python 包资源内置。安装后只依赖：

- 全局 `qros` 可执行文件
- `~/.codex/skills/qros-*`
- 少量 `~/.qros/state` / `~/.qros/logs` 本机状态目录

优点：

- 升级链路最简单
- 不存在包版本与外部 runtime 版本漂移
- 最接近“真正的全局命令行工具”

缺点：

- 包资源组织需要更严格
- 生成和安装 Codex skills 时需要显式写出 skill 文件

### Approach B: Thin CLI + Managed `~/.qros` Runtime

CLI 很薄，首次运行或安装时把完整 runtime 资产写到 `~/.qros`，后续执行都依赖这份外部运行时。

优点：

- 更接近当前实现
- 用户能直接看到安装后的 runtime 文件

缺点：

- 版本管理更复杂
- 容易出现 CLI 版本和 runtime 资产版本不一致
- 实际上还是会保留“refresh / migrate”问题

### Approach C: Keep Setup As Primary Entry

继续以 `./setup` 为安装中心，只把 skill 中的相对路径改掉。

优点：

- 改动最小

缺点：

- 没有真正解决“工具仓驱动”的心智问题
- 不符合这次要对齐 `gstack` 的目标

## Recommendation

采用 **Approach A: Package-Only Runtime**，同时在用户体验上保持 `gstack` 的 skill-first 模式。

理由：

- 用户明确要求保留 Codex skill 名称作为第一入口
- 用户希望 QROS 继续作为独立工具仓，而不是并入研究仓
- `pipx` / `uv tool install` 本身更适合“包内资源 + 全局命令”的分发模型
- 这条路能彻底消除“回源码仓跑脚本”的依赖

## Target User Experience

第一次安装：

```bash
pipx install qros
qros codex install
```

或：

```bash
uv tool install qros
qros codex install
```

之后用户在任意研究仓里打开 Codex，直接输入：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
```

系统应表现为：

- Codex 能在 `~/.codex/skills/` 找到 `qros-research-session`
- skill 调用全局 `qros session --cwd <current-project> ...`
- QROS 从包内资源装载 workflow runtime
- QROS 把产物写到当前研究仓的 `outputs/<lineage>/...`

用户不需要：

- clone QROS 仓库再使用
- 记住 `python scripts/...`
- 手工切换回工具仓更新 runtime

## Install Surface

新的安装和维护接口只保留这套：

- `qros codex install`
- `qros codex refresh`
- `qros codex check`
- `qros doctor`
- `qros session`
- `qros review`

其中：

- `qros codex install` 负责把 `qros-*` skills 写入 `~/.codex/skills/`
- `qros codex refresh` 用当前已安装包内容重写 skills
- `qros codex check` 校验 skills 和本机状态目录是否完整
- `qros doctor` 输出版本、安装状态、skill 注册状态和关键路径
- `qros session` / `qros review` 是稳定执行层

对外不再推荐 `./setup`。

## Skill Model

保留现有 `qros-*` skill 名称，不改用户入口习惯。

但 skill 内容必须从：

```text
python scripts/run_research_session.py --outputs-root outputs ...
```

改成：

```text
qros session --cwd "$PWD" --raw-idea "..."
```

或等价的稳定命令形式。

这意味着 skill 只承载：

- 用户交互约束
- 阶段治理规则
- 对全局 `qros` 命令的调用方式

skill 不再承载源码仓相对路径知识。

## Runtime Layout

安装后的稳定布局建议如下：

```text
~/.codex/skills/
  qros-research-session/
    SKILL.md
    agents/openai.yaml
  qros-mandate-review/
  qros-data-ready-review/
  ...

~/.qros/
  manifest.json
  state/
  logs/
```

说明：

- `~/.codex/skills/` 放的是用户可发现的 skills
- `~/.qros/` 只放本机状态、日志和安装元数据
- 模板、文档、runtime 代码应从已安装 Python 包内读取，而不是复制整套源码到 `~/.qros/`

## Execution Model

所有运行命令都需要显式接受“当前研究根”。

建议统一设计为：

- `qros session --cwd <path> --raw-idea <text>`
- `qros session --cwd <path> --lineage-id <id>`
- `qros session --cwd <path> --lineage-id <id> --confirm-mandate`
- `qros review --cwd <stage-dir>`

关键规则：

- `--cwd` 指向研究仓根目录或 stage 所在目录
- `outputs-root` 默认解析为 `<cwd>/outputs`
- 任何生成产物都不得写到 `~/.qros/`
- `~/.qros/` 只允许保存本机状态与诊断信息

## Packaging Model

仓库需要从“脚本仓”提升为“可安装 Python 工具包”：

- 发布名改为 `qros`
- 提供 `project.scripts.qros`
- 把必要的 skill 模板、docs、schema、templates 纳入 package data
- CLI 从包资源渲染 Codex skills 并写入 `~/.codex/skills/`

现有 `tools/` 中的 runtime 逻辑可以继续复用，但对外入口应统一从新 CLI 暴露。

## Testing Strategy

测试分三层：

### 1. Packaging / CLI

- `qros --help`
- `qros codex install`
- `qros codex check`
- `qros doctor`

### 2. Skill Rendering

- 生成后的 `SKILL.md` 不应再包含 `python scripts/`
- 生成后的 `SKILL.md` 必须只调用 `qros ...`
- 所有 `qros-*` skills 都应安装到正确目录

### 3. Runtime Routing

- 在临时研究目录运行 `qros session --cwd <tmp>`
- 验证 `outputs/` 生成在该目录下
- 验证不会向工具安装目录误写研究产物

## Non-Goals

这次不做：

- 兼容旧 `./setup` 安装
- 兼容已有 `repo-local` / `user-global` manifest
- 多宿主支持，如 Claude / Gemini / Cursor
- 自动远程升级或在线下载 runtime
- 更改 QROS 工作流阶段定义

## Migration Decision

由于当前没有真实用户，本次直接切换，不保留兼容层。

这意味着：

- 旧文档可直接改写
- 旧安装脚本可以下线或仅保留极薄提示
- 所有面向用户的入口都以 `qros` 包 + `qros codex install` 为准

## Success Criteria

实现完成后，应满足以下条件：

- 用户无需 clone QROS 仓库即可使用
- 用户只需安装一次全局工具
- 用户在任意研究仓里能直接使用 `qros-*` skill
- skill 背后不再依赖仓库相对路径
- 研究产物始终落在当前研究仓
- QROS 升级路径收敛为包升级 + `qros codex refresh`
