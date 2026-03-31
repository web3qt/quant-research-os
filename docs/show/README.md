# QROS 项目思路讲解

这份文档适合直接拿来做项目演示。

可直接编辑的图文件在这里：[qros-demo.drawio](/Users/mac08/workspace/web3qt/quant-research-os/docs/show/qros-demo.drawio)

如果只讲一句话：

> QROS 不是“某个策略代码仓”，而是一个把量化研究从模糊想法推进成可冻结、可复现、可审查、可回退研究线的流程操作系统。

## 建议演示顺序

1. 先讲“QROS 是什么”
2. 再讲“QROS 怎么跑起来”
3. 最后讲“为什么它对老板、开发、研究员都重要”

## 一、项目总览图

```mermaid
flowchart LR
    A["原始交易想法<br/>Raw Idea"] --> B["Idea Intake<br/>先问清问题，不先看结果"]
    B --> C["Mandate Freeze<br/>冻结研究边界、时间窗、Universe、路线"]

    C --> D["QROS 核心治理层"]

    D --> D1["Stage Contract<br/>每阶段有明确输入/输出"]
    D --> D2["Formal Artifacts<br/>正式产物落盘，不靠口头记忆"]
    D --> D3["Review Gates<br/>每阶段都要评审 closure"]
    D --> D4["Failure Handling<br/>失败要分流，不允许静默重试"]
    D --> D5["Lineage Control<br/>变更要记账，可追溯"]

    C --> E["Runtime / Skills / Session"]
    E --> E1["统一入口: qros-research-session"]
    E --> E2["按阶段切换 skill"]
    E --> E3["在当前 research repo 写入 outputs/<lineage_id>/<stage>"]

    D --> F["研究主流程推进"]
    E --> F

    F --> G["最终形成的不是聊天记录<br/>而是可审计研究线"]

    G --> G1["可复现"]
    G --> G2["可审查"]
    G --> G3["可恢复"]
    G --> G4["可晋级 / 可回退 / 可开子谱系"]

    classDef main fill:#d9f2d9,stroke:#4a7c59,stroke-width:1.5px,color:#111;
    classDef control fill:#e8eefc,stroke:#4a6fa5,stroke-width:1.2px,color:#111;
    classDef runtime fill:#f5ead6,stroke:#b67b2d,stroke-width:1.2px,color:#111;
    classDef outcome fill:#f7dfe5,stroke:#b35d74,stroke-width:1.2px,color:#111;

    class A,B,C,D,F,G main;
    class D1,D2,D3,D4,D5 control;
    class E,E1,E2,E3 runtime;
    class G1,G2,G3,G4 outcome;
```

## 二、主流程图

```mermaid
flowchart TB
    A["00 idea_intake<br/>判断这个想法值不值得正式研究"] --> B["00 mandate<br/>冻结研究问题和边界"]
    B --> C{"冻结 research_route"}

    C -->|time_series_signal| D["01 data_ready"]
    D --> E["02 signal_ready"]
    E --> F["03 train_freeze"]
    F --> G["04 test_evidence"]
    G --> H["05 backtest_ready"]
    H --> I["06 holdout_validation"]

    C -->|cross_sectional_factor| J["01 csf_data_ready"]
    J --> K["02 csf_signal_ready"]
    K --> L["03 csf_train_freeze"]
    L --> M["04 csf_test_evidence"]
    M --> N["05 csf_backtest_ready"]
    N --> O["06 csf_holdout_validation"]

    I --> P["07 promotion_decision"]
    O --> P
    P --> Q["08 shadow_admission"]
    Q --> R["09 canary_production"]

    S["每个阶段都必须有<br/>formal artifacts + review closure"] -.-> D
    S -.-> E
    S -.-> F
    S -.-> G
    S -.-> H
    S -.-> I
    S -.-> J
    S -.-> K
    S -.-> L
    S -.-> M
    S -.-> N
    S -.-> O

    T["如果 review verdict 是<br/>RETRY / NO-GO / CHILD LINEAGE<br/>则转 failure handling，不继续直推下一阶段"] -.-> P

    classDef main fill:#d9f2d9,stroke:#4a7c59,stroke-width:1.5px,color:#111;
    classDef ts fill:#dfe8ff,stroke:#4a6fa5,stroke-width:1.2px,color:#111;
    classDef csf fill:#efe2ff,stroke:#7a4fa3,stroke-width:1.2px,color:#111;
    classDef gov fill:#ffe7c7,stroke:#b67b2d,stroke-width:1.2px,color:#111;

    class A,B,C,P,Q,R main;
    class D,E,F,G,H,I ts;
    class J,K,L,M,N,O csf;
    class S,T gov;
```

## 三、怎么讲这个项目

### 先讲定位

这个仓库最容易被误解成“量化策略模板库”，但它其实不是。

它真正做的是两件事：

1. 规定研究必须怎么被定义、冻结、审查和推进
2. 让 agent 在真实 research repo 里把每个阶段的正式产物写出来，而不是停留在聊天和口头判断

### 再讲它解决的问题

传统研究流程常见的混乱是：

- 想法、边界、结果混在一起
- 看了结果再改研究问题
- 数据、信号、训练、回测混着做
- 失败后偷偷重试，没有变更记录
- 最后没人说得清这个结论到底靠什么证据成立

QROS 的做法是把这些问题拆成阶段治理：

- 先 `idea_intake`
- 再 `mandate freeze`
- 再按阶段推进
- 每阶段都要求正式 artifact
- 每阶段都要 review closure
- 失败必须进入 failure handling，而不是默默重跑

### 最后讲它为什么重要

对老板：

- 它把研究从“个人经验驱动”变成“组织可治理流程”
- 能看清一条研究线为什么推进、为什么被拒、为什么回退

对研究员：

- 它强制区分 hypothesis、data contract、signal contract、test evidence、backtest evidence
- 可以避免“先看到结果再回写故事”

对开发和 agent：

- 它明确告诉系统下一步该做什么、该写什么 artifact、什么情况下必须停下来问人
- 可以恢复 session，可以按 stage review，可以做 failure routing

## 四、30 秒版本

QROS 是一个量化研究流程操作系统。它不负责替你保存某个策略本身，而是负责把一个模糊研究想法，经过 intake、mandate、data、signal、train、test、backtest、holdout 这些阶段，变成一条可复现、可审查、可回退的正式研究线。核心不是“算出了什么结果”，而是“这个结果是按什么治理纪律被产生出来的”。

## 五、3 到 5 分钟讲稿

如果我要用最短时间介绍这个项目，我会这样讲：

第一，这个仓库不是一个具体策略仓，也不是一个普通的研究脚手架。它更像一个研究治理系统，专门解决量化研究里最常见的问题，比如边做边改、看完结果再改问题、失败不留痕、流程不可复盘。

第二，QROS 的核心思想是，研究不能靠聊天记录推进，必须靠正式 artifact 推进。一个原始想法先进入 `idea_intake`，先确认 observation、hypothesis、kill criteria 和 scope。只有这个想法值得继续，才进入 `mandate`，把研究边界、时间窗、Universe、参数边界和研究路线冻结下来。

第三，从 `mandate` 之后，流程会按 `research_route` 分成两条线。一条是时序信号路线，走 `data_ready -> signal_ready -> train_freeze -> test_evidence -> backtest_ready -> holdout_validation`。另一条是横截面因子路线，走对应的 `csf_*` 独立阶段。这说明 QROS 并不是只有一条固定研究模板，而是先冻结路线，再按路线执行不同合同。

第四，QROS 每个阶段都强调三件事。第一，要有正式产物，而不是空目录和说明文档。第二，要有 review closure，阶段通过不是自己说了算。第三，失败不能悄悄重试，而是要进入 failure handling，看是允许 retry、必须回退，还是应该开 child lineage。

第五，所以这个项目的价值，不只是帮研究员更规范，也是在帮组织建立研究治理能力。老板看到的是过程可控，研究员得到的是研究纪律，开发和 agent 得到的是清晰的阶段合同和确定的执行入口。

如果用一句话收尾，那就是：QROS 让量化研究从“讨论一个想法”，升级成“经营一条可审计的研究生命线”。

## 六、演示时的建议

如果你现场只讲一页，优先讲“项目总览图”。

如果你有 3 到 5 分钟，建议顺序是：

1. 先讲一句话定位
2. 指着总览图讲治理机制
3. 指着主流程图讲 stage 推进和 route 分流
4. 最后分别点一下老板、研究员、开发能得到什么

如果你要给老板做汇报，可以重点强调这三个词：

- `可治理`
- `可审计`
- `可追溯`

如果你要给开发和研究员讲，可以重点强调这四个词：

- `freeze`
- `artifact`
- `review`
- `lineage`
