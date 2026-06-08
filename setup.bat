@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ============================================
echo   AI ID Photo Generator - 설치 및 실행
echo ============================================
echo.

:: Node.js 설치 확인
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Node.js가 설치되어 있지 않습니다.
    echo Node.js를 설치하려면 https://nodejs.org/ 를 방문하세요.
    start https://nodejs.org/
    echo Node.js 설치 후 이 파일을 다시 실행해주세요.
    pause
    exit /b 1
)

echo [확인] Node.js 버전:
node -v

:: Node.js 18 이상 권장
node -e "const v=parseInt(process.version.split('.')[0].replace('v','')); if(v<18){console.log('[경고] Node.js 18 이상 권장 (현재 v'+v+')')}" 2>nul

:: npm 설치 확인
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] npm이 없습니다. Node.js를 재설치해주세요.
    pause
    exit /b 1
)
echo [확인] npm 버전:
npm -v
echo.

:: .env.local 파일 확인 및 생성
if not exist ".env.local" (
    echo [설정] .env.local 파일이 없습니다.
    echo GEMINI_API_KEY=여기에_API_키_입력> .env.local
    echo.
    echo ================================================
    echo  중요: Gemini API 키를 설정해야 합니다!
    echo  발급 주소: https://aistudio.google.com/app/apikey
    echo ================================================
    echo.
    set /p APIKEY="Gemini API 키를 입력하세요 (건너뛰려면 Enter): "
    if not "!APIKEY!"=="" (
        echo GEMINI_API_KEY=!APIKEY!> .env.local
        echo [완료] API 키 저장 완료.
    ) else (
        echo [안내] .env.local 파일을 직접 편집해주세요.
        start notepad .env.local
    )
    echo.
) else (
    echo [확인] .env.local 존재
    findstr /c:"여기에_API_키_입력" .env.local >nul 2>&1
    if !errorlevel! equ 0 (
        echo [경고] API 키가 설정되지 않았습니다!
        echo .env.local 파일에서 GEMINI_API_KEY를 수정해주세요.
        start notepad .env.local
        echo.
    )
)

:: 패키지 설치
if not exist "node_modules" (
    echo [설치] 패키지 설치 중...
    npm install
    if %errorlevel% neq 0 (
        echo [오류] npm install 실패.
        echo 해결 방법:
        echo   1. 인터넷 연결 확인
        echo   2. npm cache clean --force 실행 후 재시도
        pause
        exit /b 1
    )
    echo [완료] 패키지 설치 완료.
) else (
    echo [확인] 패키지 이미 설치됨. 업데이트 확인 중...
    npm install --silent 2>nul
)
echo.

:: 개발 서버 실행
echo ============================================
echo   서버 시작: http://localhost:3000
echo   종료: Ctrl+C
echo ============================================
echo.
npm run dev

pause
