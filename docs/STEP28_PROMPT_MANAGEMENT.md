# STEP 28: Prompt Management, Versioning, Release, and Experimentation

See full architecture documentation in [docs/prompt_management_architecture.md](file:///c:/Users/HP/Desktop/LLM%20Layer/docs/prompt_management_architecture.md).

## Quick Reference Summary

- **Package**: `backend/app/services/prompts/`
- **Database Tables**:
  - `prompts`
  - `prompt_versions`
  - `prompt_releases`
  - `prompt_experiments`
  - `prompt_experiment_variants`
  - `prompt_experiment_assignments`
- **Migration**: `025_prompt_management.py`
- **API Endpoints**:
  - `/api/prompts` (CRUD, list with filters)
  - `/api/prompts/{id}/versions` (monotonic version creation, list)
  - `/api/prompts/{id}/versions/{v_id}/publish` (render immutable)
  - `/api/prompts/{id}/versions/diff` (unified line diff, masked secrets)
  - `/api/prompts/{id}/releases` (list releases)
  - `/api/prompts/{id}/releases` (promote to environment)
  - `/api/prompts/{id}/rollback` (rollback release)
  - `/api/prompts/{id}/resolve` (resolve prompt key + environment)
  - `/api/prompts/{id}/preview` (safe variable rendering preview)
  - `/api/prompts/{id}/test` (test execution through AI Gateway)
  - `/api/prompt-experiments` (A/B testing with deterministic allocation)
- **Frontend Pages**:
  - `/app/prompts` (Prompt Registry)
  - `/app/prompts/new` (New Prompt Draft)
  - `/app/prompts/[promptId]` (Hub: Editor, Versions & Diff, Releases, Experiments)
