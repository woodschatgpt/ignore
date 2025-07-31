import pandas as pd
from datetime import datetime
# Assume sync_outliers is imported

def test_sync_outliers_minimal():
    # Shared columns
    match_cols = ["COB_DATE", "LEVEL2_NAME", "LOB", "NODE_ID", "NODE_NAME", "METRIC_NAME"]
    client_cols = [
        "REVIEW_STATUS", "OUTLIER_STATUS", "COMMENT", "UPDATED_DATE", 
        "UPDATED_BY", "AUDIT_HISTORY", "REVALIDATION_STATUS", "__row_key__"
    ]
    # 1. Old dataframe: contains an old version of "row1" and an "orphaned" row
    old_data = [
        # Existing row, value will be updated
        ["2025-07-31", "L2", "LOB1", "N1", "Node1", "MetricA", 10.0, "Closed", "", "", "2025-07-30 12:00:00", "UserA", "[]", "", ""],
        # Orphaned row, will become "missing"
        ["2025-07-31", "L2", "LOB2", "N2", "Node2", "MetricB", 5.0, "Closed", "", "", "2025-07-30 12:00:00", "UserA", "[]", "", ""],
    ]
    # 2. New dataframe: row1 must update value, row3 is "new"
    new_data = [
        ["2025-07-31", "L2", "LOB1", "N1", "Node1", "MetricA", 20.0],   # Updated value
        ["2025-07-31", "L2", "LOB3", "N3", "Node3", "MetricC", 3.0],    # New row
    ]

    old_cols = match_cols + ["metric_value"] + [c for c in client_cols if c != "__row_key__"]
    new_cols = match_cols + ["metric_value"]

    old_df = pd.DataFrame(old_data, columns=old_cols)
    new_df = pd.DataFrame(new_data, columns=new_cols)

    # Run sync
    result = sync_outliers(old_df, new_df)

    # Test: N1 (updated), N2 (missing), N3 (new)
    res = result.set_index(match_cols)
    # 1. Check value updated and REVALIDATION_STATUS="updated"
    assert res.loc[("2025-07-31", "L2", "LOB1", "N1", "Node1", "MetricA")].metric_value == 20.0
    assert res.loc[("2025-07-31", "L2", "LOB1", "N1", "Node1", "MetricA")].REVALIDATION_STATUS == "updated"

    # 2. New row has REVALIDATION_STATUS="new" and REVIEW_STATUS="Open"
    assert res.loc[("2025-07-31", "L2", "LOB3", "N3", "Node3", "MetricC")].REVALIDATION_STATUS == "new"
    assert res.loc[("2025-07-31", "L2", "LOB3", "N3", "Node3", "MetricC")].REVIEW_STATUS == "Open"

    # 3. Orphaned old row is marked as "missing"
    assert res.loc[("2025-07-31", "L2", "LOB2", "N2", "Node2", "MetricB")].REVALIDATION_STATUS == "missing"

    print("All assertions passed.")

# Invoke test manually (if not using pytest runner)
test_sync_outliers_minimal()
