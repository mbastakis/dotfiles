# AGENTS.md -- Magenta Apprentice Platform Engineering Workspace

This workspace is primarily GitOps + Terraform infrastructure.
When operating here, focus on `argocd/` and `iac/` first.

## Agent Scope

- Primary concerns: Helm templating, ArgoCD app-of-apps, env wiring, AWS dependencies.
- Skip app-source unit-test workflows unless explicitly requested.
- Treat each top-level directory as an independent Git repository.

## Platform Repository Map

- `argocd/root-app-of-apps/`: root app-of-apps Helm charts for dev/playground/prod.
- `argocd/*-root-fiber-app-of-apps/`: environment-specific Fiber ArgoCD Applications.
- `argocd/helm-charts/magenta-apprentice-helm/`: main Magenta Apprentice chart.
- `argocd/helm-charts/`: supporting charts (keycloak, langfuse, trigger, anonymization, ner-model, sap-gui).
- `iac/aws/iac-dev/` and `iac/aws/iac-playground/`: app dependencies per account.
- `iac/aws/aicc-aws-cluster/`: shared cluster infra for staging/prod-style envs.

## Environments and AWS Accounts

| Account | Account ID | Cluster | Environments |
|---|---|---|---|
| Dev | `076811069858` | `aicc-cndtag-dev` | `dev`, `staging`, `feature-branch` |
| Playground | `970547348009` | `aicc-playground` | `playground` |
| Prod | `620453162886` | `aicc-prod-ec1-shared-eks-0` | `prod` |

## ArgoCD Topology (How Things Connect)

1. Root charts in `argocd/root-app-of-apps/<env>-root-app-of-apps/` create `AppProject app-of-apps` plus one `Application` per entry in `values.yaml`.
2. The `fiber` project points to `argocd/dev-root-fiber-app-of-apps/`, `argocd/playground-root-fiber-app-of-apps/`, or `argocd/prod-root-fiber-app-of-apps/`.
3. Fiber app-of-apps repos define app-level Applications (`magenta-apprentice` in all envs, `anonymization-service` in playground/prod).
4. Dev has a feature-branch controller app that watches `argocd/helm-charts/magenta-apprentice-helm/feature-branch/applications/`.

## Magenta Apprentice Dependencies

- Chart dependency: Bitnami PostgreSQL (`postgresql.enabled` gates subchart usage).
- Database mode:
  - `playground`, `feature-branch`: in-cluster PostgreSQL
  - `dev`, `staging`, `prod`: external AWS RDS (`externalDatabase`)
- Auth: Keycloak OIDC enabled in `dev/staging/prod`, disabled in `playground/feature-branch`.
- Storage: S3 report buckets via `REPORT_STORAGE_*` values/env vars.
- Observability: backend/evaluator point to in-cluster Langfuse service.
- Orchestration: backend uses `agent-gateway`; gateway provisions MCP servers (`playwright-mcp`, `playwright-vnc`).
- Cross-service dependencies:
  - `trigger-service` uses Magenta Apprentice API + Keycloak token endpoint
  - `anonymization-service` needs `ner-model` endpoint (`nerModelUrl`)

## Validation Commands (Build/Lint/Test Equivalent)

### Root app-of-apps chart validation

```bash
helm lint argocd/root-app-of-apps/dev-root-app-of-apps -f argocd/root-app-of-apps/dev-root-app-of-apps/values.yaml
helm template dev-root-app-of-apps argocd/root-app-of-apps/dev-root-app-of-apps -f argocd/root-app-of-apps/dev-root-app-of-apps/values.yaml

# Single-template validation (single-test equivalent)
helm template dev-root-app-of-apps argocd/root-app-of-apps/dev-root-app-of-apps -f argocd/root-app-of-apps/dev-root-app-of-apps/values.yaml -s templates/projects.yaml
```

### Magenta Apprentice chart validation

```bash
cd argocd/helm-charts/magenta-apprentice-helm
helm dependency build .
helm lint . -f default-values.yaml -f dev/values.yaml

sops -d dev/secrets.enc.yaml > /tmp/dev-secrets.raw.yaml
helm template magenta-apprentice . -f default-values.yaml -f dev/values.yaml -f /tmp/dev-secrets.raw.yaml
rm /tmp/dev-secrets.raw.yaml

# Render a single resource for targeted debugging
helm template magenta-apprentice . -f default-values.yaml -f dev/values.yaml -s templates/agent-gateway/configmap.yaml
```

### Feature-branch validation

```bash
cd argocd/helm-charts/magenta-apprentice-helm
helm template ma-fb-feat-aiccn-2394 . -f default-values.yaml -f feature-branch/values.yaml -f feature-branch/values/feat-aiccn-2394-values.yaml
kubectl apply --dry-run=server -f feature-branch/applications/feat-aiccn-2394.yaml
```

### Supporting chart quick checks

```bash
helm lint argocd/helm-charts/trigger-service-helm -f argocd/helm-charts/trigger-service-helm/default-values.yaml -f argocd/helm-charts/trigger-service-helm/dev/values.yaml
helm lint argocd/helm-charts/keycloak-helm -f argocd/helm-charts/keycloak-helm/default-values.yaml -f argocd/helm-charts/keycloak-helm/dev-values.yaml
cd argocd/helm-charts/langfuse-helm && ./helm-template.sh dev
```

### Terraform validation

```bash
cd iac/aws/aicc-aws-cluster
make plan env=prod tfvars=aicc-prod
make plan env=staging tfvars=staging

cd iac/aws/iac-dev/terraform
terraform fmt -recursive && terraform validate && terraform plan

cd iac/aws/iac-playground/terraform
terraform fmt -recursive && terraform validate && terraform plan
```

## Code Style Guidelines (Platform)

### YAML / Helm formatting and structure

- Use 2-space indentation; no tabs.
- Keep env var values quoted strings in rendered manifests.
- Keep baseline in `default-values.yaml`; keep only env deltas in env values files.
- Keep secrets only in SOPS-encrypted `*.enc.yaml` files.

### Helm template conventions

- Reuse helpers from `templates/_helpers.tpl` for labels, selectors, images, service accounts.
- Keep component naming consistent: `backend`, `frontend`, `user-interface`, `agent-gateway`, `evaluator`.
- Use conditionals/`with` to avoid emitting empty YAML blocks.
- Preserve key casing conventions:
  - values: camelCase (`mcpPath`, `ssePath`, `additionalUrls`, `staticUrl`)
  - generated app config where required: snake_case

### ArgoCD manifest conventions

- Keep finalizer `resources-finalizer.argocd.argoproj.io`.
- Keep automated sync with `prune` + `selfHeal` unless release strategy requires otherwise.
- Preserve existing sync options (`ServerSideApply`, `PruneLast`, `FailOnSharedResource`, `CreateNamespace` where used).
- Preserve value file ordering in Application specs:
  1. defaults
  2. environment/base overrides
  3. branch overrides (if any)
  4. secrets (`secrets://...` for ArgoCD)

### Error handling and safety

- Fail fast for invalid critical config (`fail` / `required` in templates).
- Ensure DB mode stays valid (`externalDatabase.enabled` xor `postgresql.enabled`).
- Do not introduce insecure defaults for auth/ingress/secrets.

## Cursor and Copilot Rules

- Cursor rules exist only in `magenta-apprentice/.cursor/rules/`:
  - `ods-rules.mdc`
  - `merge-request.mdc`
- No `.cursorrules` found at workspace root.
- No `.github/copilot-instructions.md` found in this workspace.
- These rules are mostly frontend/MR oriented, typically not platform-change critical.
