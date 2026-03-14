# Files Contract

This directory is the detailed file-storage, media-serving, and frontend
upload contract for playbook-generated apps that support uploaded binaries.

This directory is part of the playbook and defines the implementation
contract. Generated application source files must be written under `app/`, not
here.

Normative language in this directory MUST be interpreted using RFC 2119-style
semantics:

- `MUST` / `MUST NOT`: absolute implementation requirements
- `SHOULD` / `SHOULD NOT`: strong defaults that MAY be changed only with an
  explicit documented reason
- `MAY`: permitted optional behavior

The agent MUST NOT load every file by default. It MUST load only the parts
needed for the current task.

The agent MUST load these files when the app includes uploaded files, served
media, or attachment metadata:

- [storage-and-serving.md](storage-and-serving.md)
- [uploads-and-frontend-integration.md](uploads-and-frontend-integration.md)

This directory is a supporting contract for the uploads feature pack.

Rules:

- the agent MUST normally enter this directory only through
  `../../features/uploads/README.md`
- the agent MUST NOT treat this directory as a core contract layer
- if uploads are disabled or undecided, this directory MUST remain unloaded

The spec in this directory is the contract. The agent MUST NOT invent a
database-binary upload design, raw-path frontend contract, or direct-DB BLOB
model outside the rules defined here.
