# QROS Installation And Onboarding Design

**Date:** 2026-03-25  
**Status:** Draft approved for direction  
**Scope:** `Codex-only`, `installer-core first`, `repo-local + user-global`

## Goal

把当前仓库从“内部可运行的 skill/runtime 原型”提升为“别人安装后就能按流程使用”的系统。

第一版只解决一件事：

- 提供顶层 `setup`
- 支持 `repo-local` 与 `user-global` 两种安装模式
- 给出清晰的 `README / install / quickstart`
- 让用户能从安装直接走到第一条 `idea -> mandate -> review` 最小闭环

## Core Principle

参考 `gstack`，这里要做的不是单独补一个脚本，而是补齐一套完整入口：

- 仓库分发
- setup 安装
- 生成/复制技能
- runtime 归位
- quickstart 指引

所以目标不是：

`docs + scripts + skills`

而是：

`repo -> setup -> installed assets -> guided workflow`

## Current Gap

当前仓库已经有：

- `qros-*` skills
- `idea_intake -> mandate` runtime
- `stage review` runtime
- 相关 SOP、schema、examples

但还缺：

- 顶层 `README.md`
- 顶层 `setup`
- 明确安装模式
- 安装后目录约定
- first-run quickstart
- freshness / refresh / check 机制

这会导致当前系统只适合作者本人维护，不适合团队直接安装使用。

## Approaches Considered

### Approach A: Minimal Setup Wrapper

只新增顶层 `setup` 和 `README`，直接围绕当前目录结构复制文件。

优点：

- 最快落地
- 改动面小

缺点：

- 安装边界容易漂移
- 后续升级和 refresh 会变脆
- 不利于扩宿主

### Approach B: Installer-Core First

新增一个共享安装核心，`setup` 只做参数解析和调用。`repo-local` 与 `user-global` 共用同一套 manifest、拷贝逻辑和完整性校验。

优点：

- 结构清晰
- 安装模式一致
- 后续加 `check / refresh / upgrade` 更顺
- 最接近长期产品化方向

缺点：

- 第一版比最小脚本多一层抽象

### Approach C: CLI-First

直接做 `qros setup / qros init / qros review run`，顶层 `setup` 只是薄包装。

优点：

- 用户心智统一
- 后续扩展顺滑

缺点：

- 范围过大
- 会把“安装层”和“统一 CLI 层”一起做，第一版风险高

## Recommendation

第一版采用 **Approach B: Installer-Core First**。

原因：

- 用户明确要求对齐 `gstack` 的安装与使用范式
- 双安装模式需要共享逻辑，不适合散落在 shell 里
- 当前仓库已经有多个 runtime 入口，值得先统一安装层，再考虑统一 CLI

## Supported Install Modes

第一版只支持：

- `--host codex`
- `--mode repo-local`
- `--mode user-global`
- `--mode auto`

不做：

- Claude / Gemini / Cursor 多宿主实现
- 网络下载或全局环境注入
- 自动修改用户 IDE / agent 配置

目录和接口应预留多宿主扩展位，但实际功能只实现 Codex。

## Asset Model

### Source Assets

保留在源码仓库，供开发、再生成和维护使用：

- `.agents/skills/`
- `scripts/`
- `tools/`
- `templates/`
- `docs/gates/`
- `docs/check-sop/`
- `docs/intake-sop/`
- `docs/experience/`

### Installed Assets

由 `setup` 挑选并复制到目标位置，不复制整个仓库。

第一版安装包边界：

- `qros-*` skills
- runtime scripts
- runtime tools
- 必要 templates
- 必要 SOP/schema/examples 文档
- install manifest

不复制：

- `tests/`
- `docs/plans/`
- `.git/`
- 缓存、构建或开发临时文件

## Install Layout

### Repo-Local

安装到当前项目内：

```text
<project-root>/
  .agents/skills/
    qros-idea-intake-author/
    qros-mandate-author/
    qros-mandate-review/
    qros-data-ready-review/
    qros-signal-ready-review/
  .qros/
    bin/
    scripts/
    tools/
    templates/
    docs/
    install-manifest.json
```

### User-Global

安装到用户目录：

```text
~/.codex/skills/
  qros-idea-intake-author/
  qros-mandate-author/
  qros-mandate-review/
  qros-data-ready-review/
  qros-signal-ready-review/

~/.qros/
  bin/
  scripts/
  tools/
  templates/
  docs/
  install-manifest.json
```

## Why Separate `.qros/`

把 runtime 与 skills 分开是刻意设计：

- skill 必须放在 Codex 可发现位置
- runtime/docs/templates 不应散落在项目根目录
- repo-local 和 user-global 需要对称结构
- refresh / check 需要明确的安装根
- 后续扩多宿主时只需要替换 skill 安装位置

## Setup Interface

第一版顶层命令：

```bash
./setup --host codex --mode repo-local
./setup --host codex --mode user-global
./setup --host codex --mode auto
./setup --host codex --refresh
./setup --host codex --check
```

### `--mode repo-local`

- 安装到当前仓库
- 复制 skills 到 `.agents/skills/`
- 复制 runtime/docs/templates 到 `.qros/`
- 写 `.qros/install-manifest.json`

### `--mode user-global`

- 安装到用户目录
- 复制 skills 到 `~/.codex/skills/`
- 复制 runtime/docs/templates 到 `~/.qros/`
- 写 `~/.qros/install-manifest.json`

### `--mode auto`

推荐默认逻辑：

- 若当前目录像项目仓库并已存在 `.agents/`，优先走 `repo-local`
- 否则走 `user-global`

### `--refresh`

- 基于 manifest 做覆盖更新
- 重新复制技能和 runtime 资产
- 不触碰用户自己的 research outputs

### `--check`

只校验，不写文件。至少检查：

- 技能目录是否存在
- runtime 目录是否完整
- manifest 是否存在且字段完整
- 关键脚本是否可读可执行

## Installer Core

建议新增：

- `tools/install_runtime.py`

职责：

- 参数规范化
- 解析目标根目录
- 计算安装资产清单
- 执行复制
- 写 manifest
- 执行完整性校验

顶层 `setup` 只负责：

- 参数解析
- 调用安装核心
- 打印用户可读结果

## Install Manifest

建议 manifest 至少记录：

- `project_name`
- `host`
- `install_mode`
- `installed_at`
- `source_repo_path`
- `source_git_commit`
- `skills_root`
- `runtime_root`
- `installed_skills`
- `installed_runtime_files`
- `version_marker`

用途：

- `setup --refresh`
- `setup --check`
- 后续 `qros upgrade`
- 问题排查

## Freshness And Drift

第一版不做复杂的模板再生成系统，只做文件级 freshness：

- 安装时总是以源码仓库为准刷新 skills
- `--check` 报告 manifest 与目标目录是否一致
- 对于 repo-local 模式，允许重复执行 `./setup --refresh`

目标是先解决“可重复安装”，不是先解决“二进制级升级器”。

## README Structure

建议新增顶层 `README.md`，结构直接面向首次安装者：

1. 一句话定位
2. Quick start
3. Install
4. First workflow
5. Install modes
6. Runtime layout
7. Troubleshooting

### Quick Start

README 首屏应该只展示最短路径：

1. clone 仓库
2. `./setup --host codex --mode user-global` 或 `repo-local`
3. scaffold 一条 lineage
4. author `idea_intake`
5. build `mandate`
6. run `mandate review`

### First Workflow

第一条演示链固定为当前已可运行的最小闭环：

```bash
python scripts/scaffold_idea_intake.py --lineage-root outputs/<lineage_id>
python scripts/build_mandate_from_intake.py --lineage-root outputs/<lineage_id>
python scripts/run_stage_review.py
```

并明确告诉用户先使用：

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`

## Additional Experience Docs

建议新增：

- `docs/experience/installation.md`
- `docs/experience/quickstart-codex.md`

前者负责安装模式、refresh、check、故障排查。  
后者负责 5 分钟跑通第一条 lineage。

## Error Handling

第一版直接失败并给出明确错误：

- 目标目录不可写
- 源资产缺失
- host 不支持
- mode 冲突
- manifest 缺失但用户要求 refresh/check

原则是：

- 不静默跳过关键资产
- 不自动改用户其他配置
- 不删除未知用户文件

## Testing Strategy

第一版至少需要覆盖：

- repo-local 安装
- user-global 安装
- auto 模式分流
- refresh 覆盖更新
- check 成功与失败
- manifest 内容正确
- README / docs 引用的命令与实际文件一致

## Non-Goals

第一版不做：

- 多宿主 setup
- 联网安装
- 自动 PATH 配置
- 统一 `qros` CLI
- 自动生成 research outputs

这些属于下一阶段工作，不应和安装层一起耦合。

## Result

完成后，项目的对外使用方式会从：

`读文档 -> 猜脚本 -> 猜技能`

变成：

`clone -> ./setup -> quickstart -> 按 stage 使用 qros skills`

这才是与 `gstack` 对齐的最小可用产品入口。
