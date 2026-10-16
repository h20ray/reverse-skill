#Requires -Version 5.1
# Contract test: the verdict-language rule (ADF-R54) must stay present and cross-linked.
#
# The rule exists because a settled result was once written up as "leaning toward", i.e. a
# measured conclusion was hedged back into a hypothesis. It is prose, so nothing at runtime
# can enforce it — the durable part is that the contract files still SAY it, and that the
# rule keeps its ID and its companions. This test fails if the guidance is deleted, renamed,
# or silently decoupled from ADF-R4* / RULES.md.
param(
    [string]$PackageRoot = ''
)
$ErrorActionPreference = 'Stop'
$scriptDir = $PSScriptRoot
$skillsRoot = Split-Path -Parent $scriptDir
if (-not $PackageRoot) { $PackageRoot = Split-Path -Parent $skillsRoot }

$fail = New-Object System.Collections.Generic.List[string]
function Ok($m) { Write-Host "[OK] $m" -ForegroundColor Green }
function Bad($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; [void]$fail.Add($m) }

function Read-Text([string]$rel) {
    $p = Join-Path $PackageRoot $rel
    if (-not (Test-Path -LiteralPath $p)) { return $null }
    return [IO.File]::ReadAllText($p)
}

# --- 1. RULES.md carries the behaviour rule ------------------------------------------------
$rules = Read-Text 'RULES.md'
if ($null -eq $rules) {
    Bad 'RULES.md not found'
} else {
    if ($rules -match 'Verdict Before Hypothesis') { Ok 'RULES.md: verdict-language section present' }
    else { Bad 'RULES.md: verdict-language section missing' }
    if ($rules -match 'settled') { Ok 'RULES.md: names the settled state' }
    else { Bad 'RULES.md: does not name the settled state' }
    if ($rules -match 'ranked\s+hypothesis') { Ok 'RULES.md: forbids a ranked hypothesis list on settled evidence' }
    else { Bad 'RULES.md: ranked-hypothesis prohibition missing' }
    # must not be read as relaxing the authorization surface
    if ($rules -match '\*{0,2}not\*{0,2}\s+a relaxation of authorization') { Ok 'RULES.md: scoped as non-relaxing of authorization' }
    else { Bad 'RULES.md: missing the authorization non-relaxation note' }
    # the pre-existing confidence-label rule must SURVIVE (this rule is not a repeal of it)
    if ($rules -match 'Uncertain conclusions MUST be labeled with confidence level') { Ok 'RULES.md: confidence-label rule still present' }
    else { Bad 'RULES.md: confidence-label rule was removed; verdict rule is not a repeal of it' }
}

# --- 2. ops/evidence-finding-path.md carries the write-up contract -------------------------
$efp = Read-Text 'skills/ops/evidence-finding-path.md'
if ($null -eq $efp) {
    Bad 'skills/ops/evidence-finding-path.md not found'
} else {
    if ($efp -match 'Verdict language') { Ok 'evidence-finding-path.md: verdict-language section present' }
    else { Bad 'evidence-finding-path.md: verdict-language section missing' }
    if ($efp -match 'R4\*') { Ok 'evidence-finding-path.md: cross-linked to ADF-R4*' }
    else { Bad 'evidence-finding-path.md: ADF-R4* cross-link missing' }
    if ($efp -match 'MUST NOT') { Ok 'evidence-finding-path.md: carries a MUST NOT' }
    else { Bad 'evidence-finding-path.md: no MUST NOT; contract is advisory only' }
}

# --- 3. ADF-R54 is declared once, in the overlay ID space, and is not a routing id ---------
$adf = Read-Text 'skills/ops/analysis-decision-framework.md'
if ($null -eq $adf) {
    Bad 'skills/ops/analysis-decision-framework.md not found'
} else {
    if ($adf -match 'R54') { Ok 'analysis-decision-framework.md: R54 in the Synthesis checklist' }
    else { Bad 'analysis-decision-framework.md: R54 missing from the checklist' }
    if ($adf -match 'ADF-R54') { Ok 'analysis-decision-framework.md: R54 marked as an ADF overlay id' }
    else { Bad 'analysis-decision-framework.md: R54 not disambiguated from routing R54' }
}

$bs = Read-Text 'skills/ops/analysis-blindspot-cookbook.md'
if ($null -eq $bs) {
    Bad 'skills/ops/analysis-blindspot-cookbook.md not found'
} else {
    if ($bs -match 'ADF-R54') { Ok 'blindspot cookbook: ADF-R54 recipe present' }
    else { Bad 'blindspot cookbook: ADF-R54 recipe missing' }
    if ($bs -match 'R4\\\*') { Ok 'blindspot cookbook: ADF-R54 names R4* as its companion' }
    else { Bad 'blindspot cookbook: ADF-R54 does not name R4*' }
}

# --- 4. R54 must NOT collide with a real routing id ---------------------------------------
$routingPath = Join-Path $PackageRoot 'skills/config/routing.json'
if (Test-Path -LiteralPath $routingPath) {
    $routing = Get-Content -LiteralPath $routingPath -Raw
    if ($routing -match '"R54"') {
        Bad 'routing.json declares an R54; the ADF-R54 overlay id now collides'
    } else {
        Ok 'routing.json: no R54, so ADF-R54 does not collide'
    }
} else {
    Bad 'skills/config/routing.json not found'
}

# --- 5. The rule must survive in the mirror rule sets -------------------------------------
# RULES.md is the Windows canonical set; RULES_zh.md and kali/RULES-kali.md are the Chinese and
# Kali mirrors. A behaviour rule that exists in only one of them silently stops applying on the
# other platforms, so each mirror must carry the same section and the same identifier.
foreach ($mirror in @('RULES_zh.md', 'kali/RULES-kali.md')) {
    $text = Read-Text $mirror
    if ($null -eq $text) { Bad "$mirror not found"; continue }
    if ($text -match '结论优先于假设') { Ok "${mirror}: verdict-language section present" }
    else { Bad "${mirror}: verdict-language section missing" }
    if ($text -match 'R54') { Ok "${mirror}: names R54" }
    else { Bad "${mirror}: does not name R54" }
    if ($text -match '置信度') { Ok "${mirror}: confidence-label rule still present" }
    else { Bad "${mirror}: confidence-label rule was removed; verdict rule is not a repeal of it" }
    if ($text -match 'ADF-R2') { Ok "${mirror}: reserves hypothesis language for ADF-R2" }
    else { Bad "${mirror}: does not scope hypothesis language to ADF-R2" }
}

Write-Host ''
if ($fail.Count -gt 0) {
    Write-Host ("[FAIL] verdict-language contract: {0} problem(s)" -f $fail.Count) -ForegroundColor Red
    exit 1
}
Write-Host '[OK] verdict-language contract intact' -ForegroundColor Green
exit 0
