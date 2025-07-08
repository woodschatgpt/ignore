# 📄 Outlier Revalidation – sync_outliers Function Walkthrough

This document explains **step by step** how the `sync_outliers` function works, with **real sample data** at each stage.

---

## ✅ Purpose

The function **sync_outliers** is used to merge:

- ✅ `old_df`: Your *existing* stored outlier data (e.g. from S3)
- ✅ `new_df`: The *newly recalculated* outlier data from the source system

It figures out:

- Which records have **changed** (and need to be updated)
- Which are **new** (not in old)
- Which are **missing** (gone from new)

It also **logs all changes** into an audit trail for traceability.

---

## ✅ Matching Keys

The function uses these columns to identify a unique record:

COB_DATE, LEVEL2_NAME, LOB, NODE_ID, NODE_NAME, METRIC_NAME


---

## ✅ Sample Input Data

### 🟠 Old Outlier Data (`old_df`)

| COB_DATE   | LEVEL2_NAME | NODE_ID | NODE_NAME | METRIC_NAME | Metric_value | REVIEW_STATUS | AUDIT_HISTORY |
|------------|--------------|---------|-----------|--------------|---------------|---------------|----------------|
| 2025-06-30 | BookA        | 123     | Node1     | Notional     | 100.0         | Closed        | []             |

✅ This is your **stored** outlier result from a previous run.

---

### 🟠 New Recalculated Data (`new_df`)

| COB_DATE   | LEVEL2_NAME | NODE_ID | NODE_NAME | METRIC_NAME | Metric_value |
|------------|--------------|---------|-----------|--------------|---------------|
| 2025-06-30 | BookA        | 123     | Node1     | Notional     | 100.0         | *(old copy)*  
| 2025-06-30 | BookA        | 123     | Node1     | Notional     | 105.0         | *(latest value)*  
| 2025-06-30 | BookB        | 456     | Node2     | Exposure     | 200.0         | *(new record)*  

✅ Notice duplicate rows for **BookA** — because source table appends recalculations every day.

---

## ✅ Step-by-Step What the Code Does

---

### 1️⃣ Remove Duplicates in new_df

**Code:**

```python
new_df = new_df.drop_duplicates(subset=MATCH_KEY_COLS, keep='last')
```
✅ Keeps only the last occurrence for each unique key.

✅ Ensures only the latest recalculation is used.

Resulting new_df after deduplication:

|COB_DATE |	LEVEL2_NAME |	NODE_ID	| NODE_NAME |	METRIC_NAME |	Metric_value|
|---------|-------------|---------|-----------|-------------|-------------|
|2025-06-30| BookA	    | 123	    |Node1      |Notional     |	105.0       |
|2025-06-30| BookB	    |456	    |Node2	    |Exposure	    |200.0        |


✅ The older 100.0 row for BookA is dropped.

## 2️⃣ Create Synthetic Join Keys
✅ The function builds a single key column by combining the MATCH_KEY_COLS:

```python
__row_key__ = "2025-06-30-BookA-123-Node1-Notional"
```

✅ Makes it easy to match records across dataframes.

## 3️⃣ Create Lookup Tables
✅ Converts both dataframes to indexed lookups:
**code**
```python
old_lookup = old_df.set_index("__row_key__")
new_lookup = new_df.set_index("__row_key__")
```
✅ Enables fast matching by key.

4️⃣ Process Each Row in new_df
The function loops through each new recalculated row:

➜ If It Matches in old_df:

✅ Example: BookA

Metric_value (old)	Metric_value (new)
100.0	105.0
✅ They’re different → it’s an update!

✅ Code will:

*  Save the old row (excluding client fields) into AUDIT_HISTORY
*  Replace Metric_value with new (105.0)
*  Preserve REVIEW_STATUS
**code**
```python
Add metadata:
UPDATED_BY = "System"
UPDATED_DATE = current timestamp
REVALIDATION_STATUS = "updated"
```
✅ So BookA row will now look like:

|COB_DATE|	...	|Metric_value|	REVIEW_STATUS	|AUDIT_HISTORY	| REVALIDATION_STATUS|
|--------|------|------------|----------------|---------------|--------------------|
|2025-06-30|	...|	105.0|	Closed|	[ { "Metric_value": 100.0 } ]|	updated|

➜ If It Does Not Match in old_df:

✅ Example: BookB

✅ New row not seen before → add it:

*  REVIEW_STATUS = "Open"
*  AUDIT_HISTORY = []
*  REVALIDATION_STATUS = "new"
*  System metadata for who/when

✅ Resulting BookB row:

|COB_DATE	|...	|Metric_value|	REVIEW_STATUS|	AUDIT_HISTORY	|REVALIDATION_STATUS|
|---------|-----|------------|---------------|----------------|-------------------|
|2025-06-30|	...	|200.0	|Open	|[]|	new|

## 5️⃣ Handle Missing Records
✅ For any old_df row not found in new_df:

✅ Mark:

REVALIDATION_STATUS = "missing"

✅ This flags rows that are no longer present in the new data.

✅ In our example there’s no missing row, but if there were, it would be marked.

## 6️⃣ Clean Up
✅ Finally, remove the temporary __row_key__ column used for joins.

✅ Final Resulting Merged Data

|COB_DATE|	LEVEL2_NAME|	NODE_ID	|NODE_NAME	|METRIC_NAME|	Metric_value|	REVIEW_STATUS|	AUDIT_HISTORY|	REVALIDATION_STATUS|	UPDATED_BY	|UPDATED_DATE|
|--------|-------------|----------|-----------|-----------|-------------|--------------|---------------|---------------------|--------------|------------|
|2025-06-30|	BookA|	123|	Node1|	Notional|	105.0|	Closed|	[ { "Metric_value": 100.0, ... } ]|	updated	|System|	timestamp|
|2025-06-30|	BookB|	456|	Node2|	Exposure|	200.0|	Open|	[]|	new|	System|	timestamp|

✅ BookA is updated, old value archived in AUDIT_HISTORY.

✅ BookB is new.

✅ Any missing rows would be marked with missing.

## ✅ Summary

✅ Cleans up duplicate recalculated rows in new_df.

✅ Matches records by business key.

✅ Detects and logs changes.

✅ Preserves client review metadata.

✅ Tracks everything with:

```
AUDIT_HISTORY
REVALIDATION_STATUS ("updated", "new", "missing")
```
✅ Fully ready to write back to S3 for tracking over time.
