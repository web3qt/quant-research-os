# QROS Runtime 指南

## 作用域

本文件约束 `runtime/` 子树，包括 `bin/`、`scripts/`、`tools/`、`hooks/`。

## 目的

这里是真实生效的 runtime / helper / scaffold 实现层，不是 `harness/tools/` 的演示副本。

## Runtime 规则

- 输出字段名和 artifact 名应以实际 freeze draft、formal artifact、runtime shape 为准
- 如果文档、skill 和 runtime 字段不一致，优先修正文档与 skill，使其对齐 runtime 真值
- scaffold 与 helper 的产物名应稳定，避免无理由改名
- 如果修改输出字段、artifact contract 或用户工作流，必须同步更新最近的测试和说明文档
- 新增注释优先使用清晰、简短、面向维护者的中文说明

## 不要做的事

- 不要让 runtime helper 偷偷发明第二套命名体系
- 不要只改运行时而不更新配套测试和文档
- 不要让关键输出对象只存在于内存或日志里而不正式落盘
