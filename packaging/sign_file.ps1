param([Parameter(Mandatory=$true)][string]$Path,
      [Parameter(Mandatory=$true)][string]$Thumbprint)
$ErrorActionPreference = 'Stop'
Import-Module Microsoft.PowerShell.Security
$cert = Get-Item -LiteralPath "Cert:\CurrentUser\My\$Thumbprint"
if (!$cert.HasPrivateKey) { throw 'Private signing key missing' }
$result = Set-AuthenticodeSignature -LiteralPath $Path -Certificate $cert -HashAlgorithm SHA256
if (!$result.SignerCertificate -or $result.SignerCertificate.Thumbprint -ne $cert.Thumbprint -or
    $result.Status -notin @('Valid', 'NotTrusted', 'UnknownError')) {
    throw "Signing failed: $($result.Status) $($result.StatusMessage)"
}
Write-Output "$Path : $($result.Status) / $($cert.Thumbprint)"
