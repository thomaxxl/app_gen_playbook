# SAFRS Required Reading

These tracked notes are the mandatory SAFRS design inputs for backend design
and backend implementation work.

Backend authors MUST read these files before approving a custom endpoint,
custom read model, `JABase`, or other non-default API lane for DB-backed
resources or relationships:

- [Quickstart-FastAPI.md](Quickstart-FastAPI.md)
- [API-Functionality.md](API-Functionality.md)
- [Relationships-and-Includes.md](Relationships-and-Includes.md)
- [JSON-encoding-and-decoding.md](JSON-encoding-and-decoding.md)
- [RPC.md](RPC.md)
- [Instances-without-a-SQLAlchemy-model.md](Instances-without-a-SQLAlchemy-model.md)

These notes are intentionally short. They exist to make the SAFRS-first API
design lane explicit inside the playbook and to point authors at the local
examples already present in this workspace.
