# Upstream Synchronization Report

Sync date: 2026-07-19

## Recovery points (created before any synchronization work)

| Repository | Original branch | Original HEAD | Backup branch | Backup tag | Working branch |
|---|---|---|---|---|---|
| `Aref20/saleor` | `main` | `de38395214b55e1ceb4f54b99c7d0919231ea585` | `backup/pre-upstream-sync-20260719` | `pre-upstream-sync-20260719` | `chore/sync-saleor-upstream-20260719` |
| `Aref20/saleor-dashboard` | `main` | `161449d37cd6d0c9aa4030f25d4cd4f3070ea69f` | `backup/pre-upstream-sync-20260719` | `pre-upstream-sync-20260719` | `chore/sync-dashboard-upstream-20260719` |

Remotes in both clones: `origin` → `Aref20/...`, `upstream` → `saleor/...`. All upstream
branches and tags fetched.

## Synchronization targets

### Production target (selected)

| Component | Target | Verified facts |
|---|---|---|
| Saleor Core | tag `3.23.18` (released 2026-07-14) | Latest stable release of the 3.23 line. Fork merge-base `bb7e9fbb23` **is an ancestor** of this tag (verified with `git merge-base --is-ancestor`), so a true fast-history merge is possible: 242 upstream commits to integrate. |
| Saleor Dashboard | tag `3.23.17` (released 2026-07-16) | Latest stable Dashboard release generated against the 3.23 schema. Fork merge-base `8c3bd9e374` is an ancestor; 365 upstream commits to integrate. |
| GraphQL schema | Core 3.23.18 `saleor/graphql/schema.graphql`, regenerated post-merge | Dashboard codegen re-run against this schema (see Phase D). |
| Storefront | latest `saleor/storefront` default-branch revision at project creation time | Recorded in the storefront repository's own docs. |

**Why these versions are compatible:** Core 3.23.18 and Dashboard 3.23.17 are the current
tips of the same 3.23 minor line; Saleor releases Dashboard patches against the matching
Core minor schema. The fork baselines (Core `3.23.0-a.0` dev line, Dashboard `3.22.20`)
are both ancestors of these tags, so nothing is skipped or rewound.

**Known upgrade risks:**

1. The fork's gateway plugins use the legacy Payments API (`BasePlugin` payment hooks).
   Risk that 3.23 stable removed/renamed hooks — mitigated by verifying the surviving
   built-in gateways (Adyen/NP Atobarai) after merge and running the gateway test suites.
2. Dashboard 3.22 → 3.23 crosses a minor boundary: regenerated GraphQL types may surface
   type errors in any customized UI. (The fork has no custom UI — risk is low.)
3. `uv.lock` / dependency drift — resolved by regenerating the lock file, not merging it.
4. Upstream main (development branch) is intentionally NOT the production target.

**Rollback point:** `pre-upstream-sync-20260719` tag in each repository
(`git checkout main && git reset --hard pre-upstream-sync-20260719` restores the exact
pre-sync state; backup branches provide the same commit).

### Upstream-main tracking target (optional, non-production)

A development integration branch per repo may be created after the production sync to
prove the custom code compiles/tests against current upstream `main`
(Core `upstream/main`, 305 commits ahead of fork base at audit time). This branch is
explicitly not deployable unless all stability checks pass.

## Windows workarounds applied to the local clones (not committed)

- `saleor-dashboard`: upstream tracks a file literally named
  `.github/instructions/*.instructions.md`; `*` is invalid in Windows filenames and both
  checkout and index writes fail. Local repo config: `core.protectNTFS=false` plus a
  non-cone sparse-checkout rule excluding `/.github/instructions/`. The path stays in
  the index/history untouched; it is simply never materialized in the working tree.
- `saleor-dashboard`: `core.longpaths=true` for deep node paths.

## Conflict log

(Recorded during Phase C/D merges — see sections below.)

### Core merge (3.23.18 → chore/sync-saleor-upstream-20260719)

_Pending._

### Dashboard merge (3.23.17 → chore/sync-dashboard-upstream-20260719)

_Pending._
