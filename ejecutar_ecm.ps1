# Script para ejecutar el proyecto ECM/SIS2, invocado por el Task Scheduler
# de Windows. Notifica a un canal de Teams tanto si sale bien como si falla.

$proyectoDir = "C:\Users\Fabian.Castillo\proyecto_ecm"
$pythonExe   = "C:\ProgramData\anaconda3\python.exe"
$webhookUrl  = "https://default3356d409ed5a4badac05b557a2a898.63.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/f2879a20a7fc4f288194686c2ad8791c/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=n6ofXCnsTmcj6bV1DtFVERg1Twmw9oTzuef08pFgXO8"
$logFile     = "$proyectoDir\Results\log_ejecucion.txt"

Set-Location $proyectoDir

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "`n===== Ejecucion iniciada: $timestamp =====" -Encoding utf8

& $pythonExe ServiceSoftwareFiles.py 2>&1 | Out-File -FilePath $logFile -Append -Encoding utf8
$exitCode = $LASTEXITCODE

Add-Content -Path $logFile -Value "===== Ejecucion terminada con codigo: $exitCode =====" -Encoding utf8

# Toma las ultimas lineas relevantes del log de esta corrida para incluir
# un resumen real en el mensaje de Teams (filas exitosas, cambios en SQL)
$resumenLog = (Get-Content -Path $logFile -Tail 10 -Encoding utf8) -join " | "

if ($exitCode -eq 0) {
    $titulo  = "Extraccion SIS2/ECM completada OK"
    $detalle = "La ejecucion en la VM termino sin errores. Resumen: $resumenLog"
} else {
    $titulo  = "Falla en extraccion SIS2/ECM"
    $detalle = "La ejecucion en la VM termino con error (codigo $exitCode). Resumen: $resumenLog"
}

$body = @{
    titulo  = $titulo
    detalle = $detalle
    fecha   = $timestamp
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri $webhookUrl -Method Post -Body $body -ContentType "application/json"
} catch {
    Add-Content -Path $logFile -Value "No se pudo enviar la notificacion a Teams: $_" -Encoding utf8
}