param([string]$Bundle, [string]$Thumbprint)
$ErrorActionPreference = 'Stop'
$cert = Get-Item "Cert:\CurrentUser\My\$Thumbprint"
$rsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
try {
    $bytes = [System.IO.File]::ReadAllBytes((Join-Path $Bundle 'integrity.json'))
    $signature = $rsa.SignData($bytes, [System.Security.Cryptography.HashAlgorithmName]::SHA256,
        [System.Security.Cryptography.RSASignaturePadding]::Pkcs1)
    [System.IO.File]::WriteAllText((Join-Path $Bundle 'integrity.sig'),
        [Convert]::ToBase64String($signature), [System.Text.Encoding]::ASCII)
} finally { $rsa.Dispose() }
