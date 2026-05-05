# Corvus 30-Day Design Partner And Accelerator Plan

Dates: May 4, 2026 to June 2, 2026

Primary outcome by June 2, 2026:
- [ ] One active manufacturing or aerospace design partner has agreed to a structured pilot or discovery sprint.
- [ ] Corvus has a credible accelerator application package: narrative, demo, customer discovery evidence, product plan, and founder thesis.
- [ ] Corvus Debrief can clearly show how messy production data turns into a useful daily manufacturing summary.

Operating principle:
Corvus should stay narrow enough to ship and learn, but credible enough that a serious manufacturing leader can see the larger system. The goal is not to build every connector, agent, or workflow in 30 days. The goal is to prove that the product can ingest real operational data, explain what changed, and help a team make better production decisions.

## Week 1: Positioning, Target User, And Demo Shape

Dates: May 4 to May 10, 2026

Expected outcome:
- [ ] Corvus has a crisp wedge: who it helps, what data it starts with, what meeting or workflow it improves, and why now.
- [ ] There is a believable design partner list and outreach message.
- [ ] The demo scope is locked for the month.

Why this matters:
Without a tight wedge, Corvus can accidentally become "AI for manufacturing data," which sounds big but is hard to buy. A design partner needs to understand the first useful job Corvus will do for them.

### Product And Strategy

- [ ] Define the first wedge in one sentence.
  - Suggested version: "Corvus turns messy production exports from MES, ERP, and shop-floor systems into an evidence-backed daily debrief for manufacturing leaders."
  - Rationale: This keeps the product focused on debriefing and decision support, not generic dashboards or broad factory automation.

- [ ] Define the first buyer/user profile.
  - Primary user: production manager, operations manager, manufacturing engineer, program manager, or startup hardware/manufacturing founder.
  - First customer profile: small to mid-sized aerospace, defense, hardware, or precision manufacturing company with messy production tracking.
  - Rationale: These users feel the pain but may still be reachable without enterprise sales cycles.

- [ ] Pick the first workflow Corvus owns.
  - Recommended workflow: daily production debrief or weekly operations review.
  - Inputs: work orders, operations, notes, delays, scrap/rework flags, material constraints.
  - Outputs: summary, blockers, risks, follow-ups, and evidence.
  - Rationale: A recurring meeting creates a clear reason to use the product repeatedly.

- [ ] Write the "not yet" list.
  - Not yet: full MES replacement.
  - Not yet: machine control.
  - Not yet: predictive maintenance.
  - Not yet: full quality management system.
  - Not yet: universal connector marketplace.
  - Rationale: This protects the 30-day plan from scope creep.

### Customer Discovery

- [ ] Build a list of 25 possible design partner leads.
  - Include: aerospace suppliers, machine shops, hardware startups, operations consultants, manufacturing engineers, plant managers, and founders in your network.
  - Rationale: You need enough outreach volume to get one serious yes.

- [ ] Create a short lead tracker.
  - Fields: company, contact, role, source, manufacturing type, likely pain, outreach date, response, next step, notes.
  - Rationale: Customer discovery gets real when it is tracked like a pipeline.

- [ ] Draft a short design partner ask.
  - Goal: ask for a 30-minute conversation and permission to test Corvus on sample or anonymized operational data.
  - Rationale: Do not lead with "pilot" too early. Lead with a low-friction learning ask.

### Build

- [ ] Freeze the month-one demo path.
  - Recommended path: CSV upload or sample dataset -> source classification -> schema mapping -> canonical records -> domain agents -> debrief summary.
  - Rationale: This demonstrates the architecture without requiring live integrations.

- [ ] Create or refine two demo datasets.
  - Dataset 1: clean MES-style work order export.
  - Dataset 2: messy real-world export with inconsistent headers, missing fields, notes, delays, and quality/material signals.
  - Rationale: Robustness is more convincing than a perfect toy file.

## Week 2: Design Partner Outreach And Product Proof

Dates: May 11 to May 17, 2026

Expected outcome:
- [ ] At least 10 outbound conversations or requests have been sent.
- [ ] At least 3 discovery calls are scheduled or completed.
- [ ] Corvus can produce a strong debrief from a messy manufacturing CSV.

Why this matters:
Week 2 should force reality into the product. The questions people ask, the files they mention, and the workflows they describe should shape what gets built.

### Customer Discovery

- [ ] Send 10 direct outreach messages.
  - Target: people close enough to manufacturing operations to have real data pain.
  - Rationale: You are looking for signal, not approval.

- [ ] Ask the same five questions in each discovery call.
  - What production meeting or report is most painful right now?
  - What systems hold the data for that meeting?
  - What exports, reports, or screenshots do people use today?
  - What decisions are delayed because the data is messy or scattered?
  - If Corvus worked, what would you expect to see every morning or every week?
  - Rationale: Repeated questions make patterns easier to spot.

- [ ] Ask for sample data, even if anonymized.
  - Acceptable: CSV export, Excel report, screenshot, report template, fake-but-realistic sample, or column headers only.
  - Rationale: The shape of their data matters as much as what they say.

### Build

- [ ] Add a "source confidence" display to the demo output.
  - Show: detected source type, mapped fields, unmapped fields, missing critical fields, and confidence.
  - Rationale: Manufacturing users need to trust how Corvus interpreted their file.

- [ ] Improve evidence-backed debrief output.
  - Each finding should include: claim, supporting rows/fields, severity, and suggested follow-up.
  - Rationale: A useful debrief should be auditable, not magical.

- [ ] Create a saved example report.
  - Include: executive summary, work order status, blockers, quality/material signals, and next actions.
  - Rationale: This becomes the artifact you can send after calls.

### Accelerator Prep

- [ ] Start the accelerator application source folder.
  - Include: one-liner, founder thesis, problem, customer, product, traction, market, why now, demo link, and roadmap.
  - Rationale: Applications get stronger when evidence is collected during the month, not written at the end.

## Week 3: Pilot Packaging And Credibility

Dates: May 18 to May 24, 2026

Expected outcome:
- [ ] One high-probability design partner is identified.
- [ ] Corvus has a simple pilot offer.
- [ ] The demo is credible enough to show live.

Why this matters:
This week turns interest into a concrete next step. The partner should know what they give you, what Corvus gives them, and how long the first experiment takes.

### Design Partner Packaging

- [ ] Write a one-page design partner brief.
  - Include: problem, what Corvus will test, data needed, timeline, expected output, confidentiality posture, and success criteria.
  - Rationale: A one-page brief makes the ask feel professional without making it heavy.

- [ ] Define a 2-week pilot shape.
  - Day 1: collect sample exports and understand workflow.
  - Days 2-4: map data and generate first debrief.
  - Days 5-7: review output with user and tune.
  - Week 2: run recurring debrief on updated data or a second dataset.
  - Rationale: A short pilot is easier to accept and easier to learn from.

- [ ] Define pilot success criteria.
  - Example: Corvus identifies top blockers with 80% user agreement.
  - Example: Corvus reduces debrief prep time from hours to minutes.
  - Example: Corvus finds one missed risk or follow-up.
  - Rationale: Design partners need a clear reason to continue.

### Build

- [ ] Add a lightweight "design partner mode" demo.
  - Should show: upload/intake status, mapping review, generated debrief, and exportable report.
  - Rationale: This makes the architecture understandable to non-technical stakeholders.

- [ ] Add a small set of manufacturing-specific debrief templates.
  - Daily production debrief.
  - Work order risk review.
  - Material blocker review.
  - Quality-lite review.
  - Rationale: Templates make Corvus feel opinionated and useful.

- [ ] Validate the system against at least three CSV shapes.
  - Clean MES export.
  - Messy work order tracker.
  - Quality/material notes mixed into production data.
  - Rationale: The CSV mapping work becomes credible only when it survives variation.

### Accelerator Prep

- [ ] Draft the accelerator narrative.
  - Opening: manufacturing teams are drowning in operational data but still running meetings from manual exports.
  - Why now: AI makes messy data interpretation and workflow-specific reasoning newly practical.
  - Why you: aerospace/manufacturing exposure plus willingness to build close to the workflow.
  - Rationale: The story should connect market timing, founder insight, and product wedge.

- [ ] Capture proof points.
  - Discovery calls completed.
  - Sample data reviewed.
  - Demo screenshots or local demo.
  - Design partner status.
  - Rationale: Even early applications need evidence of motion.

## Week 4: Close The Partner And Submit-Ready Application

Dates: May 25 to June 2, 2026

Expected outcome:
- [ ] One design partner has agreed to a pilot, data review, or recurring discovery sprint.
- [ ] Accelerator application materials are complete.
- [ ] Corvus has a live or recorded demo showing the full debrief flow.

Why this matters:
The final week is about conversion. The product does not need to be complete, but the story, demo, and next customer step should feel real.

### Design Partner Close

- [ ] Follow up with every warm lead.
  - Ask for one of three commitments: sample data, pilot call, or intro to the right operations owner.
  - Rationale: Warm follow-up is where many early partnerships happen.

- [ ] Secure a specific next step with one partner.
  - Best: pilot agreement.
  - Good: scheduled data review.
  - Acceptable: recurring discovery with sample reports.
  - Rationale: For the accelerator, one concrete design partner is more powerful than vague interest.

- [ ] Write the partner hypothesis.
  - "If Corvus can ingest their production exports and produce a trusted daily debrief, then the next valuable workflow is..."
  - Rationale: This keeps the pilot tied to learning, not just delivery.

### Build

- [ ] Record a 2-3 minute demo.
  - Show: upload, mapping, classification, canonical interpretation, domain agents, debrief output.
  - Rationale: A short demo helps with accelerators, intros, and partner follow-ups.

- [ ] Create a polished sample debrief artifact.
  - Format: PDF, markdown, or HTML.
  - Include: summary, evidence, risks, next actions, and source confidence.
  - Rationale: People understand the product fastest through the output.

- [ ] Run a final smoke test.
  - Test: existing unit tests.
  - Test: demo path.
  - Test: messy CSV path.
  - Rationale: Before outreach or application submission, the demo should be dependable.

### Accelerator Application

- [ ] Finalize application answers.
  - Problem.
  - Customer.
  - Current workaround.
  - Product.
  - Market.
  - Why now.
  - Why you.
  - Traction.
  - Next milestone.
  - Rationale: Strong answers should be short, concrete, and evidence-backed.

- [ ] Prepare supporting assets.
  - Demo video.
  - Product screenshots.
  - Design partner brief.
  - Discovery call notes summary.
  - 30-day progress summary.
  - Rationale: These assets make Corvus look serious even before revenue.

## Weekly Scorecard

Update every Sunday.

### May 10, 2026

- [ ] Wedge is clear.
- [ ] Lead list has 25 names.
- [ ] Outreach message is written.
- [ ] Demo scope is frozen.
- [ ] Two sample datasets exist.

Notes:

### May 17, 2026

- [ ] 10 outreach messages sent.
- [ ] 3 discovery calls scheduled or completed.
- [ ] At least one sample data artifact requested.
- [ ] Corvus produces a useful debrief from messy CSV data.
- [ ] Accelerator application folder started.

Notes:

### May 24, 2026

- [ ] One high-probability partner identified.
- [ ] One-page design partner brief drafted.
- [ ] Pilot scope is defined.
- [ ] Three CSV shapes tested.
- [ ] Accelerator narrative drafted.

Notes:

### June 2, 2026

- [ ] One design partner has agreed to a next step.
- [ ] Demo video recorded.
- [ ] Sample debrief artifact polished.
- [ ] Smoke tests completed.
- [ ] Accelerator application is ready to submit.

Notes:

## Daily Rhythm

Use this simple daily loop from May 4 to June 2, 2026.

- [ ] 30 minutes: customer outreach or follow-up.
- [ ] 30 minutes: customer discovery notes, lead tracker, or partner brief.
- [ ] 90 minutes: product build or demo polish.
- [ ] 20 minutes: accelerator application evidence capture.

Rationale:
The danger in this month is overbuilding without enough market contact. This daily rhythm keeps customer signal and product progress moving together.

## What To Avoid For These 30 Days

- [ ] Do not build a full connector platform before one partner validates the intake workflow.
- [ ] Do not over-invest in generic chat before Corvus has a great debrief output.
- [ ] Do not try to cover every manufacturing department yet.
- [ ] Do not pitch Corvus as a replacement for MES, ERP, QMS, or BI.
- [ ] Do not wait for perfect product polish before asking for data.

## Best Version Of The Month

By June 2, 2026, the strongest outcome is:

Corvus has one real manufacturing partner willing to test the product, a demo that turns messy operational data into an evidence-backed debrief, and an accelerator application that shows a founder moving quickly at the intersection of AI and manufacturing operations.

