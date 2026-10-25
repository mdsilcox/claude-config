<#
.SYNOPSIS
Installs this claude-config repo into %USERPROFILE%\.claude on the Windows desktop.

.DESCRIPTION
Backs up everything it replaces to %USERPROFILE%\.claude\backups\pre-claude-config-<time>\ first.
Leaves alone: ~/.claude.json (MCP servers, trust decisions), credentials, projects\ (transcripts and
auto memory), plugins\ and skills\synced\. Safe to run again.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File install\install-windows.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File install\install-windows.ps1
powershell -ExecutionPolicy Bypass -File install\install-windows.ps1 -RemoveApiKey
#>
param([switch]$DryRun, [switch]$RemoveApiKey)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$Claude = Join-Path $env:USERPROFILE '.claude'
$Backup = Join-Path $Claude ('backups\pre-claude-config-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))

function Invoke-Step([string]$Description, [scriptblock]$Action) {
    Write-Host "-> $Description"
    if (-not $DryRun) { & $Action }
}

Invoke-Step "Back up the current config to $Backup" {
    New-Item -ItemType Directory -Force -Path $Backup | Out-Null
    foreach ($name in 'CLAUDE.md', 'settings.json', 'agents', 'skills', 'hooks', 'tools', 'templates') {
        $path = Join-Path $Claude $name
        if (Test-Path $path) { Copy-Item -Path $path -Destination $Backup -Recurse -Force }
    }
}

Invoke-Step 'Create the hooks interpreter (a uv-managed venv; the hooks use the standard library only)' {
    $venv = Join-Path $Claude 'hooks\.venv'
    if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) { uv venv --python 3.12 $venv | Out-Host }
}

Invoke-Step 'Retire the old agents, skills, tools and templates (they stay in the backup)' {
    foreach ($dir in 'agents', 'skills', 'tools', 'templates') {
        $path = Join-Path $Claude $dir
        if (Test-Path $path) {
            Get-ChildItem -Path $path -Force | Where-Object { $_.Name -ne 'synced' } | Remove-Item -Recurse -Force
        }
    }
}

Invoke-Step 'Copy hooks, agents, skills and templates' {
    $pairs = @(
        @('shared\hooks', 'hooks'), @('shared\agents', 'agents'), @('shared\skills', 'skills'),
        @('templates', 'templates')
    )
    foreach ($pair in $pairs) {
        $dst = Join-Path $Claude $pair[1]
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Get-ChildItem -Path (Join-Path $Repo $pair[0]) -Force | Copy-Item -Destination $dst -Recurse -Force
    }
}

# Settings go last, so every hook they name already exists.
Invoke-Step 'Install the global CLAUDE.md and settings.json' {
    Copy-Item -Path (Join-Path $Repo 'windows\CLAUDE.md') -Destination (Join-Path $Claude 'CLAUDE.md') -Force
    Copy-Item -Path (Join-Path $Repo 'windows\settings.json') -Destination (Join-Path $Claude 'settings.json') -Force
}

$key = [Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY', 'User')
if ($RemoveApiKey -and $key) {
    # Renamed rather than deleted, so the value isn't lost if a project still needs it. Claude Code
    # ignores ANTHROPIC_API_KEY_OFF; move the value into that project's .env, then delete the variable.
    Invoke-Step 'Rename the user ANTHROPIC_API_KEY to ANTHROPIC_API_KEY_OFF (Claude Code stops billing it)' {
        [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY_OFF', $key, 'User')
        [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', $null, 'User')
    }
} elseif ($key) {
    Write-Warning ('ANTHROPIC_API_KEY is set for your user account. Claude Code in a new terminal uses it ' +
        'instead of your Max plan (always, in claude -p). Rerun with -RemoveApiKey, or keep the key in the one project .env that needs it.')
}
Remove-Variable key

Write-Host ''
Write-Host 'Done. Next: restart the Claude desktop app, run "claude doctor" in a new terminal, and check /status and /hooks in a session.'
if (-not $DryRun) { Write-Host "Backup of the old config: $Backup" }
