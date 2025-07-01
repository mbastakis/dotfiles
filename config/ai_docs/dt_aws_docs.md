# Deutsche Telekom AWS Infrastructure Documentation

## Overview
Deutsche Telekom's AWS infrastructure is a comprehensive enterprise cloud platform managed by the Cloud Center of Excellence (CCoE). It provides standardized, secure, and cost-optimized AWS services across multiple organizational units with strong governance, automation, and compliance frameworks.

## AWS Landing Zone Architecture

### Account Structure & Organization
- **AWS Organizations**: Centralized multi-account management strategy
- **Organization Units (OUs)**: DTIT, National Companies, and specialized units
- **Darwin Integration**: All AWS accounts linked to Darwin (DTIT's central CMDB) via w5baseid for ITSM integration
- **Account Lifecycle Management**: Automated provisioning with ~2 weeks setup time due to corporate tool integration

### Account Types

#### Sandbox Accounts
- **Lifecycle**: 6-month auto-nuke
- **Data Classification**: DSK0/Open data only
- **Purpose**: Learning, experimentation, proof-of-concepts
- **Requirements**: Minimal - no cost object or RPA required

#### Development/Testing Accounts
- **Lifecycle**: Unlimited with proper justification
- **Data Classification**: Up to DSK1/Internal data
- **Requirements**: RPA/WAF required, cost object mandatory
- **Network**: Shared Blue/Green VPC access

#### Reference/Production Accounts
- **Lifecycle**: Unlimited for production workloads
- **Data Classification**: Up to DSK3/Confidential data
- **Requirements**: Full security compliance, hardened configurations
- **Network**: Dedicated VPC with strict security controls

## Network Architecture & Security

### VPC Structure
```yaml
# Network Configuration
shared_vpc:
  blue_vpc: 
    description: Corporate Network DTAG (CNDTAG) connectivity
    connectivity: On-premises integration
  green_vpc:
    description: Alternative network access
    connectivity: Internet with controls
  magenta_vpc:
    description: Default for sandbox accounts
    connectivity: Basic internet access

security_groups:
  - presentation_layer: Web-facing components
  - application_layer: Business logic tier
  - database_layer: Data persistence tier
```

### Firewall & Network Security

#### Cloud Firewall
- **Hardware**: Fortinet 1500D cluster
- **Locations**: Magdeburg-new and Biere-1 datacenters
- **Management**: fftcomagdecl170 cluster identifier

#### Forward Proxy Area (FPA)
- **Transparent Proxy**: AWS Network Firewall integration
- **Explicit Proxy**: Squid-based proxy services
- **Access Control**: Whitelist-based internet access
- **Self-Service**: GitLab merge request-based whitelisting automation

#### TUFIN/FIAT Integration
- **Automation**: Corporate FIAT system integration
- **Firewall Rules**: Automated management and provisioning
- **Compliance**: Corporate firewall policy enforcement

## Security & Compliance Framework

### DevSecOps Integration
```yaml
# Security Services Configuration
aws_config:
  conformance_packs: 
    - DevSecOps controls
    - AWS security best practices
    - Custom compliance rules
  remediation: Automated where possible

security_hub:
  centralized_findings: true
  automated_cleanup: Security Hub Cleaner tool
  integration: DevSecOps account forwarding

guard_duty:
  enabled: all_accounts
  event_forwarding: central_logging_account
  threat_detection: automated_response

cloudtrail:
  status: activated_all_accounts
  forwarding: central_logging_account
  compliance: audit_ready
```

### Security Incident Response
- **Resource Isolation API**: Automated IAM user and EC2 instance isolation
- **SSM Automation Documents**: Self-service security response tools
- **Cross-account Roles**: `SRE_Security_Response_API_Assume_Role` for incident response
- **Automated Response**: Lambda-based security automation

### AWS Key Re-rolling
- **Automation**: Lambda-based IAM access key rotation
- **Schedule**: Configurable rotation intervals
- **Integration**: Corporate identity management systems
- **Compliance**: Automated key lifecycle management

## Cost Management & Financial Operations

### Cost Reporting & Analytics
```python
# Cost Management Tools
cost_explorer_alternative = {
    "platform": "QuickSight",
    "deployment": "DTIT automation account",
    "features": ["Custom dashboards", "Cost allocation", "Trend analysis"]
}

automated_reporting = {
    "platform": "Lambda",
    "output": "PDF reports",
    "distribution": "Email automation",
    "schedule": "Monthly and on-demand"
}

cost_optimization = {
    "tools": ["EBS Optimizer", "RDS cleanup", "Lambda optimization"],
    "automation": "Scheduled cleanup scripts",
    "savings": "Night-time shutdown for dev resources"
}
```

### CUDOS (Cost and Usage Dashboard Optimization Service)
- **Architecture**: S3 → Glue Crawler → Athena → QuickSight pipeline
- **Features**: Advanced cost analytics and optimization recommendations
- **Integration**: Corporate billing systems and cost allocation

### Resource Management
- **Account Nuking**: Self-service cleanup for sandbox/training via CodeBuild
- **EBS Optimizer**: GP2 to GP3 migration automation
- **Cost Categories**: Integration with internal billing and charge-back systems

## CI/CD Integration & DevOps

### GitLab Integration
```yaml
# OIDC Configuration
gitlab_oidc:
  provider: AWS IAM Identity Provider
  authentication: OpenID Connect tokens
  security: Short-lived tokens, no long-term keys
  
terraform_backend:
  state_storage: S3 with versioning
  locking: DynamoDB
  encryption: AES-256

deployment_patterns:
  environments: [dev, staging, prod]
  approval_gates: Required for production
  cross_account: Assume-role patterns
```

### Infrastructure as Code

#### Terraform Implementation
```hcl
# Core Terraform Configuration
provider "aws" {
  region = "eu-central-1"
  
  default_tags {
    tags = {
      owner       = var.owner
      environment = var.environment
      terraform   = "true"
    }
  }
}

# S3 Backend Configuration
terraform {
  backend "s3" {
    bucket         = "dtit-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

#### AWS Service Catalog
- **Pre-approved Templates**: PSA-approved infrastructure components
- **Self-Service**: EC2, S3, RDS provisioning
- **Governance**: Standardized deployments with built-in compliance
- **Products**: FPA whitelisting, DNS automation, certificate management

### Jump-Start Solutions
```terraform
# Example: EC2 with Oracle Database Integration
module "ec2_oracle" {
  source = "./modules/aws-ec2-exaCC"
  
  instance_type = "r5.xlarge"
  storage_encrypted = true
  vpc_id = var.vpc_id
  subnet_id = var.private_subnet_id
}

# S3 Static Website Hosting
module "static_website" {
  source = "./modules/aws-s3-static-pages"
  
  bucket_name = var.website_bucket
  cloudfront_enabled = true
  encryption = "AES256"
}
```

## Container Orchestration & Kubernetes

### EKS Cluster Management
```yaml
# Karpenter Configuration
karpenter:
  node_provisioning: dynamic
  instance_types: [t3.medium, t3.large, m5.large]
  storage:
    type: gp3
    size: 50Gi
    iops: 3000
    encrypted: true

networking:
  vpc_isolation: true
  security_groups: restrictive
  subnets: private_only
```

### Application Deployment
- **ArgoCD**: GitOps-based deployments
- **Helm Charts**: Standardized application packaging
- **Istio Service Mesh**: Security and observability
- **Monitoring Stack**: Grafana, Prometheus, Fluent Bit

## Common Development Commands

### AWS CLI with Federated Access
```bash
# Corporate SSO Login
aws sso login --profile dtit-dev

# AssumeRole for Cross-Account Access
aws sts assume-role \
  --role-arn "arn:aws:iam::ACCOUNT:role/CrossAccountRole" \
  --role-session-name "session-name"

# Terraform Deployment
terraform init -backend-config="bucket=dtit-terraform-state"
terraform plan -var-file="environments/dev.tfvars"
terraform apply
```

### Container and Kubernetes Operations
```bash
# EKS Cluster Access
aws eks update-kubeconfig --region eu-central-1 --name dtit-cluster

# Karpenter Node Management
kubectl apply -f nodepool.yaml
kubectl get nodepool

# ArgoCD Application Deployment
kubectl apply -f argocd-application.yaml
argocd app sync app-name
```

### Security Operations
```bash
# AWS Config Compliance Check
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name "required-tags"

# Security Hub Findings
aws securityhub get-findings \
  --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}]}'

# IAM Access Key Rotation
python key-rotation-script.py --user-name service-account
```

## Monitoring & Operations

### Centralized Monitoring
```yaml
# Monitoring Configuration
cloudwatch:
  metrics: Custom and AWS service metrics
  logs: Centralized log aggregation
  alarms: Automated alerting

grafana:
  dashboards: Infrastructure and application metrics
  data_sources: [CloudWatch, Prometheus]
  alerting: Webex Teams integration

observability:
  logging: Fluent Bit → CloudWatch
  metrics: Prometheus → Grafana
  tracing: AWS X-Ray integration
```

### Operational Automation
- **Account Creation**: Streamlined provisioning workflows
- **DNS Management**: Route53 hosted zone automation
- **Certificate Management**: ACM with automated validation
- **Backup Automation**: RDS, EBS, and S3 backup strategies

## Best Practices

### Security
- Use IAM roles and assume-role patterns instead of access keys
- Implement least-privilege access principles
- Enable all security services (GuardDuty, Config, Security Hub)
- Use VPC endpoints for secure service communication
- Encrypt all data at rest and in transit

### Cost Optimization
- Use Spot instances for non-critical workloads
- Implement auto-scaling based on demand
- Regular cost reviews and optimization scripts
- Use reserved instances for predictable workloads
- Enable cost allocation tags for accurate billing

### Infrastructure as Code
- Store all infrastructure as Terraform code
- Use S3 backend with state locking
- Implement proper branching and approval workflows
- Version control all configuration changes
- Use modules for reusable components

### Development
- Follow GitOps principles with ArgoCD
- Use standardized CI/CD pipelines
- Implement proper testing strategies
- Use Service Catalog for approved patterns
- Document all architectural decisions

## Common Issues & Solutions

### Issue 1: Account Access Problems
**Problem**: Cannot access AWS account through corporate SSO
**Solution**: 
- Verify Darwin application ID assignment
- Check AD/CIAM group memberships
- Contact CCoE ServiceDesk for account provisioning status
- Ensure VPN connection for corporate network access

### Issue 2: Network Connectivity Issues
**Problem**: Cannot reach on-premises resources from AWS
**Solution**:
- Verify VPC selection (Blue/Green for corporate connectivity)
- Check security group rules and NACLs
- Validate routing table configurations
- Confirm Direct Connect or VPN status

### Issue 3: CI/CD Pipeline Failures
**Problem**: GitLab CI/CD cannot deploy to AWS
**Solution**:
- Verify OIDC provider configuration
- Check IAM role trust relationships
- Validate cross-account role permissions
- Ensure proper GitLab variable configuration

### Issue 4: Compliance Violations
**Problem**: AWS Config or Security Hub compliance failures
**Solution**:
- Review conformance pack requirements
- Use automated remediation where available
- Check resource tagging compliance
- Contact DevSecOps team for complex violations

## Enhancement Process

### AWS Service Requests
- **Channel**: CCoE ServiceDesk via JIRA
- **Timeline**: Standard ~2 weeks for account provisioning
- **Requirements**: Business justification, cost object, technical requirements
- **Onboarding**: Mandatory sessions with AWS onboarding team

### Infrastructure Changes
- **Process**: GitLab merge requests for infrastructure changes
- **Review**: Technical and security review required
- **Testing**: Validation in development environment first
- **Deployment**: Automated through CI/CD pipelines

## Resources

### Internal Documentation
- [AWS Landing Zone Hub](https://mdx.pages.devops.telekom.de/docs/tools/deployment-targets/aws-landing-zone/)
- CCoE ServiceDesk for account requests
- Darwin CMDB for application registration
- Corporate security policies and guidelines

### Training and Certification Paths
- AWS Certified Developer Associate
- AWS Certified DevOps Professional
- AWS Certified Solutions Architect Professional
- AWS Certified SysOps Administrator Associate
- Internal workshops and training sessions

### Key Repositories
- `ccoe/teams/aws/`: Core AWS team tools and automation
- `ccoe/innersource/aws-jump-start-solutions/`: Reference architectures
- `ccoe/common/cicd/aws/`: CI/CD integration tools
- `ccoe/teams/cloud-adoption/examples/`: Training and examples

## Notes for AI Assistance

When helping with Deutsche Telekom AWS projects:

1. **Account Context**: Always consider the account type (sandbox/dev/prod) and associated restrictions
2. **Security First**: Prioritize security best practices and compliance requirements
3. **Cost Awareness**: Consider cost implications and optimization opportunities
4. **Network Architecture**: Understand VPC connectivity requirements for corporate integration
5. **Automation**: Leverage existing automation tools and Service Catalog products
6. **Compliance**: Be aware of DSK data classification and PSA requirements
7. **CI/CD Integration**: Use GitLab OIDC patterns and standardized pipelines
8. **Support Channels**: Direct to appropriate teams (CCoE, DevSecOps, AWS onboarding)

This AWS infrastructure represents a mature, enterprise-grade cloud platform with sophisticated governance, security, automation, and cost management capabilities designed specifically for Deutsche Telekom's enterprise requirements and compliance needs.