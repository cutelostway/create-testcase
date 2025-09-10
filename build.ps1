param(
    [switch]$Run,
    [switch]$Public,
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    $potential = @("py", "python", "python3")
    foreach ($cmd in $potential) {
        try {
            $version = & $cmd --version 2>$null
            if ($LASTEXITCODE -eq 0 -or $version) { return $cmd }
        } catch {}
    }
    throw "Không tìm thấy Python. Vui lòng cài đặt Python 3.10+ và thêm vào PATH."
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Resolve-Python

$venvPath = Join-Path $root ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Tạo virtual environment..." -ForegroundColor Cyan
    & $python -m venv $venvPath
}

$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Không tìm thấy script kích hoạt venv: $activateScript"
}

Write-Host "Kích hoạt virtual environment..." -ForegroundColor Cyan
. $activateScript

Write-Host "Nâng cấp công cụ build (pip, wheel, setuptools)..." -ForegroundColor Cyan
python -m ensurepip --upgrade | Out-Null
python -m pip install --upgrade pip wheel setuptools

$req = Join-Path $root "requirements.txt"
if (Test-Path $req) {
    Write-Host "Cài đặt phụ thuộc từ requirements.txt..." -ForegroundColor Cyan
    python -m pip install -r $req
} else {
    Write-Warning "Không tìm thấy requirements.txt, bỏ qua cài đặt phụ thuộc."
}

# Kiểm tra streamlit đã sẵn sàng
try {
    streamlit --version | Out-Null
} catch {
    throw "Streamlit chưa được cài. Kiểm tra requirements hoặc cài: pip install streamlit"
}

# Xác định địa chỉ bind
$address = if ($Public) { "0.0.0.0" } else { "localhost" }

if ($Run) {
    Write-Host "Khởi chạy ứng dụng Streamlit..." -ForegroundColor Green
    Write-Host "Address: $address  |  Port: $Port" -ForegroundColor DarkGray

    # Thông tin truy cập
    if ($Public) {
        try {
            $ips = (Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -ne '127.0.0.1' }).IPAddress
            if (-not $ips) {
                $ips = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -ne '127.0.0.1' }).IPAddress
            }
            if ($ips) {
                Write-Host "Thiết bị khác trong cùng mạng có thể truy cập: http://$($ips[0]):$Port" -ForegroundColor Yellow
            } else {
                Write-Host "Thiết bị khác trong cùng mạng có thể truy cập: http://<IP-cua-ban>:$Port" -ForegroundColor Yellow
            }
            Write-Host "Nếu cần, mở firewall Windows cho cổng $Port" -ForegroundColor DarkYellow
            Write-Host "netsh advfirewall firewall add rule name=\"Streamlit $Port\" dir=in action=allow protocol=TCP localport=$Port" -ForegroundColor DarkYellow
        } catch {}
    } else {
        Write-Host "Truy cập cục bộ: http://localhost:$Port" -ForegroundColor Yellow
    }

    streamlit run app.py --server.port $Port --server.address $address
} else {
    Write-Host "\nMôi trường đã sẵn sàng." -ForegroundColor Green
    Write-Host "Để chạy ứng dụng local: .\\build.ps1 -Run" -ForegroundColor Yellow
    Write-Host "Để cho máy khác trong LAN truy cập: .\\build.ps1 -Run -Public -Port 8501" -ForegroundColor Yellow
    Write-Host "Gợi ý mở firewall (nếu cần):" -ForegroundColor DarkYellow
    Write-Host "netsh advfirewall firewall add rule name=\"Streamlit 8501\" dir=in action=allow protocol=TCP localport=8501" -ForegroundColor DarkYellow
    Write-Host "Hoặc chạy thủ công:" -ForegroundColor Yellow
    Write-Host "1) .\\.venv\\Scripts\\Activate.ps1"
    Write-Host "2) streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
}
