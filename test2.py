import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Assuming Reader and other imports are already present in your test file

class TestOutlier(unittest.TestCase):

    # Your existing test methods...

    def test_read_with_monthly_revalidation_true(self):
        cob_date_str = "2025-07-31"
        params = {
            "cobDate": cob_date_str,
            "monthly_revalidation": "true",   # as string to also test str->bool logic
            "m2_env": "testEnv",
            "hydra_env": "testHydra",
            "metric": "POSITION",
            "to_list": ["test@example.com"],
            "cc_list": ["cc@example.com"]
        }

        class DummyWorkItem:
            def getRequestParams(self_inner):
                return params

        workItem = DummyWorkItem()
        reader = Reader()

        with patch.object(reader, "_processoutlierDetection", autospec=True) as mock_process, \
             patch("lib.logging.info") as mock_log_info, \
             patch("lib.logging.error") as mock_log_error:

            # Side effect: raise on cob_date - 2 days, succeed otherwise
            def side_effect(self_arg, work_item_arg, dt_arg, *args, **kwargs):
                if dt_arg == datetime.strptime(cob_date_str, "%Y-%m-%d").date() - timedelta(days=2):
                    raise Exception("Simulated error")
                return f"processed-{dt_arg.isoformat()}"

            mock_process.side_effect = side_effect

            # Call method under test
            reader.read(workItem)

            # Assert called for 5 consecutive dates
            base_date = datetime.strptime(cob_date_str, "%Y-%m-%d").date()
            expected_dates = [base_date - timedelta(days=i) for i in range(5)]

            actual_dates = [call.args[2] for call in mock_process.call_args_list]  # index 2 for dt_arg
            self.assertEqual(expected_dates, actual_dates)

            # Check that the method logged errors due to simulated exceptions
            self.assertTrue(mock_log_error.called, "Expected error logs for simulated exceptions")

            # Check info logging happened multiple times during processing
            self.assertGreaterEqual(mock_log_info.call_count, 3)

# If you want to run this test standalone, add:
# if __name__ == "__main__":
#     unittest.main()
