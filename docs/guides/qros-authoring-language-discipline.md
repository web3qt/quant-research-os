# QROS Authoring 语言规范

## 目的

这个文档承载 authoring / grouped confirmation / explanation surfaces 的统一语言规则，避免在多个 author skill 中重复硬编码同一段中英文约束。

## 规则

- 对 machine-readable 字段名、文件名、枚举值、命令、schema key 和上下游契约引用，保持英文或既有约定，不得为了中文化破坏契约。
- 对 hypothesis、counter-hypothesis、why、risk、evidence、uncertainty、kill reason、summary、rationale 等解释性内容，默认先判断是否适合中文；适合则优先用中文表达。
- 只有在英文表达更精确、需要与固定术语或上下游契约严格对齐、或用户明确要求英文时，才保留英文。

## Post-Mandate Stage Program 注释

- 对 `mandate` 之后的 lineage-local stage program，`run_stage.py` 与关键 helper 必须为真实产生产物的程序补清晰、简短、面向维护者的中文注释。
- 至少要覆盖关键步骤、阶段门禁、分支判断、program provenance / `program_hash` 绑定，以及其他容易被误读的关键 generation logic。
- 这里强调的是关键步骤中文注释，不要求逐行注释，也不要求为了形式感回填历史代码。
