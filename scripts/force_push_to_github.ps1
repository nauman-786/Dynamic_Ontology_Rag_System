<#
.SYNOPSIS
    Force-push the current workspace to a remote Git repository (destructive).

.DESCRIPTION
    This script initializes a git repository (if needed), creates a single
    commit of the current workspace, and force-pushes it to the provided
    remote URL/branch. THIS WILL OVERWRITE THE REMOTE branch history.

    Use only if you understand the destructive nature of a force push.

.PARAMETER RemoteUrl
    The Git remote URL to push to (e.g. https://github.com/owner/repo.git).

.PARAMETER Branch
    The branch name to push to. Defaults to 'main'.

.EXAMPLE
    .\force_push_to_github.ps1 -RemoteUrl 'https://github.com/nauman-786/Dynamic_Ontology_Rag_System.git' -Branch main

NOTES
    - You must have credentials set up (SSH key or HTTPS credentials via credential helper).
    - This script does NOT create or delete GitHub repository itself — it only pushes commits.
    - It will prompt for confirmation before performing the destructive push.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl,

    [Parameter(Mandatory = $false)]
    [string]$Branch = "main"
)

function Confirm-DestructiveAction {
    param([string]$message)
    Write-Host "WARNING: $message" -ForegroundColor Yellow
    $resp = Read-Host "Type 'YES' to proceed"
    return $resp -eq 'YES'
}

if (-not (Confirm-DestructiveAction "This will overwrite the remote branch '$Branch' at $RemoteUrl and cannot be undone.")) {
    Write-Host "Aborted by user." -ForegroundColor Cyan
    exit 1
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git is not installed or not in PATH. Install git and retry." -ForegroundColor Red
    exit 2
}

$cwd = Get-Location
Write-Host "Preparing repository in $cwd" -ForegroundColor Green

if (-not (Test-Path (Join-Path $cwd '.git'))) {
    git init
    Write-Host "Initialized new git repository." -ForegroundColor Green
} else {
    Write-Host "Existing git repository detected." -ForegroundColor Green
}

# Ensure remote is set
try {
    git remote remove origin 2>$null | Out-Null
} catch {}

git remote add origin $RemoteUrl
Write-Host "Remote 'origin' set to $RemoteUrl" -ForegroundColor Green

# Create a commit with all files
git add --all
try {
    git commit -m "Deploy workspace: force push from local" -q
} catch {
    Write-Host "No changes to commit or commit failed (continuing)." -ForegroundColor Yellow
}

# Force push to remote
Write-Host "About to force-push to origin/$Branch" -ForegroundColor Yellow
git push origin HEAD:$Branch --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "Force push completed successfully." -ForegroundColor Green
} else {
    Write-Host "Force push failed. Check git output and credentials." -ForegroundColor Red
    exit $LASTEXITCODE
}
