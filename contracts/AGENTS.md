# QROS contracts 指南

## 作用域

本文件约束 `contracts/` 子树。

## 目的

这里保存 QROS 的 machine-readable 合同面，供 runtime、review engine、skill 生成与验证层直接读取。

## 编辑规则

- 优先保持字段名、枚举值、层级结构稳定。
- 如果修改 schema、policy 或 gate 语义，必须同步更新：
  - 对应 runtime 读取逻辑
  - 相关测试
  - 仍然面向用户的说明文档
- 不要把演示性、聊天式或只适合人工阅读的说明混入 machine-readable 合同文件。
- 新增合同时，优先复用现有术语，不要为同一阶段或 verdict 再发明第二套命名。

## 测试要求

- 合同变更至少要补存在性、字段映射或契约测试。
- 如果改动会影响 stage gate、review checklist 或 runtime 路由，必须补对应回归测试。
