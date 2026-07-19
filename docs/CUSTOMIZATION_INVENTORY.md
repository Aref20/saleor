# Customization Inventory

Audit date: 2026-07-19
Auditor: automated repository inspection (git merge-base analysis, file diffs, commit-by-commit review)

This document inventories every deviation of the customized forks from their upstream sources:

| Repository | Fork | Upstream | Fork HEAD | Merge base with upstream |
|---|---|---|---|---|
| Core | `Aref20/saleor` (main) | `saleor/saleor` | `de38395214b55e1ceb4f54b99c7d0919231ea585` | `bb7e9fbb23dbe57d7af07fe33f8eb227c9241be6` (3.23.0-a.0 dev line) |
| Dashboard | `Aref20/saleor-dashboard` (main) | `saleor/saleor-dashboard` | `161449d37cd6d0c9aa4030f25d4cd4f3070ea69f` | `8c3bd9e374f2438604917f5294d273c903fda395` (3.22.20) |

Custom commits not present upstream:

**Core (5 commits ahead, 305 behind upstream main at audit time):**

1. `91b3ab563c` — Add Cash on Delivery payment gateway plugin (2026-01-28)
2. `4cafefa325` — Pin Python version to 3.12 for Heroku deployment (2026-01-29)
3. `4b7e472d17` — Add setuptools dependency to fix pkg_resources ImportError (2026-01-29)
4. `dc6f2ed4a6` — Update uv.lock to reflect pyproject.toml changes (2026-01-29)
5. `de38395214` — HyperPay payment gateway integration + seeding and connection test scripts (2026-02-03)

**Dashboard (1 commit ahead, 366 behind upstream main at audit time):**

1. `161449d37c` — vite.config.js entry path change (2026-01-29). Despite the commit message
   ("Add generated GraphQL types, hooks, and type policies…"), the actual diff is a single
   line in `vite.config.js`; the regenerated GraphQL artifacts produced no diff against
   what upstream already tracks.

## Customization matrix

| Area | Repository | Files | Custom behavior | Upstream conflict risk | Preservation strategy | Test coverage |
|---|---|---|---|---|---|---|
| Cash on Delivery gateway | Core | `saleor/payment/gateways/cash_on_delivery/{__init__.py,plugin.py,tests/*}` | Legacy-API `BasePlugin` payment gateway: authorize at checkout, manual capture on delivery, currency allow-list, no token required | LOW (new files, no upstream counterpart) | **Preserve unchanged**; verify legacy payment-plugin hooks still exist in 3.23.18; adapt only if the `BasePlugin` payment interface changed | `tests/test_cash_on_delivery.py` (103 lines) |
| COD plugin registration | Core | `saleor/settings.py` (`BUILTIN_PLUGINS` +1 line) | Registers COD plugin | MEDIUM (upstream edits the same list) | **Preserve** — re-apply line during conflict resolution | covered indirectly by plugin tests |
| HyperPay gateway | Core | `saleor/payment/gateways/hyperpay/{__init__.py,consts.py,hyperpay_api.py,plugin.py,tests/*}` | Legacy-API `BasePlugin` gateway for HyperPay (MENA: VISA/MASTER/MADA/AMEX/APPLEPAY). Copy-and-Pay widget flow: `prepare_checkout` returns checkout id (client token), status polling, capture/refund/void via back-office API, test/live endpoint separation, result-code regex mapping | LOW (new files) | **Preserve + adapt**; credentials come from plugin configuration (Access Token uses `ConfigurationTypeField.SECRET`); verify against 3.23.18 plugin interface | `tests/test_hyperpay.py` (263 lines) |
| HyperPay plugin registration | Core | `saleor/settings.py` (`BUILTIN_PLUGINS` +1 line) | Registers HyperPay plugin | MEDIUM (same list) | **Preserve** — re-apply during conflict resolution | indirect |
| Windows compatibility | Core | `saleor/core/rlimit.py` | `import resource` wrapped in try/except (module is POSIX-only); `validate_and_set_rlimit` becomes a no-op on Windows | MEDIUM (upstream may modify this file) | **Preserve** — required for local development on Windows; harmless on Linux | none (trivial guard) |
| Python pin | Core | `.python-version` (new), `.gitignore` (+1) | Pins Python 3.12 for Heroku/uv | LOW | **Preserve** | n/a |
| Dependency changes | Core | `pyproject.toml` | (a) `pytest-memray` removed from dev deps (POSIX-only, breaks Windows installs); (b) `setuptools` added (pkg_resources needed at runtime on Python 3.12 Heroku) | MEDIUM–HIGH (upstream bumps deps frequently) | **Preserve intent, re-verify**: keep `setuptools` if anything still imports `pkg_resources` after sync; keep memray removal (document as Windows-dev accommodation; CI on Linux may re-add) | n/a |
| Lock file | Core | `uv.lock` | Regenerated after the above | HIGH (upstream regenerates constantly) | **Regenerate** with `uv lock` after merge — never hand-merged | n/a |
| Dev container | Core | `.devcontainer/backend.env`, `.devcontainer/docker-compose.yml` | Exposes API on host `:8000`; moves Postgres host port to `5435`; adds `ALLOWED_CLIENT_HOSTS` / `ALLOWED_GRAPHQL_ORIGINS` for a localhost storefront | LOW | **Preserve unchanged** (dev-only, no production impact) | n/a |
| Debug scripts | Core | `check_origins.py`, `check_settings.py`, `settings_output.txt`, `debug_hyperpay.py`, `debug_hyperpay_list.py`, `debug_output.txt`, `list_metadata.py`, `list_metadata_file.py`, `metadata_output.txt`, `test_db_conn.py` | One-off local debugging aids and their captured output | LOW | **Remove** — temporary artifacts; audited for secrets (none found: only default `saleor:saleor@localhost` dev credentials and mock values). Their loss is documented here. | n/a |
| Seed scripts | Core | `seed_basics.py`, `saleor/seed_produce.py`, `saleor/seed_produce_shell.py`, `saleor/seed_produce_simple.py` | Three near-duplicate variants of a "Fresh Produce" demo-catalog seeder (categories, product type, products, channel listings, stock) plus a basics bootstrap | LOW | **Consolidate**: keep one cleaned, idempotent utility at `scripts/seed_fresh_finds.py`; remove the duplicates. Kept separate from debugging utilities per policy. | manual (idempotent `get_or_create`) |
| Vite entry path | Dashboard | `vite.config.js` | `createHtmlPlugin` entry changed from `path.resolve(__dirname, "src", "index.tsx")` to `"/index.tsx"` — Windows `path.resolve` produces a backslash absolute path that `vite-plugin-html` rejects | MEDIUM (upstream touches vite config regularly) | **Preserve intent**: re-verify after sync; keep the POSIX-style entry if upstream still uses `path.resolve` | dev-build smoke |
| Generated GraphQL artifacts | Dashboard | `src/graphql/*` (no actual diff vs upstream base) | None — regeneration produced identical output | n/a | **Regenerate** from the synchronized Core schema; never hand-merge | typecheck + build |

## Classification summary

- **Preserve unchanged**: COD gateway, HyperPay gateway, `.devcontainer` changes, `.python-version`, rlimit Windows guard
- **Adapt to new upstream API**: plugin registrations in `settings.py` (conflict re-application); gateway code only if the 3.23.18 `BasePlugin` payment interface changed
- **Replace with supported Saleor mechanism**: none required at this stage. Both gateways use the legacy Payments API, which remains functional in 3.23; a Transactions-API/Payment-App migration is documented as the forward path in `PAYMENT_ARCHITECTURE.md` but is not forced during synchronization (safety rule: no broad Core rewrites during sync)
- **Remove (temporary/unsafe)**: the ten debug scripts/outputs listed above; two duplicate seed variants
- **Needs a migration**: none — no custom database migrations exist in either fork (verified: no files under `*/migrations/` differ from upstream)
- **Needs manual business verification**: HyperPay live credentials/channel setup; COD fee and eligibility policy per channel (business decisions, not code)

## Secrets audit

Every custom file was searched for credentials, tokens, endpoint secrets and connection
strings. Findings:

- `test_db_conn.py`: contains `postgres://saleor:saleor@localhost` — the default local
  docker-compose development credentials, not a real secret. File is removed anyway.
- `debug_hyperpay.py`: mock configuration values (`"test"`). Removed.
- HyperPay/COD gateway code: all credentials flow from Dashboard plugin configuration;
  the HyperPay Access Token field is declared `ConfigurationTypeField.SECRET`.
- No API keys, webhook secrets, app tokens or live endpoints are committed anywhere in
  either fork.

**Result: PASS — no secret rotation required.**
