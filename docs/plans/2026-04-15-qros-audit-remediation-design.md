# QROS Audit Remediation Design

**Goal:** 收敛当前仓库里已经确认的四类问题：全量测试失败、tier 漏测、review skill boilerplate 过重、author language discipline 硬编码分散。

## Design

- Anti-drift / closure 线：把真正的语义投影与当前 runtime contract 对齐。`semantic_projection` 忽略实例级 lineage 选择文案；metamorphic 测试不再把 slug 冲突副作用误判成 raw idea 语义变化；closure writer 的路径文档和测试统一到 `review/closure/` 真值。
- Verification tier 线：把这次暴露真实失败的 focused tests 纳入 `full-smoke`，让 tier 门禁对 anti-drift 语义和 closure context 推断都有覆盖。
- Review skill 线：保留 stage-specific gate/checklist/rollback/downstream，抽出共享审查协议到单一文档，再由模板生成的 review skills 引用它，减少 13 个 review skill 的重复体积。
- Author language 线：把中英文切换规则抽到单一文档，让 author skills 和 `qros-research-session` 只保留引用，不再内联重复规则块。

## Verification

- Focused tests 覆盖 anti-drift、closure writer、skill generation、author skill contract、verification tiers。
- 然后跑 `smoke`、`full-smoke`、全量 `pytest`，确认原来的 4 个失败消失，且 tier 已覆盖这批修复点。
