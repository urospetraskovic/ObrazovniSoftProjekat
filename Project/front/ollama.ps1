# Ollama wrapper - works on any machine
# Usage: .\ollama.ps1 serve
#        .\ollama.ps1 pull qwen2.5:7b-instruct-q4_K_M

param([Parameter(ValueFromRemainingArguments=$true)] $Arguments)

$OllamaPaths = @(
    "$env:USERPROFILE\AppData\Local\Programs\Ollama\ollama.exe",
    "C:\Program Files\Ollama\ollama.exe",
    "${env:ProgramFiles}\Ollama\ollama.exe"
)

foreach ($Path in $OllamaPaths) {
    if (Test-Path $Path) {
        & $Path @Arguments
        exit $LASTEXITCODE
    }
}

Write-Host "Error: Ollama not found" -ForegroundColor Red
Write-Host "Please install from: https://ollama.ai" -ForegroundColor Yellow
exit 1
