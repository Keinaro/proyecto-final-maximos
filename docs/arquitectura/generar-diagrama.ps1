# Script fuente para regenerar docs/arquitectura/diagrama.png (Criterio A3)
# Uso desde la raíz del repo:
#   $c = Get-Content -Raw -Encoding UTF8 "docs/arquitectura/generar-diagrama.ps1"; Invoke-Expression $c

Add-Type -AssemblyName System.Drawing

$width = 1850
$height = 1220
$bmp = New-Object System.Drawing.Bitmap($width, $height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$g.Clear([System.Drawing.Color]::FromArgb(248, 250, 252))

$fontTitle = New-Object System.Drawing.Font("Segoe UI", 20, [System.Drawing.FontStyle]::Bold)
$fontSubTitle = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Regular)
$fontGroup = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$fontBoxTitle = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$fontBoxBody = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Regular)
$fontCode = New-Object System.Drawing.Font("Consolas", 9, [System.Drawing.FontStyle]::Bold)
$fontArrow = New-Object System.Drawing.Font("Consolas", 8.5, [System.Drawing.FontStyle]::Bold)

function New-RoundedRect([int]$x, [int]$y, [int]$w, [int]$h, [int]$r) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    return $path
}

function Draw-GroupBox($x, $y, $w, $h, $title, $bgColor, $borderColor, $dashed=$false) {
    $path = New-RoundedRect $x $y $w $h 14
    $brush = New-Object System.Drawing.SolidBrush($bgColor)
    $pen = New-Object System.Drawing.Pen($borderColor, 2)
    if ($dashed) {
        $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
    }
    $g.FillPath($brush, $path)
    $g.DrawPath($pen, $path)
    $textBrush = New-Object System.Drawing.SolidBrush($borderColor)
    $g.DrawString($title, $fontGroup, $textBrush, ($x + 16), ($y + 10))
}

function Draw-Card($x, $y, $w, $h, $headerText, $lines, $headerColor, $borderColor) {
    $path = New-RoundedRect $x $y $w $h 10
    $bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
    $g.FillPath($bgBrush, $path)

    $headerRect = New-Object System.Drawing.Rectangle($x, $y, $w, 32)
    $headerBrush = New-Object System.Drawing.SolidBrush($headerColor)
    $g.SetClip($path)
    $g.FillRectangle($headerBrush, $headerRect)
    $g.ResetClip()

    $pen = New-Object System.Drawing.Pen($borderColor, 2)
    $g.DrawPath($pen, $path)

    $whiteBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
    $g.DrawString($headerText, $fontBoxTitle, $whiteBrush, ($x + 12), ($y + 6))

    $bodyBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(30, 41, 59))
    $currY = $y + 40
    foreach ($line in $lines) {
        if ($line.StartsWith("CODE:")) {
            $codeText = $line.Substring(5)
            $codeBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(15, 118, 110))
            $g.DrawString($codeText, $fontCode, $codeBrush, ($x + 12), $currY)
        } else {
            $g.DrawString($line, $fontBoxBody, $bodyBrush, ($x + 12), $currY)
        }
        $currY += 19
    }
}

function Draw-Arrow($x1, $y1, $x2, $y2, $label, $color, $dashed=$false, $labelOffsetX=0, $labelOffsetY=-18) {
    $pen = New-Object System.Drawing.Pen($color, 2.5)
    if ($dashed) {
        $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
    }
    $cap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap(6, 6, $true)
    $pen.CustomEndCap = $cap
    $g.DrawLine($pen, $x1, $y1, $x2, $y2)

    if ($label -ne "") {
        $midX = [int](($x1 + $x2) / 2) + $labelOffsetX
        $midY = [int](($y1 + $y2) / 2) + $labelOffsetY
        $size = $g.MeasureString($label, $fontArrow)
        $bgRect = New-Object System.Drawing.RectangleF(($midX - $size.Width/2 - 5), ($midY - 2), ($size.Width + 10), ($size.Height + 4))
        $bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(245, 255, 255, 255))
        $borderPen = New-Object System.Drawing.Pen($color, 1)
        $g.FillRectangle($bgBrush, $bgRect)
        $g.DrawRectangle($borderPen, $bgRect.X, $bgRect.Y, $bgRect.Width, $bgRect.Height)
        $txtBrush = New-Object System.Drawing.SolidBrush($color)
        $g.DrawString($label, $fontArrow, $txtBrush, ($midX - $size.Width/2), $midY)
    }
}

$headerBanner = New-Object System.Drawing.Rectangle(0, 0, $width, 78)
$bannerBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(15, 23, 42))
$g.FillRectangle($bannerBrush, $headerBanner)
$white = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
$muted = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(148, 163, 184))
$g.DrawString("Diagrama de Arquitectura · Clínica Veterinaria Máximos (Caso 1: Pacientes y Citas)", $fontTitle, $white, 30, 14)
$g.DrawString("Criterio A3 · GKE Standard Zonal (gke-maximos) · Namespace: maximos · 2 Nodos e2-small Spot · Terraform IaC + Artifact Registry", $fontSubTitle, $muted, 32, 48)

Draw-Card 30 220 280 130 "Usuario / Navegador Externo" @(
    "Cliente web fuera del clúster (E5)",
    "Accede vía HTTP a la IP Pública",
    "CODE:GET /  (UI HTML/CSS/JS)",
    "CODE:/api/pacientes, /api/citas"
) ([System.Drawing.Color]::FromArgb(30, 64, 175)) ([System.Drawing.Color]::FromArgb(30, 64, 175))

Draw-Card 30 430 280 150 "Terraform (IaC · D1-D5)" @(
    "Archivos: versions.tf, main.tf,",
    "variables.tf, outputs.tf",
    "Declara: Clúster GKE, Spot Pool,",
    "Service Account IAM y",
    "CODE:Artifact Registry (vet-repo)"
) ([System.Drawing.Color]::FromArgb(109, 40, 217)) ([System.Drawing.Color]::FromArgb(109, 40, 217))

Draw-GroupBox 350 95 1470 1090 "Google Cloud Platform (Proyecto GCP · Región / Zona)" ([System.Drawing.Color]::FromArgb(241, 245, 249)) ([System.Drawing.Color]::FromArgb(71, 85, 105)) $false

Draw-Card 380 390 320 215 "Artifact Registry (C1-C3)" @(
    "Repositorio Docker: vet-repo",
    "CODE:REGION-docker.pkg.dev/",
    "CODE:PROJECT_ID/vet-repo",
    "Imágenes publicadas (linux/amd64):",
    "• frontend:v1.0.0",
    "• pacientes:v1.0.0 / v1.1.0 (F3)",
    "• citas:v1.0.0",
    "• db:16 (copia de postgres:16)"
) ([System.Drawing.Color]::FromArgb(2, 132, 199)) ([System.Drawing.Color]::FromArgb(2, 132, 199))

Draw-Card 380 650 320 150 "IAM Service Account Nodos" @(
    "CODE:gke-nodes-maximos",
    "Permisos del Node Pool:",
    "• roles/artifactregistry.reader",
    "• roles/logging.logWriter",
    "• roles/monitoring.metricWriter"
) ([System.Drawing.Color]::FromArgb(71, 85, 105)) ([System.Drawing.Color]::FromArgb(71, 85, 105))

Draw-GroupBox 730 140 1060 1020 "Clúster GKE Standard Zonal: gke-maximos  |  Node Pool: spot-pool (2x e2-small · spot = true · D5)" ([System.Drawing.Color]::FromArgb(236, 253, 245)) ([System.Drawing.Color]::FromArgb(13, 148, 136)) $false

Draw-GroupBox 760 190 1000 945 "Namespace: maximos  (00-namespace.yaml · A5)" ([System.Drawing.Color]::FromArgb(255, 255, 255)) ([System.Drawing.Color]::FromArgb(15, 118, 110)) $true

Draw-Card 800 240 380 140 "Punto de Entrada Público (E5)" @(
    "CODE:Service: frontend (LoadBalancer)",
    "Asigna EXTERNAL-IP pública en GCP",
    "Puerto externo: 80 -> targetPort: 80",
    "Selector: app=frontend"
) ([System.Drawing.Color]::FromArgb(217, 119, 6)) ([System.Drawing.Color]::FromArgb(217, 119, 6))

Draw-Card 1280 240 440 155 "Frontend Web + Proxy Inverso (B4, E6)" @(
    "CODE:Deployment: frontend (nginx:1.27-alpine)",
    "Sirve estáticos (/usr/share/nginx/html)",
    "Proxy Inverso por DNS interno (nginx.conf):",
    "CODE:/api/pacientes   -> http://pacientes:8080",
    "CODE:/api/citas       -> http://citas:8080",
    "CODE:/api/integrantes -> http://pacientes:8080"
) ([System.Drawing.Color]::FromArgb(13, 148, 136)) ([System.Drawing.Color]::FromArgb(13, 148, 136))

Draw-Card 800 460 430 215 "Microservicio A · Pacientes (B1, A4, F1, F3)" @(
    "CODE:Service: pacientes (ClusterIP :8080)",
    "CODE:Deployment: pacientes (1 -> 3 réplicas F1)",
    "Endpoints REST JSON:",
    "• GET/POST /pacientes",
    "• GET/PUT/DELETE /pacientes/{id} (409 si citas)",
    "• GET /integrantes (lee carnés de BD · A4)",
    "• GET /health (v1.0.0 -> v1.1.0 en F3)"
) ([System.Drawing.Color]::FromArgb(15, 118, 110)) ([System.Drawing.Color]::FromArgb(15, 118, 110))

Draw-Card 1290 460 430 215 "Microservicio B · Citas (B2)" @(
    "CODE:Service: citas (ClusterIP :8080)",
    "CODE:Deployment: citas (containerPort: 8080)",
    "Endpoints REST JSON:",
    "• GET /citas (acepta ?paciente_id=N)",
    "• POST /citas (valida FK paciente_id -> 400)",
    "• GET/PUT/DELETE /citas/{id}",
    "• GET /health (readiness / liveness probe)"
) ([System.Drawing.Color]::FromArgb(37, 99, 235)) ([System.Drawing.Color]::FromArgb(37, 99, 235))

Draw-Card 800 745 430 165 "Configuración y Credenciales (E2, E3)" @(
    "CODE:ConfigMap: app-config (E2)",
    "PORT=8080, DB_HOST=db, DB_PORT=5432, DB_NAME=vetdb",
    "CODE:Secret: db-secret (E3 · Opaque)",
    "DB_USER, DB_PASSWORD (Inyectados vía envFrom",
    "en pacientes, citas y db)"
) ([System.Drawing.Color]::FromArgb(124, 58, 237)) ([System.Drawing.Color]::FromArgb(124, 58, 237))

Draw-Card 1290 745 430 190 "Base de Datos PostgreSQL 16 (E4)" @(
    "CODE:Service: db (ClusterIP :5432)",
    "CODE:Deployment: db (imagen AR vet-repo/db:16)",
    "Estrategia: Recreate (replicas: 1)",
    "Tablas (init.sql): pacientes, citas, integrantes",
    "mountPath: /var/lib/postgresql/data",
    "PGDATA: /var/lib/postgresql/data/pgdata"
) ([System.Drawing.Color]::FromArgb(30, 58, 138)) ([System.Drawing.Color]::FromArgb(30, 58, 138))

Draw-Card 1290 965 430 135 "Almacenamiento Persistente (PVC · E4)" @(
    "CODE:PersistentVolumeClaim: db-pvc",
    "Modo: ReadWriteOnce (RWO) · Capacidad: 1Gi",
    "StorageClass por defecto (GCE Persistent Disk)",
    "Conserva datos al eliminar/recrear el pod db"
) ([System.Drawing.Color]::FromArgb(180, 83, 9)) ([System.Drawing.Color]::FromArgb(180, 83, 9))

Draw-Card 800 945 430 155 "Resumen de Comunicación DNS Interna (E6)" @(
    "1. Navegador -> http://<EXTERNAL-IP>:80",
    "2. Nginx (/api/pacientes) -> http://pacientes:8080",
    "3. Nginx (/api/citas)     -> http://citas:8080",
    "4. Microservicios         -> db:5432 (PostgreSQL)",
    "Ningún servicio interno expone IP pública."
) ([System.Drawing.Color]::FromArgb(51, 65, 85)) ([System.Drawing.Color]::FromArgb(51, 65, 85))

$blueArrow = [System.Drawing.Color]::FromArgb(30, 64, 175)
$tealArrow = [System.Drawing.Color]::FromArgb(13, 148, 136)
$dbArrow = [System.Drawing.Color]::FromArgb(30, 58, 138)
$purpleArrow = [System.Drawing.Color]::FromArgb(124, 58, 237)
$skyArrow = [System.Drawing.Color]::FromArgb(2, 132, 199)

Draw-Arrow 310 290 800 290 "HTTP :80 (IP Pública Externa)" $blueArrow $false -35 -22
Draw-Arrow 310 505 380 505 "apply" $purpleArrow $true 0 -20
Draw-Arrow 1180 310 1280 310 "port 80" ([System.Drawing.Color]::FromArgb(217, 119, 6)) $false 0 -22
Draw-Arrow 1390 395 1040 460 "DNS: http://pacientes:8080" $tealArrow $false -50 -10
Draw-Arrow 1520 395 1520 460 "DNS: http://citas:8080" ([System.Drawing.Color]::FromArgb(37, 99, 235)) $false 0 -10
Draw-Arrow 1120 675 1380 745 "TCP db:5432" $dbArrow $false -20 -12
Draw-Arrow 1520 675 1520 745 "TCP db:5432" $dbArrow $false 45 -10
Draw-Arrow 1015 745 1015 675 "envFrom" $purpleArrow $true -35 -8
Draw-Arrow 1230 825 1290 825 "env" $purpleArrow $true 0 -20
Draw-Arrow 1505 935 1505 965 "mountPath" ([System.Drawing.Color]::FromArgb(180, 83, 9)) $false 55 -10
Draw-Arrow 700 495 730 495 "" $skyArrow $true 0 0

$outPath = Join-Path (Get-Location).Path "docs\arquitectura\diagrama.png"
$bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "Saved diagram to $outPath"

