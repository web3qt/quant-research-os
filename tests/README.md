# tests 目录导航

`tests/` 现在按“测试对象”分层，而不是按文件创建时间平铺。

一级目录约定：

- `anti_drift/`：anti-drift baseline、snapshot、render、export、build 回归
- `bootstrap/`：bootstrap、setup、install、native install smoke、update 脚本
- `contracts/`：目录布局、CI、verification tier、schema 与治理契约
- `docs/`：安装文档、README、文档入口与 hygiene
- `helpers/`：测试辅助模块，不直接承载业务断言
- `review/`：review engine、closure writer、context inference、review script
- `runtime/`：各 stage runtime、lineage program、auto-program 运行时
- `session/`：research-session 编排、route、assets、failure-routing、substep
- `skills/`：skill tree、skill asset、guidance/runtime path 相关测试

如果你要快速定位：

- 看安装和入口：先去 `bootstrap/`、`docs/`
- 看主流程编排：先去 `session/`
- 看 reviewer / closure：先去 `review/`
- 看 stage 运行时：先去 `runtime/`
- 看 anti-drift：先去 `anti_drift/`
