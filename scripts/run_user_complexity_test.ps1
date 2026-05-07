param(
    [string]$RunRoot = "examples/reality-testing/runs/2026-05-07-user-complexity-live"
)

$ErrorActionPreference = "Continue"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runRootAbs = Join-Path $repoRoot $RunRoot

New-Item -ItemType Directory -Force -Path $runRootAbs | Out-Null

$sandbox = Join-Path $runRootAbs "sandbox-workspace"
New-Item -ItemType Directory -Force -Path $sandbox | Out-Null

$results = New-Object System.Collections.Generic.List[object]

function Invoke-Scenario {
    param(
        [string]$Id,
        [string]$Name,
        [scriptblock]$Script,
        [string]$Expected,
        [int[]]$ExpectedExitCodes = @(0)
    )

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $output = ""
    $exitCode = 0

    try {
        $all = & $Script 2>&1
        $output = ($all | Out-String)
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) {
            $exitCode = 0
        }
    }
    catch {
        $output = ($_ | Out-String)
        $exitCode = 1
    }

    $sw.Stop()
    $status = if ($ExpectedExitCodes -contains $exitCode) { "pass" } else { "fail" }
    $preview = (($output -replace "`r", "") -split "`n" | Select-Object -First 10) -join "`n"

    $results.Add(
        [pscustomobject]@{
            scenario_id = $Id
            name = $Name
            status = $status
            exit_code = $exitCode
            duration_s = [math]::Round($sw.Elapsed.TotalSeconds, 2)
            expected = $Expected
            output_preview = $preview
        }
    ) | Out-Null
}

Invoke-Scenario "S1" "Cold start setup and first handoff packet" {
    Set-Location $sandbox
    devcd setup --projects $sandbox --agents copilot --goal "Fix failing release gate" --next-action "Read action packet and continue" --yes
    devcd agentic action-packet
} "setup succeeds and action-packet prints usable context"

Invoke-Scenario "S2" "Mid-task handoff with blocker" {
    Set-Location $sandbox
    devcd handoff --goal "Fix failing release gate" --failure "Typecheck fails in policy slice" --next-action "Inspect typecheck output"
    devcd agentic action-packet --json
} "handoff captured and packet reflects blocker/next-action"

Invoke-Scenario "S3" "Policy boundary deny-by-default check" {
    Set-Location $sandbox
    devcd agentic run --runner codex --json
} "agentic runner start denied by policy by default" @(1)

Invoke-Scenario "S4" "MCP integration smoke path" {
    Set-Location $sandbox
    devcd integrations openclaw --smoke-test
} "read-only MCP smoke check passes"

Invoke-Scenario "S5" "Completion gate readiness" {
    Set-Location $sandbox
    devcd agentic completion-check
} "completion-check indicates readiness or actionable failure"

$csvPath = Join-Path $runRootAbs "scenario-matrix.csv"
$mdPath = Join-Path $runRootAbs "summary.md"
$logPath = Join-Path $runRootAbs "command-log.md"

$results | Export-Csv -NoTypeInformation -Encoding utf8 -Path $csvPath

$passCount = ($results | Where-Object status -eq "pass").Count
$total = $results.Count
$avgDuration = [math]::Round((($results | Measure-Object duration_s -Average).Average), 2)
$failCount = $total - $passCount

$summaryLines = @(
    "# User-Sicht Komplexitaetstest (Live)",
    "",
    "- run_date: 2026-05-07",
    "- sandbox: $sandbox",
    "- scenarios_total: $total",
    "- scenarios_pass: $passCount",
    "- scenarios_fail: $failCount",
    "- avg_duration_s: $avgDuration",
    "",
    "## Ergebnisse",
    ""
)

$summaryLines += ($results | ForEach-Object {
    "- [$($_.scenario_id)] $($_.name): $($_.status) (exit=$($_.exit_code), $($_.duration_s)s)"
})

$summaryLines += @(
    "",
    "## Naechste Fokuspunkte",
    "",
    "- Pruefen, ob Failures echte Produktprobleme vs. Setup-Artefakte sind.",
    "- Commands pro erfolgreiches Resume als KPI mittracken.",
    "- Lauf als nightly smoke wiederholen."
)

$summaryLines | Set-Content -Encoding utf8 -Path $mdPath

$logLines = New-Object System.Collections.Generic.List[string]
$logLines.Add("# Command Log (Preview je Szenario)") | Out-Null
$logLines.Add("") | Out-Null

foreach ($r in $results) {
    $logLines.Add("## $($r.scenario_id) - $($r.name)") | Out-Null
    $logLines.Add("") | Out-Null
    $logLines.Add('```text') | Out-Null
    $logLines.Add($r.output_preview) | Out-Null
    $logLines.Add('```') | Out-Null
    $logLines.Add("") | Out-Null
}

$logLines | Set-Content -Encoding utf8 -Path $logPath

Write-Output "Wrote: $csvPath"
Write-Output "Wrote: $mdPath"
Write-Output "Wrote: $logPath"
$results | Format-Table scenario_id, status, exit_code, duration_s, name -AutoSize | Out-String