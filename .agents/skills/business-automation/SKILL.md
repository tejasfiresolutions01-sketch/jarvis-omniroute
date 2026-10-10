---
name: business-automation
description: >-
  Enterprise-grade autonomous business workflow, CRM pipeline, commercial invoicing,
  accounting P&L, contract/SLA renewal tracking, multi-channel B2B outreach, and
  event-driven trigger-action automation engine for J.A.R.V.I.S.
---

# J.A.R.V.I.S. Autonomous Business Automation Skill

## Overview
The Business Automation Skill empowers J.A.R.V.I.S. with enterprise-grade autonomous commercial operations, replacing fragmented third-party platforms (Salesforce, HubSpot, Zapier, QuickBooks, FreshBooks) with a 100% free, local, private, and deterministic business intelligence engine.

---

## Architecture & Modules

### 1. CRM & Client Lifecycle Matrix
- **Pipeline Stages**: `Lead` → `Qualified` → `Discovery` → `Proposal Sent` → `Negotiation` → `Closed Won` / `Closed Lost` → `Active AMC` → `Renewed` / `Churned`.
- **Customer 360 Dossiers**: Client name, corporate entity, industry sector, contact points, pipeline valuation, stage velocity, and historical interactions.
- **Auto-Advancement**: Event-triggered stage transitions on proposal dispatch, agreement sign-off, or payment settlement.

### 2. Commercial Invoicing & Accounting Engine
- **Invoicing**: Generates structured, tax-compliant invoices with line items, quantity, unit rates, tax calculations (e.g. 18% GST with CGST/SGST splitting, or arbitrary sales tax), and corporate discounts.
- **Aging & Receivables**: Tracks payment statuses (`Draft`, `Sent`, `Paid`, `Partial`, `Overdue`), logs partial or full payment receipts, and calculates outstanding aging balances.
- **P&L Financial Reports**: Balances invoice revenue against logged operational expenses across categories (`Payroll`, `Infrastructure`, `Marketing`, `Logistics`, `Operations`, `Software`) to calculate Gross Margin and Net Operating Margin.

### 3. Event-Driven Workflow Automation (Zapier/Make Equivalent)
- **Execution Model**: Deterministic `Trigger` → `Condition` → `Action` rule engine.
- **Supported Triggers**:
  - `on_lead_created`: Fired when a new prospect enters the CRM.
  - `on_deal_won`: Fired when an account stage transitions to `Closed Won`.
  - `on_invoice_created`: Fired upon invoice issuance.
  - `on_invoice_overdue`: Fired when an invoice passes its due date without full settlement.
  - `on_contract_expiring`: Fired when an active service or AMC contract approaches its expiry window.
  - `on_custom_event`: Fired by arbitrary programmatic or user-defined triggers.
- **Supported Actions**:
  - `notify`: Vocal announcement or desktop alert.
  - `create_invoice`: Automatically generate a draft or finalized invoice.
  - `advance_stage`: Update a client's CRM pipeline position.
  - `generate_outreach`: Synthesize customized multi-channel follow-up copy.
  - `log_audit`: Persist execution details to the immutable workflow ledger.

### 4. Contract & SLA Monitoring (AMC & Retainers)
- **Contract Lifecycle**: Tracks active annual maintenance contracts (AMCs), software retainers, consulting agreements, and SLA response guarantees.
- **Proactive Renewal Safeguard**: Automatically scans for contracts expiring within designated timeframes (e.g., 30, 15, 7 days) and generates renewal proposals.

### 5. Multi-Channel B2B Outreach Cadence
- **Multi-Touch Sequences**:
  - **Day 1**: Introductory reachout & executive value summary.
  - **Day 3**: Technical proposition, capability brief, and case studies.
  - **Day 7**: Formal commercial quotation & service roadmap.
  - **Day 14**: Executive check-in & contract sign-off proposal.

### 6. Executive Business Intelligence Dashboard
- Real-time pipeline health, total pipeline value, weighted forecast.
- Outstanding aging receivables, total revenue realized, net profit margins.
- Natural language vocal executive briefings delivered via local TTS.

---

## Directive Reference

| Directive / Voice Command | Purpose |
|---------------------------|---------|
| `business automation status` | Audits business automation engine, CRM records, active workflows, and database health. |
| `onboard client <name> company <co> email <email> value <val>` | Creates or updates a B2B account in the CRM pipeline. |
| `advance client <name> to <stage>` | Transitions account lifecycle (e.g. `Qualified`, `Closed Won`). |
| `create invoice <client> for <items/desc> amount <val>` | Generates a tax-compliant commercial invoice. |
| `record payment <invoice_id> amount <val>` | Logs payment receipts against an outstanding invoice. |
| `pnl report` / `financial report` | Compiles revenue, expenses, and net profit margins. |
| `check expiring contracts` | Scans for contracts due for renewal within 30 days. |
| `run business workflow <workflow_name>` | Executes a configured trigger-action automation. |
| `business intelligence` / `business analytics` | Formats an executive briefing of key commercial KPIs. |

---

## Operational Guidelines
1. **100% Free Plan**: Rely solely on local SQLite storage, Python math, and local document generators. Never depend on paid external SaaS APIs.
2. **Zero Latency**: All CRM, invoicing, and workflow steps execute locally in sub-millisecond timeframes.
3. **Audit Trail**: Every trigger event and executed action is logged with execution timestamps in `workflow_logs`.
