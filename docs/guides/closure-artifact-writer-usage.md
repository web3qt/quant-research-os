# Closure Artifact Writer Usage

## Scope

第一版 closure writer 服务于首批 3 个 Codex stage review skills：

- `qros-mandate-review`
- `qros-data-ready-review`
- `qros-signal-ready-review`

writer 的职责不是替 review skill 生成 verdict，而是在 review 结束后把标准化 payload 写成正式 closure artifacts。

## Files Written

writer 会写 4 份文件。

写入当前 `stage_dir`：

- `review/closure/latest_review_pack.yaml`
- `review/closure/stage_gate_review.yaml`
- `review/closure/stage_completion_certificate.yaml`

写入当前 `lineage_root`：

- `latest_review_pack.yaml`

其中 lineage 根文件是最近一次 review 的镜像，不是第二份独立事实来源。

## Context Resolution

writer 支持两种上下文模式：

1. 自动推断  
从 `cwd` 向上搜索 `outputs/<lineage_id>/<stage>/` 目录结构。

2. 显式传参  
如果当前目录不在 lineage 目录树中，则显式提供：

- `stage_dir`
- `lineage_root`

## Shared Payload

第一版 payload 至少应包含：

- `lineage_id`
- `stage`
- `stage_status`
- `final_verdict`
- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `review_timestamp_utc`

如有需要，也可以补充：

- `rollback_stage`
- `allowed_modifications`
- `downstream_permissions`

## Example

```python
from pathlib import Path

from runtime.tools.review_skillgen.closure_models import build_review_payload
from runtime.tools.review_skillgen.closure_writer import write_closure_artifacts


payload = build_review_payload(
    lineage_id="topic_a",
    stage="mandate",
    final_verdict="PASS",
    stage_status="PASS",
    rollback_stage="mandate",
    allowed_modifications=["clarify wording only"],
    downstream_permissions=["data_ready"],
)

write_closure_artifacts(
    payload,
    explicit_context={
        "stage_dir": Path("outputs/topic_a/mandate"),
        "lineage_root": Path("outputs/topic_a"),
    },
)
```

## Verification

最直接的验证命令：

```bash
python -m pytest tests/review/test_closure_models.py -v
python -m pytest tests/review/test_context_inference.py -v
python -m pytest tests/review/test_closure_writer_stage_outputs.py -v
python -m pytest tests/review/test_closure_writer_lineage_mirror.py -v
python -m pytest tests/review/test_closure_writer_context_modes.py -v
python -m pytest tests -v
```
