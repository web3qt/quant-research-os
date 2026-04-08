# QROS Verification Tiers

## Purpose

QROS 现在把流程级验证显式分成 `smoke` 和 `full-smoke` 两层，避免每次都只说“跑测试”但不知道到底验证了多深。

这两个 tier 都不是单元测试的替代品。它们是**需求完成前的流程级回归门**。

## Tiers

### `smoke`

`smoke` 是快速关键路径检查，覆盖：

- `qros-research-session` 核心 stage machine
- `run_research_session.py` CLI surface
- `qros-stage-display` runtime / skill contract
- stage substep normalization
- bootstrap / install docs / skill tree 这些基础仓约束

运行命令：

```bash
python scripts/run_verification_tier.py --tier smoke
```

或安装后：

```bash
~/.qros/bin/qros-verify --tier smoke
```

### `full-smoke`

`full-smoke` 是更重的路线级/回放级演练，包含 `smoke` 全部内容，并额外覆盖：

- CSF route routing
- `csf_data_ready_author` auto-program seam
- reflection chain
- anti-drift snapshot export 与 replay

运行命令：

```bash
python scripts/run_verification_tier.py --tier full-smoke
```

或安装后：

```bash
~/.qros/bin/qros-verify --tier full-smoke
```

## 什么时候跑哪一层

- **每个新需求**：至少跑相关 focused tests + `smoke`
- **凡是改到下列内容之一**，`full-smoke` 也必须跑：
  - `qros-research-session` stage flow / gate semantics
  - review / display / next-stage orchestration
  - route split / CSF routing
  - anti-drift snapshots 或 canonical session stage naming
  - stage-display supported stage contract
  - lineage-local stage-program auto-author seams

## Dry Run / Listing

列出 tier：

```bash
python scripts/run_verification_tier.py --tier smoke --list
```

只看命令不执行：

```bash
python scripts/run_verification_tier.py --tier full-smoke --dry-run
```

## Current Boundary

这里的 `full-smoke` 仍然是**repo 内自动化 full smoke**，不是“真人在真实操作员会话里把每个支持 stage 全部 live 跑一遍”。

后者如果要做，应被视为更高一层的 operator rehearsal。
