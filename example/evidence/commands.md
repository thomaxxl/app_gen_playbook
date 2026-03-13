# Commands

Date:

- 2026-03-13

Commands executed for the current airport-app verification pass:

```bash
cd one_shot_gen/example/frontend
npm run test
npm run build
npm run test:e2e

cd one_shot_gen/example/backend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py tests/test_api_contract_fallback.py tests/test_bootstrap.py tests/test_rules.py
AIRPORT_OPS_ENABLE_TESTCLIENT=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py tests/test_rules.py
```
