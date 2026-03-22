# Logic Overview

Portable summary of the core LogicBank stance used by the playbook:

- declarative `Rule.copy`, `Rule.formula`, `Rule.sum`, `Rule.count`, and
  `Rule.constraint` are the default rule lanes
- transactional invariants belong on the shared ORM commit path
- endpoint/service code may integrate with rules, but it is not the default
  business-rule owner
- advanced events exist, but they are an exception lane that must be justified
