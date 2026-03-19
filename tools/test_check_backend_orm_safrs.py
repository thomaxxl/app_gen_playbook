from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_backend_orm_safrs import audit_backend_orm_safrs


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckBackendOrmSafrsTests(unittest.TestCase):
    def test_accepts_safrs_and_orm_backend_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/artifacts/backend-design/resource-exposure-policy.md",
                "| `Project` | yes |\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/db.py",
                "\n".join(
                    [
                        "from sqlalchemy.orm import declarative_base",
                        "Base = declarative_base()",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/models.py",
                "\n".join(
                    [
                        "from safrs import SAFRSBase",
                        "from sqlalchemy.orm import Mapped, mapped_column, relationship",
                        "from .db import Base",
                        "class Project(SAFRSBase, Base):",
                        "    id: Mapped[int] = mapped_column(primary_key=True)",
                        "EXPOSED_MODELS = (Project,)",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/fastapi_app.py",
                "\n".join(
                    [
                        "from fastapi import FastAPI",
                        "from safrs.fastapi.api import SafrsFastAPI",
                        "from .models import EXPOSED_MODELS",
                        "def create_app():",
                        '    app = FastAPI(openapi_url="/jsonapi.json")',
                        '    api = SafrsFastAPI(app, prefix="/api")',
                        "    for model in EXPOSED_MODELS:",
                        "        api.expose_object(model)",
                        "    return app",
                    ]
                )
                + "\n",
            )

            self.assertEqual(audit_backend_orm_safrs(repo_root), [])

    def test_rejects_fastapi_openapi_masquerading_as_jsonapi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/artifacts/backend-design/resource-exposure-policy.md",
                "| `Project` | yes |\n| `Run` | yes |\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/db.py",
                "\n".join(
                    [
                        "from sqlalchemy import create_engine, text",
                        "def fetch_all(connection, statement):",
                        "    return connection.execute(text(statement))",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/mirror_api.py",
                "\n".join(
                    [
                        "RESOURCE_TABLES = {'Project': 'projects'}",
                        "def load_resource_specs(settings): return []",
                        "def build_collection_document(connection, spec, request): return {'data': []}",
                        "def build_item_document(connection, spec, item_id): return {'data': {}}",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/fastapi_app.py",
                "\n".join(
                    [
                        "from fastapi import FastAPI",
                        "from .mirror_api import build_collection_document, build_item_document, load_resource_specs",
                        "def create_app():",
                        '    app = FastAPI(openapi_url="/jsonapi.json")',
                        "    for spec in load_resource_specs(None):",
                        "        app.add_api_route(spec.endpoint, build_collection_document, methods=['GET'])",
                        "        app.add_api_route(spec.endpoint + '/{item_id}', build_item_document, methods=['GET'])",
                        "    return app",
                    ]
                )
                + "\n",
            )

            issues = audit_backend_orm_safrs(repo_root)
            self.assertTrue(any("OpenAPI to /jsonapi.json" in issue for issue in issues))
            self.assertTrue(any("missing SafrsFastAPI" in issue for issue in issues))
            self.assertTrue(any("EXPOSED_MODELS" in issue for issue in issues))
            self.assertTrue(any("SAFRSBase-backed" in issue for issue in issues))
            self.assertTrue(any("SQLAlchemy ORM model definitions" in issue for issue in issues))
            self.assertTrue(any("manual collection/item document adapters" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
