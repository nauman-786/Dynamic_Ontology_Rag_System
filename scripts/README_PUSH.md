Force-push current workspace to a GitHub repository
===============================================

This document explains how to push the current workspace to a remote GitHub
repository, overwriting the remote branch history. This is destructive — be
careful.

Prerequisites
-------------
- `git` installed and available in PATH.
- Authentication configured for the remote (SSH key or HTTPS credential helper).

Usage (PowerShell)
-------------------
Open a PowerShell terminal in the workspace root (where this file lives) and run:

```powershell
# Replace with your repo URL and branch name
.\scripts\force_push_to_github.ps1 -RemoteUrl 'https://github.com/OWNER/REPO.git' -Branch main
```

Notes
-----
- The script will prompt you to type `YES` to proceed; otherwise it aborts.
- The script initializes a git repo if none exists, commits current files, and
  then performs a `git push --force` to the specified branch.
- If you prefer to review the git commit before pushing, run the script with
  `-WhatIf` removed or manually perform the steps:

```powershell
git init
git remote add origin <remote-url>
git add --all
git commit -m "Deploy workspace"
git push origin HEAD:main --force
```

Backing up the remote
---------------------
If you need to preserve existing remote history, clone the remote to a
separate folder before running the script:

```powershell
git clone https://github.com/OWNER/REPO.git repo-backup
```

Support
-------
If you want me to run these steps for you, I can prepare a non-destructive
plan and list the exact commands; you'll still need to execute them locally
or provide a GitHub token/SSH access for automated pushes.
