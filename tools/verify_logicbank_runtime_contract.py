#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import textwrap
from pathlib import Path


def _repo_root(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parents[1]


def _backend_site_packages(repo_root: Path) -> Path:
    candidates = sorted((repo_root / "app" / "backend" / ".venv" / "lib").glob("python*/site-packages"))
    if not candidates:
        raise FileNotFoundError("backend runtime site-packages directory not found under app/backend/.venv/lib")
    return candidates[0]


def _backend_python(repo_root: Path) -> Path:
    backend_python = repo_root / "app" / "backend" / ".venv" / "bin" / "python"
    if not backend_python.exists():
        raise FileNotFoundError("backend runtime python not found under app/backend/.venv/bin/python")
    return backend_python


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _signature(source: str, name: str) -> str:
    match = re.search(
        rf"def\s+{re.escape(name)}\((.*?)\)\s*(?:->\s*([^:]+))?:",
        source,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"could not find function signature for {name}")
    raw_args = match.group(1)
    raw_return = match.group(2)
    args = " ".join(part.strip() for part in raw_args.splitlines())
    args = re.sub(r"\s+", " ", args).strip()
    if raw_return:
        returned = " ".join(part.strip() for part in raw_return.splitlines())
        returned = re.sub(r"\s+", " ", returned).strip()
        return f"({args}) -> {returned}"
    return f"({args})"


def _run_executable_smoke(repo_root: Path) -> dict[str, object]:
    backend_python = _backend_python(repo_root)
    script = textwrap.dedent(
        """
        import io
        import json
        import logging

        import logic_bank
        from logic_bank.logic_bank import LogicBank, Rule
        from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
        from sqlalchemy.orm import declarative_base, relationship, sessionmaker

        Base = declarative_base()


        class Parent(Base):
            __tablename__ = "parent"

            id = Column(Integer, primary_key=True)
            name = Column(String, nullable=False)
            items = relationship("Item", back_populates="parent")


        class Item(Base):
            __tablename__ = "item"

            id = Column(Integer, primary_key=True)
            parent_id = Column(Integer, ForeignKey("parent.id"), nullable=False)
            label = Column(String, nullable=False)
            parent_name_snapshot = Column(String)
            parent = relationship("Parent", back_populates="items")
            audits = relationship("ItemAudit", back_populates="item")


        class ItemAudit(Base):
            __tablename__ = "item_audit"

            id = Column(Integer, primary_key=True)
            item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
            event_name = Column(String, nullable=False)
            parent_name_snapshot = Column(String)
            item = relationship("Item", back_populates="audits")


        captured = {}


        def record_audit(row=None, old_row=None, logic_row=None, **_kwargs):
            captured["callback_row_type"] = type(row).__name__ if row is not None else None
            captured["callback_old_row_is_none"] = old_row is None
            captured["logic_row_type"] = type(logic_row).__name__ if logic_row is not None else None
            logic_row.log("logicbank smoke early event fired")
            audit = logic_row.new_logic_row(ItemAudit)
            audit.link(to_parent=logic_row)
            audit.row.event_name = "insert"
            audit.row.parent_name_snapshot = row.parent.name
            audit.insert(reason="smoke nested audit")


        def declare_logic():
            Rule.copy(derive=Item.parent_name_snapshot, from_parent=Parent.name)
            Rule.early_row_event(Item, calling=record_audit)


        engine = create_engine("sqlite:///:memory:")
        Session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        LogicBank.activate(session=Session, activator=declare_logic)

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logic_bank.logic_logger.addHandler(handler)
        logic_bank.logic_logger.setLevel(logging.INFO)

        session = Session()
        parent = Parent(name="Northwind")
        session.add(parent)
        session.flush()
        item = Item(parent=parent, label="Widget")
        session.add(item)
        session.commit()
        session.refresh(item)
        audits = session.query(ItemAudit).filter_by(item_id=item.id).all()

        logic_bank.logic_logger.removeHandler(handler)

        smoke = {
            "callback_row_type": captured.get("callback_row_type"),
            "callback_old_row_is_none": captured.get("callback_old_row_is_none"),
            "logic_row_type": captured.get("logic_row_type"),
            "item_parent_name_snapshot": item.parent_name_snapshot,
            "audit_count": len(audits),
            "audit_parent_name_snapshot": audits[0].parent_name_snapshot if audits else None,
            "log_contains_message": "logicbank smoke early event fired" in stream.getvalue(),
            "log_contains_nested_insert": "smoke nested audit" in stream.getvalue(),
        }
        smoke["verified"] = (
            smoke["callback_row_type"] == "Item"
            and smoke["callback_old_row_is_none"] is True
            and smoke["logic_row_type"] == "LogicRow"
            and smoke["item_parent_name_snapshot"] == "Northwind"
            and smoke["audit_count"] == 1
            and smoke["audit_parent_name_snapshot"] == "Northwind"
            and smoke["log_contains_message"] is True
            and smoke["log_contains_nested_insert"] is True
        )
        print(json.dumps(smoke))
        """
    )
    completed = subprocess.run(
        [str(backend_python), "-c", script],
        capture_output=True,
        check=False,
        cwd=repo_root,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "logicbank executable smoke failed: "
            f"stdout={completed.stdout.strip()} stderr={completed.stderr.strip()}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"logicbank executable smoke returned invalid json: {completed.stdout!r}") from exc


def verify(repo_root: Path) -> dict[str, object]:
    site_packages = _backend_site_packages(repo_root)
    logicbank_root = site_packages / "logic_bank"
    init_path = logicbank_root / "__init__.py"
    logic_bank_source = _read(logicbank_root / "logic_bank.py")
    logic_row_source = _read(logicbank_root / "exec_row_logic" / "logic_row.py")
    row_event_source = _read(logicbank_root / "rule_type" / "row_event.py")
    listeners_source = _read(logicbank_root / "exec_trans_logic" / "listeners.py")
    executable_smoke = _run_executable_smoke(repo_root)

    return {
        "logicbank_module": str(init_path),
        "logicbank_activate_signature": _signature(logic_bank_source, "activate"),
        "logicrow_log_signature": _signature(logic_row_source, "log"),
        "logicrow_new_logic_row_signature": _signature(logic_row_source, "new_logic_row"),
        "event_callback_keywords_verified": "row=logic_row.row, old_row=logic_row.old_row, logic_row=logic_row" in row_event_source,
        "logic_row_log_usage_verified": "each_logic_row.log(" in listeners_source,
        "event_tokens_verified": {
            "early_row_event": "EarlyRowEvent" in row_event_source,
            "row_event": "RowEvent" in row_event_source,
            "commit_row_event": "CommitRowEvent" in row_event_source,
            "after_flush_row_event": "AfterFlushRowEvent" in row_event_source,
        },
        "executable_smoke": executable_smoke,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the installed LogicBank runtime contract.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = _repo_root(args.repo_root)
    payload = verify(repo_root)

    required_truthy = {
        "event_callback_keywords_verified": payload.get("event_callback_keywords_verified"),
        "logic_row_log_usage_verified": payload.get("logic_row_log_usage_verified"),
        "executable_smoke_verified": payload.get("executable_smoke", {}).get("verified"),
    }
    required_truthy.update(payload.get("event_tokens_verified", {}))
    failures = [name for name, ok in required_truthy.items() if not ok]

    if args.json:
        print(json.dumps({
            "ok": not failures,
            "payload": payload,
            "failures": failures,
        }, indent=2))
    else:
        print("LogicBank runtime verification")
        print(f"- module: {payload['logicbank_module']}")
        print(f"- LogicBank.activate: {payload['logicbank_activate_signature']}")
        print(f"- LogicRow.log: {payload['logicrow_log_signature']}")
        print(f"- LogicRow.new_logic_row: {payload['logicrow_new_logic_row_signature']}")
        print(f"- executable smoke: {'ok' if payload['executable_smoke']['verified'] else 'failed'}")
        print(f"- verified callback/event notes: {'ok' if not failures else ', '.join(failures)}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
