# add-posthog.ps1 — 프로젝트에 PostHog(제품 분석·세션 리플레이·에러 추적) 한 번에 심기
# 사진 스택 #5. 회장 스택에서 유일하게 비어 있던 "측정" 공정.
#
# 사용:
#   .\add-posthog.ps1 -ProjectPath C:\Users\kgg25\Desktop\myapp -ApiKey phc_xxx
#   (ApiKey = PostHog 프로젝트의 "Project API Key". 클라이언트용 공개 키라 프론트 코드에 들어가는 게 정상)
#
# [추정] 프레임워크별 정확한 최신 통합 방식은 https://posthog.com/docs 에서 재확인 권장.

param(
    [Parameter(Mandatory)][string]$ProjectPath,
    [Parameter(Mandatory)][string]$ApiKey,
    [string]$ApiHost = 'https://us.i.posthog.com'
)
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ProjectPath)) { throw "ProjectPath 없음: $ProjectPath" }
Push-Location $ProjectPath
try {
    $isNode = Test-Path 'package.json'
    if ($isNode) {
        Write-Host "posthog-js 설치 중..." -ForegroundColor Cyan
        npm install posthog-js
        if ($LASTEXITCODE -ne 0) { throw "npm install 실패" }

        $pkg    = Get-Content package.json -Raw
        $isNext = $pkg -match '"next"\s*:'

        $init = @"
// PostHog init — G2 Claude App Factory (자동 생성)
// 측정: 세션 리플레이 + 제품 분석 + 에러 추적 + 기능 플래그
// 참고: https://posthog.com/docs  (프레임워크별 권장 방식 변동 가능 [추정])
import posthog from 'posthog-js'

if (typeof window !== 'undefined') {
  posthog.init('$ApiKey', {
    api_host: '$ApiHost',
    capture_pageview: true,
    capture_exceptions: true,
  })
}

export default posthog
"@
        # Next.js(15.3+)는 instrumentation-client.js를 자동 로드. 그 외는 수동 import.
        $target = if ($isNext) { 'instrumentation-client.js' } else { 'posthog.js' }
        Set-Content -Path $target -Value $init -Encoding UTF8
        Write-Host "✅ 작성: $target" -ForegroundColor Green
        if (-not $isNext) {
            Write-Host "   앱 진입점에서 한 번 import 하세요:  import './posthog'" -ForegroundColor Yellow
        } else {
            Write-Host "   Next.js: instrumentation-client.js는 자동 로드됨(추가 import 불필요)." -ForegroundColor DarkGray
        }
    } else {
        Write-Host "Node 프로젝트 아님 → HTML 스니펫을 <head>에 붙이세요:" -ForegroundColor Yellow
        $snip = (Get-Content (Join-Path $PSScriptRoot 'posthog-snippet.html') -Raw)
        $snip = $snip.Replace('__POSTHOG_KEY__', $ApiKey).Replace('__POSTHOG_HOST__', $ApiHost)
        Write-Host $snip
    }
}
finally { Pop-Location }

Write-Host "완료. PostHog 대시보드에서 이벤트가 들어오는지 확인하세요." -ForegroundColor Green
