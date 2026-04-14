
# Stage Completion Certificate Template（机构级中文版）

> 用途：每个正式阶段关闭时统一填写，用来回答  
> **“为什么我们相信这一步已经完成且可信。”**
>
> 本模板应与以下文档一起使用：
> - `contracts/stages/workflow_stage_gates.yaml`
> - `stage_completion_standard_cn.md`
> - `review_checklist_master.yaml`
> - 对应阶段的 failure SOP
> - `lineage_change_control_sop_cn.md`
>
> 运行时正式产物应写为：
> - `<stage>/review/closure/stage_completion_certificate.yaml`
>
> 其中：
> - `latest_review_pack.yaml` 是 reviewer findings substrate
> - `stage_gate_review.yaml` 是独立 reviewer proof
> - `review/closure/stage_completion_certificate.yaml` 是 machine-readable closure proof

---

## 1. 基本信息

- `stage`:
- `lineage_id`:
- `run_id`:
- `decision_date_utc`:
- `stage_status`:  
  <!-- 允许值：PASS / CONDITIONAL PASS / PASS FOR RETRY / RETRY / NO-GO / GO / CHILD LINEAGE -->
- `review_scope`:  
  <!-- 例如：baseline only / full stage artifacts / selected params only -->
- `reviewed_by_builder`:
- `reviewed_by_reviewer`:
- `reviewed_by_auditor`:

---

## 2. 输入与输出核对

### 2.1 上游输入

- `input_artifacts`:
  - 
  - 
  - 

- `frozen_inputs_verified`:  
  <!-- true / false -->

- `frozen_input_notes`:
  - 
  - 

### 2.2 本阶段输出

- `output_artifacts`:
  - 
  - 
  - 

- `artifact_catalog_path`:
- `field_documentation_paths`:
  - 
  - 

- `required_outputs_complete`:  
  <!-- true / false -->

- `missing_or_incomplete_outputs`:
  - 
  - 

---

## 3. 六联可信完成标准

### 3.1 Contract Pass

- `contract_pass`:  
  <!-- true / false -->
- `contract_blockers`:
  - 
  - 
- `contract_reservations`:
  - 
  - 

### 3.2 Reproducibility Pass

- `reproducibility_pass`:  
  <!-- true / false -->
- `run_manifest_path`:
- `git_revision`:
- `repro_check_method`:  
  <!-- 例如：same-env rerun / independent rerun / spot recomputation -->
- `repro_check_summary`:
  - 
  - 
- `repro_blockers`:
  - 
  - 

### 3.3 Traceability Pass

- `traceability_pass`:  
  <!-- true / false -->
- `decision_evidence_links`:
  - 
  - 
  - 
- `critical_artifacts_used`:
  - 
  - 
- `critical_fields_used`:
  - 
  - 
- `traceability_blockers`:
  - 
  - 

### 3.4 Challenge Pass

- `challenge_pass`:  
  <!-- true / false -->
- `challenge_record_paths`:
  - 
  - 
- `main_challenge_questions`:
  - 
  - 
  - 
- `challenge_summary`:
  - 
  - 
- `challenge_blockers`:
  - 
  - 

### 3.5 Sanity Pass

- `sanity_pass`:  
  <!-- true / false -->
- `sanity_checks_performed`:
  - 
  - 
  - 
- `abnormal_result_triggered`:  
  <!-- true / false -->
- `abnormal_result_scope`:
  - 
  - 
- `abnormal_result_conclusion`:
- `sanity_blockers`:
  - 
  - 

### 3.6 Governance Pass

- `governance_pass`:  
  <!-- true / false -->
- `gate_doc_path`:
- `rollback_stage`:
- `allowed_modifications`:
  - 
  - 
- `downstream_permissions`:
  - 
  - 
- `residual_risks`:
  - 
  - 
- `governance_blockers`:
  - 
  - 

---

## 4. Reviewer Checklist 摘要

- `review_checklist_source`:  
  <!-- 例如：review_checklist_master.yaml / stage-specific checklist -->
- `blocking_checks_passed`:  
  <!-- true / false -->
- `blocking_checks_failed`:
  - 
  - 
- `reservation_checks_triggered`:
  - 
  - 
- `reservation_handling`:
  - 
  - 

---

## 5. 阶段结论

### 5.1 正式 verdict

- `final_verdict`:  
  <!-- PASS / CONDITIONAL PASS / PASS FOR RETRY / RETRY / NO-GO / CHILD LINEAGE -->

### 5.2 判定依据

- `decision_basis`:
  1. 
  2. 
  3. 

### 5.3 当前阶段冻结了什么

- `frozen_scope`:
  - 
  - 
  - 

### 5.4 当前阶段拒绝了什么

- `rejected_items`:
  - 
  - 
  - 

### 5.5 当前阶段残留风险

- `residual_risks_summary`:
  - 
  - 
  - 

---

## 6. 回退与分流

### 6.1 如果不是 PASS / CONDITIONAL PASS

- `rollback_required`:  
  <!-- true / false -->
- `rollback_reason`:
- `rollback_stage`:
- `allowed_modifications`:
  - 
  - 
  - 
- `forbidden_modifications`:
  - 
  - 
  - 

### 6.2 如果需要 child lineage

- `child_lineage_required`:  
  <!-- true / false -->
- `why_original_lineage_cannot_absorb_change`:
- `expected_child_lineage_topic`:
- `parent_lineage_relation_note`:

### 6.3 如果是 no-go

- `no_go_reason`:
- `closure_note_path`:

---

## 7. 下游权限

- `next_stage_allowed`:  
  <!-- true / false -->
- `next_stage_name`:
- `downstream_permissions`:
  - 
  - 
  - 
- `downstream_prohibited_actions`:
  - 
  - 
  - 

---

## 8. 签发记录

### 8.1 Builder Sign-off

- `builder_name`:
- `builder_signoff`:  
  <!-- approved / rejected -->
- `builder_comment`:

### 8.2 Reviewer Sign-off

- `reviewer_name`:
- `reviewer_signoff`:  
  <!-- approved / rejected / approved_with_reservations -->
- `reviewer_comment`:

### 8.3 Auditor / Referee Sign-off

- `auditor_name`:
- `auditor_signoff`:  
  <!-- approved / rejected / rollback / child_lineage / no_go -->
- `auditor_comment`:

---

## 9. 附录：最小填写规则

以下任一情况，默认不得写 `PASS`：

- `required_outputs_complete = false`
- `contract_pass = false`
- `reproducibility_pass = false`
- `traceability_pass = false`
- `challenge_pass = false`
- `sanity_pass = false`
- `governance_pass = false`

以下情况可以写 `CONDITIONAL PASS`，但必须在正文明确 reservations：

- 六联标准全部为 `true`
- 但存在非阻断性保留事项
- 且 `downstream_permissions` 已写清限制

以下情况适合写 `PASS FOR RETRY`：

- 当前阶段尚不能晋级
- 但 rollback stage、allowed modifications、retry hypothesis 已明确
- 且问题仍属于原谱系可修复范围

以下情况适合写 `CHILD LINEAGE`：

- 研究主问题改变
- Universe 身份改变
- 交易语义改变
- 风险字段角色改变
- 已无法沿用原证据链

---

## 10. 建议配套文件

建议与本证书一起归档：

- `review_notes.md`
- `self_challenge.md`（单人研究时至少应有）
- `approval_record.md`
- `rollback_decision.yaml`
- `frozen_spec.json`
- 对应阶段 gate 文档

---

## 11. 一句话模板

你也可以在文档开头先写一句人工摘要：

> 本阶段被判定为 `________`，因为在 `contract / repro / traceability / challenge / sanity / governance` 六个维度上，当前状态为：  
> `____ / ____ / ____ / ____ / ____ / ____`。  
> 其中主要阻断项是：`________`；  
> 允许修改范围是：`________`；  
> 下游允许消费的对象是：`________`。
