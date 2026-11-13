# Vérification du 13 novembre 2026

## Réalisé sur cet environnement Windows 11 x64 (build 26200)

- Archive originale retrouvée et extraite ; application Python/Tkinter v1.1 réutilisée.
- Trois tests automatisés réussis : export Unicode/caractères XML et PNG intégré identique à l'original ; échec d'export préservant destination et capture ; XML mal formé rejeté.
- Application compilée par PyInstaller, code de sortie 0.
- Exécutable compilé lancé avec `--self-test` : code de sortie 0, Tk 9.0.4 chargé, un moniteur détecté, hook installé puis retiré. Aucune touche injectée.
- Capture réelle par le code source dans le worker : PNG écrit, file d'attente vidée, export XHTML de 342074 octets analysé avec succès. Profil temporaire redirigé vers un dossier de test du workspace, car l'environnement restreint les écritures hors workspace. Images de ce test supprimées après vérification.
- Installateur réellement compilé par Inno Setup, compilation réussie. Ce fichier est un exécutable Windows, pas un script renommé.
- Inspection de la configuration : `PrivilegesRequired=lowest`, destination et raccourci propres à l'utilisateur, pas d'écriture HKLM ou Program Files, pas d'option de bascule en installation administrative.

Les journaux et comptes rendus JSON sont fournis dans l'archive de vérification. Les avertissements PyInstaller sur des modules optionnels ou d'autres plateformes sont conservés. Le démarrage du binaire réussit malgré ces avertissements.

## Non vérifié — nécessaire avant une diffusion large

- Installation et désinstallation complètes sous un vrai compte Windows standard : le Setup a été compilé, mais pas exécuté pour modifier le profil utilisateur réel.
- Parcours manuel complet de l'application packagée, déclenchement physique Impr. écran et conflit avec l'outil de capture Windows.
- Windows 10 ; deux moniteurs et plus, coordonnées négatives, mise à l'échelle mixte et branchement/débranchement.
- Sessions longues (30 captures et plus), espace disque saturé, fermeture pendant export, restauration après incident.
- Ouverture du XHTML dans Edge et Firefox et affichage de toutes les images.
- Mise à jour d'une installation existante, comportements SmartScreen/antivirus et politiques d'entreprise.

Le test du hook prouve son installation, pas la priorité universelle de la touche. La validation du document prouve qu'il est XML bien formé, pas sa conformité à tous les dialectes XHTML ou à tous les lecteurs.

SHA256 de l'archive source v1.1 originale :
`A219C3EE3B82589699FBEAB6EA130D61FC43CD613D62ABB7E2E736CD3E7742BE`

SHA256 du Setup livré :
`ADE3E25A1E26479F9ABEEC4109E22A1D3F91B7D9C00A8D6352101679075B1128`
