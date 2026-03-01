# PowerShell script to fetch trader@example.com account data

$BackendUrl = "http://localhost:8000"
$Email = "trader@example.com"

Write-Host "[*] Fetching trader data for: $Email" -ForegroundColor Cyan
Write-Host ""

$Uri = "$BackendUrl/dev/trader-data?email=$Email"

try {
    $Response = Invoke-RestMethod -Uri $Uri -Method Get -Headers @{"Content-Type" = "application/json"}
    
    Write-Host "[OK] User Information:" -ForegroundColor Green
    Write-Host "   Email: $($Response.user.email)"
    Write-Host "   User ID: $($Response.user.id)"
    Write-Host "   Verified: $($Response.user.verified)"
    Write-Host ""
    
    Write-Host "[INFO] MetaAPI Accounts: $($Response.summary.total_accounts)" -ForegroundColor Green
    Write-Host "   Connected: $($Response.summary.connected_accounts)" -ForegroundColor Green
    
    foreach ($account in $Response.meta_accounts) {
        $status = if ($account.connected) { "[CONNECTED]" } else { "[DISCONNECTED]" }
        Write-Host ""
        Write-Host "   Account: $($account.metaapi_account_id) $status" -ForegroundColor Yellow
        Write-Host "     MT Login: $($account.mt_login)"
        Write-Host "     Server: $($account.mt_server)"
        Write-Host "     Platform: $($account.mt_platform)"
        Write-Host "     Last Heartbeat: $($account.last_heartbeat)"
    }
    Write-Host ""
    
    Write-Host "[INFO] Open Trades: $($Response.summary.open_trades_count)" -ForegroundColor Green
    foreach ($trade in $Response.open_trades) {
        $direction = if ($trade.direction -eq "BUY") { "[BUY]" } else { "[SELL]" }
        Write-Host ""
        Write-Host "$direction Trade $($trade.id)" -ForegroundColor Cyan
        Write-Host "     Symbol: $($trade.symbol)"
        Write-Host "     Direction: $($trade.direction)"
        Write-Host "     Entry Price: $($trade.entry_price)"
        Write-Host "     Lot Size: $($trade.lot_size)"
        Write-Host "     SL: $($trade.sl) | TP: $($trade.tp)"
        Write-Host "     AI Score: $($trade.ai_score)"
        Write-Host "     Open Time: $($trade.open_time)"
    }
    Write-Host ""
    Write-Host "[OK] Done" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the backend is running on $BackendUrl"
}
