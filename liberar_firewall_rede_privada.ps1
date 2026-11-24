# Execute este script no PowerShell como Administrador somente se o celular
# nao conseguir acessar o computador pela rede Wi-Fi privada.
$regra = Get-NetFirewallRule -DisplayName "Emprega Serra - Rede Privada" -ErrorAction SilentlyContinue
if (-not $regra) {
    New-NetFirewallRule -DisplayName "Emprega Serra - Rede Privada" `
        -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5000 `
        -Profile Private -Description "Acesso local ao Emprega Serra pela rede Wi-Fi privada."
    Write-Host "Regra criada somente para redes privadas."
} else {
    Write-Host "A regra ja existe."
}
