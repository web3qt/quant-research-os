# 2026-04-21 Codex Spawn-Agent Review Design

## 背景

当前 QROS 的 review 主路径已经具备较完整的 on-disk proof chain：

- `review/request/adversarial_review_request.yaml`
- `review/request/spawned_reviewer_handoff_manifest.yaml`
- `review/request/spawned_reviewer_receipt.yaml`
- `review/result/*`
- `review/closure/*`

同时，runtime 已经支持 `spawned_agent` 与 `review_session` 两种 reviewer execution mode。

但当前用户入口仍要求人手动再开一个 Codex review session，再在那个独立会话里运行 stage-specific review skill 或 `qros-start-review`。这会带来两个问题：

1. 用户交互过重。每个 review stage 都要求再开一个 Codex，会话切换成本高。
2. 真实 reviewer execution mode 与目标能力脱节。proof chain 已经预留 `spawned_agent`，但实际主路径仍主要依赖人工开的独立 review session。

本设计的目标，是把 review 从“用户手动再开一个 Codex”重构成“用户在当前会话里显式进入 stage-specific review skill，由该 skill 内部使用 Codex `spawn_agent` 拉起 reviewer 子 agent 并完成 closure”。

## 目标

### 用户目标

- 保留 `qros-mandate-review`、`qros-data-ready-review` 这类 stage-specific review skill 作为 review 唯一入口。
- 不新增一个泛化总 review skill 来替代现有 stage-specific review skill。
- 用户不再需要手动再开一个 Codex review session。
- stage-specific review skill 进入后，应自动推进到 `review/result/*`，并继续完成 deterministic closure。

### 系统目标

- 继续保留 request / receipt / result / audit / closure 的 deterministic proof chain。
- 继续明确区分 launcher、reviewer、deterministic closer 三个角色。
- reviewer child 只能读取 `review/request/*` 与 `author/formal/*`，只能写 `review/result/*`。
- `./.qros/bin/qros-review` 仍然是唯一 deterministic closer。
- author outputs 一旦变化，旧 cycle 仍必须 stale / archive，不能复用旧 proof。

## 非目标

- 不改变 stage gate、formal checklist、rollback、downstream permission 的语义。
- 不把 reviewer judgment 全量 deterministic 化。
- 不引入数据库、服务端队列或后台 worker。
- 不把所有 review flow 塌缩成一个统一 skill。
- 不在 author 主路径里恢复自动 review 编排。

## 决策摘要

采用方案 B：

- 用户入口继续是各 stage-specific review skill。
- 通用的 spawn / wait / closure orchestration 下沉到 runtime helper。
- stage-specific review skill 只保留 stage-specific 规则与 launcher 调用顺序。
- reviewer 子 agent 不直接继承当前对话历史，只消费 runtime 生成的显式 handoff。
- reviewer 子 agent 完成后，由当前 stage-specific review skill 继续调用 `./.qros/bin/qros-review` 完成 closure。

拒绝的方案：

- 方案 A：把完整 orchestration 内联到每个 review skill。缺点是 13 份重复逻辑，后续维护和修复容易漂移。
- 方案 C：为每个 stage 再额外引入一套 reviewer child skill。缺点是概念与文件数膨胀，当前目标不需要这么重的拆分。

## 目标状态

### 用户交互

用户在当前 Codex 会话里显式进入某个 stage-specific review skill，例如：

- `qros-mandate-review`
- `qros-data-ready-review`
- `qros-signal-ready-review`

该 skill 在内部完成：

1. review-ready / handoff 前置检查
2. 注册 active review cycle
3. 生成 request / handoff manifest / receipt
4. 使用 Codex `spawn_agent` 拉起 reviewer 子 agent
5. 等待 reviewer 子 agent 完成并写出 `review/result/reviewer_findings.raw.yaml`
6. 调用 `./.qros/bin/qros-review` 完成 canonical result、write-scope audit 与 closure

用户不再手动再开一个 Codex review session，也不再需要自己手动补跑 closure。

### 角色边界

#### Launcher

由当前 stage-specific review skill 所在主会话承担。它负责：

- 执行 review-ready / handoff 自查
- 刷新 request / handoff manifest
- issue receipt
- spawn reviewer child
- wait reviewer child
- 调 deterministic closer

Launcher 不负责 reviewer judgment，不直接写 reviewer findings。

#### Reviewer Child

由 Codex `spawn_agent` 拉起，承担 adversarial reviewer 角色。它负责：

- 读取 `review/request/*`
- 读取 `author/formal/*`
- 依据当前 stage 的 formal gate、checklist、audit-only 规则作出 stage-specific judgment
- 只写 `review/result/reviewer_findings.raw.yaml`

Reviewer child 不允许：

- 修改 `author/formal/*`
- 越权写 `review/result/*` 之外的文件
- 直接写 closure artifacts
- 继承主线程的完整对话历史当作 proof source

#### Deterministic Closer

继续由 `./.qros/bin/qros-review` 承担。它负责：

- 基于 active request / receipt / runtime identity 规范化 reviewer raw findings
- 写 `adversarial_review_result.yaml`
- 写 `review_findings.yaml`
- 跑 reviewer write-scope audit
- 写 `review/closure/*`

## 详细设计

### 1. 共享 orchestration helper

新增一个共享 runtime helper，职责是“发起 spawned-agent review cycle 并等待 reviewer child 完成”，不做 stage-specific judgment。

建议放在：

- `runtime/tools/review_session_runtime.py` 扩展
  或
- 新建同级 helper，例如 `runtime/tools/review_spawn_runtime.py`

这个 helper 至少需要暴露两层能力：

1. `start_spawned_review_cycle(...)`
   负责：
   - 复用当前 `start_review_session()` 中的 context 推断、request 刷新、digest 绑定、stale archive 逻辑
   - 生成 `spawn_mode = "spawned_agent"` 的 `spawned_reviewer_receipt.yaml`
   - 返回 handoff payload、review cycle id、review runtime state

2. `build_spawned_reviewer_prompt(...)`
   负责：
   - 从当前 stage 的 request、handoff manifest、stage skill 约束中拼出 reviewer child 的明确 contract
   - 明确读写边界、禁止行为、输出文件、formal gate 关注点

这层 helper 只做启动与约束下发，不承载 stage-specific verdict 规则。

### 2. stage-specific review skill 的新职责

各个 `qros-*-review` skill 继续保留自己的 stage-specific 内容：

- stage purpose
- required inputs / outputs
- formal gate
- checklist
- audit-only
- rollback 规则
- downstream permission

但它们的“独立 review session 要求”和“执行顺序”要统一切换为新的 launcher 语义：

1. 在当前会话中执行 review-ready / handoff 自查
2. 调用共享 runtime helper 注册 spawned review cycle
3. 用 `spawn_agent` 拉起 reviewer child
4. 等待 reviewer child 落 `reviewer_findings.raw.yaml`
5. 调 `./.qros/bin/qros-review`
6. 根据 closure 结果报告 PASS / FIX_REQUIRED / non-advancing verdict

也就是说，stage-specific review skill 仍是唯一入口，但通用 orchestration 不再散落在 skill 文本里重复维护。

### 3. reviewer child contract

不为每个 stage 新建一套 reviewer child skill 目录。

改为由 runtime 基于当前 stage request 与 handoff manifest 生成统一 reviewer child contract。该 contract 必须明确：

- 你是 adversarial reviewer，不是原 author
- 只能读 `review/request/*` 与 `author/formal/*`
- 只能写 `review/result/reviewer_findings.raw.yaml`
- 不允许修改 `author/formal/*`
- 不允许手写 `adversarial_review_result.yaml`
- 不允许手写 closure artifacts
- 必须基于当前 stage 的 formal gate / checklist / rollback / downstream 规则给出 judgment

stage-specific 差异通过 handoff prompt 中的 stage section 体现，而不是复制一套 child skill 文件树。

### 4. proof chain 变化

proof chain 的主结构保持不变，但 active path 从 `review_session` 切到 `spawned_agent`：

- `spawned_reviewer_receipt.yaml.spawn_mode = "spawned_agent"`
- `spawned_reviewer_receipt.yaml.spawned_agent_id = <Codex child agent id>`
- `adversarial_review_result.yaml.reviewer_execution_mode = "spawned_agent"`

`fork_context` 继续强制为 `false`。

request / receipt / result 仍需保持：

- 相同 `review_cycle_id`
- 相同 `handoff_manifest_digest`
- reviewer identity / reviewer session binding 一致
- write root 仍是 `review/result`

### 5. deterministic closure 仍保留

stage-specific review skill 在 reviewer child 完成后，必须继续调用 `./.qros/bin/qros-review`。

因此新的 review lane 终点不是 `review/result/*`，而是 `review/closure/*` 写完。

这满足两个要求：

- reviewer judgment 由 reviewer child 负责
- 最终可推进的 closure 仍由 deterministic runtime 负责

## 失败恢复与异常路径

### reviewer child 未完成

如果 reviewer child 尚未产出 `review/result/reviewer_findings.raw.yaml`：

- stage 保持 `awaiting_spawned_reviewer_completion` 或等价 pending 状态
- 不得执行 closure
- 不得伪造 `adversarial_review_result.yaml`

### reviewer child 产物不合法

如果 raw findings 缺字段、proof chain 不一致、receipt 绑定错误、handoff digest 漂移：

- `./.qros/bin/qros-review` 必须直接失败
- 当前 cycle 必须视为无效
- runtime 给出 fresh cycle 指令

### author outputs 在 review 期间变化

如果 `author/formal/*` 在 reviewer child 执行期间发生变化：

- 当前 request 绑定 digest 失效
- 当前 cycle 必须 stale
- runtime archive 当前 request / result / closure / state
- 必须重新从 stage-specific review skill 发起新的 review cycle

### verdict = FIX_REQUIRED

如果 reviewer 结论是 `FIX_REQUIRED`：

- 允许写 `review/result/*`
- 不得写 closure artifacts
- 主 author lane 之后必须显式读取 findings，修复 author outputs，再重新发起 review

## 代码改动面

### Runtime

- `runtime/tools/review_session_runtime.py`
- 可能新增 `runtime/tools/review_spawn_runtime.py`
- `runtime/tools/review_skillgen/adversarial_review_contract.py`
- `runtime/tools/review_skillgen/review_runtime_state.py`
- `runtime/tools/review_skillgen/review_result_writer.py`
- `runtime/tools/review_skillgen/review_engine.py`

### Skill / Template

- `templates/skills/review-stage/SKILL.md.tmpl`
- 所有 `skills/*/qros-*-review/SKILL.md`
- `skills/core/qros-research-session/SKILL.md`

### Docs

- `docs/guides/qros-review-shared-protocol.md`
- `docs/guides/qros-research-session-usage.md`
- `docs/guides/codex-stage-review-skill-usage.md`

### Tests

- `tests/review/test_start_review_session.py`
- `tests/review/test_adversarial_review_runtime.py`
- `tests/review/test_review_result_writer.py`
- `tests/review/test_run_stage_review_script.py`
- `tests/session/test_research_session_runtime.py`
- `tests/session/test_research_session_assets.py`
- `tests/review/test_adversarial_review_skill_generation.py`

## 测试策略

最低需要覆盖三层测试。

### 1. Runtime 单测

锁定：

- spawned review cycle 能正确写 request / handoff manifest / receipt / state
- receipt 的 `spawn_mode` 为 `spawned_agent`
- `spawned_agent_id`、`launcher_thread_id`、digest 绑定正确
- 同一 stage 并发第二个 active reviewer child 被拒绝

### 2. Review 集成测试

锁定：

- reviewer child 只写 `reviewer_findings.raw.yaml` 时，`qros-review` 能正确生成 canonical result
- `reviewer_execution_mode = "spawned_agent"`
- write-scope audit 与 closure 正常写出
- `FIX_REQUIRED` 时不会错误地产生 closure artifacts

### 3. Session / Skill 回归测试

锁定：

- 生成后的 stage-specific review skill 文案不再要求用户手动再开一个 review session
- `qros-research-session` 文档和资产提示与新流程一致
- author outputs 改动后旧 cycle 自动 stale / archive
- reviewer child 失败或缺席时 session 状态不会假装 closure 完成

## 验证要求

这项改造触及：

- review / display / next-stage orchestration
- `qros-research-session` stage flow 口径
- stage-specific review skill 合同

因此实现阶段的最低验证要求应为：

- focused tests
- smoke
- full-smoke

spec 阶段本身不要求跑 smoke，但实现阶段必须跑。

## 迁移策略

采用单批次切换，不长期保留两套主文档口径。

顺序如下：

1. 先落 runtime helper 与测试
2. 再更新 skill 模板与生成产物
3. 再同步更新共享协议与使用文档
4. 最后跑 focused tests + smoke + full-smoke

`qros-start-review` 可以暂时保留为兼容入口或内部 helper，但不能再作为主文档推荐路径。用户面文档应统一收敛到“在当前会话里进入 stage-specific review skill，由其内部 spawn reviewer child”。

## 风险与约束

- 最大风险是 stage-specific skill 文案、runtime 真值、测试夹具三者重新出现口径漂移。
- 第二个风险是主会话等待 reviewer child 时处理超时、失败和 stale cycle 的状态转移不够硬，导致磁盘上残留半成品 result。
- 第三个风险是 reviewer child contract 若不够硬，可能出现越权改 `author/formal/*` 或直接写 closure artifacts。

因此实现时必须优先保证：

- runtime 真值先落地
- 所有 proof 字段继续由 on-disk artifacts 证明
- skill 文案只描述 runtime 已真正实现的行为

## 实现后预期结果

实现完成后，用户在当前 Codex 会话里进入任一 `qros-*-review` skill，就能完成：

- 发起 review cycle
- 拉起 adversarial reviewer 子 agent
- 产出 `review/result/*`
- 完成 `review/closure/*`

同时继续保留：

- stage-specific review 入口
- deterministic closure
- stale / archive discipline
- reviewer write-scope audit
- 可审计的 request / receipt / result / closure proof chain
