# Release Notes

本文件记录 QROS 从第一个可用版本到当前版本的用户可见变化。QROS 是流程与治理仓；release notes 重点记录 workflow、runtime、skill、contract、文档和验证能力的变化。

## 0.4.2 - 2026-04-27

### 新增

- 新增 `$qros-factor-diagnostics`：只读 CSF 因子阶段 diagnostics skill，用于查看当前或指定 lineage 的横截面因子阶段质量。
- 新增 `./.qros/bin/qros-factor-diagnostics` runtime wrapper，默认读取 active research repo 的 `outputs/`，选择最近修改 lineage，并自动推断 CSF stage。
- 新增因子检测指标库与 CSF stage diagnostic profiles：
  - `contracts/diagnostics/factor_metric_library.yaml`
  - `contracts/diagnostics/csf_stage_diagnostic_profiles.yaml`
- 新增 runtime diagnostics engine：读取 formal artifacts，汇总 observed diagnostics、missing diagnostics、evidence gaps 和 next diagnostics。
- 新增中文解释型输出：observed metric 现在包含 `severity`、`interpretation` 和 `strategy_link`，例如 Rank IC 为负时会解释“因子排序与未来收益排序反向”，并提示检查 `factor_direction`。

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

## 0.4.1 - 2026-04-27

### 改进

- 重写 README，使首页更像 Notion 风格的项目入口页。
- 强化普通用户入口：从 active research repo 打开 Codex，先 fetch `.codex/INSTALL.md`，然后使用 `$qros-research-session`、`$qros-progress` 和 `$qros-update`。
- 明确 QROS 是 workflow / governance framework，不是具体策略实现仓。

### 发布

- 将版本从 `0.4.0` 提升到 `0.4.1`。
- 同步更新 `pyproject.toml` 与 `uv.lock`。

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

## 0.1.0 - 2026-04-09

### 首个可用版本

- 建立 QROS 作为 agentic stage-gated quant research workflow framework 的基本形态。
- 提供 Codex 安装入口、repo-local runtime wrapper、stage skills、review skills、failure handling、SOP 文档和 anti-drift 基础测试。
- 覆盖从 idea intake、mandate 到 data/signal/train/test/backtest/holdout 的研究治理骨架。
- 引入 review/display/next-stage gate 纪律，要求 formal artifacts、review closure 和 gate 语义真实成立后才能推进。
- 明确本仓库是流程、工具和治理规则仓，不保存某条 live strategy lineage 的真实研究程序。
