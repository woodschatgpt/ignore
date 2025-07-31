import pandas as pd
from datetime import datetime

def test_sync_outliers():
    # Columns required for comparison and client info
    MATCH_KEY_COLS = ["COB_DATE", "LEVEL2_NAME", "LOB", "NODE_ID", "NODE_NAME", "METRIC_NAME"]
    CLIENT_COLS = [
        "REVIEW_STATUS",
        "OUTLIER_STATUS",
        "COMMENT",
        "UPDATED_DATE",
        "UPDATED_BY",
        "AUDIT_HISTORY",
        "REVALIDATION_STATUS",
        "__row_key__",
    ]

    # Mock old outlier DataFrame (historical)
    old_data = [
        {
            "COB_DATE": "2025-07-29",
            "LEVEL2_NAME": "L2A",
            "LOB": "LOB1",
            "NODE_ID": "NID1",
            "NODE_NAME": "Desk1",
            "METRIC_NAME": "MetricX",
            "metric_value": 100.0,
            "REVIEW_STATUS": "Closed",
            "OUTLIER_STATUS": "",
            "COMMENT": "",
            "UPDATED_DATE": "2025-07-29 12:00:00",
            "UPDATED_BY": "Analyst",
            "AUDIT_HISTORY": "[]",
            "REVALIDATION_STATUS": "",
            "__row_key__": "2025-07-29.L2A.LOB1.NID1.Desk1.MetricX"
        },
        {
            "COB_DATE": "2025-07-28",
            "LEVEL2_NAME": "L2B",
            "LOB": "LOB2",
            "NODE_ID": "NID2",
            "NODE_NAME": "Desk2",
            "METRIC_NAME": "MetricY",
            "metric_value": 200.0,
            "REVIEW_STATUS": "Open",
            "OUTLIER_STATUS": "",
            "COMMENT": "",
            "UPDATED_DATE": "2025-07-28 12:00:00",
            "UPDATED_BY": "System",
            "AUDIT_HISTORY": "[]",
            "REVALIDATION_STATUS": "",
            "__row_key__": "2025-07-28.L2B.LOB2.NID2.Desk2.MetricY"
        }
    ]
    old_df = pd.DataFrame(old_data)

    # Mock new outlier DataFrame (current detection)
    new_data = [
        # Update to existing (change metric_value, triggers update)
        {
            "COB_DATE": "2025-07-29",
            "LEVEL2_NAME": "L2A",
            "LOB": "LOB1",
            "NODE_ID": "NID1",
            "NODE_NAME": "Desk1",
            "METRIC_NAME": "MetricX",
            "metric_value": 150.0
        },
        # New record (not in old)
        {
            "COB_DATE": "2025-07-30",
            "LEVEL2_NAME": "L2C",
            "LOB": "LOB3",
            "NODE_ID": "NID3",
            "NODE_NAME": "Desk3",
            "METRIC_NAME": "MetricZ",
            "metric_value": 300.0
        }
    ]
    new_df = pd.DataFrame(new_data)

    # Import (or paste) sync_outliers function here before running test

    output_df = sync_outliers(old_df.copy(), new_df.copy())

    # Validate
    print(output_df[[
        "COB_DATE", "LEVEL2_NAME", "LOB", "NODE_ID", "NODE_NAME", "METRIC_NAME",
        "metric_value", "REVALIDATION_STATUS", "REVIEW_STATUS"
    ]])

# Run the test
test_sync_outliers()
