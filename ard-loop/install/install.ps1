# install.ps1 — ARD Loop(CAR 자율학습 시스템) 로컬 설치 (Windows)
# 한 번 실행하면: 의존성 설치 + 스크립트 비치 + CAR 에이전트 등록 +
#   harvester(일)·supervisor(주) Task Scheduler 등록 + SessionStart 훅 배선.
# 멱등. 실행: pwsh -File install.ps1   (또는 .\install.ps1)

$ErrorActionPreference = 'Stop'
Write-Host "=== ARD Loop / CAR 설치 ===" -ForegroundColor Cyan

# 0) 경로 해석
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')   # <ARD>
$loop     = Join-Path $repoRoot 'ard-loop'
$ardOps   = Join-Path $HOME '.claude\ard'
$agentsDir = Join-Path $HOME '.claude\agents'
$hooksDir  = Join-Path $HOME '.claude\hooks'

# python 실행기 탐색
$py = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command py -ErrorAction SilentlyContinue)
if (-not $py) { Write-Host "[MISSING] python — 설치 후 재실행" -ForegroundColor Yellow; return }
$pyExe = $py.Source
Write-Host "  python: $pyExe" -ForegroundColor Green

# 1) 운영 디렉토리 생성
foreach ($d in @($ardOps, (Join-Path $ardOps 'config'), (Join-Path $ardOps 'queue'),
                 (Join-Path $ardOps 'reports'), (Join-Path $ardOps 'harvester'),
                 (Join-Path $ardOps 'hooks'), (Join-Path $ardOps 'pull'), $agentsDir, $hooksDir)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

# 2) 스크립트·설정 비치
Copy-Item (Join-Path $loop 'config\sources.json')              (Join-Path $ardOps 'config\sources.json') -Force
Copy-Item (Join-Path $loop 'harvester\car_harvester.py')       (Join-Path $ardOps 'harvester\car_harvester.py') -Force
Copy-Item (Join-Path $loop 'harvester\car_github_harvester.py') (Join-Path $ardOps 'harvester\car_github_harvester.py') -Force
Copy-Item (Join-Path $loop 'hooks\car_dispatch.py')            (Join-Path $ardOps 'hooks\car_dispatch.py') -Force
Copy-Item (Join-Path $loop 'hooks\car_supervisor.py')      (Join-Path $ardOps 'hooks\car_supervisor.py') -Force
Copy-Item (Join-Path $loop 'hooks\car_dispatch.py')        (Join-Path $hooksDir 'car_dispatch.py') -Force
Copy-Item (Join-Path $loop 'pull\car_pull.py')             (Join-Path $ardOps 'pull\car_pull.py') -Force
New-Item -ItemType Directory -Force -Path (Join-Path $ardOps 'notifier') | Out-Null
Copy-Item (Join-Path $loop 'notifier\car_notify.py')       (Join-Path $ardOps 'notifier\car_notify.py') -Force
Copy-Item (Join-Path $repoRoot 'agents\CAR.md')            (Join-Path $agentsDir 'car.md') -Force
Write-Host "  비치: $ardOps, CAR 에이전트 → $agentsDir\car.md" -ForegroundColor Green

# 일회성 공지 seed — 노트북 켤 때 dispatch가 회장께 surface (max_shows회)
$notice = @{
    id = "yt-setup-and-verify"
    max_shows = 5
    shown = 0
    text = ("유튜브 갈래는 회장이 직접 셋업하기로 함 — 리마인드: ① 회장 로컬에서 video-reading 스킬/유튜브 채널 확정. " +
            "② 설치 검증 필수: (a) python <ARD ops>\harvester\car_github_harvester.py --force 로 깃허브 큐 쌓이나, " +
            "(b) python ...\car_harvester.py --force 로 유튜브 자막 쌓이나, (c) schtasks /query /TN G2-ARD-GitHub 로 스케줄 등록됐나, " +
            "(d) settings.json SessionStart에 car_dispatch 들어갔나(.bak 백업 확인). 이상 시 Alpha에게 보고.")
} | ConvertTo-Json -Compress
$noticesFile = Join-Path $ardOps 'notices.jsonl'
if (-not (Test-Path $noticesFile) -or -not (Select-String -Path $noticesFile -SimpleMatch 'yt-setup-and-verify' -Quiet)) {
    Add-Content -Path $noticesFile -Value $notice -Encoding UTF8
    Write-Host "  공지 seed: 다음 세션부터 회장께 리마인드" -ForegroundColor Green
}

# 3) 자막 라이브러리 설치
Write-Host "  youtube-transcript-api 설치 중..." -ForegroundColor Cyan
& $pyExe -m pip install --quiet --upgrade youtube-transcript-api
if ($LASTEXITCODE -eq 0) { Write-Host "  ✅ youtube-transcript-api" -ForegroundColor Green }
else { Write-Host "  ⚠️ pip 실패 — 수동: $pyExe -m pip install youtube-transcript-api" -ForegroundColor Yellow }

# 4) [옵션 B — 상주 데몬] Task Scheduler 등록. 2026-07-09 lean 개편 이후 이건 '선택'.
#    기본(옵션 A, 권장): car_dispatch가 SessionStart에 harvest+supervisor(24h 게이트)를 자동 실행
#    → 회장이 Claude Code를 열 때(≈매일)만 돌아 새 상주 데몬 0 (PC경량 원칙). schtasks는
#    회장이 'Claude를 안 여는 날에도 수확/감독이 돌길' 원할 때만 필요. 원치 않으면 이 블록 skip 가능.
$harvPath = Join-Path $ardOps 'harvester\car_harvester.py'
$ghPath   = Join-Path $ardOps 'harvester\car_github_harvester.py'
$supPath  = Join-Path $ardOps 'hooks\car_supervisor.py'
try {
    schtasks /Create /F /SC DAILY  /ST 09:00 /TN "G2-ARD-Harvester"  /TR "`"$pyExe`" `"$harvPath`"" | Out-Null
    schtasks /Create /F /SC DAILY  /ST 09:15 /TN "G2-ARD-GitHub"     /TR "`"$pyExe`" `"$ghPath`"" | Out-Null
    schtasks /Create /F /SC ONLOGON          /TN "G2-ARD-GitHub-Logon" /TR "`"$pyExe`" `"$ghPath`"" | Out-Null
    schtasks /Create /F /SC WEEKLY /D MON /ST 09:30 /TN "G2-ARD-Supervisor" /TR "`"$pyExe`" `"$supPath`"" | Out-Null
    Write-Host "  ✅ Task Scheduler: Harvester(일 09:00)·GitHub(일 09:15 +로그온)·Supervisor(월 09:30)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Task Scheduler 등록 실패(관리자 권한 필요할 수 있음). 수동 등록 안내는 README 참조." -ForegroundColor Yellow
}

# 5) SessionStart 훅 배선 (settings.json 안전 병합)
$settings = Join-Path $HOME '.claude\settings.json'
$cmd = "`"$pyExe`" `"$(Join-Path $hooksDir 'car_dispatch.py')`""
try {
    if (Test-Path $settings) { Copy-Item $settings "$settings.bak" -Force }
    $cfg = if (Test-Path $settings) { Get-Content $settings -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    if (-not $cfg.hooks) { $cfg | Add-Member -NotePropertyName hooks -NotePropertyValue ([pscustomobject]@{}) -Force }
    if (-not $cfg.hooks.SessionStart) { $cfg.hooks | Add-Member -NotePropertyName SessionStart -NotePropertyValue @() -Force }
    $already = ($cfg.hooks.SessionStart | ConvertTo-Json -Depth 10) -match 'car_dispatch'
    if (-not $already) {
        $entry = [pscustomobject]@{ hooks = @([pscustomobject]@{ type = 'command'; command = $cmd }) }
        $cfg.hooks.SessionStart = @($cfg.hooks.SessionStart) + $entry
        ($cfg | ConvertTo-Json -Depth 12) | Set-Content $settings -Encoding UTF8
        Write-Host "  ✅ SessionStart 훅 등록(settings.json, 백업 .bak 생성)" -ForegroundColor Green
    } else {
        Write-Host "  SessionStart 훅 이미 등록됨" -ForegroundColor DarkGray
    }
} catch {
    Write-Host "  ⚠️ settings.json 자동 병합 실패. 수동으로 SessionStart hooks에 추가:" -ForegroundColor Yellow
    Write-Host "     command: $cmd" -ForegroundColor Yellow
}

# 6) 스모크 실행 (깃허브·유튜브가 실제로 쌓이는지)
Write-Host "  GitHub 수확 1회 실행(스모크)..." -ForegroundColor Cyan
& $pyExe $ghPath --force
Write-Host "  YouTube 수확 1회 실행(스모크)..." -ForegroundColor Cyan
& $pyExe $harvPath --force --limit 2
Write-Host ""
Write-Host "✅ 설치 완료. 노트북 켤 때(로그온)·세션 시작 시 깃허브를 바로 확인하고," -ForegroundColor Green
Write-Host "   큐가 차면 Alpha가 CAR을 자동 소환합니다." -ForegroundColor Green
Write-Host "   수동 확인:  $pyExe `"$ghPath`" --force   /   큐: $ardOps\queue" -ForegroundColor DarkGray
