# GMP Policy Gate

The gate decides whether the agent may act, must ask, or must refuse. In a regulated plant that decision is not a design preference. Most of it is written down, and citing the rule beats defending an opinion.

This file answers four questions the rest of the folder does not: what an audit trail must contain, what a signature means, who is allowed to approve what, and what counts as a change to a validated system.

GAMP references are to the **second edition (ISPE, 2022)**. Page numbers differ from the 2008 first edition and one appendix used here was retired; see the edition note at the end.

## Classify the action first

Every rule downstream depends on this. GAMP 5 2nd ed, App O6 §38.4.3, p. 307 names five types of change, and your three on-screen options are three different ones. That is what makes the gate defensible rather than arbitrary.

```
  GAMP TYPE                      YOUR OPTION            CONTROL PATH
  ─────────                      ───────────            ────────────
  Like-for-Like Replacement      C: shutdown +          lowest. components
  or Repair                         bearing inspect     pre-approved during
  p. 307                                                initial validation.
  "typically low-risk"                                  record the repair AND
  "triggered by the incident                            its verification.
   and problem management
   process following the
   detection of a failure"

  Temporary Change               B: turret 46 → 35      carries a ROLLBACK
  p. 307                            RPM until planned   OBLIGATION. must be
  "planned to be in place            intervention       rolled back and
   for a limited period"                                reviewed through formal
  "particular attention                                 change management
   to the reversal"                                     before becoming
                                                        permanent.

  Standard/Routine Change        diagnostic-only        pre-defined work
  p. 307                            reads               instruction. record it.

  Emergency Change               only if delay itself   criteria must be
  p. 307                            causes greater      defined BEFORE the
                                    harm                incident. may need
                                                        retrospective
                                                        documentation.

  (not a change at all)          A: keep running        DEVIATION.
                                    outside the limit   21 CFR 211.100(b):
                                                        recorded and justified.
```

**Two build consequences, both cheap and both easy to miss.**

Option B is a Temporary Change, so your incident object needs a rollback field: when does the reduced speed get reviewed, and who reverses it. A temporary change with no reversal plan is the failure mode the regulation calls out by name. Add `rollback_review_by` to the schema at 0:00.

Option C is triggered by incident and problem management, which is precisely what your agent is. That means your agent is not bolted onto the change process, it sits at its documented entry point. Say that in the pitch.

## Who approves what

Two regimes, and they agree.

**US regulation, the binding part:**

- **21 CFR 211.22** gives the quality control unit the responsibility and authority to approve or reject procedures and specifications affecting identity, strength, quality and purity, and to review production records.
- **21 CFR 211.100(a)** requires production and process control procedures, *including any changes*, to be drafted, reviewed and approved by the appropriate organizational units **and** reviewed and approved by the quality control unit.
- **21 CFR 211.68(b)** requires changes to master production and control records to be "instituted only by authorized personnel."

**GAMP 5 2nd ed, App O6 §38.4.1, p. 305** splits operational change four ways, which is more useful than the regulation because it separates the technical owner from the process owner:

```
  Process Owner       ensures the change control and configuration
                      management process and procedures exist
  System Owner        coordinates changes, evaluates technical impact
  Quality Unit        ensures the process and procedures are followed
  Task/Action Owners  ensure completion within defined timelines
```

So a two-approver gate is structural, not stylistic: the operating unit approves the intervention, the quality unit approves that the process was followed and the batch position is sound. Model it as an AND-join. One signature must not satisfy it.

## What a signature has to show

**21 CFR 11.50** requires a signed electronic record to display the printed name of the signer, the date and time of signing, and **the meaning of the signing** (review, approval, responsibility, or authorship). **11.70** requires signatures to be linked to their records so they cannot be excised, copied, or transferred.

GAMP says the same thing independently: **App M1 §5.2** requires that "the meaning of each approval signature should be defined."

Two approvers both labelled "Approved" is what this rule exists to prevent.

```
  Maintenance Supervisor    "intervention approved"
  Quality Assurance         "batch disposition reviewed"
  + printed name, timestamp, and meaning stored on each
```

## What the audit trail must contain

**21 CFR 11.10(e)** requires secure, computer-generated, time-stamped audit trails that independently record the date and time of operator entries and actions that create, modify, or delete electronic records, and requires that record changes not obscure previously recorded information.

**EU GMP Annex 11 ¶9** adds that for any change or deletion of GMP-relevant data the *reason* is documented, and that audit trails are convertible to an intelligible form and regularly reviewed.

The FDA data integrity guidance is explicit that review frequency is risk-based rather than fixed, so you state your frequency and justify it instead of guessing a number someone can call wrong.

Minimum fields, and this is the shape to write into the schema:

```
  who      user identity, not a shared login
  what     the action, and the record it touched
  when     system-generated timestamp, not user-entered
  why      the reason for the change or override
  before   the prior value, still readable afterwards
```

`why` and `before` are the two everyone forgets and the two an inspector opens first.

For a repair specifically, GAMP O6 p. 307 adds one more: **verification of successful repair or replacement should also be recorded.** Your post-intervention telemetry check is that record. If you cut the verification step for time, cut it knowing it is the field a regulated buyer would ask for.

## Your architecture is static and supervised, and that is an argument

GAMP 5 2nd ed added **Appendix D11, Artificial Intelligence and Machine Learning, p. 269**. Most of it covers training models, which you are not doing. One distinction on **p. 278** is the part that matters, and it is a pitch line:

```
  STATIC + SUPERVISED                      DYNAMIC or UNSUPERVISED
  offline. changes to the case data        online learning. model
  and algorithm are controlled and         parameters update during
  identifiable. data acquisition and       operation. or data that
  annotation validated before              cannot be validated piece
  inclusion.                               by piece.
        |                                        |
        v                                        v
  "standard data validation                "will require additional
   change-management processes             controls such as continual
   should be sufficient"                   and robust performance
                                           evaluation"
```

Your build is the left column: a stock open-weights model, no training during operation, a curated corpus validated before ingestion. Under D11 that keeps you inside ordinary change control instead of obliging you to stand up a continual performance-evaluation regime.

That turns a constraint into a design choice. You already decided not to fine-tune because the build-window rule forbids bringing a trained artifact. Now it has a second, better reason, and the second reason is the one to say out loud to judges.

D11 also gives the framing for your metrics: performance metrics "act as the technical specifications for the acceptability of the ML model" (p. 270). That is GAMP telling you the numbers are the spec, not a report card written afterwards. It is the same rule `proving-it-works-and-pitching-it.md` states, from a source a pharma judge already respects.

In all cases D11 requires periodic review and monitoring of model performance to identify bias and overfitting (p. 278). Periodic review is **App O8, p. 313**.

## Writing the rules so they actually run

Regulatory prose is full of words that are not predicates. Decompose until every leaf is checkable against a field that exists in your incident object.

```
  NOT IMPLEMENTABLE          IMPLEMENTABLE
  ─────────────────          ─────────────
  "quality may be            any measured CQA-linked parameter
   affected"                 outside its approved limit
                             → weight_rsd_pct > tolerance
                             OR vibration > max_vibration

  "significant               proposed value outside the qualified
   parameter change"         range for the running product
                             → new_rpm NOT IN qualified_speed_range

  "appropriate               approver_role IN required_approvers
   approval"                 AND all required roles signed
```

A worked rule set, in dependency order:

1. Any monitored parameter outside its approved limit: autonomous continuation is **DENY**. The machine is outside its qualified state and that is a deviation regardless of anything else.
2. Action classifies as **repair or like-for-like replacement**, no specification changes: **HUMAN_APPROVAL**, operating unit approves. Record the repair and its verification.
3. Action classifies as **temporary change** and the proposed value is inside the qualified range: **HUMAN_APPROVAL**, operating unit and quality unit both approve, and the record carries a rollback review date. No rollback date means the gate returns **DENY**, because a temporary change with no reversal plan is not a temporary change.
4. Proposed value **outside the qualified range**: **DENY** the autonomous path. Surface it as requiring a change-control record, not an approval click.
5. A batch is running and any CQA-linked parameter has moved: flag for quality-unit disposition. The agent never declares a batch acceptable or unacceptable; it flags and routes.
6. Diagnostic-only action that reads data, changes nothing and stops nothing: **ALLOW** autonomously and log it as a standard/routine change.

Rule 5 keeps the system honest. Batch disposition is a quality-unit judgment under 211.22, and an agent that makes it has taken a decision the regulation assigns to a person.

Rule 3's rollback clause is the one nobody else in the room will have.

## Say "designed against," never "compliant"

Part 11 applies to electronic records a predicate rule requires you to keep. A demo is not a regulated system and has no validation package. The accurate claim is that the gate is *designed against* 21 CFR Part 11, 211.22, 211.100 and GAMP 5's change-control model. That claim is checkable and survives questioning. "Compliant" invites a request for documentation you do not have.

Label synthetic plant data as simulated everywhere it appears, including in the audit log.

## Eval

- Actions classified into a named GAMP change type before any rule runs: target 100%
- Rules whose leaves reference a field that exists in the incident schema: target 100%
- Rules containing an unevaluable phrase (may, appropriate, significant, adequate): target 0
- Temporary changes approved without a rollback review date: target 0
- Approver roles required by a rule that map to a named regulatory or GAMP basis: target 100%
- Signature records carrying name, timestamp and a distinct meaning: target 3 of 3 fields, 0 duplicate meanings
- Audit entries carrying who / what / when / why / prior value: target 5 of 5
- Repairs recorded without a verification entry: target 0
- Batch-disposition decisions taken autonomously by the agent: target 0
- Qualified-range fields present in the schema for every parameter a rule tests: target 100%
- Uses of the word "compliant" in the pitch or UI: target 0
- Synthetic data displayed without a simulated-data label: target 0

## Sources

- **21 CFR Part 11** — Electronic Records; Electronic Signatures. 11.10(e) audit trails, 11.50 signature manifestations, 11.70 signature-record linking.
- **21 CFR Part 211** — cGMP for Finished Pharmaceuticals. 211.22 quality control unit, 211.68 automatic/mechanical/electronic equipment, 211.100 written procedures and deviations.
- **FDA, Data Integrity and Compliance With Drug CGMP: Questions and Answers**, final guidance, December 2018.
- **EU GMP Annex 11, Computerised Systems**, European Commission, 2011 version in force. ¶9 audit trails, ¶10 change and configuration management, ¶11 periodic evaluation. EU, not FDA. Say which when citing.
- **ISPE, GAMP 5: A Risk-Based Approach to Compliant GxP Computerized Systems, Second Edition**, 2022, ISBN 978-1-946964-57-1.
  - App M1 §5.2 — approval roles, meaning of each approval signature
  - App M8 — Project Change and Configuration Management
  - App D11, p. 269 — Artificial Intelligence and Machine Learning; static/supervised vs dynamic/unsupervised at p. 278; metrics as technical specification at p. 270
  - App O4, p. 295 — Incident Management and Problem Management
  - App O6, p. 303 — Operational Change and Configuration Management; responsibilities §38.4.1 p. 305; types of change §38.4.3 p. 307; configuration baseline as the reference for the validated state p. 309
  - App O8, p. 313 — Periodic Review
- **Joint US FDA / Health Canada / UK MHRA, Good Machine Learning Practice for Medical Device Development: Guiding Principles** — cited by D11 as reference [78]. Free, short, and the right citation for using AI responsibly in a regulated context.

**Edition notes.** GAMP 5 2nd ed retired **Appendix O7 (Repair Activity)**; repair requirements now live in O6 under Types of Change, p. 307. **Appendix S5** is also retired. The 2nd ed added D8 Agile, D10 Distributed Ledger, and D11 AI/ML, plus a "critical thinking" theme running through the main body. Cite as "GAMP 5 (2nd ed., 2022)" so the year never becomes the thing you get corrected on.

**One practical note.** The 2022 PDF in hand carries a personal licence watermark for another named individual. Cite it freely; do not redistribute the file to the team folder or the judges.
