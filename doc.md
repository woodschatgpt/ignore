# 📄 Outlier Detector – Monthly Revalidation Workflow Document

---

## Overview

This document describes the plan for implementing **Monthly Revalidation** in the Outlier Detector pipeline.

The goal is to re-run outlier detection for the past 30 days, compare results with existing stored outlier data, and update them as needed—while maintaining a complete audit history of changes.

---

## Purpose of Monthly Revalidation

- Ensure outlier records in S3 remain accurate and up-to-date.
- Capture any changes in recalculated metrics from EOD or TRD summary tables.
- Maintain client-reviewed metadata and a full audit history of updates.
- Support compliance and review processes.

---

## Data Source Behavior

- The `eod_summary` (for positions) and `trd_summary` (for transactions) tables **append** data daily.
- They contain **historical** entries.
- For any `cob_date`, these tables may have **multiple rows** over time representing recalculations or corrections.

✅ The key columns used to uniquely identify business records for comparison are:

COB_DATE, LEVEL2_NAME, LOB, NODE_ID, NODE_NAME, METRIC_NAME


---

## Revalidation Workflow Steps

### Step 1: Load All Existing Outlier Data from S3

- For the target `COB_DATE` (e.g. 30-Jun-2025), load **all** previously stored outlier records from S3.
- Includes:
  - System-generated metric columns (e.g. `Metric_value`, `STD_DEV`)
  - Client review metadata (e.g. `REVIEW_STATUS`, `COMMENT`, `AUDIT_HISTORY`, `UPDATED_BY`, `UPDATED_DATE`)

---

### Step 2: For Each Row in Old S3 Data, Get Matching Row from Newly Recalculated Data

- Query the EOD summary or TRD summary table for **all rows** matching the same `COB_DATE`.
- Use the business key columns to identify **matching rows** in the new recalculation:

COB_DATE, LEVEL2_NAME, LOB, NODE_ID, NODE_NAME, METRIC_NAME

- This new data may contain:
  - The **original** (previous) value.
  - A **newer** updated value.

✅ Because these tables append daily, we may see **both old and new entries** for the same key.

---

### Step 3: Determine the Latest Value

- For each matching business key:
  - Identify the *most recent* recalculated value in the new data.
  - This latest value is what the outlier detector will use for comparison.

---

### Step 4: Compare Old and New Values

- Ignore client metadata fields during comparison.
- Focus only on system-generated columns like `Metric_value`, `STD_DEV`, bounds, etc.
- If any of these system values have changed between old and new:

✅ Then:

- Append the entire **old row** to the `AUDIT_HISTORY` column.
- Replace the metric columns with the **new** recalculated values.
- Set:
  - `UPDATED_BY = "System"`
  - `UPDATED_DATE = current timestamp`
  - `REVALIDATION_STATUS = "updated"`

---

### Step 5: Handle Missing Records

- If a row from **old S3 data** does **not** have any match in the newly recalculated data:
  - Mark it as:

REVALIDATION_STATUS = "missing"


- Retain it in the final output for audit purposes.

---

### Step 6: Handle New Records

- If a row is found in the new recalculated data **but did not exist** in old S3 data:
  - Add it as a **new** record.
  - Initialize:
    - `REVIEW_STATUS = "Open"`
    - `AUDIT_HISTORY = []`
    - `UPDATED_BY = "System"`
    - `UPDATED_DATE = current timestamp`
    - `REVALIDATION_STATUS = "new"`

---

### Step 7: Save the Updated Data Back to S3

- For each `COB_DATE` processed, save the **fully updated** outlier dataset back to S3.
- Includes:
  - System-generated columns (updated as needed)
  - Client review metadata (preserved or initialized)
  - Audit history of all changes
  - `REVALIDATION_STATUS` for easy tracking

---

## Example Scenario Using Sample Data

### Old Outlier Data (S3 on Day 1)

| COB_DATE | LEVEL2_NAME | LOB | NODE_ID | NODE_NAME | METRIC_NAME | Metric_value |
|----------|--------------|-----|---------|-----------|--------------|--------------|
| a        | a            | a   | a       | a         | a            | a            |

---

### Newly Recalculated Data (Day 2 with Revalidation Run)

| COB_DATE | LEVEL2_NAME | LOB | NODE_ID | NODE_NAME | METRIC_NAME | Metric_value |
|----------|--------------|-----|---------|-----------|--------------|--------------|
| a        | a            | a   | a       | a         | a            | a            |
| a        | a            | a   | a       | a         | a            | a!           |

**Explanation:**
- On Day 2, the source table *appends* recalculation rows.
- It contains both:
  - Old value: `Metric_value = a`
  - New value: `Metric_value = a!`

✅ The latest value (`a!`) is what revalidation uses.

---

### Final Updated Outlier Data Saved to S3

| COB_DATE | LEVEL2_NAME | LOB | NODE_ID | NODE_NAME | METRIC_NAME | Metric_value | AUDIT_HISTORY                      | UPDATED_BY | UPDATED_DATE | REVALIDATION_STATUS |
|----------|--------------|-----|---------|-----------|--------------|--------------|------------------------------------|------------|--------------|---------------------|
| a        | a            | a   | a       | a         | a            | a!           | [ { ...previous row with a... } ] | System     | current_date | updated             |

---

## Summary of REVALIDATION_STATUS Meanings

| Value   | Meaning                                                         |
|---------|-----------------------------------------------------------------|
| updated | Matched row found in new data, with changed system-generated values |
| missing | Old row no longer present in new recalculated data              |
| new     | Newly detected row in new data, not found in old S3 data        |

---

## Benefits of This Workflow

- Preserves all **client-reviewed** fields like `REVIEW_STATUS` and `COMMENT`.
- Ensures **latest recalculation** is always used.
- Tracks every change with full **AUDIT_HISTORY**.
- Flags new, updated, and missing rows clearly for follow-up.
- Automatable for entire 30-day revalidation runs.

---

## Next Steps

- Finalize implementation in code.
- Test with multiple `COB_DATE` samples.
- Validate updates to `AUDIT_HISTORY` and `REVALIDATION_STATUS`.
- Schedule regular monthly revalidation runs.

