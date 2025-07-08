import pandas as pd
import numpy as np
import ast
from datetime import datetime

# Client metadata columns that shouldn't be compared
CLIENT_COLS = [
    "REVIEW_STATUS",
    "OUTLIER_STATUS",
    "COMMENT",
    "UPDATED_DATE",
    "UPDATED_BY",
    "AUDIT_HISTORY",
    "REVALIDATION_STATUS"
]

# Business key columns for identifying unique records
MATCH_KEY_COLS = [
    "COB_DATE",
    "LEVEL2_NAME",
    "LOB",
    "NODE_ID",
    "NODE_NAME",
    "METRIC_NAME"
]

def sync_outliers(old_df, new_df):
    updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Remove duplicates in new_df: keep last occurrence (latest)
    new_df = new_df.drop_duplicates(subset=MATCH_KEY_COLS, keep='last')

    # Create a synthetic join key for easy matching
    old_df["__row_key__"] = old_df[MATCH_KEY_COLS].astype(str).agg("-".join, axis=1)
    new_df["__row_key__"] = new_df[MATCH_KEY_COLS].astype(str).agg("-".join, axis=1)

    # Create lookup tables
    old_lookup = old_df.set_index("__row_key__")
    new_lookup = new_df.set_index("__row_key__")

    # Track which old keys were matched
    matched_old_keys = set()

    # Process new data rows
    for new_key, new_row in new_lookup.iterrows():
        if new_key in old_lookup.index:
            # Matched old row exists
            matched_old_keys.add(new_key)
            old_row = old_lookup.loc[new_key].copy()

            # Compare only system columns (ignore client columns)
            diffs = {}
            compare_cols = [col for col in new_df.columns if col not in CLIENT_COLS]
            for col in compare_cols:
                old_val = old_row.get(col)
                new_val = new_row.get(col)
                if pd.isnull(old_val) and pd.isnull(new_val):
                    continue
                if isinstance(old_val, (float, np.float64)) and isinstance(new_val, (float, np.float64)):
                    if not np.isclose(old_val, new_val, rtol=1e-6, equal_nan=True):
                        diffs[col] = old_val
                elif old_val != new_val:
                    diffs[col] = old_val

            if diffs:
                # It's an updated record
                # Append entire old row (minus client fields) to AUDIT_HISTORY
                audit_record = old_row.drop(labels=CLIENT_COLS, errors="ignore").to_dict()

                old_audit = old_row.get("AUDIT_HISTORY", [])
                if isinstance(old_audit, str):
                    try:
                        old_audit = ast.literal_eval(old_audit)
                    except Exception:
                        old_audit = []
                if not isinstance(old_audit, list):
                    old_audit = []

                old_audit.append(audit_record)

                # Update old_df with new values
                for col in compare_cols:
                    old_df.loc[old_df["__row_key__"] == new_key, col] = new_row[col]

                old_df.loc[old_df["__row_key__"] == new_key, "AUDIT_HISTORY"] = old_audit
                old_df.loc[old_df["__row_key__"] == new_key, "UPDATED_BY"] = "System"
                old_df.loc[old_df["__row_key__"] == new_key, "UPDATED_DATE"] = updated_at
                old_df.loc[old_df["__row_key__"] == new_key, "REVALIDATION_STATUS"] = "updated"

            else:
                # No change – clear any old REVALIDATION_STATUS
                old_df.loc[old_df["__row_key__"] == new_key, "REVALIDATION_STATUS"] = ""

        else:
            # New record not in old_df
            new_entry = new_row.to_dict()
            new_entry.update({
                "REVIEW_STATUS": "Open",
                "UPDATED_BY": "System",
                "UPDATED_DATE": updated_at,
                "AUDIT_HISTORY": [],
                "REVALIDATION_STATUS": "new"
            })
            old_df = pd.concat([old_df, pd.DataFrame([new_entry])], ignore_index=True)

    # Handle missing records (in old but not in new)
    all_new_keys = set(new_lookup.index)
    for old_key in old_df["__row_key__"]:
        if old_key not in all_new_keys:
            old_df.loc[old_df["__row_key__"] == old_key, "REVALIDATION_STATUS"] = "missing"

    # Remove temp join key
    old_df.drop(columns="__row_key__", inplace=True, errors="ignore")

    return old_df
