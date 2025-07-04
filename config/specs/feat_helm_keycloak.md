# Keycloak Helm Chart Refactoring Specification

## Overview
This specification outlines the refactoring plan for the Keycloak Helm chart to align with established conventions used across other helm-charts in the aws-playground project. The refactoring will address secret management, configuration structure, and deployment practices to ensure consistency and security.

## Current State Analysis

### Issues Identified
1. **Missing Dependencies**: Chart depends on Bitnami Keycloak 24.4.13 but dependencies not downloaded
2. **Insecure Secret Management**: Passwords stored as environment variable placeholders (`${KEYCLOAK_ADMIN_PWD}`)
3. **Invalid Ingress Configuration**: References to `nonexistingservice` in extra paths
4. **Empty SOPS Configuration**: `.sops.yaml` exists but is empty
5. **Inconsistent Documentation**: README contains incorrect title and spelling errors
6. **Missing Testing Scripts**: No `helm-template.sh` for local testing

### Current File Structure
```
keycloak-helm/
├── Chart.yaml
├── values.yaml (contains secrets as env vars)
├── default-values.yaml
├── README.md (incorrect content)
├── .sops.yaml (empty)
└── .gitignore
```

## Requirements

### 1. Secret Management Compliance
- **R1.1**: Migrate from environment variable placeholders to SOPS-encrypted secrets
- **R1.2**: Create `playground-secrets.enc.yaml` following project conventions
- **R1.3**: Configure SOPS with AWS KMS key: `arn:aws:kms:eu-central-1:970547348009:alias/argocd-sops`
- **R1.4**: Ensure ArgoCD compatibility with `secrets://` prefix

### 2. Configuration Structure Alignment
- **R2.1**: Maintain separation between base config (`default-values.yaml`) and secrets
- **R2.2**: Remove secrets from `values.yaml` or repurpose file appropriately
- **R2.3**: Follow two-file pattern (base + encrypted secrets) used by other charts

### 3. Deployment Readiness
- **R3.1**: Resolve Helm dependencies (`helm dependency update`)
- **R3.2**: Fix ingress configuration issues
- **R3.3**: Create local testing script (`helm-template.sh`)
- **R3.4**: Ensure chart can be deployed via ArgoCD

### 4. Documentation and Standards
- **R4.1**: Fix README.md title and spelling errors
- **R4.2**: Document installation and configuration procedures
- **R4.3**: Align with Keycloak security best practices
- **R4.4**: Follow Deutsche Telekom compliance requirements

## Implementation Plan

### Phase 1: Dependencies and Basic Fixes
1. **Download Dependencies**
   ```bash
   cd argocd/helm-charts/keycloak-helm
   helm dependency update
   ```

2. **Fix Documentation**
   - Update README.md title from "langfuse-helm" to "keycloak-helm"
   - Fix spelling from "Keycloack" to "Keycloak"
   - Add proper installation instructions

3. **Fix Ingress Configuration**
   - Replace `nonexistingservice` with correct service name
   - Verify service references in extra paths

### Phase 2: Secret Management Refactoring
1. **Create SOPS Configuration**
   ```yaml
   # .sops.yaml
   creation_rules:
     - kms: arn:aws:kms:eu-central-1:970547348009:alias/argocd-sops
       encrypted_regex: '^(data|stringData)$'
   ```

2. **Create Encrypted Secrets File**
   ```yaml
   # playground-secrets.enc.yaml
   keycloak:
     auth:
       adminPassword: actual_encrypted_password
     postgresql:
       auth:
         postgresPassword: actual_encrypted_password
         password: actual_encrypted_password
   ```

3. **Migrate Secrets from values.yaml**
   - Remove environment variable placeholders
   - Move sensitive data to encrypted file
   - Update ArgoCD application to use `secrets://` prefix

### Phase 3: Configuration Structure Alignment
1. **Restructure default-values.yaml**
   - Keep only non-sensitive base configuration
   - Remove all password/secret references
   - Maintain operational settings (replicas, resources, etc.)

2. **Update or Remove values.yaml**
   - Option A: Remove file entirely (follow langfuse pattern)
   - Option B: Use for environment-specific overrides only
   - Ensure no secrets remain in this file

3. **Create helm-template.sh**
   ```bash
   #!/usr/bin/env bash
   helm template keycloak . -f default-values.yaml -f secrets://playground-secrets.enc.yaml
   ```

### Phase 4: Security and Compliance
1. **Keycloak Security Configuration**
   - Verify admin IP whitelist settings
   - Ensure SCRAM-SHA-256 authentication for PostgreSQL
   - Validate pod security contexts
   - Review resource limits and security profiles

2. **Database Security**
   - Confirm PostgreSQL integration settings
   - Verify database isolation configuration
   - Check connection pooling and SSL settings

3. **Monitoring and Observability**
   - Verify ServiceMonitor configuration
   - Check custom metrics for user events
   - Ensure proper logging configuration

### Phase 5: Testing and Validation
1. **Local Testing**
   - Test chart rendering with `helm-template.sh`
   - Validate generated manifests
   - Check secret resolution

2. **ArgoCD Integration**
   - Test deployment via ArgoCD
   - Verify secret decryption
   - Check application sync status

3. **Functional Testing**
   - Verify Keycloak admin access
   - Test database connectivity
   - Check ingress routing

## Detailed Implementation Steps

### Step 1: Prepare Environment
```bash
# Navigate to chart directory
cd argocd/helm-charts/keycloak-helm

# Install required tools
brew install sops helm

```

### Step 2: Download Dependencies
```bash
# Update Chart.lock and download dependencies
helm dependency update
```

### Step 3: Create SOPS Configuration
```bash
# Create .sops.yaml
cat > .sops.yaml << 'EOF'
creation_rules:
  - kms: arn:aws:kms:eu-central-1:970547348009:alias/argocd-sops
    encrypted_regex: '^(data|stringData)$'
EOF
```

### Step 4: Create Encrypted Secrets
```bash
# Create playground-secrets.enc.yaml with actual values
sops playground-secrets.enc.yaml
# Add secrets in editor, then encrypt
```

### Step 5: Update Configuration Files
1. **Remove secrets from values.yaml**
2. **Clean up default-values.yaml**
3. **Fix ingress configuration**
4. **Update README.md**

### Step 6: Create Testing Script
```bash
# Create helm-template.sh
cat > helm-template.sh << 'EOF'
#!/usr/bin/env bash
helm template keycloak . -f default-values.yaml -f secrets://playground-secrets.enc.yaml
EOF
chmod +x helm-template.sh
```

### Step 7: Update ArgoCD Application
```yaml
# In ArgoCD application manifest
spec:
  source:
    helm:
      valueFiles:
        - default-values.yaml
        - secrets://playground-secrets.enc.yaml
```

## Security Considerations

### SOPS Encryption
- Use AWS KMS with organization-controlled keys
- Encrypt entire secret values, not just sensitive parts
- Maintain audit trail of secret modifications

### Keycloak Security
- Enable IP whitelisting for admin access
- Use strong authentication methods
- Implement proper session management
- Configure secure database connections

### Network Security
- Implement proper ingress rules
- Use TLS termination at ingress
- Configure network policies if required

## Acceptance Criteria

### Configuration Management
- [ ] All secrets migrated to SOPS-encrypted file
- [ ] Environment variable placeholders removed
- [ ] ArgoCD can decrypt and apply secrets
- [ ] Chart follows project conventions

### Deployment Readiness
- [ ] Helm dependencies resolved
- [ ] Chart templates render without errors
- [ ] ArgoCD can sync application successfully
- [ ] Keycloak pods start and become ready

### Security Compliance
- [ ] No plaintext secrets in repository
- [ ] SOPS encryption working correctly
- [ ] Database connections secure
- [ ] Admin access properly restricted

### Documentation and Testing
- [ ] README.md updated and accurate
- [ ] helm-template.sh script works
- [ ] Installation instructions provided
- [ ] Configuration examples included

### Functional Validation
- [ ] Keycloak web interface accessible
- [ ] Admin login working
- [ ] Database integration functional
- [ ] Ingress routing working
- [ ] Monitoring metrics available

## Success Metrics

1. **Security**: Zero plaintext secrets in repository
2. **Consistency**: Chart follows all project conventions
3. **Reliability**: Chart deploys successfully via ArgoCD
4. **Maintainability**: Clear documentation and testing procedures
5. **Compliance**: Meets Deutsche Telekom security requirements

## Risk Assessment

### High Risk
- **Secret Exposure**: Improper SOPS configuration could expose secrets
- **Service Disruption**: Incorrect migration could break existing deployments
- **Access Loss**: Wrong admin configuration could lock out administrators

### Medium Risk
- **Deployment Failure**: Dependency issues could prevent deployment
- **Configuration Drift**: Inconsistent patterns could cause maintenance issues

### Mitigation Strategies
- Test in non-production environment first
- Backup existing configuration before changes
- Use staging ArgoCD application for validation
- Implement proper secret rotation procedures

## Post-Implementation Actions

1. **Update team documentation** with new procedures
2. **Train team members** on SOPS usage
3. **Set up monitoring** for chart deployment health
4. **Plan regular security reviews** of configuration
5. **Document lessons learned** for future chart migrations

## Notes

- This refactoring aligns with the patterns established by LiteLLM and test-repo charts
- The approach maintains backward compatibility while improving security
- SOPS integration enables proper secret management in GitOps workflows
- The changes support Deutsche Telekom's infrastructure security requirements
