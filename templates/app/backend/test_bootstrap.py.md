# `backend/tests/test_bootstrap.py`

See also:

- [../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md](../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md)
- [../../../specs/contracts/backend/validation.md](../../../specs/contracts/backend/validation.md)

```python
import shutil
from pathlib import Path

import pytest

from my_app import create_app
from my_app.bootstrap import validate_admin_schema, validate_observer_database
from my_app.config import get_settings
from my_app.db import build_engine, session_scope
from my_app.models import ArtifactPackage, Run, RunFile

REQUIRED_RESOURCES = {
    "Project",
    "Run",
    "RunPhaseStatus",
    "ArtifactPackage",
    "Artifact",
    "HandoffMessage",
    "Blocker",
    "EvidenceItem",
    "VerificationCheck",
    "WorkerState",
    "OrchestratorEvent",
    "RunFile",
    "ChangeRequest",
}


def configure_test_env(monkeypatch, tmp_path: Path, copy_observer_db: bool = True) -> Path:
    app_root = Path(__file__).resolve().parents[2]
    playbook_root = app_root.parent
    db_path = tmp_path / "observer.sqlite3"
    if copy_observer_db:
        shutil.copy2(playbook_root / "run_dashboard" / "run_dashboard.sqlite3", db_path)
    monkeypatch.setenv("MY_APP_DB_PATH", str(db_path))
    monkeypatch.setenv(
        "MY_APP_ADMIN_YAML_PATH",
        str(app_root / "reference" / "admin.yaml"),
    )
    return db_path


def test_admin_schema_has_required_resources(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    schema = validate_admin_schema(get_settings())
    assert REQUIRED_RESOURCES.issubset(set(schema["resources"]))


def test_observer_startup_reads_mirrored_run_data(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()

    session_factory = app.state.session_factory
    with session_scope(session_factory) as session:
        assert session.query(Run).count() > 0
        assert session.query(ArtifactPackage).count() > 0
        assert session.query(RunFile).count() > 0


def test_validate_observer_database_rejects_empty_sqlite(monkeypatch, tmp_path):
    db_path = configure_test_env(monkeypatch, tmp_path, copy_observer_db=False)
    engine = build_engine(f"sqlite:///{db_path}")

    with pytest.raises(RuntimeError):
        validate_observer_database(engine)
```

Notes:

- This observer app is read-only and should not seed placeholder PM data.
- Validation should prove the mirrored run-dashboard database exists and is
  usable, not that a starter seed can create demo rows.
