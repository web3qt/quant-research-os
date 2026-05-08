# Release Notes

本文件记录 QROS 从第一个可用版本到当前版本的用户可见变化。QROS 是流程与治理仓；release notes 重点记录 workflow、runtime、skill、contract、文档和验证能力的变化。

---

<br>

## 0.4.10 - 2026-05-08

### 改进

- 明确 `qros-update` 是 Codex 和 Claude Code 的统一用户更新入口；普通用户只需要在 active research repo 根目录输入 `qros-update`。
- 更新 README、installation guide、quickstart、Codex / Claude Code 安装说明和 `qros-update` skill，强调 updater 会自动识别当前 host，并刷新全局 QROS 安装与当前 repo 的 `./.qros/` runtime。
- 保留 `--host codex` / `--host claude-code` 作为高级/manual override，不再把它们写成普通用户路径。

### 验证

- 本版本发布前已运行 qros-update focused tests、docs/bootstrap minimum 和 smoke。
- `pyproject.toml`、`uv.lock` 与 README version badge 同步到 `0.4.10`。

---

<br>

## 0.4.9 - 2026-05-07

### 修复

- `qros-update --host auto` 现在会在 `QROS_HOST` 之后优先读取当前 agent 环境标记，再读取 repo-local manifest，避免旧版更新曾把 Claude Code repo 的 manifest 误写成 Codex 后继续锁死在 Codex surface。
- 保留 repo-local manifest 作为环境不明确时的 fallback，因此普通无 env wrapper 仍能按已有安装记录刷新。
- 更新 `qros-update` skill 和 installation guide，明确旧 wrapper 迁移后的自愈行为边界。

### 验证

- 本版本发布前已运行 qros-update focused tests、docs/bootstrap minimum 和 smoke。
- `pyproject.toml`、`uv.lock` 与 README version badge 同步到 `0.4.9`。

---

<br>

## 0.4.8 - 2026-05-07

### 修复

- 修复旧版 repo-local `qros-update` wrapper 的迁移问题：旧 wrapper 会默认传 `--host codex`，最新 updater 现在会把这种未标记的历史默认值当作 `auto`，继续按 `QROS_HOST`、当前 repo 的 `./.qros/install-manifest.json.host` 和 agent 环境解析真实 host。
- 新版 `qros-update` wrapper 在用户显式传 `--host codex` 或 `--host claude-code` 时会附带 explicit marker，确保手动覆盖仍然优先。
- 更新 installation guide 和 `qros-update` skill，明确旧 wrapper 直接运行也能在拉到新版 source 后刷新 Claude Code surface。

### 验证

- 本版本发布前已运行 qros-update focused tests、docs/bootstrap minimum 和 smoke。
- `pyproject.toml`、`uv.lock` 与 README version badge 同步到 `0.4.8`。

---

<br>

## 0.4.7 - 2026-05-07

### 改进

- `qros-update` 默认改为 `--host auto`，会自动按显式 `--host`、`QROS_HOST`、当前 repo 的 `./.qros/install-manifest.json.host`、当前 agent 环境变量顺序解析 Codex / Claude Code host。
- `qros-update` shell wrapper 不再默认硬编码 Codex；Claude Code research repo 可以直接运行 `./.qros/bin/qros-update` 刷新 `~/.claude/*` 与 repo-local runtime。
- `run_qros_update.py` 输出 resolved host，方便确认本次更新到底刷新了 Codex 还是 Claude Code surface。
- 更新 `qros-update` skill、installation guide 和 Codex README，使用户文档与 auto-host runtime 行为一致。

### 验证

- 本版本发布前已运行 qros-update focused tests、docs/bootstrap minimum 和 smoke。
- `pyproject.toml`、`uv.lock` 与 README version badge 同步到 `0.4.7`。

---

<br>

## 0.4.6 - 2026-05-07

### 新增

- 新增 `qros-check-stage-entry` repo-local runtime guard，用于 stage-specific author / review skill 进入前校验当前 lineage 的 runtime `current_stage`。
- 新增 `runtime/tools/stage_entry_guard.py` 与 `runtime/scripts/check_stage_entry.py`，支持 JSON 输出和明确的 mismatch 诊断。

### 改进

- 所有 stage-specific author skills 现在必须先运行 `./.qros/bin/qros-check-stage-entry --stage <stage_id> --lane author`，防止 current stage 仍停在上游 handoff / confirmation 时直接写下游 artifact。
- 所有 stage-specific review skills 现在必须先运行 `./.qros/bin/qros-check-stage-entry --stage <stage_id> --lane review`，防止 stage 不匹配时启动 reviewer 或运行 `qros-review-cycle prepare`。
- review skill 生成模板已同步更新，后续重新生成 review skills 时会保留 runtime entry guard。
- 更新 `qros-research-session`、`using-qros`、installation guide 和 research session usage 文档，明确 `qros-research-session` 是普通阶段推进的唯一总控入口。

### 验证

- 本版本发布前已运行 focused tests、docs/bootstrap minimum、smoke 和 full-smoke。
- `pyproject.toml`、`uv.lock` 与 README version badge 同步到 `0.4.6`。

---

<br>

## 0.4.5 - 2026-05-06

### 新增

- 新增 host-neutral review protocol 设计，review runtime 不再绑定 codex，支持 codex 和 claude-code 双 host。
- 新增 host-aware reviewer invocation kinds、context isolation policies 和 handoff delivery methods 三层抽象，用于描述不同 host 的 review agent 启动方式。
- 新增 `_resolve_host_from_manifest` 自动从 `.qros/install-manifest.json` 推断 host，review cycle 无需显式传 `--host`。

### 改进

- 重命名所有 `spawned_reviewer_*` 符号为 `reviewer_*`（receipt、handoff manifest、env vars），消除 codex spawn 耦合。
- 环境变量统一：`CODEX_THREAD_ID` → `QROS_REVIEWER_SESSION_ID` / `QROS_LAUNCHER_SESSION_ID` / `QROS_LAUNCHER_THREAD_ID`，参数 `--spawned-agent-id` → `--reviewer-agent-id`。
- 删除 codex-specific 入口脚本：`qros-spawn-reviewer`、`qros-start-spawned-review`、`start_spawned_review_cycle.py`、`gen_codex_stage_review_skills.py`、`issue_spawned_reviewer_receipt.py`。
- reviewer handoff prompt 根据 host 生成不同的约束指令和 write-scope 提示。
- 同步更新全部 review skill SKILL.md（CSF/TSS/backtest/signal/data/holdout/train_freeze/mandate/test_evidence）使用 host-neutral contract 名称。
- 同步更新 README、installation guide、stage-freeze field guide、review constraint map、review shared protocol 等文档。
- 新增 `.planning/codebase/` 全量代码地图（ARCHITECTURE、CONCERNS、CONVENTIONS、INTEGRATIONS、STACK、STRUCTURE、TESTING）和 Phase 3 host-neutral review protocol spec。

### 验证

- 更新全部 review runtime tests 适配 host-neutral contract 和新命名。
- `pyproject.toml` 版本同步到 `0.4.5`。

---

<br>

## 0.4.4 - 2026-05-06

### 新增

- 新增 TSS test evidence review runtime parity 覆盖，锁定 route-specific review runtime 与 stage evaluator 的一致性。
- 新增 TSS failure routing skills：
  - `qros-tss-test-evidence-failure`
  - `qros-tss-train-freeze-failure`

### 改进

- 强化 `tss_test_evidence` proof gates、artifact contract runtime 与 semantic validation，减少 formal artifacts 缺字段或证据漂移时被误放行的风险。
- review runtime 现在会在 handoff 前预检配置，并对 route-specific run manifests、raw reviewer findings schema 和全局 evidence 输出更明确的错误。
- install runtime 增加 QROS install drift 报告，便于识别 active research repo 中的 `.qros/` 与当前发布版本不一致。
- 同步更新 TSS SOP、stage artifact map、review checklist、installation docs 和 using-qros 文档入口。

### 验证

- 为 TSS test evidence proof gates、review preflight、review result writer、failure skills、install runtime 和 route docs 增加回归测试。
- 本版本发布前已运行 focused tests、docs/bootstrap minimum、smoke 和 full-smoke。
- `pyproject.toml` 与 `uv.lock` 同步到 `0.4.4`。

---

<br>

## 0.4.3 - 2026-04-28

### 新增

- 新增 `time_series_signal` 路线的 TSS 全阶段主线，与 CSF 横截面因子路线并行：
  - `tss_data_ready`
  - `tss_signal_ready`
  - `tss_train_freeze`
  - `tss_test_evidence`
  - `tss_backtest_ready`
  - `tss_holdout_validation`
- 新增 TSS stage artifact contracts、semantic validators、runtime builders、author/review skills 和 route-specific tests。
- 新增 `$qros-signal-diagnostics`：只读 TSS 信号 diagnostics skill，用于查看时间序列信号质量、事件证据、回测结果和 holdout 稳定性。
- 新增 `./.qros/bin/qros-signal-diagnostics` runtime wrapper，支持从 active research repo 读取当前 lineage 并输出 TSS diagnostics。

### 改进

- 将 QROS 当前主流程明确拆成 `time_series_signal` 与 `cross_sectional_factor` 两条 route，避免继续把无前缀 `data_ready / signal_ready / ...` 当作新 TSS lineage 的 canonical 口径。
- 更新 `qros-research-session`、`using-qros`、README、Codex guide、quickstart、SOP 和可视化文档，使用户入口和 runtime 实现一致。
- 将 `docs/` 下的主要用户 / 维护者文档改成中文优先展示，同时保留命令、字段名、stage id、schema id 和 artifact 名。
- README 起步说明改为"新建研究文件夹并在其中打开 Codex"，强调研究产物会写入该研究文件夹。

### 验证

- 为 TSS route 增加 contract、runtime、session routing、review preflight、agent behavior、docs、skill tree 和 pipeline 测试。
- 为中文优先文档新增 `tests/docs/test_docs_chinese_first.py`，防止主要入口文档回退成英文主标题。
- 本版本发布前已运行 focused docs tests、完整 `tests/docs`、docs/bootstrap minimum、smoke 和 full-smoke。
- `pyproject.toml` 与 `uv.lock` 同步到 `0.4.3`。

---

<br>

## 0.4.2 - 2026-04-27

### 新增

- 新增 `$qros-factor-diagnostics`：只读 CSF 因子阶段 diagnostics skill，用于查看当前或指定 lineage 的横截面因子阶段质量。
- 新增 `./.qros/bin/qros-factor-diagnostics` runtime wrapper，默认读取 active research repo 的 `outputs/`，选择最近修改 lineage，并自动推断 CSF stage。
- 新增因子检测指标库与 CSF stage diagnostic profiles：
  - `contracts/diagnostics/factor_metric_library.yaml`
  - `contracts/diagnostics/csf_stage_diagnostic_profiles.yaml`
- 新增 runtime diagnostics engine：读取 formal artifacts，汇总 observed diagnostics、missing diagnostics、evidence gaps 和 next diagnostics。
- 新增中文解释型输出：observed metric 现在包含 `severity`、`interpretation` 和 `strategy_link`，例如 Rank IC 为负时会解释"因子排序与未来收益排序反向"，并提示检查 `factor_direction`。

### 改进

- README、Codex guide 和 research session usage 文档改为以 Codex 提问为主路径，例如：
  - `$qros-factor-diagnostics 看下当前 lineage 的因子诊断`
  - `$qros-factor-diagnostics mean IC 为负说明什么，跟当前策略方向有没有冲突`
  - `$qros-factor-diagnostics 不要只给数字，用中文解释这些指标说明什么`
- `$qros-factor-diagnostics` 的文本输出从英文指标列表升级为中文结构化解释：
  - 先说结论
  - 怎么理解这些数
  - 跟当前策略的关系
  - 缺什么证据
  - 下一步建议补充的 diagnostics
- 明确 diagnostics 不是 review、不是 gate、不写 review closure、不修改 `*_gate_decision.md`，也不替代 `$qros-review`。

### 验证

- 为 factor diagnostics 增加 contract、runtime、docs、skill tree 和 bootstrap 测试。
- 本版本发布前已运行 focused tests、docs/bootstrap minimum 和 smoke。
- `pyproject.toml` 与 `uv.lock` 同步到 `0.4.2`。

---

<br>

## 0.4.1 - 2026-04-27

### 改进

- 重写 README，使首页更像 Notion 风格的项目入口页。
- 强化普通用户入口：从 active research repo 打开 Codex，先 fetch `.codex/INSTALL.md`，然后使用 `$qros-research-session`、`$qros-progress` 和 `$qros-update`。
- 明确 QROS 是 workflow / governance framework，不是具体策略实现仓。

### 发布

- 将版本从 `0.4.0` 提升到 `0.4.1`。
- 同步更新 `pyproject.toml` 与 `uv.lock`。

---

<br>

## 0.4.0 - 2026-04-27

### 新增

- 纳入 `uv.lock`，让依赖解析和本地验证更可复现。
- 增加 agent behavior eval harness，用于评估 QROS agent 行为是否符合流程纪律。
- 扩展 idea intake、mandate 与 CSF artifact shape 校验。

### 改进

- 系统性强化 CSF route 各阶段合同：
  - `csf_data_ready`
  - `csf_signal_ready`
  - `csf_train_freeze`
  - `csf_test_evidence`
  - `csf_backtest_ready`
  - `csf_holdout_validation`
- 强化 freeze flow 和 CSF data gate，减少 placeholder 或合同说明被误认为 stage 完成的风险。
- 为 artifact 字段补充说明，使 runtime-facing shape 更容易审查。

### 修复

- 修复 anti-drift CI 依赖安装，明确安装 `pyarrow` 和项目测试依赖。

---

<br>

## 0.3.0 - 2026-04-23

### 新增

- 新增 `$qros-progress` 只读进度查询入口，用于查看当前 lineage、stage、gate 状态、blocking reason 和 next action。
- 新增 review flow spawned-agent 相关能力，让 adversarial review handoff 更可追溯。
- 新增三层测试基础设施，覆盖 CSF pipeline validation、contracts、runtime 和 anti-drift。

### 改进

- 优化 QROS runtime workflow，包括 verification tiers、stage evaluation 和测试组织。
- 强化 review pipeline：parquet 读取超时、streaming reads、session isolation。
- 将 review cycle 拆分为 content、binding 和 protocol lanes。
- 对 post-mandate stage program boundary 做硬化，避免 framework 侧隐式生成或替代 lineage-local 程序。
- 对 CSF train/test formal artifacts 做对齐。

### 修复

- 修复 gate failure package disposition state。
- 让 stale review handoff 在 reviewer launch 前失败。
- 阻止 reviewer write-scope drift 后继续写 closure。

---

<br>

## 0.2.0 - 2026-04-16

### 新增

- 新增 `$qros-update` 路径，让用户可以从 Codex 中刷新到最新发布版，并同步当前 repo 的 `./.qros/` runtime。
- 引入 repo-local `.qros` wrapper / manifest 模式，将真实 runtime 状态保留在 active research repo，而不是散落到 home-level state。

### 改进

- README 重构为更清晰的入口页，降低新用户第一次使用 QROS 的导航成本。
- 强化 contract-driven review verdict vocabulary，减少 review 状态词漂移。
- 移除 abandoned post-holdout governance branch 和 future-stage vocabulary，保持 active product surface 与真实 runtime 一致。
- 强化 CSF review gates，防止低质量证据静默推进。
- 明确 contracts、skills、runtime、docs、tests 的职责边界。

### 修复

- 修复 Codex-first delivery 和 runtime layering 的多处文档 / wrapper 不一致。
- 缩小 shared skill drift，恢复 verification trust。

---

<br>

## 0.1.0 - 2026-04-09

### 首个可用版本

- 建立 QROS 作为 agentic stage-gated quant research workflow framework 的基本形态。
- 提供 Codex 安装入口、repo-local runtime wrapper、stage skills、review skills、failure handling、SOP 文档和 anti-drift 基础测试。
- 覆盖从 idea intake、mandate 到 data/signal/train/test/backtest/holdout 的研究治理骨架。
- 引入 review/display/next-stage gate 纪律，要求 formal artifacts、review closure 和 gate 语义真实成立后才能推进。
- 明确本仓库是流程、工具和治理规则仓，不保存某条 live strategy lineage 的真实研究程序。
