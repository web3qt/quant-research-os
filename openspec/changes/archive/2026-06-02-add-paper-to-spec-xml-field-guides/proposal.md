## Why

`contracts/paper_to_spec/*.yaml` 已经是 paper-to-spec validators 读取的 machine-readable 真值层，但字段语义主要靠 skill 和文档散落解释。研究员和 agent 在生成 `paper_*_spec.yaml` 时容易不清楚字段含义、证据口径、常见错误和阻断问题边界。

现在需要为 PaperSpec / `qros-paper-to-spec` 增加一层中文字段解释和 LLM 友好的结构化指南，同时保持 YAML contracts 作为 canonical runtime validation source。

## What Changes

- 新增 paper-to-spec XML field guides，覆盖 6 个 paper spec contract 的顶层字段、核心字段、optional blocks、blocking groups 和 handoff 字段。
- 每个字段指南包含中文名称、字段含义、为什么重要、填写规则、示例、常见错误和阻断提示。
- 更新 `qros-paper-to-spec` skill 和用户文档，要求生成 spec 前参考 XML field guide，但最终正式 artifact 仍为 `paper_*_spec.yaml`。
- 新增 contract-guide parity 测试，确保 YAML contract 中仍被引用的 required fields / core fields / optional blocks 都能在 XML guide 中找到解释。
- 不替换 `contracts/paper_to_spec/*.yaml`，不改变现有 validator 默认 contract 路径，不改变正式 `paper_*_spec.yaml` artifact 格式。

## Capabilities

### New Capabilities

- `paper-to-spec-field-guides`: Provide XML field guides with Chinese explanations for paper-to-spec contracts and require PaperSpec/qros-paper-to-spec generation to use them as semantic guidance while YAML contracts remain canonical.

### Modified Capabilities

- None.

## Impact

- Affected contracts/docs/skills/tests:
  - `contracts/paper_to_spec/field_guides/*.fields.xml`
  - `skills/core/qros-paper-to-spec/SKILL.md`
  - `docs/guides/qros-paper-to-spec-usage.md`
  - `tests/contracts/` or `tests/skills/` parity coverage for XML field guides
- Runtime validators remain YAML-based and deterministic.
- No stage flow, gate semantics, route split, review orchestration, failure handling, or live lineage artifact format changes.
- No new third-party dependency is expected; XML parsing can use Python standard library for tests.
