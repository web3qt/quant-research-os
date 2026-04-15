# QROS 工作原理：两层运行时架构

本文解释 QROS 的运行机制——宿主 AI Runtime（Claude Code / Codex）与 QROS Python Runtime 如何协作，以及研究流程是如何被推进和约束的。

如果你是第一次接触 QROS，建议先读 [README](../../README.md) 了解项目定位，再回来理解运行机制。

---

## 整体架构：宿主 + QROS

```mermaid
graph TB
    subgraph Host["宿主 Runtime<br/>(Claude Code / Codex)"]
        LLM["LLM 推理引擎"]
        Tools["工具调用能力<br/>Bash / Read / Write"]
        LLM --> Tools
    end

    subgraph QROS["QROS 层"]
        Skill["SKILL.md<br/>行为规范"]
        PyRuntime["Python Runtime<br/>确定性状态机"]
        YAML["YAML 合约<br/>门控真相"]
    end

    User["用户"] -->|"原始想法"| LLM
    Tools -->|"调用"| PyRuntime
    LLM -->|"读取"| Skill
    PyRuntime -->|"读取"| YAML
    PyRuntime -->|"返回状态面板"| LLM
    Skill -->|"引导对话"| User
```

**核心分工**：

| 维度 | 宿主 Runtime | QROS Runtime |
|------|-------------|--------------|
| 本质 | LLM 推理引擎 + 工具调度 | 确定性状态机 + 合约执行器 |
| 职责 | 理解意图、生成文本、调用工具 | 判断阶段、校验产物、推进状态 |
| 确定性 | 不确定（LLM 输出可变） | 完全确定（同输入同输出） |
| 存储 | 对话历史在内存 | 状态在磁盘 YAML/Markdown 文件 |
| 失败模式 | 理解偏差、幻觉 | 文件缺失、合约违反 |

---

## 执行流程：一次完整调用

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as Agent (LLM)
    participant S as SKILL.md
    participant R as qros-session (Python)
    participant D as 磁盘产物

    U->>A: "我想研究动量因子"
    A->>S: 读取行为规范
    A->>R: ./.qros/bin/qros-session --raw-idea "研究动量因子"

    R->>D: 检查 outputs/ 目录
    R-->>A: 返回状态面板<br/>📍 idea_intake<br/>▶ 确认 observation 和 hypothesis

    loop 分组确认循环
        A->>U: "你的主要假说是什么？"
        U->>A: "BTC 领动高流动性 ALT"
        A->>D: 写入 draft 产物
    end

    A->>R: --confirm-intake
    R->>D: 校验 idea_brief.md、scorecard.yaml、gate_decision.yaml
    R-->>A: ✅ 推进到 mandate_confirmation_pending

    A->>U: "是否确认进入 mandate？"
    U->>A: "确认"
    A->>R: --confirm-mandate
    R->>D: 校验 mandate 产物完整性
    R-->>A: 推进到 mandate_author
```

每个阶段都遵循相同的循环：

```
Agent 对话 → 调用 runtime → runtime 校验磁盘产物 → 返回状态 → Agent 继续对话
```

---

## QROS Runtime 内部结构

```mermaid
graph TB
    subgraph Entry["入口"]
        Shell["bin/qros-session<br/>(Shell 包装)"]
    end

    subgraph Scripts["命令行层"]
        RunSession["run_research_session.py<br/>参数解析 + 输出格式化"]
    end

    subgraph Core["核心状态机"]
        RS["research_session.py<br/>~3200 行"]
        RS -->|"67 种状态"| SessionStage["SessionStage"]
    end

    subgraph StageRuntimes["各阶段 Runtime"]
        Idea["idea_runtime.py"]
        Data["data_ready_runtime.py"]
        Signal["signal_ready_runtime.py"]
        Train["train_runtime.py"]
        Test["test_evidence_runtime.py"]
        BT["backtest_runtime.py"]
        Holdout["holdout_runtime.py"]
        CSF["csf_*_runtime.py ×6"]
    end

    subgraph Review["审查引擎"]
        RE["review_engine.py"]
        Closure["closure_writer.py"]
        Adv["adversarial_review_contract.py"]
    end

    subgraph Program["谱系程序"]
        LP["lineage_program_runtime.py"]
        Scaffold["stage_program_scaffold.py"]
    end

    Shell --> RunSession
    RunSession --> RS
    RS --> StageRuntimes
    RS --> Review
    RS --> Program

    RS -->|"返回"| Status["SessionStatus<br/>(dataclass)"]
    Status -->|"退出码 + JSON"| RunSession
```

### 各模块职责

| 模块 | 职责 |
|------|------|
| `research_session.py` | 核心状态机：检测当前阶段、推进状态、返回 SessionStatus |
| `*_runtime.py` | 各阶段脚手架：生成 freeze draft、校验冻结组、检查产物 |
| `review_engine.py` | 审查引擎：加载合约、检查产物、生成审查判定 |
| `lineage_program_runtime.py` | 谱系程序：验证 stage_program.yaml、执行 entrypoint、记录 provenance |
| `run_research_session.py` | CLI 入口：参数解析、调用核心状态机、格式化输出面板 |

---

## 退出码：runtime 与 Agent 的通信协议

`qros-session` 通过退出码向 Agent 传递语义化信号：

```mermaid
graph LR
    R["qros-session"] -->|"exit 0"| OK["一切正常，可继续"]
    R -->|"exit 2"| Confirm["等待用户确认<br/>FREEZE_APPROVAL_MISSING"]
    R -->|"exit 3"| NoProg["谱系程序缺失<br/>STAGE_PROGRAM_MISSING"]
    R -->|"exit 4"| BadProg["谱系程序合约违反<br/>STAGE_PROGRAM_INVALID"]
    R -->|"exit 5"| ExecFail["程序执行失败<br/>PROGRAM_EXECUTION_FAILED"]
    R -->|"exit 6"| BadOut["产物不完整<br/>OUTPUTS_INVALID"]
    R -->|"exit 7"| ReviewPend["等待审查<br/>REVIEW_PENDING"]
    R -->|"exit 8"| FailHandle["需要失败处理<br/>FAILURE_HANDLER_REQUIRED"]
```

Shell 包装器将退出码 2-8 映射为 `exit 0`（非致命阻塞），只有真正的系统错误才传递非零退出码。Agent 不会因为阻塞而报错，而是读到状态面板后知道该做什么。

---

## 双层防护：软约束 + 硬约束

```mermaid
graph TB
    subgraph Soft["第一层：软约束 (SKILL.md)"]
        S1["Working Rules:<br/>先确认 observation"]
        S2["再确认 primary hypothesis"]
        S3["再确认 data_source / bar_size"]
        S4["不得静默填写 scorecard"]
        S1 --> S2 --> S3 --> S4
    end

    subgraph Hard["第二层：硬约束 (Python Runtime)"]
        H1["idea_brief.md 存在？"]
        H2["qualification_scorecard.yaml 存在？"]
        H3["idea_gate_decision.yaml = GO_TO_MANDATE？"]
        H4{"全部通过？"}
        H1 --> H2 --> H3 --> H4
        H4 -->|"否"| Block["blocking_reason_code =<br/>FREEZE_APPROVAL_MISSING"]
        H4 -->|"是"| Advance["推进到下一阶段"]
    end

    Soft -.->|"Agent 可能不听话"| Hard
    Hard -->|"不满足就 blocking"| Stop["状态不推进"]
```

- **软约束**（SKILL.md）告诉 Agent "你应该这样做"——但 LLM 可能跳步
- **硬约束**（Python Runtime）检查磁盘产物 "文件在不在？合约满不满足？"——不满足就阻塞

即使 Agent 试图跳步，runtime 发现磁盘上缺文件就不会推进状态。这就是 QROS 的核心保障：**用确定性代码约束不确定性 AI**。

---

## SKILL.md 的角色：Agent 操作手册

SKILL.md 不执行任何代码。它是一份给 LLM 的行为规范，告诉 Agent：

1. 什么时候该停下来问用户
2. 按什么顺序确认冻结组
3. 什么条件下才能推进到下一阶段
4. 什么时候必须切换到失败处理

```mermaid
graph LR
    subgraph "三者关系"
        Skill["SKILL.md<br/>(行为规范)"]
        Runtime["Python Runtime<br/>(状态机 + 校验)"]
        Contract["YAML 合约<br/>(门控真相)"]
    end

    Skill -->|"引导"| Agent["Agent 如何对话"]
    Runtime -->|"校验"| Disk["磁盘产物"]
    Contract -->|"定义"| Gate["门控标准"]

    Runtime -->|"读取"| Contract
    Skill -->|"引用"| Contract
```

合约 YAML 是三者共享的真相来源：runtime 读它做校验，SKILL.md 读它引导对话，测试读它验证一致性。

---

## 状态生命周期：从 idea_intake 到 holdout_validation

```mermaid
stateDiagram-v2
    [*] --> idea_intake: 用户提出原始想法

    idea_intake --> intake_confirm: 填写 observation / hypothesis / route
    intake_confirm --> mandate_confirm: GO_TO_MANDATE

    mandate_confirm --> mandate_author: 用户确认进入 mandate
    mandate_author --> mandate_review: 产物写入完成

    mandate_review --> dr_confirm: PASS
    mandate_review --> fail: RETRY / NO-GO

    dr_confirm --> data_ready_author: 用户确认 data_ready 参数
    data_ready_author --> data_ready_review: 产物写入完成

    data_ready_review --> sr_confirm: PASS
    data_ready_review --> fail: RETRY / NO-GO

    sr_confirm --> signal_ready_author: 用户确认 signal 参数
    signal_ready_author --> signal_ready_review: 产物写入完成

    signal_ready_review --> tf_confirm: PASS

    tf_confirm --> train_freeze_author: 用户确认 train 参数
    train_freeze_author --> train_freeze_review: 产物写入完成

    train_freeze_review --> te_confirm: PASS

    te_confirm --> test_evidence_author: 用户确认 test 参数
    test_evidence_author --> test_evidence_review: 产物写入完成

    test_evidence_review --> bt_confirm: PASS

    bt_confirm --> backtest_ready_author: 用户确认 backtest 参数
    backtest_ready_author --> backtest_ready_review: 产物写入完成

    backtest_ready_review --> hv_confirm: PASS

    hv_confirm --> holdout_author: 用户确认 holdout 参数
    holdout_author --> holdout_review: 产物写入完成

    holdout_review --> [*]: 完成

    fail --> [*]: 失败处理

    note right of fail
        失败路由判定：
        PASS_FOR_RETRY / RETRY /
        NO-GO / CHILD_LINEAGE
        切入 qros-stage-failure-handler
    end note
```

每个阶段都经过相同的子循环：

```mermaid
graph LR
    A["确认待定<br/>*_confirmation_pending"] -->|"用户确认"| B["创作阶段<br/>*_author"]
    B -->|"产物写入完成"| C["审查确认<br/>*_review_confirmation_pending"]
    C -->|"用户确认"| D["审查阶段<br/>*_review"]
    D -->|"PASS"| E["下一阶段确认<br/>*_next_stage_confirmation_pending"]
    D -->|"RETRY/NO-GO"| F["失败处理"]
    E -->|"用户确认"| A2["下一阶段确认待定"]
```

---

## 产物目录结构

每次 runtime 校验和推进时，检查的是用户研究仓库中的磁盘产物：

```mermaid
graph TB
    subgraph "outputs/<lineage_id>/"
        subgraph "stage_dir/"
            A["author/draft/<br/>freeze_draft.yaml 等工作文件"]
            B["author/formal/<br/>artifact_catalog.md<br/>field_dictionary.md<br/>program_execution_manifest.json"]
            C["review/request/<br/>审查请求"]
            D["review/result/<br/>审查判定"]
            E["review/closure/<br/>stage_completion_certificate.yaml"]
        end
        subgraph "program/"
            P1["stage_program.yaml"]
            P2["README.md"]
            P3["entrypoint.py / .rs / .sh"]
            P4["common/<br/>共享库"]
        end
    end
```

Runtime 的校验逻辑是：**产物文件存在于磁盘 + 内容符合合约 = 阶段完成**。不依赖对话历史，不依赖 Agent 记忆。

---

## 与宿主 Runtime 的边界

```mermaid
graph TB
    subgraph "宿主负责 (不可替代)"
        H1["理解用户自然语言意图"]
        H2["生成解释性文本和对话"]
        H3["调用工具 (Bash/Read/Write)"]
        H4["按 SKILL.md 引导与用户交互"]
    end

    subgraph "QROS 负责 (确定性保障)"
        Q1["检测当前阶段"]
        Q2["校验产物完整性"]
        Q3["推进状态机"]
        Q4["生成审查判定"]
        Q5["记录 provenance"]
        Q6["反漂移快照"]
    end

    H1 -.->|"用户意图"| Q1
    H3 -.->|"调用 qros-session"| Q2
    Q2 -.->|"状态面板"| H2
    H4 -.->|"确认后调用"| Q3
```

关键边界原则：

1. **QROS 不做推理**——不替用户判断假说是否合理，只校验产物是否完整
2. **宿主不做校验**——LLM 不自己判断阶段是否完成，而是调 runtime 检查
3. **产物优于记忆**——正式结论依赖磁盘文件，不依赖对话历史
4. **合约是共享真相**——runtime 和 SKILL.md 都从同一份 YAML 合约读取门控标准

---

## 延伸阅读

- [阶段冻结字段说明](stage-freeze-group-field-guide.md) — 各阶段冻结组的字段解释
- [QROS 统一研究会话说明](qros-research-session-usage.md) — qros-research-session 的使用方法
- [研究工作流 SOP](../sop/main-flow/research_workflow_sop.md) — 各阶段操作规范
- [验证层级说明](qros-verification-tiers.md) — smoke / full-smoke 验证
