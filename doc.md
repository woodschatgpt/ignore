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

