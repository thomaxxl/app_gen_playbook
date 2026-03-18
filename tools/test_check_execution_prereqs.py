from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_execution_prereqs import CheckResult


class CheckExecutionPrereqsTests(unittest.TestCase):
    def test_imports_tool_symbols(self) -> None:
        result = CheckResult("name", "ok", "detail")
        self.assertEqual(result.name, "name")


if __name__ == "__main__":
    unittest.main()
