# Backend Templates

These snippets correspond to:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../README.md](../../../README.md)
- [../../../specs/contracts/rules/README.md](../../../specs/contracts/rules/README.md)

Use them to assemble the generated backend skeleton under `app/backend/`
described in this playbook.

Backend template decision tree:

1. persisted DB row data => SAFRS resource
2. DB relationship => ORM relationship plus SAFRS relationship URL/include
3. computed resource field => `jsonapi_attr`
4. explicit operation => `jsonapi_rpc`
5. only then consider `JABase` or another documented exception

Suggested copy order:

1. `requirements.txt.md`
2. `config.py.md`
3. `db.py.md`
4. `models.py.md`
5. `../rules/rules.py.md`
6. `bootstrap.py.md`
7. `__init__.py.md`
8. `app.py.md`
9. `fastapi_app.py.md`
10. `run.py.md`
11. `conftest.py.md`
12. `test_api_contract.py.md`
13. `test_api_contract_fallback.py.md`
14. `test_bootstrap.py.md`
15. `../rules/test_rules.py.md`
16. `../project/run.sh.md`
17. `../project/README.app.md`
18. `run_with_spa.py.md` if the app should serve a built SPA itself
19. `files/README.md` plus the `files/` snippets if the app supports uploaded
    media
20. `test_uploads.py.md` if the app supports uploaded media
