param([string]$Subject = 'CN=RauVolt StepsShot')
$ErrorActionPreference = 'Stop'
# Never add this certificate to Trusted Root or Trusted Publishers automatically.
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject $Subject `
    -CertStoreLocation Cert:\CurrentUser\My -KeyAlgorithm RSA -KeyLength 3072 `
    -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotAfter (Get-Date).AddYears(3)
$cert.Thumbprint
