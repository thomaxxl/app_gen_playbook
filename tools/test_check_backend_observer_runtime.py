from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_backend_observer_runtime import audit_backend_observer_runtime


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckBackendObserverRuntimeTests(unittest.TestCase):
    def test_accepts_db_backed_observer_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "app/README.md",
                "This run observer reads current-run status from the mirrored run_dashboard.sqlite3 data set in read-only mode.\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/config.py",
                'DEFAULT_DB_PATH = BACKEND_DIR / "data" / "run_observer.sqlite3"\n',
            )
            write_file(
                repo_root / "app/backend/src/my_app/bootstrap.py",
                "\n".join(
                    [
                        "from sqlalchemy import inspect",
                        "def validate_observer_database(engine):",
                        "    inspector = inspect(engine)",
                        "    if not inspector.has_table('runs'):",
                        "        raise RuntimeError('missing runs')",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/fastapi_app.py",
                "\n".join(
                    [
                        "from .db import build_engine, build_session_factory",
                        "def create_app():",
                        "    engine = build_engine('sqlite:///observer.sqlite3')",
                        "    session_factory = build_session_factory(engine)",
                        "    return object()",
                    ]
                )
                + "\n",
            )

            self.assertEqual(audit_backend_observer_runtime(repo_root), [])

    def test_rejects_seeded_recovery_runtime_for_observer_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "app/README.md",
                "This run observer reads current-run status from the mirrored run_dashboard.sqlite3 data set in read-only mode.\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/config.py",
                'DEFAULT_DB_PATH = BACKEND_DIR / "data" / "run_observer.sqlite3"\n',
            )
            write_file(
                repo_root / "app/backend/src/my_app/bootstrap.py",
                "\n".join(
                    [
                        "def ensure_schema(engine):",
                        "    db_path.unlink()",
                        "    Base.metadata.create_all(engine)",
                        "def validate_observer_database(engine):",
                        "    ensure_schema(engine)",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/fastapi_app.py",
                "\n".join(
                    [
                        "def _runtime_resource_records():",
                        "    return {}",
                        "def create_app():",
                        '    mode = "schema-driven-runtime-recovery"',
                        "    return _runtime_resource_records()",
                    ]
                )
                + "\n",
            )

            issues = audit_backend_observer_runtime(repo_root)
            self.assertTrue(any("seeded in-memory recovery records" in issue for issue in issues))
            self.assertTrue(any("rewrites the mirrored SQLite file" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
