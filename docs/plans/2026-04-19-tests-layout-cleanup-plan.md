# tests 目录分层重整计划

日期：2026-04-19

## 背景

当前 `tests/` 目录几乎完全平铺，随着 runtime、review、install、anti-drift 与 session 相关回归持续增加，测试入口已经不再具备“看目录即可判断测试职责”的可读性。

本次改动目标不是改变测试语义，而是把现有测试按对象分层，让维护者能够快速定位：

- 哪些测试锁定 bootstrap / install
- 哪些测试锁定 docs / contract
- 哪些测试锁定 session orchestration
- 哪些测试锁定 stage runtime / review engine / anti-drift

## 目标目录

计划将 `tests/` 收敛为以下结构：

- `tests/anti_drift/`：anti-drift baseline、snapshot、render、export、summary/build 回归
- `tests/bootstrap/`：bootstrap、setup、install、native install smoke、update 脚本
- `tests/contracts/`：目录布局、CI / verification tier / schema / contract 级测试
- `tests/docs/`：README、安装文档、doc hygiene、runtime-facing 文档入口
- `tests/helpers/`：测试辅助模块
- `tests/review/`：review engine、closure writer、context inference、render、review 脚本
- `tests/runtime/`：各 stage runtime、lineage program、auto-program 运行时测试
- `tests/session/`：research-session、route、author assets、failure-routing、substep 编排
- `tests/skills/`：skill tree、skill asset / guidance / runtime path 相关测试

## 实施步骤

1. 先补 `tests` 分层 contract 测试，锁定目标目录与代表性入口。
2. 迁移测试文件与 helper 模块到新目录。
3. 修正以下硬编码路径与导入：
   - `runtime/tools/verification_tiers.py`
   - `.github/workflows/anti-drift.yml`
   - 现有测试中的 `from tests.test_*` 导入
   - 现有测试中的 `Path(__file__).resolve().parents[1]`
   - 根 `AGENTS.md` 与少量仍引用旧路径的活跃文档
4. 为 `tests/` 根和每个一级分类目录补简短 `README.md`，让目录本身承担导航作用。
5. 跑 focused tests 与 `smoke`，确认结构重整没有破坏现有验证链。

## 风险控制

- 不改测试断言语义，优先只改路径、导入与导航说明。
- 不批量修改 `docs/archive/` 历史计划中的旧测试路径，避免把历史执行记录改写成当前结构。
- 若发现某些测试对目录深度有隐藏假设，统一收敛到共享 helper，避免未来再次与层级绑定。

## 验证计划

- focused:
  - `python -m pytest tests/contracts/test_tests_layout.py -q`
  - `python -m pytest tests/contracts/test_verification_tiers.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py tests/session/test_research_session_runtime.py tests/session/test_run_research_session_script.py tests/review/test_review_engine.py -q`
- smoke:
  - `python runtime/scripts/run_verification_tier.py --tier smoke`
