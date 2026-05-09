# Prior Authorization Autopilot Agent — Hackathon Plan

## 1. Problem Statement

Prior authorization (PA) is one of the most painful administrative burdens in healthcare:

- Physicians spend **~20 hours/week** on paperwork; PA is a top contributor
- Average PA takes **1–3 days** to process; urgent cases can be delayed fatally
- **25% of physicians** report PA causes serious adverse events for patients
- Payers reject ~10% of PA requests on first submission; appeals are manual and slow

**The gap:** No intelligent system currently automates the full PA lifecycle — from clinical order → payer criteria check → submission → denial appeal — using open standards like FHIR and A2A.

---

## 2. Solution Overview

**ClearPath** — A2A Prior Authorization Autopilot Agent

An intelligent orchestrator agent that automates the entire prior authorization workflow by coordinating with specialist sub-agents using A2A, pulling real patient data via FHIR, and leveraging MCP tools for payer rules and document generation.

> "From clinical order to authorization decision — in minutes, not days."

---

## 3. Architecture

### Agent Roles (A2A)

```
┌─────────────────────────────────────────────────────┐
│              CLEARPATH ORCHESTRATOR AGENT           │
│         (Main A2A Agent on Prompt Opinion)          │
└────────────────────┬────────────────────────────────┘
                     │ coordinates via A2A
         ┌───────────┼───────────┐
         ▼           ▼           ▼
  ┌─────────┐  ┌──────────┐  ┌────────────┐
  │ Patient  │  │  Payer   │  │  Document  │
  │ Records  │  │  Rules   │  │ Generation │
  │  Agent   │  │  Agent   │  │   Agent    │
  └────┬─────┘  └────┬─────┘  └─────┬──────┘
       │              │              │
  FHIR Server    Payer Criteria   PA Letter /
  (patient Dx,   Database (MCP)   Appeal Draft
  labs, meds)                     (MCP)
```

### Data Flow

1. **Trigger:** Clinician places an order (e.g., MRI lumbar spine, specialty drug)
2. **Orchestrator** receives the order via SHARP context (patient ID + FHIR token)
3. **Patient Records Agent** fetches: diagnosis codes, relevant labs, prior treatments, demographics via FHIR R4
4. **Payer Rules Agent** retrieves payer-specific PA criteria for the procedure/drug code
5. **Orchestrator** runs eligibility check: does patient data satisfy payer criteria?
6. If YES → **Document Agent** drafts and submits PA request
7. If NO / DENIED → **Document Agent** drafts clinical appeal with supporting evidence
8. Clinician receives a summary with status + any action needed
