# QROS Authoring Language Discipline

## Purpose

这个文档承载 authoring / grouped confirmation / explanation surfaces 的统一语言规则，避免在多个 author skill 中重复硬编码同一段中英文约束。

## Rules

- 对 machine-readable 字段名、文件名、枚举值、命令、schema key 和上下游契约引用，保持英文或既有约定，不得为了中文化破坏契约。
- 对 hypothesis、counter-hypothesis、why、risk、evidence、uncertainty、kill reason、summary、rationale 等解释性内容，默认先判断是否适合中文；适合则优先用中文表达。
- 只有在英文表达更精确、需要与固定术语或上下游契约严格对齐、或用户明确要求英文时，才保留英文。
