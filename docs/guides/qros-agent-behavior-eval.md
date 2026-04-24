# QROS Agent Behavior Eval

本文说明 QROS 的真实 agent 行为回归测试边界。

这套 eval 用来验证 agent 是否按 skill-first 方式进入 QROS 工作流，而不是只验证 runtime 函数本身。它关注稳定行为信号：

- 目标 skill 是否触发
- 目标 skill 之前是否出现非白名单 tool call
- runtime status 是否停在预期 stage
- 必要 artifact 是否存在
- 禁止提前生成的 artifact 是否不存在
- `qros-validate-stage` 对 `idea_intake` shape 是否通过

## 执行边界

真实 agent eval 是 manual / nightly，不进入默认 pytest，也不进入 smoke。默认 pytest 只跑 fake transcript、case contract、parser 和 assertion 测试。

原因是模型输出和工具事件格式可能波动。普通 CI 应该验证 harness 本身是稳定的，真实 agent 运行结果作为人工或夜间信号记录。

## 命令

手动运行时使用：

```bash
qros-agent-eval \
  --case naive_raw_idea_triggers_research_session \
  --work-root /tmp/qros-agent-eval \
  --agent-command-template '<agent command that writes JSONL to {transcript_path}>'
```

`--agent-command-template` 是必填项。命令模板可使用这些占位符：

- `{prompt_path}`
- `{transcript_path}`
- `{work_dir}`
- `{prompt}`

每次运行会写出：

- `prompt.txt`
- `transcript.jsonl`
- `result.yaml`

## Fake Transcript

开发 harness 时不要调用真实模型。使用 fake transcript：

```bash
python runtime/scripts/run_agent_behavior_eval.py \
  --case naive_raw_idea_triggers_research_session \
  --work-root /tmp/qros-agent-eval \
  --transcript-path tests/agent_eval/fixtures/fake_agent_success.jsonl
```

## MVP Cases

- `naive_raw_idea_triggers_research_session`
- `explicit_idea_intake_author_skill_first`
- `partial_intake_does_not_go_to_mandate`
- `no_confirmation_no_mandate_formal_artifacts`
- `raw_idea_scaffold_passes_artifact_shape_validator`

这些 case 定义在：

```text
contracts/agent_eval/qros_agent_behavior_eval_cases.yaml
```

## 断言原则

不要断言 assistant 的自然语言原文。只断言可稳定复现的行为信号，例如 skill call、tool call 顺序、runtime current_stage、artifact 存在性和 validator 结果。
