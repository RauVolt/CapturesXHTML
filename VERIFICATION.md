# Vérification StepsShot 1.0.3 — 24 novembre 2026

## Résultats locaux

- Compilation réelle sous Windows 11 x64, Python 3.12.14, PyInstaller 6.22.3 et Inno Setup 6.4.3.
- 30 tests réussis : captures et curseur natif, raccourcis, interface, choix d’écran, sauvegarde progressive, conflits externes, historique, export DOCX et nouveaux contrôles d’intégrité.
- Vérification structurelle DOCX : en-tête égal au nom du fichier sans extension, date JJ/MM/AAAA, champs natifs PAGE et NUMPAGES et tabulation droite sur la largeur utile.
- Programme compilé : un moniteur détecté, hook installé, Tk 8.6.12, pipeline de capture avec curseur et export DOCX réussis, dans un profil de test isolé.
- Inventaire signé du bundle intact accepté. Sur une copie isolée, modification du programme, d’un fichier de données, de l’inventaire ou ajout d’une DLL : refus avec code 2. Après restauration : code 0.
- Signatures Authenticode présentes sur EXE, Setup et désinstalleur généré par Inno. Empreinte du certificat local : `9A161C00509DFDAA6A0F80AAFDA989CE0171BAC8` ; CN=RauVolt StepsShot ; expiration 24/11/2029.
- Windows retourne UnknownError avec le motif explicite « certificat racine non approuvé » pour le fichier intact autosigné. Sur une copie dont un octet du stub EXE est modifié, Windows retourne HashMismatch. Aucune autorité de confiance n’a été installée.
- Clé privée non exportable dans le magasin personnel Windows. Aucun PFX ni clé privée dans les livrables. Certificat public livré séparément. Pas d’horodatage.

## Limites de vérification

- Aucun rendu visuel du DOCX dans Word ou Writer : poursuite sans Word à la demande de l’utilisateur. Les champs de pagination sont calculés par le logiciel bureautique ; le total affiché après ouverture reste à vérifier dans celui-ci.
- Aucune installation, mise à jour ou désinstallation de l’application existante sur le profil utilisateur. Le Setup et le désinstalleur sont compilés et signés ; leur installation réelle reste à tester.
- Pas de poste Windows 10, de DPI mixtes ni de test exhaustif des raccourcis physiques.
- Ce contrôle s’effectue dans l’application, après chargement du runtime ; il peut être supprimé en modifiant le programme. Il ne remplace pas une politique de contrôle imposée par Windows.
- Les fichiers de désinstallation Inno sont exclus de l’inventaire applicatif ; le désinstalleur bénéficie de sa propre signature Authenticode.
- La CI recrée sa propre identité autosignée éphémère à chaque build. Son certificat n’est pas celui du build local. Le rapport CI donne son commit et son environnement ; les essais locaux ne constituent pas un test du binaire CI.
