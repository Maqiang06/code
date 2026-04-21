# 量化交易助手自我进化系统 - Windows安装脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "量化交易助手自我进化系统 安装程序" -ForegroundColor Cyan
Write-Host "版本: 1.0.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查Python版本
Write-Host "检查Python版本..." -ForegroundColor Yellow
$pythonVersion = & python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: Python未找到，请先安装Python 3.8或更高版本" -ForegroundColor Red
    exit 1
}

# 提取Python版本号
$pythonVersionStr = $pythonVersion -replace "Python ", ""
$versionParts = $pythonVersionStr.Split('.')
$majorVersion = [int]$versionParts[0]
$minorVersion = [int]$versionParts[1]

if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
    Write-Host "错误: 需要 Python 3.8 或更高版本，当前版本: $pythonVersionStr" -ForegroundColor Red
    exit 1
}

Write-Host "检测到 Python $pythonVersionStr" -ForegroundColor Green

# 检查pip
Write-Host "检查pip..." -ForegroundColor Yellow
& pip --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: pip未找到，请先安装pip" -ForegroundColor Red
    exit 1
}

# 安装选项
Write-Host ""
Write-Host "安装选项:" -ForegroundColor Cyan
Write-Host "1. 基础安装 (仅核心功能)" -ForegroundColor Yellow
Write-Host "2. 完全安装 (包含Web界面和机器学习功能)" -ForegroundColor Yellow
Write-Host "3. 开发环境安装 (包含所有开发工具)" -ForegroundColor Yellow

$installOption = Read-Host "请选择安装选项 (1/2/3, 默认:2)"
if ([string]::IsNullOrWhiteSpace($installOption)) {
    $installOption = "2"
}

# 创建虚拟环境（可选）
$createVenv = Read-Host "是否创建虚拟环境? (y/n, 默认:y)"
if ([string]::IsNullOrWhiteSpace($createVenv)) {
    $createVenv = "y"
}

if ($createVenv -eq "y") {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    & python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "警告: 虚拟环境创建失败，继续系统安装..." -ForegroundColor Yellow
    } else {
        Write-Host "虚拟环境已创建，请手动激活:" -ForegroundColor Green
        Write-Host "venv\Scripts\Activate.ps1" -ForegroundColor Cyan
        Write-Host "或使用: .\venv\Scripts\Activate" -ForegroundColor Cyan
    }
}

# 安装包
Write-Host "安装qtassist-self-evolution包..." -ForegroundColor Yellow

switch ($installOption) {
    "1" {
        Write-Host "执行基础安装..." -ForegroundColor Green
        & pip install -e .
    }
    "2" {
        Write-Host "执行完全安装..." -ForegroundColor Green
        & pip install -e .[all]
    }
    "3" {
        Write-Host "执行开发环境安装..." -ForegroundColor Green
        & pip install -e .[all,dev]
    }
    default {
        Write-Host "无效选项，使用完全安装..." -ForegroundColor Yellow
        & pip install -e .[all]
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: 包安装过程中出现错误" -ForegroundColor Red
}

# 验证安装
Write-Host ""
Write-Host "验证安装..." -ForegroundColor Yellow
& python -c "import qtassist_self_evolution; print('✓ qtassist_self_evolution 导入成功')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 包安装成功" -ForegroundColor Green
} else {
    Write-Host "✗ 包安装失败" -ForegroundColor Red
    exit 1
}

# 检查命令行工具
Write-Host ""
Write-Host "检查命令行工具..." -ForegroundColor Yellow
& where.exe qtassist-evolution 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 命令行工具已安装" -ForegroundColor Green
    Write-Host "使用方法: qtassist-evolution --help" -ForegroundColor Cyan
} else {
    Write-Host "命令行工具未找到，可能需要重启终端或手动添加到PATH" -ForegroundColor Yellow
}

# 创建数据目录
Write-Host ""
Write-Host "创建数据目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data", "logs" | Out-Null

# 显示后续步骤
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "1. 初始化系统: qtassist-evolution init" -ForegroundColor Yellow
Write-Host "2. 启动Web控制面板: qtassist-evolution web" -ForegroundColor Yellow
Write-Host "3. 查看帮助: qtassist-evolution --help" -ForegroundColor Yellow
Write-Host ""
Write-Host "文档:" -ForegroundColor Cyan
Write-Host "- 用户指南: 查看 docs/USAGE.md" -ForegroundColor Yellow
Write-Host "- API文档: 查看 docs/API.md" -ForegroundColor Yellow
Write-Host ""
Write-Host "注意:" -ForegroundColor Cyan
Write-Host "1. 如果创建了虚拟环境，请先激活虚拟环境" -ForegroundColor Yellow
Write-Host "2. 如果命令行工具不可用，请确保Python Scripts目录在PATH中" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan