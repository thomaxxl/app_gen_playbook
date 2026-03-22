from __future__ import annotations

import unittest
from pathlib import Path

from verify_logicbank_runtime_contract import verify


class VerifyLogicbankRuntimeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_verify_reports_executable_smoke_success(self) -> None:
        payload = verify(self.repo_root)

        self.assertIn("session", payload["logicbank_activate_signature"])
        self.assertIn("activator", payload["logicbank_activate_signature"])
        self.assertIn("constraint_event", payload["logicbank_activate_signature"])
        self.assertIn("aggregate_defaults", payload["logicbank_activate_signature"])
        self.assertIn("all_defaults", payload["logicbank_activate_signature"])
        self.assertIn("msg: str", payload["logicrow_log_signature"])
        self.assertIn("new_row_class", payload["logicrow_new_logic_row_signature"])
        self.assertTrue(payload["event_callback_keywords_verified"])
        self.assertTrue(payload["logic_row_log_usage_verified"])
        self.assertTrue(all(payload["event_tokens_verified"].values()))

        smoke = payload["executable_smoke"]
        self.assertTrue(smoke["verified"])
        self.assertEqual(smoke["callback_row_type"], "Item")
        self.assertTrue(smoke["callback_old_row_is_none"])
        self.assertEqual(smoke["logic_row_type"], "LogicRow")
        self.assertEqual(smoke["item_parent_name_snapshot"], "Northwind")
        self.assertEqual(smoke["audit_count"], 1)
        self.assertEqual(smoke["audit_parent_name_snapshot"], "Northwind")
        self.assertTrue(smoke["log_contains_message"])
        self.assertTrue(smoke["log_contains_nested_insert"])


if __name__ == "__main__":
    unittest.main()
