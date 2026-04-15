# QROS Skills 指南

## 作用域

本文件约束 `skills/` 子树。

## 目的

这里是真实生效的 QROS workflow / stage skill 目录，不是 `harness/skills/` 的演示副本。

## Skills 规则

- 每个 skill 只解决一类明确问题，不要把 author / review / failure handling 混成一个入口
- skill 名称必须直接反映用途，并与正式 stage 名、artifact 名保持一致
- stage-aware 的 skill 必须明确输入、输出、禁止行为和阶段边界
- 如果 skill 会引用字段、freeze group 或 artifact，命名必须与 runtime-facing 对象一致
- 修改影响用户 workflow、artifact contract 或 stage 语义时，优先同时更新测试和文档

## 不要做的事

- 不要在 skill 里重复整仓地图或泛化流程说明
- 不要发明与 runtime / contracts 脱节的第二套命名
- 不要把 review closure、failure routing、authoring 逻辑混写成一个模糊 skill
