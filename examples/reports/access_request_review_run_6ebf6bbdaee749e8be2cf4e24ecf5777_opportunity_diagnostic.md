# Workflow AI Opportunity Diagnostic

**Workflow:** `access_request_review`  
**Run:** `run_6ebf6bbdaee749e8be2cf4e24ecf5777`  
**Diagnostic version:** `1.0.0`

## Executive Diagnostic

**Headline:** The best first AI investment is exception preparation for identity analysts, not access decisions or provisioning.

> The workflow is structured enough for useful AI assistance but not for agentic decision-making. The immediate value lies in reducing the repeated work of organizing exceptions and evidence. Higher autonomy will be unlocked primarily by codifying routing, authority, state, and data rules—not by giving the model more tools.

**Current automation ceiling:** read_only_ai_assist

**Recommendation:** Pilot a read-only intake exception packet assistant that uses externally generated validation results and approved metadata to prepare deficiency checklists, discrepancy summaries, and reviewer questions. Keep raw restricted request fields, routing decisions, communications, workflow updates, approvals, and provisioning outside the model.

**Recommended first pilot:** Read-only intake exception packet preparation for identity analyst review, using deterministic required-field and HR verification results rather than raw restricted request content.


**Do not start with:**
- AI approval or rejection of access requests
- Autonomous privileged or sensitive-access triage
- Autonomous provisioning or permission changes
- Autonomous clarification, escalation, or report distribution
- Autonomous ticket-status or approval-evidence updates

**Top blockers:**
- Most fields needed to understand the requested access are currently blocked from model context.
- Mandatory-review criteria and the sensitive-system inventory are incomplete, so AI cannot safely determine when additional review is unnecessary.
- The required-control lookup returned empty mappings and therefore provides no production authorization for governed actions.
- Reviewer authority, delegation rules, approval semantics, and allowed ticket-state transitions are not defined.
- No workflow performance baseline or AI acceptance thresholds have been established.

**Recommended next 30 days:**
- Define the exact model-context allowlist and test redaction against representative records.
- Create deterministic required-field and HR-verification result flags that can be passed to the model without exposing blocked source values.
- Baseline identity analyst handling time, clarification cycles, deficiency types, and correction rates.
- Assemble a human-reviewed evaluation set covering standard, privileged, and clarification cases.
- Resolve ownership and remediation for the empty required-control mappings.
- Document mandatory-review triggers, reviewer authority, and the allowed workflow states before considering recommendation or action capabilities.

## Non-Obvious Insights

These are the findings most likely to change how a workflow owner thinks about the AI opportunity.

### The pilot is really testing a context-transformation layer

**Insight:** Because raw decision-relevant fields are blocked, the first pilot must test whether deterministic checks can transform sensitive request data into useful, non-sensitive validation flags and evidence metadata.

**Why this is not obvious:** The visible opportunity appears to be natural-language review of the access request, but the current policy boundary removes most of the language and attributes needed for that task.

**Business implication:** Pilot success depends as much on the quality of the external validation and minimization design as on the model itself.

**Recommended action:** Evaluate the model only after the allowlist, redaction, and external validation-result format have been tested on representative cases.

**Evidence:** DOC-002, DOC-004, POLICY-001

### The highest-value work may be exception packaging rather than straight-through processing

**Insight:** The sample records illustrate a standard request, a privileged request requiring security review, and an incomplete privileged request requiring clarification. The work changes materially by exception type.

**Why this is not obvious:** A linear ten-step workflow can look suitable for end-to-end automation, but actual analyst effort is likely concentrated around ambiguous and higher-risk branches.

**Business implication:** AI should first reduce the effort of assembling clear exception packets while preserving human ownership of routing and decisions.

**Recommended action:** Segment pilot results by standard, privileged, and clarification cases instead of reporting only an overall average.

**Evidence:** DOC-002, DOC-003, DOC-004

### Process codification, not more tool access, is the main autonomy unlock

**Insight:** The workflow already identifies the necessary human actors, but it lacks complete criteria for mandatory review, reviewer authorization, ticket transitions, SLA escalation, evidence retention, and exceptions.

**Why this is not obvious:** Agentic programs often focus first on integrations and tool permissions. Here, integrations would amplify ambiguity unless the operating rules are made explicit.

**Business implication:** Funding process redesign and reference-data ownership will unlock more safe automation than granting the model write access.

**Recommended action:** Prioritize decision tables, authority rules, state semantics, and evidence requirements before implementing governed action tools.

**Evidence:** DOC-001, DOC-002, DOC-003, POLICY-002

### The strongest early value signal is reviewer behavior, not AI agreement with historical outcomes

**Insight:** Historical approval outcomes are not documented as a complete or reliable decision standard. Reviewer acceptance, correction, missed-deficiency, and evidence-traceability measures are more appropriate for an assistive pilot.

**Why this is not obvious:** Teams may try to score the model by whether it predicts approval or rejection, even though the pilot should not be making those decisions and complete decision criteria are missing.

**Business implication:** The evaluation should focus on whether AI makes analysts faster and more consistent without concealing uncertainty or missing required review.

**Recommended action:** Capture reviewer edits, rejected suggestions, missed deficiencies, and traceability to approved evidence before considering decision-support expansion.

**Evidence:** DOC-001, DOC-002, DOC-003


## Automation Ceiling

**Current ceiling:** read_only_ai_assist

**Summary:** AI may search approved workflow documents and prepare read-only checklists, summaries, and candidate work queues from approved, minimized inputs. It should not determine final routing, communicate externally, update records, approve access, or provision permissions.

**Why this is the ceiling:**
- Employee and manager identifiers, requested systems, access levels, privilege indicators, business justifications, approval evidence, and provisioning records are currently blocked from model context.
- The complete criteria for privileged, sensitive, custom, API, SSO, dependency, elevated, or security-related routing are not documented.
- The required-control service returned empty mappings for governed actions.
- Approval authority, delegation, state-transition, retention, and exception rules remain incomplete.
- Policy requires explicit human approval before write actions and recorded approvals before provisioning.

**What would raise the ceiling:**
- A validated field-level allowlist, redaction process, and approved model-processing boundary
- Authoritative deterministic routing criteria and maintained reference data
- Resolved required-control mappings with fail-closed behavior
- Documented reviewer authority and delegation rules
- Defined approval and ticket-state semantics
- Human-reviewed quality thresholds and production monitoring

**What prevents higher autonomy:**
- The model currently cannot see much of the information needed for useful access analysis.
- Allowing the model to infer missing routing rules could bypass mandatory review.
- A model recommendation could be mistaken for an accountable human decision.
- Provisioning and record writes could cause unauthorized access or damage audit evidence.
- The organization has not defined measurable conditions under which AI performance would justify expansion.

**Evidence:** DOC-001, DOC-002, DOC-003, DOC-004, POLICY-001, POLICY-002

## Recommended First AI Use Case

### Read-only intake exception packet assistant

**Description:** Prepare a structured packet for the identity analyst from documented required-field rules, externally generated completeness and HR-verification results, and approved metadata. The packet should identify human-confirmed missing or conflicting items, summarize verification-result metadata, cite workflow requirements, and draft reviewer questions. It must not inspect blocked raw fields, determine final routing, communicate, or update the workflow.

**Risk level:** medium

**Readiness:** ready_for_pilot

**Suggested pilot scope:** Use a representative, human-reviewed evaluation set segmented into standard, privileged, and clarification cases. Operate in shadow mode with no workflow, notification, approval, or provisioning writes. Compare AI-prepared packets with current analyst preparation.

**Why this is the right first pilot:**
- It targets repeated analyst work that occurs before approvals and provisioning.
- It can operate with externally produced validation flags rather than raw restricted request values.
- It supports standard, privileged, and clarification patterns without making access decisions.
- It produces measurable outputs such as preparation time, correction rate, missed deficiencies, and traceability.
- It directly tests whether the current data boundary can support useful AI before investment in broader integrations.

**Expected value:**
- Reduced analyst effort assembling intake and discrepancy information
- More consistent deficiency packets
- Fewer avoidable omissions in clarification preparation
- Faster identification of cases needing human attention
- Better evidence traceability for later reviewer stages

**Boundaries / blocked actions:**
- Approve or reject access
- Clear a request from application-owner or security review
- Make final identity or employment verification
- Route or return a request
- Send a clarification
- Change ticket or approval status
- Provision or modify access
- Ingest blocked raw request fields

**Success measures:**
- Change in analyst packet-preparation time versus baseline
- Reviewer correction and rejection rates
- False deficiency and missed-deficiency rates
- Repeat clarification cycles
- Percentage of material statements traceable to approved evidence
- Blocked-field exposure and context-filter failure rate
- Analyst usefulness rating segmented by case type

**Evidence:** DOC-001, DOC-002, DOC-003, DOC-004, POLICY-001, POLICY-002

## Automation Misconceptions to Avoid

### Use AI to approve standard-looking requests and send only privileged cases to humans.

**Why it is wrong or premature:** The model cannot currently use several central access attributes, and the organization has not defined complete criteria for sensitive, custom, API, SSO, dependent, or security-related routing. A standard-looking request could still require mandatory review.

**Safer alternative:** Use deterministic external rules to identify mandatory-review candidates and let AI prepare an advisory checklist without clearing any request from review.

**Evidence:** DOC-001, DOC-002, DOC-003, POLICY-001

### Once approval status says approved, an agent can provision access and update the ticket.

**Why it is wrong or premature:** The packet does not define approval-state semantics, required reviewer validation, delegations, allowed state transitions, or exception handling. Policy also requires recorded approvals and explicit human approval for writes.

**Safer alternative:** Allow AI to prepare a read-only provisioning and record-update proposal while authorized IT personnel and the identity analyst verify prerequisites and execute exact approved actions.

**Evidence:** DOC-001, DOC-002, DOC-003

### An empty required-control lookup means no additional controls are required.

**Why it is wrong or premature:** The explicit policy requires approvals, evidence preservation, additional review, and human authorization for writes. The empty lookup is inconsistent with those documented obligations.

**Safer alternative:** Fail closed and require the policy owner to resolve the control mappings before any production governed action.

**Evidence:** DOC-003, POLICY-002

## Operational Pattern Analysis

### Repeated validation followed by exception branching

**Operational dependency:** Identity analysts combine required-field checks, authoritative HR verification results, and indicators of privileged, sensitive, custom, API, SSO, security-related, or dependent access.

**AI opportunity created by this pattern:** AI can consistently organize externally generated validation results into deficiency checklists, discrepancy summaries, and reviewer questions.

**AI limitation created by this pattern:** The same attributes that drive useful analysis are sensitive or blocked, and the authoritative branching criteria are incomplete.

**What this means for the pilot:** The pilot should evaluate exception-packet quality from minimized validation metadata, not raw-request interpretation or autonomous routing.

**Evidence:** DOC-001, DOC-002, DOC-003, DOC-004, POLICY-001

### Multi-reviewer evidence assembly before a consequential action

**Operational dependency:** Application owners and security reviewers make accountable decisions, and provisioning waits for all applicable recorded outcomes.

**AI opportunity created by this pattern:** AI can reduce reviewer preparation effort by organizing evidence, unresolved questions, and missing prerequisites.

**AI limitation created by this pattern:** The model cannot substitute for reviewer judgment, validate undocumented authority, or treat generated text as approval evidence.

**What this means for the pilot:** Reviewer-packet preparation can be explored after the intake pilot, but approval outcomes and workflow advancement must remain human-recorded.

**Evidence:** DOC-001, DOC-002, DOC-003

### Administrative follow-through with audit consequences

**Operational dependency:** Provisioning, ticket updates, evidence retention, SLA escalation, and weekly reporting depend on accurate state and approved disclosure.

**AI opportunity created by this pattern:** AI can draft structured updates, candidate queues, and reports.

**AI limitation created by this pattern:** Even clerical errors can alter access, misstate workflow status, omit evidence, or disclose restricted information.

**What this means for the pilot:** Draft generation may be tested later, but execution and distribution must remain approval-gated and audited.

**Evidence:** DOC-001, DOC-002, DOC-003, POLICY-001

## Pilot Learning Objectives

### Determine whether minimized validation metadata is sufficient to produce useful intake exception packets.

**Why it matters:** If useful output requires blocked request content, the proposed architecture will not support the intended use case under the current policy boundary.

**How to test:** Compare AI-prepared packets with identity analyst-prepared packets across representative standard, privileged, and clarification cases while excluding blocked fields.

**Pass/fail signal:** Pass if analysts can complete review with fewer manual assembly steps and without repeatedly consulting omitted data solely to understand the packet; fail if outputs are routinely too generic or misleading.

**Expansion decision supported:** Whether to expand from document search and checklists into broader intake assistance.

**Evidence:** DOC-002, DOC-004, POLICY-001

### Verify that the context filter reliably blocks restricted fields and unsafe free text.

**Why it matters:** The pilot cannot be considered successful if productivity gains depend on prohibited data exposure.

**How to test:** Run representative and adversarial payloads containing identifiers, access details, privilege indicators, justifications, and notes through the pre-invocation filter and inspect model inputs and approved logs.

**Pass/fail signal:** Pass only if blocked fields are consistently excluded and filter failures are visible and fail closed.

**Expansion decision supported:** Whether any production model processing of workflow metadata is acceptable.

**Evidence:** DOC-004, POLICY-001

### Measure whether AI reduces analyst effort without increasing missed deficiencies or false conflict flags.

**Why it matters:** Faster packet preparation is not valuable if analysts must perform extensive corrections or if required clarification is missed.

**How to test:** Collect baseline and pilot handling time, reviewer corrections, false deficiency flags, missed deficiencies, and repeated clarification cycles.

**Pass/fail signal:** Pass if handling effort improves while error and correction measures remain within workflow-owner-approved acceptance thresholds.

**Expansion decision supported:** Whether the assistant should move from controlled evaluation to routine read-only use.

**Evidence:** DOC-002, DOC-003, DOC-004

### Confirm that every material output is traceable to an approved validation result or workflow requirement.

**Why it matters:** Reviewers must be able to distinguish evidence-backed findings from model inference before relying on summaries.

**How to test:** Require packet statements to cite the relevant required-field rule, external verification result, or documented workflow requirement and have analysts flag unsupported statements.

**Pass/fail signal:** Pass if material findings are consistently traceable and unsupported conclusions are detected before use.

**Expansion decision supported:** Whether to add reviewer summaries or advisory recommendations.

**Evidence:** DOC-002, DOC-003

### Identify which request patterns benefit from AI and which should bypass it.

**Why it matters:** Standard, privileged, and incomplete requests may have different preparation effort, correction rates, and risk.

**How to test:** Segment pilot measures by human-confirmed case type and compare usefulness, corrections, and time impact.

**Pass/fail signal:** Pass if the workflow owner can define a bounded population where benefit is repeatable and risk is controlled.

**Expansion decision supported:** Which request types should be included in later phases.

**Evidence:** DOC-002, DOC-003, DOC-004

## Autonomy Unlock Path

This path distinguishes the current safe posture from future autonomy that may become possible after process, data, and control changes.

### read_only_ai_assist → human_reviewed_recommendations

**Required changes:**
- Validate the model-context allowlist and redaction process.
- Create authoritative external validation-result formats.
- Document mandatory-review criteria and the sensitive-system inventory.
- Define reviewer-specific acceptance and correction procedures.
- Label all AI outputs as advisory and prevent recommendation-driven workflow advancement.

**Validation required:**
- No blocked fields appear in model context or inappropriate logs.
- Missed-deficiency, false-flag, correction, and traceability measures meet approved thresholds.
- Reviewers can identify the evidence supporting each material statement.
- No recommendation is recorded as an approval or security outcome.

**Risks that must be reduced:**
- Sensitive-data exposure
- Incorrect or missed review triggers
- Recommendations being mistaken for decisions
- Unsupported summaries

**Evidence:** DOC-001, DOC-002, DOC-003, DOC-004, POLICY-001

### human_reviewed_recommendations → approval_gated_actions

**Required changes:**
- Resolve required-control mappings.
- Define reviewer authorization and delegation validation.
- Document approval, rejection, and ticket-state semantics and allowed transitions.
- Define exact evidence prerequisites for each action.
- Implement exact-action human approval, durable audit records, and fail-closed execution.
- Define failure, correction, rollback, and exception procedures.

**Validation required:**
- No write or communication executes without the required named human approval.
- Provisioning fails closed when approvals or reviewer information are missing.
- Proposed and executed changes match exactly.
- Prior record history and approval evidence remain preserved.
- Unauthorized reviewers and invalid state transitions are rejected.

**Risks that must be reduced:**
- Unauthorized provisioning
- Invalid workflow advancement
- Evidence loss or misassociation
- Misdirected communication
- Uncontrolled write execution

**Evidence:** DOC-001, DOC-002, DOC-003, POLICY-002

### approval_gated_actions → limited_automation_candidate

**Required changes:**
- Restrict automation to scheduled read-only analytics and candidate-queue preparation.
- Define the SLA escalation threshold and approved report scope.
- Establish monitoring ownership, rollback procedures, and operating thresholds.
- Continue human approval for all decisions, writes, communications, provisioning, and report distribution.

**Validation required:**
- The automated scope contains no autonomous write or external communication path.
- False-alert, missed-alert, filter-failure, and correction measures remain acceptable.
- Rollback and disablement procedures are tested.
- Monitoring evidence is complete and reviewable.

**Risks that must be reduced:**
- Incorrect scheduled queue generation
- Undefined SLA interpretation
- Sensitive-data leakage in reports
- Unmonitored degradation

**Evidence:** DOC-001, DOC-002, DOC-003, POLICY-001, POLICY-002

## Sample Record Patterns

### Standard request versus exception-driven handling

**Records observed:** AR-1001, AR-1002, AR-1003

**What the pattern shows:** The illustrative records include one apparently standard read-only request, one privileged request awaiting security review, and one privileged request returned for incomplete or unclear information.

**AI opportunity:** A read-only assistant can normalize these cases into consistent analyst packets showing completeness results, external verification outcomes, unresolved items, and human review requirements.

**Risk or limitation:** Three illustrative records do not establish production frequencies, and the model must not infer that the standard-looking case is safe to approve or that the privilege field alone captures every review trigger.

**Recommended handling:** Use the three patterns as initial evaluation strata, then expand the test set with human-confirmed representative cases before drawing operational conclusions.

**Evidence:** DOC-004

### Privilege and clarification can coexist

**Records observed:** AR-1003

**What the pattern shows:** A request can require clarification while also carrying a privileged-access indicator.

**AI opportunity:** AI can prepare a deficiency packet while preserving the fact that higher-risk review may still be required after clarification.

**Risk or limitation:** A simplistic workflow could treat return-for-clarification as replacing the security-review requirement and lose the higher-risk routing obligation.

**Recommended handling:** Represent clarification needs and mandatory-review triggers as separate attributes rather than a single exclusive status.

**Evidence:** DOC-002, DOC-003, DOC-004

### Free-text ambiguity drives exception work

**Records observed:** AR-1001, AR-1002, AR-1003

**What the pattern shows:** Business justifications and notes range from standard explanations to emergency context and incomplete role mapping.

**AI opportunity:** If an approved protected handling method is established later, AI could help structure reviewer questions and summarize human-confirmed deficiencies.

**Risk or limitation:** Business justification and access details are blocked, and notes require redaction; unrestricted free-text ingestion is not ready.

**Recommended handling:** For the first pilot, use human-confirmed deficiency categories or redacted structured flags rather than raw justification and notes.

**Evidence:** DOC-004, POLICY-001

## Top Readiness Blockers

### CRITICAL — Decision-relevant data is blocked from model context

**Description:** The current classification prevents the model from receiving identifiers and several access attributes central to intake analysis and routing.

**Business impact:** A raw-request assistant would either violate the data boundary or generate low-value output from incomplete context.

**Technical/control impact:** A field-level allowlist, redaction layer, payload rejection, and externally computed validation metadata are prerequisites.

**Recommended remediation:**
- Confirm field mappings, including privilege and notes fields.
- Define the minimum model-context schema.
- Test redaction and rejection against representative records.
- Keep original requests and authoritative verification data outside the model.

**Likely owner:** Identity team with data governance review

**Evidence:** DOC-002, DOC-004, POLICY-001

### CRITICAL — Mandatory-review criteria are incomplete

**Description:** The workflow identifies categories requiring additional review but does not define a complete sensitive-system inventory or authoritative routing criteria.

**Business impact:** Requests could be delayed by excessive routing or exposed to risk by missed security review.

**Technical/control impact:** AI cannot safely clear a request from review; routing must remain human-controlled until deterministic rules exist.

**Recommended remediation:**
- Define each mandatory-review trigger.
- Establish ownership for the sensitive-system and routing reference data.
- Specify treatment of uncertain or conflicting indicators.
- Require fail-closed routing when criteria cannot be resolved.

**Likely owner:** Identity workflow owner with security reviewer

**Evidence:** DOC-001, DOC-002, DOC-003

### HIGH — Required-control mappings are unresolved

**Description:** The control service returned empty mappings for governed actions despite explicit workflow policy requirements.

**Business impact:** Production implementation teams lack a reliable control authorization basis and may interpret silence inconsistently.

**Technical/control impact:** Governed actions must fail closed until mappings and implementation evidence are confirmed.

**Recommended remediation:**
- Determine why the lookup returned empty results.
- Map each governed action to applicable controls.
- Define fail-closed behavior for unresolved lookups.
- Obtain policy-owner confirmation before production use.

**Likely owner:** Policy owner

**Evidence:** DOC-003, POLICY-002

### HIGH — Authority and state semantics are undocumented

**Description:** The packet does not define how authorized application owners, security reviewers, IT personnel, or delegations are validated, nor the allowed approval and ticket-state transitions.

**Business impact:** A technically correct recommendation could still be acted on by the wrong person or applied in the wrong workflow state.

**Technical/control impact:** Approval-gated actions cannot be reliably enforced without role validation and deterministic transition rules.

**Recommended remediation:**
- Define authorized reviewer sources and delegation rules.
- Document approval, rejection, and pending-state meanings.
- Define allowed state transitions and invalid-transition handling.
- Specify emergency and exception handling.

**Likely owner:** Workflow owner

**Evidence:** DOC-002, DOC-003

### HIGH — Measurement baselines and acceptance thresholds are missing

**Description:** The packet does not provide current handling time, clarification rates, error rates, correction rates, or approved thresholds for AI outputs.

**Business impact:** The organization cannot determine whether the pilot creates value or whether quality is sufficient for expansion.

**Technical/control impact:** There is no evidence-based release gate for moving beyond read-only evaluation.

**Recommended remediation:**
- Collect pre-pilot operational baselines.
- Define material-error and data-exposure criteria.
- Set workflow-owner-approved acceptance thresholds.
- Assign monitoring and correction ownership.

**Likely owner:** Workflow owner

**Evidence:** DOC-001, DOC-003

### MEDIUM — SLA and reporting operating rules are incomplete

**Description:** No threshold defines approaching the SLA deadline, and report content, recipient scope, and handling requirements are not fully specified.

**Business impact:** Automated queue preparation or reporting could generate inconsistent escalations or disclose unnecessary information.

**Technical/control impact:** SLA queues and report drafts cannot progress beyond bounded evaluation until these rules are approved.

**Recommended remediation:**
- Define the escalation threshold and unresolved-status criteria.
- Define report fields, aggregation level, recipient scope, and review requirements.
- Keep sending and distribution human-approved.

**Likely owner:** Identity team lead and security lead

**Evidence:** DOC-001, DOC-002, DOC-003, POLICY-001

## Process Redesign Requirements

### CRITICAL — Separate authoritative validation from AI explanation

**Current gap:** Useful validation currently depends on restricted request and HR data that should remain outside model context.

**Required change:** Create deterministic required-field, HR-verification, and policy-trigger checks outside the model and expose only approved result metadata to AI.

**Why this is required for AI readiness:** This preserves authoritative source checks while giving the assistant enough structured context to prepare useful analyst packets.

**Unlocks:**
- Read-only intake exception packets
- Discrepancy summaries
- Reviewer checklists

**Evidence:** DOC-002, DOC-004, POLICY-001

### CRITICAL — Codify mandatory-review routing

**Current gap:** Named risk categories lack complete authoritative criteria and reference data.

**Required change:** Define deterministic decision tables for privileged, sensitive, custom, API, SSO, dependency, elevated, and security-related conditions, including uncertain cases.

**Why this is required for AI readiness:** Neither AI nor conventional automation can safely route or clear requests consistently without explicit rules.

**Unlocks:**
- Reliable review-trigger flags
- Reviewer queue preparation
- Safer advisory triage

**Evidence:** DOC-001, DOC-002, DOC-003

### HIGH — Define authority and delegation rules

**Current gap:** The workflow names reviewer roles but does not define how authorized individuals or delegations are validated.

**Required change:** Document the authoritative basis for application-owner, security-reviewer, authorized IT, identity-analyst, and delegated authority.

**Why this is required for AI readiness:** Approval-gated actions are not meaningful unless the system can verify that the approver is authorized for the specific action.

**Unlocks:**
- Reviewer-specific queues
- Approval-gated routing
- Controlled action execution

**Evidence:** DOC-002, DOC-003

### HIGH — Define workflow states and transitions

**Current gap:** Approval, rejection, pending, clarification, and ticket-state semantics and allowed transitions are not documented.

**Required change:** Specify allowed states, transition prerequisites, actor authority, evidence requirements, and invalid-transition handling.

**Why this is required for AI readiness:** Draft updates and approval-gated writes cannot be validated without an authoritative state model.

**Unlocks:**
- Structured update proposals
- Deterministic transition validation
- Approval-gated record updates

**Evidence:** DOC-002, DOC-003

### MEDIUM — Define SLA and reporting operating rules

**Current gap:** The escalation threshold, report contents, disclosure scope, and detailed handling requirements are unspecified.

**Required change:** Approve the SLA threshold, unresolved-status criteria, report fields, aggregation level, recipient scope, and review requirements.

**Why this is required for AI readiness:** Candidate queues and reports will otherwise be inconsistent or disclose unnecessary information.

**Unlocks:**
- SLA candidate queues
- Escalation drafts
- Weekly report drafts

**Evidence:** DOC-001, DOC-002, DOC-003, POLICY-001

### HIGH — Define evidence lifecycle and exception handling

**Current gap:** Retention duration, storage, disposal, emergency handling, correction, and failure procedures are not provided.

**Required change:** Document evidence lifecycle rules and procedures for emergency requests, failed actions, corrections, rollback, and disputed AI output.

**Why this is required for AI readiness:** Higher autonomy cannot preserve auditability or recover safely from errors without these operating rules.

**Unlocks:**
- Durable audit design
- Controlled record updates
- Approval-gated action recovery

**Evidence:** DOC-001, DOC-002, DOC-003

## Control Gap Remediation Plan

### CRITICAL — Model-context boundary enforcement

**Current gap:** Restricted fields could enter the model unless filtering is implemented and field mappings are confirmed.

**Risk if unresolved:** Exposure of PII, confidential access details, approval evidence, or provisioning information.

**Recommended control:** Use a field-level allowlist, pre-invocation redaction, payload rejection, approved metadata-only logging, and tests for the privilege and notes field mappings.

**Validation method:** Inspect model inputs and logs from representative and adversarial test payloads and verify fail-closed behavior.

**Evidence:** DOC-004, POLICY-001

### HIGH — Unresolved required-control mappings

**Current gap:** The control lookup returned empty mappings for all queried governed actions.

**Risk if unresolved:** Teams may deploy governed capabilities without confirmed policy coverage.

**Recommended control:** Require policy-owner resolution and fail closed whenever applicable controls cannot be determined.

**Validation method:** Verify that each proposed action has an approved control mapping and that unmapped actions are blocked.

**Evidence:** DOC-003, POLICY-002

### CRITICAL — Deterministic mandatory-review routing

**Current gap:** Review triggers are described but not fully defined.

**Risk if unresolved:** Privileged or sensitive requests could bypass required review.

**Recommended control:** Maintain authoritative routing criteria and reference data outside the model; allow AI to flag possible triggers but never clear review.

**Validation method:** Test the routing rules against human-confirmed standard, privileged, sensitive, custom, and ambiguous cases.

**Evidence:** DOC-001, DOC-002, DOC-003

### HIGH — Reviewer authority and exact-action approval

**Current gap:** Reviewer and delegation validation is undefined.

**Risk if unresolved:** An unauthorized person could approve a decision or action.

**Recommended control:** Verify reviewer authority for the specific request and require approval of the exact proposed action, recipient, or record change.

**Validation method:** Test authorized, unauthorized, delegated, expired, and mismatched reviewer scenarios.

**Evidence:** DOC-002, DOC-003

### CRITICAL — Pre-provisioning verification

**Current gap:** Recorded approval and reviewer prerequisites are not expressed as deterministic executable checks.

**Risk if unresolved:** Access could be provisioned without all applicable approvals.

**Recommended control:** Use an external fail-closed gate that verifies recorded application-owner approval, security outcome when applicable, reviewer information, and specific authorized IT approval.

**Validation method:** Attempt provisioning proposals with missing, conflicting, invalid, and complete approval evidence and confirm only complete cases can reach human execution.

**Evidence:** DOC-001, DOC-002, DOC-003

### HIGH — Evidence-preserving write validation

**Current gap:** Exact state-transition, evidence-validation, and history-preservation behavior is not defined.

**Risk if unresolved:** Ticket updates could overwrite, omit, or misassociate approval and provisioning evidence.

**Recommended control:** Validate exact proposed changes, required evidence references, allowed transitions, and reviewer identity while preserving prior values and durable audit history.

**Validation method:** Test valid and invalid writes, concurrent corrections, missing evidence, and audit-history preservation.

**Evidence:** DOC-002, DOC-003, POLICY-001

### HIGH — Human-reviewed communication execution

**Current gap:** Clarification, escalation, and reporting drafts could be inaccurate, misdirected, or over-disclose information.

**Risk if unresolved:** Restricted information or incorrect workflow messages could be sent.

**Recommended control:** Require human verification of facts, recipient, disclosure scope, and exact content before any controlled communication.

**Validation method:** Test incorrect recipients, excessive disclosure, unsupported facts, and unapproved versions and confirm they cannot be sent.

**Evidence:** DOC-002, DOC-003, POLICY-001

## Value Hypotheses

These are directional hypotheses to test during a controlled pilot, not guaranteed ROI claims.

### Identity analyst productivity

**Hypothesis:** Structured AI-prepared intake exception packets will reduce the time analysts spend assembling completeness and discrepancy information.

**Expected directional impact:** Lower preparation effort without transferring verification or decision authority to AI.

**Required measurements:**
- Packet-preparation time
- Total intake handling time
- Analyst review time
- AI output correction time

**Baseline data needed:**
- Current time spent preparing intake and deficiency summaries
- Current case volume by human-confirmed pattern
- Current rework time

**Evidence:** DOC-001, DOC-002, DOC-003

### Intake quality

**Hypothesis:** Consistent checklist and deficiency-packet preparation will reduce avoidable omissions and repeated clarification cycles.

**Expected directional impact:** Fewer missed required fields and fewer clarification exchanges caused by incomplete deficiency descriptions.

**Required measurements:**
- Missed-deficiency rate
- False-deficiency rate
- Clarification return rate
- Number of clarification cycles per returned request

**Baseline data needed:**
- Current deficiency categories
- Current clarification frequency
- Current repeated-clarification frequency

**Evidence:** DOC-002, DOC-003, DOC-004

### Reviewer readiness

**Hypothesis:** Evidence-linked summaries will reduce the effort required for application-owner and security-review preparation.

**Expected directional impact:** Faster reviewer orientation and fewer follow-ups for missing evidence, while decisions remain human-controlled.

**Required measurements:**
- Reviewer preparation time
- Missing-evidence follow-ups
- Summary correction rate
- Unsupported-statement rate

**Baseline data needed:**
- Current reviewer preparation time
- Current follow-up frequency
- Current evidence-deficiency types

**Evidence:** DOC-001, DOC-002, DOC-003

### SLA visibility

**Hypothesis:** After an escalation threshold is defined, a read-only candidate queue will reduce manual backlog-review effort and improve consistency.

**Expected directional impact:** More consistent identification of near-deadline unresolved requests without autonomous escalation.

**Required measurements:**
- Queue preparation time
- Missed candidate rate
- False candidate rate
- Age of unresolved requests at human escalation

**Baseline data needed:**
- Current backlog-review effort
- Current escalation timing
- Current missed or late escalation occurrences

**Evidence:** DOC-001, DOC-002, DOC-003

### Auditability

**Hypothesis:** Evidence-linked AI outputs and exact-action approval records will improve the traceability of analyst preparation and later governed actions.

**Expected directional impact:** Fewer unsupported summaries and clearer linkage between evidence, reviewer decisions, and approved actions.

**Required measurements:**
- Evidence traceability rate
- Unsupported-statement rate
- Missing reviewer metadata rate
- Incomplete audit-event rate

**Baseline data needed:**
- Current evidence completeness
- Current reviewer metadata completeness
- Current audit exception types

**Evidence:** DOC-002, DOC-003

## Measurement Plan

### Intake packet preparation time

**Why it matters:** Tests the primary productivity hypothesis without relying on approval outcomes.

**How to measure:** Compare analyst time for current preparation with time to review and correct AI-prepared packets for comparable human-confirmed case types.

**Baseline required:** True

**Target or success signal:** A repeatable reduction in preparation effort without deterioration in deficiency accuracy.

### Missed-deficiency rate

**Why it matters:** A missed required or conflicting item can cause incorrect advancement or later rework.

**How to measure:** Count human-confirmed deficiencies absent from the AI packet divided by all human-confirmed deficiencies.

**Baseline required:** True

**Target or success signal:** No material increase from current analyst performance and performance within an approved acceptance threshold.

### False-deficiency rate

**Why it matters:** False flags create unnecessary clarification and analyst work.

**How to measure:** Count AI-flagged deficiencies rejected by the identity analyst and segment by deficiency category.

**Baseline required:** True

**Target or success signal:** A correction burden low enough that net analyst effort improves.

### Reviewer correction rate

**Why it matters:** Shows whether outputs are usable or merely shift work into editing.

**How to measure:** Track packets requiring material additions, removals, or factual corrections.

**Baseline required:** True

**Target or success signal:** Material corrections decline during the pilot and remain within an approved threshold.

### Evidence traceability rate

**Why it matters:** Reviewers must be able to verify material statements.

**How to measure:** Sample material packet statements and determine whether each links to an approved validation result or documented requirement.

**Baseline required:** False

**Target or success signal:** Material statements are consistently evidence-linked before expansion.

### Clarification cycles per returned request

**Why it matters:** A complete deficiency packet should reduce repeated requests for missing information.

**How to measure:** Count manager clarification exchanges from initial return until intake is complete.

**Baseline required:** True

**Target or success signal:** A directional reduction without over-requesting unnecessary information.

### Blocked-field exposure rate

**Why it matters:** Any productivity gain is unacceptable if restricted data enters model context.

**How to measure:** Inspect filtered payloads and approved model-input logs for blocked fields and unsafe free text.

**Baseline required:** False

**Target or success signal:** No blocked fields reach model context; any filter uncertainty fails closed.

### Analyst usefulness by case type

**Why it matters:** Standard, privileged, and clarification cases may benefit differently.

**How to measure:** Collect a structured analyst assessment and correction burden for each human-confirmed case type.

**Baseline required:** False

**Target or success signal:** At least one bounded case population shows repeatable usefulness sufficient to justify routine read-only use.

### Mandatory-review trigger miss rate

**Why it matters:** Later advisory triage must not conceal requests requiring application-owner or security review.

**How to measure:** Compare AI flags with human-confirmed outcomes from authoritative routing criteria after those criteria are documented.

**Baseline required:** True

**Target or success signal:** Meets a workflow-owner-approved threshold before any triage expansion; AI never clears review on its own.

### Governed-action control failure rate

**Why it matters:** Any later action capability must reliably reject missing approval, invalid authority, or invalid state.

**How to measure:** Run controlled negative tests for missing approvals, unauthorized reviewers, invalid transitions, and mismatched actions.

**Baseline required:** False

**Target or success signal:** All invalid governed actions fail closed before approval-gated capabilities are introduced.

## Questions for the Workflow Owner

- **CRITICAL** — Which exact fields and derived validation results may be sent to the approved model environment, and what retention and logging behavior is permitted?
  - Why it matters: The first pilot cannot be designed until the usable model-context boundary is explicit.
  - Answer needed for: Pilot input schema, Redaction design, Logging design
- **CRITICAL** — Can deterministic services produce field-presence, HR-verification, and discrepancy results without exposing the underlying restricted values to the model?
  - Why it matters: The recommended pilot depends on transforming sensitive source data into approved validation metadata.
  - Answer needed for: First pilot feasibility, Context minimization, Authoritative verification boundary
- **CRITICAL** — What is the authoritative inventory of sensitive systems, and what are the complete criteria for privileged, custom, API, SSO, dependency, elevated, and security-related review?
  - Why it matters: These rules determine mandatory review and cannot be safely inferred by AI.
  - Answer needed for: Routing rules, Reviewer queues, Later advisory triage
- **HIGH** — How are authorized application owners, security reviewers, IT personnel, identity analysts, and delegations validated for a specific request?
  - Why it matters: An approval gate is ineffective if reviewer authority cannot be verified.
  - Answer needed for: Reviewer-specific workflows, Approval-gated actions, Audit evidence
- **HIGH** — What do each approval and ticket status mean, and which transitions are allowed from each state?
  - Why it matters: Structured update proposals and action gates require deterministic state semantics.
  - Answer needed for: Workflow advancement, Record-update validation, Failure handling
- **HIGH** — Why did the required-control lookup return empty mappings, and who can approve the corrected mappings?
  - Why it matters: Empty mappings cannot serve as authorization for production capabilities.
  - Answer needed for: Production control design, Governed action approval, Fail-closed behavior
- **MEDIUM** — What threshold defines a request as approaching its SLA deadline, and which unresolved statuses qualify?
  - Why it matters: Without this rule, candidate escalation queues will be inconsistent.
  - Answer needed for: SLA queue preparation, Escalation drafts, SLA measurement
- **HIGH** — What evidence is required for approval, security review, provisioning, rejection, status change, escalation, and report distribution, and how long must it be retained?
  - Why it matters: Evidence completeness and retention determine whether later actions are safe and auditable.
  - Answer needed for: Evidence-linked summaries, Pre-provisioning gates, Record updates, Audit design
- **MEDIUM** — What are the approved contents, aggregation level, recipient scope, and handling rules for the weekly access review report?
  - Why it matters: Draft reporting cannot be safely evaluated without a defined disclosure boundary.
  - Answer needed for: Report-generation pilot, Data minimization, Distribution approval
- **HIGH** — What emergency, exception, correction, rollback, and failed-action procedures apply to this workflow?
  - Why it matters: Higher autonomy requires a safe human path when normal prerequisites or automated checks fail.
  - Answer needed for: Production operations, Approval-gated actions, Rollback design
- **HIGH** — What current handling-time, clarification, error, rework, and SLA measures can be baselined before the pilot?
  - Why it matters: Without baseline data, the organization cannot distinguish useful assistance from added review overhead.
  - Answer needed for: Value measurement, Pilot success criteria, Expansion decision
- **HIGH** — What correction, missed-deficiency, false-flag, traceability, and data-exposure thresholds must the pilot meet before expansion?
  - Why it matters: The workflow needs explicit evidence-based release gates rather than subjective confidence in model output.
  - Answer needed for: Pilot pass or fail, Scope expansion, Monitoring and rollback

## Evidence Catalog

- **DOC-001** — Evidence item
  - # Process Narrative The access request review workflow manages employee requests for application, data, and system access. Managers submit access requests for employees who need new or changed permissions. The identity team reviews required intake fields, verifies employee information against the HR system, and checks whether the request involves privileged access, sensitive systems, custom roles, APIs, or security-related permissions. Requests with missing, unclear, or conflicting informatio...
- **DOC-002** — Evidence item
  - # Current Workflow Steps 1. Manager submits an access request for an employee, including employee identifier, requested system, access level, business justification, and required fields. 2. Identity analyst verifies employee identifier, employee email, manager email, role, and employment status against the HR source system. 3. Identity analyst reviews the request for privileged access, sensitive systems, custom permissions, APIs, SSO, security requirements, or system access dependencies. 4. M...
- **DOC-003** — Evidence item
  - # Policy and Controls - Access requests require a valid employee identifier, manager, requested system, access level, and business justification. - Requests with missing, unclear, incomplete, or conflicting intake information must be routed back for clarification. - Privileged access requires application owner approval and security review. - Access to sensitive systems requires additional review before provisioning. - Provisioning actions must not occur until required approvals are recorded. ...
- **DOC-004** — Evidence item
  - request_id,employee_identifier,employee_email,manager_email,requested_system,access_level,business_justification,approval_status,ticket_status,sla_due_date,contains_privileged_access,notes AR-1001,E-48191,alex.rivera@example.com,manager.one@example.com,Customer Data Warehouse,read_only,Needs access for monthly reporting,pending_review,intake_complete,2026-08-15,false,Manager provided standard reporting justification AR-1002,E-57203,jordan.lee@example.com,manager.two@example.com,Production Adm...
- **POLICY-001** — Evidence item
  - Policy-server classifications for workflow data elements.
- **POLICY-002** — Evidence item
  - Policy-server required-control lookup results for governed workflow actions.
