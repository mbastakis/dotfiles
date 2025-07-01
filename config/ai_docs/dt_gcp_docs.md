# Deutsche Telekom Google Cloud Platform (GCP) Documentation

## Overview
The Deutsche Telekom Google Cloud Landing Zone (GCLZ) is a comprehensive enterprise cloud management platform that provides managed Google Cloud Platform services to Deutsche Telekom subsidiaries and business units. It includes automated project provisioning, security controls, billing management, and operational governance.

## Key Architecture Components

### 1. Core Platform Services
- **Cloud Shepherd (CS)**: Self-service portal at https://cs.telekom.de/ for GCP project ordering
- **CSBFF (Cloud Shepherd Backend For Frontend)**: API service bridging Cloud Shepherd and Project Factory
- **Project Factory Self-Service (PFSS)**: Terraform-based infrastructure automation
- **gclzctl**: Command-line utility tool for operators and developers (written in Go)

### 2. Project Types and Environments

#### Managed Projects
- **`dev`**: Non-production environment in public cloud
- **`prd`**: Production environment in public cloud
- Cost object assignment required
- Full network connectivity to Telekom infrastructure

#### Sandbox Projects
- **`sbx`**: Sandbox environment with 90-day lifetime and $100 budget limit
- Automatic cleanup when limits exceeded
- No cost object required (handled automatically)

#### Sovereign Controls Projects
- **`scd`**: Non-production sovereign controls environment
- **`scp`**: Production sovereign controls environment
- Enhanced security and data residency controls for compliance
- Managed by T-Systems under specific compliance requirements

### 3. Legal Entity Support
- **DE0360**: Deutsche Telekom IT (primary)
- **DE1000**: Other legal entities (VTI, DT Technik, etc.)
- Separate billing, networking, and governance per entity

## Technical Implementation

### Infrastructure Architecture
```yaml
# Core Configuration Structure
environments:
  DevOrg: Development/testing environment
  ProdOrg: Production environment
billing:
  currency: USD
  legalEntities: [DE0360, DE1000]
  retention: 24 months
network:
  architecture: Shared VPC with hub-and-spoke topology
  connectivity: Private connectivity to Telekom intranet
  regions: Europe-West3 (primary)
```

### Security and Identity Management

#### Google Groups Integration
- `mgt-[PROJECT-ID]-owners@gc.telekom.net`: Project owners
- `mgt-[PROJECT-ID]-members@gc.telekom.net`: Project members
- Integration with Cloud Identity

#### Workload Identity Federation
- GitLab CI/CD integration with OIDC
- Short-lived tokens (1-hour expiration)
- Eliminates need for JSON service account keys

#### Service Accounts
- `automation@[PROJECT-ID].iam.gserviceaccount.com`: For CI/CD automation
- Proper IAM role assignments based on project requirements

### Organization Policies and Compliance

#### Security Controls
- Resource creation restrictions
- Location constraints (Europe-focused)
- Service usage limitations
- Organization-level policy enforcement

#### Tagging Strategy
- `InfoSecClass`: Open, Internal, Confidential (default)
- `NetworkLayer`: web, app, db (for firewall controls)
- Mandatory tagging with enforcement

## Cost Management and Optimization

### Billing Architecture
- Legal entity-specific billing accounts
- Project-level cost allocation
- Monthly billing reports with cost object mapping
- Integration with SAP for internal charge-back

### Cost Optimization Features
- **Nighttime and Weekend Saving (NTS)**: Automatic VM shutdown (18:00-7:00 weekdays + weekends)
- **Committed Use Discounts (CUD)**: Automated discount optimization
- **Budget Alerts**: Project-level spending monitoring

## Common Development Patterns

### Project Creation Workflow
```bash
# Through Cloud Shepherd UI at https://cs.telekom.de/
1. Select legal entity (DE0360/DE1000)
2. Choose environment (dev/prd/sbx/scd/scp)
3. Provide cost object (for managed projects)
4. Submit request for automated provisioning
```

### GitLab CI/CD Integration
```yaml
# Example GitLab CI configuration
variables:
  GCP_PROJECT_ID: de0360-2-prd-ops-central
  SERVICE_ACCOUNT: de0360-2-prd-ops-cntrl-cicd-sa@de0360-2-prd-iac-core-0.iam.gserviceaccount.com
  WIF_PROVIDER: projects/882631720962/locations/global/workloadIdentityPools/de0360-2-ops-central/providers/de0360-2-ops-central-0

auth:
  id_tokens:
    OIDC_TOKEN:
      aud: https://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
```

### Infrastructure Blueprints
Available Terraform modules in `/blueprints/`:
- **Cloud Storage Buckets**: With versioning and uniform access
- **Compute VMs**: Private IP configurations with shared VPC
- **GitLab CI Integration**: Workload Identity Federation setup
- **Docker CI/CD**: Container-based pipeline setups

## Operational Commands

### gclzctl CLI Tool
```bash
# Billing operations
gclzctl billing generate-report --env prod
gclzctl billing list-accounts

# Configuration validation
gclzctl config validate
gclzctl docs serve  # Start documentation server
```

### Common Terraform Operations
```bash
# Initialize and apply blueprints
terraform init
terraform plan -var="project_id=your-project-id"
terraform apply

# For shared VPC VM deployment
cd blueprints/vm-with-private-ip/
terraform init
terraform apply -var="project_id=your-gcp-project"
```

## Advanced Security Features

### Cloud Armor Configuration
- **WAF Rules**: SQL injection, XSS, RCE protection
- **DDoS Protection**: Layer 7 defense with adaptive protection
- **Geo-blocking**: Regional restrictions
- **Rate Limiting**: Sophisticated rate-based bans
- **Threat Intelligence**: Integration with Google's threat feeds

### Sovereign Controls
- Enhanced security controls for sensitive data
- Compliance with German/EU data protection requirements
- Separate infrastructure stack from public cloud
- Customer-managed encryption keys

## Monitoring and Operations

### Operational Tools
- **SIEM Integration**: Log forwarding to central SIEM
- **Sparrow monitoring**: Platform health and performance
- **Grafana dashboards**: Custom monitoring
- **Alert management**: Via Webex integration

### Support and Escalation
- **JIRA-based request workflow**: Feature requests and issues
- **Google support integration**: P1/P2/P3 ticket routing
- **Policy exception process**: Organizational policy exceptions

## Development Resources

### Documentation and Training
- **Centralized Documentation**: https://mdx.pages.devops.telekom.de/docs/tools/deployment-targets/google-landing-zone/
- **API Documentation**: OpenAPI 3.0.3 specifications
- **Cookbooks**: Practical how-to guides organized by categories

### Enhancement Process
- **EEP (Enhancement and Evolution Proposals)**: For new features
- **ADR (Architecture Decision Records)**: For technical decisions
- **GitLab merge request-based review**: Implementation tracking

## Common Issues & Solutions

### Issue 1: Project Creation Failures
**Problem**: Project creation through Cloud Shepherd fails
**Solution**: 
- Verify cost object validity for managed projects
- Check legal entity permissions
- Ensure naming conventions are followed
- Review organization policy constraints

### Issue 2: Network Connectivity Issues
**Problem**: Cannot access resources in shared VPC
**Solution**:
- Verify shared VPC spoke assignment
- Check firewall rules and organization policies
- Confirm Private Google Access configuration
- Review IAM permissions for network resources

### Issue 3: Authentication Failures in CI/CD
**Problem**: GitLab CI/CD cannot authenticate to GCP
**Solution**:
- Verify Workload Identity Federation configuration
- Check service account IAM bindings
- Ensure OIDC token configuration is correct
- Validate WIF provider and pool settings

### Issue 4: Billing and Cost Issues
**Problem**: Unexpected charges or billing allocation issues
**Solution**:
- Review project tagging for cost allocation
- Check if NTS (Nighttime/Weekend Saving) is properly configured
- Verify budget alerts are set up
- Contact billing team for cost object validation

## Best Practices

### Security
- Always use Workload Identity Federation instead of service account keys
- Implement proper tagging strategy for security and cost management
- Follow principle of least privilege for IAM assignments
- Use organization policies for guardrails

### Cost Optimization
- Enable NTS for development VMs
- Use sandbox projects for experimentation
- Monitor spending with budget alerts
- Leverage committed use discounts for predictable workloads

### Development
- Use provided blueprints as starting points
- Follow GitLab CI/CD patterns for automation
- Implement proper testing in development environments
- Document architectural decisions with ADRs

## Resources

### Internal Links
- [Cloud Shepherd Portal](https://cs.telekom.de/)
- [MDX Documentation Hub](https://mdx.pages.devops.telekom.de/docs/tools/deployment-targets/google-landing-zone/)
- GitLab CI/CD Integration documentation
- Billing reports and cost management tools

### Key Repositories
- `ccoe/teams/gcloud-landing-zone/gclzctl/`: CLI tool source code
- `ccoe/teams/gcloud-landing-zone/blueprints/`: Infrastructure templates
- `ccoe/teams/gcloud-landing-zone/project-creation-api/`: API specifications
- `ccoe/teams/gcloud-landing-zone/operations/`: Operational procedures

## Notes for AI Assistance

When helping with Deutsche Telekom GCP projects:

1. **Environment Context**: Always consider the specific environment (dev/prd/sbx/scd/scp) and legal entity (DE0360/DE1000)

2. **Security First**: Prioritize Workload Identity Federation, proper IAM, and organization policy compliance

3. **Cost Awareness**: Consider cost implications and recommend appropriate optimization strategies

4. **Compliance**: Be aware of sovereign controls requirements for sensitive data

5. **GitLab Integration**: Leverage existing CI/CD patterns and Workload Identity Federation

6. **Documentation**: Refer to centralized MDX documentation hub for user-facing information

7. **Escalation**: Use proper channels (JIRA, support tickets) for issues requiring platform team intervention

This platform represents a mature, enterprise-grade cloud management solution with sophisticated governance, security, and operational capabilities designed specifically for Deutsche Telekom's requirements and compliance needs.