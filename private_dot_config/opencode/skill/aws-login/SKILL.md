---
name: aws-login
description: Use aws-login wrappers for AWS and kubectl commands with strict environment verification.
version: 1.0.0
last_updated: 2026-02-26
---

# AWS Login

## Overview

Use this skill for AWS CLI and kubectl operations in AICC accounts.
All operational commands must run through `aws-login exec`.

## Command Pattern (Use First)

Before writing the final command, construct it in this format:

```bash
aws-login exec <env> -- <tool> <command>
```

- `<env>` is one of `playground`, `dev`, `prod`
- `<tool>` is `kubectl` or `aws`
- Do not run raw `kubectl` or `aws` operational commands directly

## Environment Management

### AWS Environments

- `playground` - experimentation environment (requires MFA)
- `dev` - development environment (active by default)
- `prod` - production environment (requires extra caution)

### Environment Verification Protocol (Required)

Before any AWS or kubectl operation, you must:

1. Check current kubectl context:

```bash
kubectl config current-context
```

2. Check conversation history for previously established environment preference.
3. Verify alignment using this mapping:

| Environment  | Kubectl Context                                                            | Account ID     |
| ------------ | -------------------------------------------------------------------------- | -------------- |
| `playground` | `arn:aws:eks:eu-central-1:970547348009:cluster/aicc-playground`            | `970547348009` |
| `dev`        | `arn:aws:eks:eu-central-1:076811069858:cluster/aicc-cndtag-dev`            | `076811069858` |
| `prod`       | `arn:aws:eks:eu-central-1:620453162886:cluster/aicc-prod-ec1-shared-eks-0` | `620453162886` |

4. Apply context switching behavior:
   - If conversation has established environment preference and current context differs: switch context
   - If no previous environment was mentioned: use current kubectl context as-is
   - If user explicitly requests different environment: switch context

5. Switch kubectl context with:

```bash
kubectl config use-context <context-arn>
```

Example:

```bash
kubectl config use-context arn:aws:eks:eu-central-1:076811069858:cluster/aicc-cndtag-dev
```

## Examples

```bash
# Dev: list pods in all namespaces
aws-login exec dev -- kubectl get pods -A

# Playground: view namespaces
aws-login exec playground -- kubectl get namespaces

# Dev: list EKS clusters
aws-login exec dev -- aws eks list-clusters --region eu-central-1

# Prod: verify account identity before any prod action
aws-login exec prod -- aws sts get-caller-identity
```

## Output Guidance

- State the selected environment before command execution
- Show full wrapped command in responses
- For `prod`, call out risk and keep commands explicit and minimal
