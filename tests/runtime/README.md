# runtime

这一层锁定 stage-local runtime：

- mainline 与 CSF 各阶段 runtime
- lineage-local stage program runtime / negative path
- auto-program 运行时

这里更偏“单阶段运行时正确性”，不负责整条 session orchestration。
