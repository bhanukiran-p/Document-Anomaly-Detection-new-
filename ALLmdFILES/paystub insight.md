# Paystub Insights Dashboard – Design & Implementation Guide

This document describes how to build a **Paystub Insights** dashboard based on the `v_paystub_insights` / `view paystub.csv` data. It mirrors the **Checks Insights** page patterns (CSV upload + DB + charts) but is tailored for **income + fraud analytics on paystubs**.

---

## 1. Data Model (Paystub View)

Source: `view paystub.csv` (export from DB view)

**Columns available:**

- `paystub_id` – unique ID for the paystub
- `document_id` – FK to `documents` table
- `employee_name`
- `employee_address` (often null)
- `employee_id_number`
- `employer_id`
- `employer_name`
- `employer_address`
- `employer_country`
- `gross_pay`
- `net_pay`
- `ai_recommendation` – APPROVE / ESCALATE / REJECT (and possibly others)
- `fraud_risk_score` – numeric (0–1)
- `risk_level` – LOW / MEDIUM / HIGH
- `model_confidence` – numeric (0–1)
- `anomaly_count` – integer
- `fraud_types` – string label / array-like text (e.g., `FABRICATED_DOCUMENT`, `UNREALISTIC_PROPORTIONS`, etc.)
- `created_at`
- `updated_at`

This is already an **analytics-ready view**: one row per paystub, with both **payroll metrics** and **fraud/AI metrics**.

---

## 2. Dashboard Goals

The Paystub Insights dashboard should answer:

1. **Risk & Fraud**
   - How many paystubs are low / medium / high risk?
   - What % of paystubs are being **APPROVED vs ESCALATED vs REJECTED**?
   - Which employers are sending the riskiest paystubs?
   - Which fraud types are most common?

2. **Income & Payroll**
   - What are the typical **gross vs net pay** levels?
   - Average gross pay and net pay across the dataset
   - Net-to-gross ratio distribution (normal vs suspicious)

3. **Employer & Employee Patterns**
   - Which employers have the most paystubs in the system?
   - Which employers have higher average fraud risk?
   - How many **unique employees** are represented?

4. **Operational / Monitoring**
   - How many paystubs processed over time?
   - Are high-risk paystubs increasing or decreasing?
   - Model confidence ranges and anomaly counts distribution

---

## 3. Core Metrics

From the paystub view, compute:

### 3.1 Summary KPIs (cards at top)

- **Total Paystubs**: `count(*)`
- **Avg Fraud Risk Score (%)**: `avg(fraud_risk_score) * 100`
- **Avg Gross Pay**: `avg(gross_pay)`
- **Avg Net Pay**: `avg(net_pay)`
- **High-Risk Paystubs**: count where `fraud_risk_score >= 0.75` or `risk_level = 'HIGH'`
- **Decision Breakdown**:
  - `APPROVE` count
  - `ESCALATE` count
  - `REJECT` count

Optional extra KPIs:

- **Unique Employers**: `count(distinct employer_id)`
- **Unique Employees**: `count(distinct employee_id_number)` or `employee_name`

### 3.2 Derived Metrics

- **Net-to-Gross Ratio** (per row):
  - `net_to_gross = net_pay / NULLIF(gross_pay, 0)`
- **Fraud Share**:
  - `% of rows where fraud_types != [] / not null / not "NO_FLAG"`

---

## 4. Charts & Visualizations

### 4.1 Risk Score Distribution (Bar Chart)

Similar to Checks:

- Buckets: `0–25%`, `25–50%`, `50–75%`, `75–100%`
- X-axis: bucket
- Y-axis: count of paystubs in that range

**Input:** `fraud_risk_score` (0–1) converted to 0–100.

---

### 4.2 AI Decision Breakdown (Pie Chart)

- Categories:
  - APPROVE
  - ESCALATE
  - REJECT

**Logic:**

- Normalize `ai_recommendation` to uppercase.
- Count occurrences of each value.
- Use in a Pie chart: `{ name: 'APPROVE', value: 120 }`, etc.

---

### 4.3 Risk by Employer (Dual Bar Chart)

Goal: See **which employers** are riskiest and how many paystubs each contributes.

Data structure per employer:

- `name`: employer_name
- `avgRisk`: avg fraud_risk_score * 100
- `count`: number of paystubs for
