# Paper-to-Spec Clean Removal Design

## Context

`qros-paper-to-spec` 目前暴露的是旧版 fast-lane：Codex 读取论文来源后生成 `strategy_spec.yaml`，再通过 repo-local wrapper 物化 bundle，并可选继续进入 baseline scaffold。这个路径已经不符合新的研究方向。

新的方向是先围绕 PDF 读取覆盖和 crypto perpetual data requirements 建立 `paper_data_spec.yaml`。在设计 `paper_data_spec` 前，需要先把旧的 `paper -> strategy_spec -> baseline` 用户能力清理干净，避免两套入口并存。

## Decision

先删除旧 paper-to-strategy-spec 能力，再重新设计 data-spec-first 的 `qros-paper-to-spec` v2。

本阶段不实现 `paper_data_spec`，只完成旧能力清理：

- 删除旧 `strategy_spec` contract。
- 删除旧 repo-local materializer wrapper。
- 删除旧 baseline scaffold wrapper。
- 删除旧 runtime helper 和脚本。
- 删除旧 paper-to-spec runtime tests。
- 更新 README、Codex guide、usage guide、skill 文档和相关 docs/bootstrap tests，使它们不再宣称旧能力可用。

`qros-paper-to-spec` 这个 skill 名称可以保留，但内容必须变成 v2 重建设计入口：旧 `strategy_spec.yaml` / baseline materializer 已移除，后续第一产物将是 `paper_data_spec.yaml`。

## Removal Scope

删除以下旧 runtime 和 contract 文件：

```text
contracts/paper_to_spec/strategy_spec_contract.yaml
runtime/tools/paper_to_spec.py
runtime/scripts/run_paper_to_spec.py
runtime/bin/qros-paper-to-spec
runtime/tools/paper_to_spec_baseline.py
runtime/scripts/run_paper_to_spec_baseline.py
runtime/bin/qros-paper-to-spec-baseline
```

删除旧 runtime 测试目录：

```text
tests/paper_to_spec/
```

同步更新这些主动引用旧能力的文件：

```text
README.md
docs/README.codex.md
docs/guides/qros-paper-to-spec-usage.md
skills/core/qros-paper-to-spec/SKILL.md
tests/bootstrap/test_project_bootstrap.py
tests/docs/test_install_docs.py
tests/docs/test_paper_to_spec_docs.py
tests/skills/test_paper_to_spec_assets.py
```

如果实现时发现其他 active docs、skills、SOP 或 tests 仍引用 `qros-paper-to-spec-baseline`、`--spec-file`、`strategy_spec.yaml` 作为 paper-to-spec 默认产物，也必须同步清理。

## User-Facing Behavior After Cleanup

清理后，普通用户不再能通过 repo-local wrapper 调用：

```text
./.qros/bin/qros-paper-to-spec
./.qros/bin/qros-paper-to-spec-baseline
```

文档不再出现这些旧用法：

```text
$qros-paper-to-spec <pdf> -> strategy_spec.yaml
./.qros/bin/qros-paper-to-spec --spec-file ...
./.qros/bin/qros-paper-to-spec-baseline --spec-path ...
--auto-implement
```

`qros-paper-to-spec` skill 文档应明确：

- 旧 `strategy_spec` materializer 已移除。
- 旧 baseline scaffold 已移除。
- v2 将采用 data-spec-first 方向。
- 当前阶段不应继续承诺直接从 PDF 生成完整 strategy spec 或回测代码。

## Non-Goals

本阶段不做以下工作：

- 不新增 `paper_data_spec_contract.yaml`。
- 不新增 `paper_data_spec.yaml` materializer。
- 不新增 `runtime/tools/paper_data_spec.py`。
- 不新增 `runtime/scripts/run_paper_data_spec.py`。
- 不新增新的 repo-local wrapper。
- 不实现 PDF 读取覆盖报告。
- 不实现 signal/train/test/backtest spec。
- 不进入 `qros-research-session` 主流程。

## Data-Spec Direction Kept For Next Phase

下一阶段重新设计 `qros-paper-to-spec` v2 时，第一产物应是：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

该方向保留以下已确认原则：

- 面向 generic crypto perpetuals，并允许 exchange profile 覆盖。
- 核心数据字段采用严格阻断。
- 字段库使用分层结构：core fields 必填，optional blocks 按 PDF 内容触发。
- reading coverage 可以先内嵌到 `paper_data_spec.yaml`，避免增加过多治理文件。
- 第一版最多新增一个 data-spec contract 文件，避免拆出过多 policy/profile/library 文件。

## Testing

删除旧能力后，需要运行 focused tests：

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py tests/docs/test_paper_to_spec_docs.py tests/skills/test_paper_to_spec_assets.py
```

如果这些测试被同步删除或合并，应运行实际保留下来的 docs/bootstrap/skills focused tests。

如果清理影响 bootstrap 安装产物清单或 repo-local runtime 安装说明，至少运行：

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
```

本阶段不改变 `qros-research-session` stage flow、review routing、CSF/TSS route split 或 stage-display contract，因此不要求 full-smoke。

## Risks

主要风险是留下旧口径残余：文档或 skill 仍暗示 `strategy_spec.yaml`、`qros-paper-to-spec-baseline`、`--auto-implement` 可用。实现时必须用 repo-wide search 清理这些 active references。

另一个风险是删除 wrapper 后外部脚本直接调用旧命令会失败。该风险是有意接受的，因为目标是先干净移除旧能力，再重建 data-spec-first 入口。

