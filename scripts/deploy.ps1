# AstroSense Production Deployment Script for Windows
# PowerShell script to deploy AstroSense in production mode

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackup = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Status {
    param(
        [string]$Status,
        [string]$Message
    )
    
    switch ($Status) {
        "OK" { Write-Host "✓ $Message" -ForegroundColor $Green }
        "WARN" { Write-Host "⚠ $Message" -ForegroundColor $Yellow }
        "ERROR" { Write-Host "✗ $Message" -ForegroundColor $Red }
        "INFO" { Write-Host "ℹ $Message" -ForegroundColor $Blue }
    }
}

function Test-Prerequisites {
    Write-Status "INFO" "Checking prerequisites..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Status "OK" "Docker found: $dockerVersion"
    }
    catch {
        Write-Status "ERROR" "Docker is not installed or not in PATH"
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-Status "OK" "Docker Compose found: $composeVersion"
    }
    catch {
        Write-Status "ERROR" "Docker Compose is not installed or not in PATH"
        exit 1
    }
    
    # Check environment file
    if (!(Test-Path ".env.production")) {
        Write-Status "ERROR" "Production environment file not found: .env.production"
        Write-Status "INFO" "Copy .env.production.example to .env.production and configure it"
        exit 1
    }
    
    Write-Status "OK" "Prerequisites check passed"
}

function Backup-Database {
    if ($SkipBackup) {
        Write-Status "INFO" "Skipping database backup (--SkipBackup specified)"
        return
    }
    
    Write-Status "INFO" "Creating database backup..."
    
    # Create backups directory if it doesn't exist
    if (!(Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backups/astrosense_backup_$timestamp.sql"
    
    try {
        # Load environment variables
        Get-Content ".env.production" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
        
        $postgresUser = $env:POSTGRES_USER
        $postgresDb = $env:POSTGRES_DB
        
        # Create backup
        docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U $postgresUser $postgresDb > $backupFile
        
        if (Test-Path $backupFile) {
            Write-Status "OK" "Database backup created: $backupFile"
        } else {
            Write-Status "WARN" "Database backup may have failed"
        }
    }
    catch {
        Write-Status "WARN" "Database backup failed: $($_.Exception.Message)"
    }
}

function Deploy-Application {
    Write-Status "INFO" "Deploying AstroSense application..."
    
    try {
        # Pull latest images
        Write-Status "INFO" "Pulling latest Docker images..."
        docker-compose -f docker-compose.prod.yml pull
        
        # Build application images
        Write-Status "INFO" "Building application images..."
        docker-compose -f docker-compose.prod.yml build --no-cache
        
        # Start services
        Write-Status "INFO" "Starting services..."
        docker-compose -f docker-compose.prod.yml up -d
        
        # Wait for services to be ready
        Write-Status "INFO" "Waiting for services to be ready..."
        Start-Sleep -Seconds 30
        
        # Check service status
        $services = docker-compose -f docker-compose.prod.yml ps --services
        $runningServices = 0
        
        foreach ($service in $services) {
            $status = docker-compose -f docker-compose.prod.yml ps $service
            if ($status -match "Up") {
                Write-Status "OK" "Service $service is running"
                $runningServices++
            } else {
                Write-Status "ERROR" "Service $service is not running"
            }
        }
        
        if ($runningServices -eq $services.Count) {
            Write-Status "OK" "All services are running successfully"
        } else {
            Write-Status "WARN" "$runningServices of $($services.Count) services are running"
        }
    }
    catch {
        Write-Status "ERROR" "Deployment failed: $($_.Exception.Message)"
        exit 1
    }
}

function Test-Deployment {
    Write-Status "INFO" "Testing deployment..."
    
    # Test health endpoints
    $endpoints = @(
        @{ Name = "Main Health"; Url = "http://localhost/health" },
        @{ Name = "Backend API"; Url = "http://localhost:8000/health" },
        @{ Name = "Frontend"; Url = "http://localhost:3000" }
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.Url -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Status "OK" "$($endpoint.Name) is responding"
            } else {
                Write-Status "WARN" "$($endpoint.Name) returned status $($response.StatusCode)"
            }
        }
        catch {
            Write-Status "ERROR" "$($endpoint.Name) is not responding: $($_.Exception.Message)"
        }
    }
}

function Show-DeploymentInfo {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $Blue
    Write-Host "AstroSense Deployment Complete" -ForegroundColor $Blue
    Write-Host "========================================" -ForegroundColor $Blue
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor $Blue
    Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor $Green
    Write-Host "  Backend API: http://localhost:8000" -ForegroundColor $Green
    Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor $Green
    Write-Host "  Grafana:     http://localhost:3001" -ForegroundColor $Green
    Write-Host "  Prometheus:  http://localhost:9090" -ForegroundColor $Green
    Write-Host ""
    Write-Host "Useful Commands:" -ForegroundColor $Blue
    Write-Host "  View logs:   docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor $Yellow
    Write-Host "  Stop:        docker-compose -f docker-compose.prod.yml down" -ForegroundColor $Yellow
    Write-Host "  Restart:     docker-compose -f docker-compose.prod.yml restart" -ForegroundColor $Yellow
    Write-Host "  Status:      docker-compose -f docker-compose.prod.yml ps" -ForegroundColor $Yellow
    Write-Host ""
}

# Main deployment process
function Main {
    Write-Host "========================================" -ForegroundColor $Blue
    Write-Host "AstroSense Production Deployment" -ForegroundColor $Blue
    Write-Host "========================================" -ForegroundColor $Blue
    Write-Host "Environment: $Environment" -ForegroundColor $Blue
    Write-Host "Timestamp: $(Get-Date)" -ForegroundColor $Blue
    Write-Host ""
    
    # Check prerequisites
    Test-Prerequisites
    
    # Confirm deployment
    if (!$Force) {
        $confirmation = Read-Host "Continue with production deployment? (y/N)"
        if ($confirmation -ne "y" -and $confirmation -ne "Y") {
            Write-Status "INFO" "Deployment cancelled by user"
            exit 0
        }
    }
    
    # Create backup
    Backup-Database
    
    # Deploy application
    Deploy-Application
    
    # Test deployment
    Test-Deployment
    
    # Show deployment info
    Show-DeploymentInfo
    
    Write-Status "OK" "Deployment completed successfully!"
}

# Run main function
Main