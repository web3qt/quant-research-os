# QROS Retire Clear/Resume Protocol Design

## Context

当前 QROS 的 post-review handoff 把两件事绑在了一起：

1. 阶段交接
2. 清空对话上下文

这套 `clear/resume` 语义一开始是为了降低长上下文带来的漂移，但在 Codex 的真实使用里，它把用户带到了一个不稳定的体验：用户按提示切到下一个 skill 之后，系统又要求重新理解 `clear` 边界，甚至把 shell 级恢复动作暴露给普通推进路径。

这对 QROS 的主流程不合适。用户真正需要的是“直接进入下一个 skill，并继续按磁盘真值校验状态”，而不是“先清空对话，再恢复”。

## Decision

退役 `clear/resume` 作为 workflow 协议。

从此以后，QROS 的正常推进只做一件事：在满足阶段门禁后，直接推荐下一个 QROS skill。用户可以在当前会话继续，也可以切到新会话，但系统不再要求、也不再提示清空上下文。

这意味着：

- 不再把 `/clear` 作为普通用户路径的一部分
- 不再把 `qros-resume` 作为普通流程中的推荐动作
- 不再输出 `clear_required` / `clear_instruction` 这类 workflow 语义
- 不再把 `backend_resume_command` 暴露给常规 handoff

保留的只有一条规则：下一个 skill 仍然必须按磁盘状态重新校验自己能不能接手。

## Goals

- 让 PASS-like boundary 变成直接的 skill handoff，而不是对话清空边界
- 让用户在 Codex 里只看到 skill 名称和阶段语义，不看到 shell 命令提示
- 让后续 skill 自己重新读取磁盘状态，而不是依赖上下文清理
- 保留失败处理、review gate、stage-entry guard 和 lineage lock 的硬校验

## Non-Goals

- 不改 review verdict 语义
- 不放松 stage gate
- 不允许跳过 `mandate_next_stage_confirmation_pending` 这类明确的 next-stage 确认边界
- 不把聊天历史变成事实来源
- 不要求用户手动执行任何 shell 命令来推进正常 workflow

## Options Considered

1. 删除 `clear/resume` 协议并改成直接 skill handoff
   - 优点：语义最干净，用户体验最一致
   - 缺点：要同步改 runtime、docs、tests

2. 仅隐藏用户可见 clear 文案，协议内部继续保留
   - 优点：改动小
   - 缺点：协议双轨，后续仍会制造歧义

3. 保留旧协议并加新的 handoff 层
   - 优点：兼容性最好
   - 缺点：复杂度最高，容易继续混淆用户

推荐方案：1。

## Proposed Architecture

### 1. Direct handoff model

把 post-review 之后的状态建模为“下一阶段 skill 推荐”，而不是“清空上下文后恢复”。

新的状态投影只需要表达：

- 当前 stage
- 当前 blocking reason
- 推荐进入的下一个 skill
- 推荐理由
- 下一步应做什么

不再需要 clear/resume 专用字段。

### 2. Workflow renderers

`qros-review`、`qros-session` 和 `qros-progress` 统一改成同一套 direct handoff 文案：

- PASS-like boundary 后，直接打印下一步 skill
- 不打印 `/clear`
- 不打印 `qros-resume`
- 不打印任何“先清空上下文”的引导

### 3. Skill entry behavior

stage-specific author skill 仍然要做两件事：

- 读取磁盘真值
- 校验当前 stage 是否真的允许进入

但它不再要求用户先清空上下文，也不再把“恢复会话”当成它的前置动作。

如果当前 stage 还停在 `*_next_stage_confirmation_pending`，skill 应该直接告诉用户“先完成上游 stage 的确认”，而不是要求 clear。

### 4. Legacy recovery separation

如果仓库里仍保留 `qros-resume` 或类似恢复入口，它只能是非普通 workflow 的兼容/调试工具，不能被正常 handoff 语义引用，也不能出现在用户推进路径里。

## Data Flow

1. review closure 或 session status 读取当前 lineage 的磁盘状态
2. 状态解析器判断当前 stage 和下一步可进入的 skill
3. renderer 输出 direct handoff 文案
4. 用户直接进入推荐 skill
5. 新 skill 重新读取磁盘状态并继续校验

这里不再有“清空上下文 -> 恢复”的中间层。

## Error Handling

- 如果当前仍在 `mandate_next_stage_confirmation_pending`，输出应明确提示“先完成 mandate next-stage confirmation”，而不是 clear/resume 提示
- 如果 required upstream artifacts 缺失，输出缺失项和上游 skill 入口
- 如果遇到 failure-class verdict，继续走 failure handling，不进入普通 handoff
- 如果 stage-entry guard 不匹配，直接拒绝进入当前 skill，并给出正确的上游 skill 或 stage recovery 路径

## Testing

需要锁住这些行为：

- `qros-review` PASS 输出不再包含 `/clear`
- `qros-session` 和 `qros-progress` 不再输出 `clear_required` / `clear_instruction`
- PASS-like boundary 只推荐下一个 skill，不推荐 `qros-resume`
- `qros-csf-data-ready-author` 在 `mandate_next_stage_confirmation_pending` 下提示上游 stage 交接，而不是 clear/resume
- 所有旧的 clear/resume 断言改为 direct handoff 断言
- bootstrap / install 测试仍可保留对调试恢复入口的存在性检查，但不能把它当普通用户路径

因为这会同时影响 session flow、review flow、skill entry 和 docs，验证至少需要 focused tests，并按仓库规则补 smoke / full-smoke。

## Documentation Updates

需要同步更新：

- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-review-shared-protocol.md`
- `skills/core/qros-research-session/SKILL.md`
- `skills/core/qros-progress/SKILL.md`
- `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- 其他仍提到 `clear/resume` 作为普通用户推进路径的说明文档

文档里只保留 skill 名称和阶段语义，不保留“先清空上下文再继续”的普通流程说法。

## Success Criteria

- 用户在 Codex 里不再被引导去清空上下文
- 用户只看到“进入下一个 skill”这类 direct handoff 提示
- 同一条 lineage 的后续 skill 能在不依赖 clear 的情况下继续按磁盘状态校验
- `clear/resume` 不再是普通 workflow 的一等公民
