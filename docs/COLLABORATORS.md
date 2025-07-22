# Repository Collaborator Management

This repository now includes automated tools for managing collaborators using Infrastructure as Code principles.

## Files Added

- `.github/collaborators.yml` - Configuration file defining repository collaborators and their permissions
- `.github/workflows/manage-collaborators.yml` - GitHub Actions workflow for automated collaborator management
- `bin/manage-collaborators.sh` - Local script for managing collaborators using GitHub CLI

## Current Collaborators

As defined in `.github/collaborators.yml`:

- **rantallanb** - Write permission level (added 2024-07-22)

## Usage

### Method 1: Automatic via GitHub Actions

The GitHub Actions workflow will automatically run when:
- The `.github/collaborators.yml` file is modified
- The workflow file itself is updated
- Manually triggered via GitHub's "Actions" tab

### Method 2: Manual via Local Script

```bash
# Ensure GitHub CLI is installed and authenticated
gh auth login

# Run the collaborator management script
./bin/manage-collaborators.sh
```

### Method 3: Direct GitHub CLI Commands

```bash
# Add a collaborator with write permission
gh api repos/mbastakis/dotfiles/collaborators/rantallanb \
  --method PUT \
  --field permission=push

# List current collaborators
gh api repos/mbastakis/dotfiles/collaborators | jq -r '.[] | "\(.login) - \(.permissions | to_entries | map(select(.value == true)) | map(.key) | join(", "))"'
```

## Permission Levels

- `pull` - Read-only access
- `push` - Read-write access (equivalent to "write")
- `maintain` - Maintain access (manage issues, PRs, some settings)
- `triage` - Triage access (manage issues and PRs)
- `admin` - Admin access (full access including settings and collaborators)

## Adding New Collaborators

1. Edit `.github/collaborators.yml`
2. Add the new collaborator with their desired permission level
3. Commit and push the changes
4. The GitHub Actions workflow will automatically apply the changes

Or use the local script:

```bash
./bin/manage-collaborators.sh
```

## Requirements

- Repository admin permissions
- GitHub CLI (`gh`) installed and authenticated (for local script)
- `administration: write` permission for the GitHub Actions workflow