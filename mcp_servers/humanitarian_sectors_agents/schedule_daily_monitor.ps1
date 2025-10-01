# PowerShell script to schedule daily OpenAI usage monitoring
# Run this script once to set up automatic daily monitoring

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Sudan Humanitarian AI - Schedule Daily Monitor" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Get current script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$batchFile = Join-Path $scriptDir "run_daily_monitor.bat"

Write-Host "[INFO] Script directory: $scriptDir" -ForegroundColor Green
Write-Host "[INFO] Batch file: $batchFile" -ForegroundColor Green

# Check if batch file exists
if (Test-Path $batchFile) {
    Write-Host "[FOUND] Daily monitor batch file exists" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Batch file not found: $batchFile" -ForegroundColor Red
    exit 1
}

# Ask user for preferred time
Write-Host "`n[SETUP] When would you like to run daily monitoring?" -ForegroundColor Yellow
Write-Host "1. 9:00 AM (recommended for morning review)" -ForegroundColor White
Write-Host "2. 6:00 PM (end of day review)" -ForegroundColor White
Write-Host "3. Custom time" -ForegroundColor White

$choice = Read-Host "Enter your choice (1-3)"

switch ($choice) {
    "1" { $time = "09:00" }
    "2" { $time = "18:00" }
    "3" {
        $time = Read-Host "Enter time in 24-hour format (HH:MM, e.g., 14:30)"
        if ($time -notmatch "^\d{2}:\d{2}$") {
            Write-Host "[ERROR] Invalid time format. Please use HH:MM" -ForegroundColor Red
            exit 1
        }
    }
    default {
        Write-Host "[ERROR] Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n[CREATING] Scheduled task for $time daily..." -ForegroundColor Yellow

# Create scheduled task
$taskName = "Sudan_Humanitarian_AI_Monitor"
$taskDescription = "Daily OpenAI API usage monitoring for Sudan Humanitarian Platform"

try {
    # Delete existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "[INFO] Removing existing scheduled task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # Create new scheduled task
    $action = New-ScheduledTaskAction -Execute $batchFile -WorkingDirectory $scriptDir
    $trigger = New-ScheduledTaskTrigger -Daily -At $time
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $taskDescription

    Write-Host "[SUCCESS] Scheduled task created successfully!" -ForegroundColor Green
    Write-Host "[INFO] Task name: $taskName" -ForegroundColor White
    Write-Host "[INFO] Schedule: Daily at $time" -ForegroundColor White
    Write-Host "[INFO] Command: $batchFile" -ForegroundColor White

    # Show next run time
    $task = Get-ScheduledTask -TaskName $taskName
    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Host "[INFO] Next run time: $($taskInfo.NextRunTime)" -ForegroundColor Cyan

} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[ALTERNATIVE] You can run the monitoring manually:" -ForegroundColor Yellow
    Write-Host "  Double-click: run_daily_monitor.bat" -ForegroundColor White
    Write-Host "  Or run: python usage_dashboard.py" -ForegroundColor White
}

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Write-Host "`n[MANUAL OPTIONS] You can also:" -ForegroundColor Yellow
Write-Host "• Double-click 'run_daily_monitor.bat' anytime" -ForegroundColor White
Write-Host "• Run 'python usage_dashboard.py' from command line" -ForegroundColor White
Write-Host "• Open 'usage_monitor.html' in your browser" -ForegroundColor White
Write-Host "• Check 'local_usage_tracking.json' for data" -ForegroundColor White

Write-Host "`n[MANAGE TASK] To manage the scheduled task:" -ForegroundColor Yellow
Write-Host "• Open 'Task Scheduler' (taskschd.msc)" -ForegroundColor White
Write-Host "• Look for: $taskName" -ForegroundColor White
Write-Host "• You can run, disable, or modify it there" -ForegroundColor White

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")