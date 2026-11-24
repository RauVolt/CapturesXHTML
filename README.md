# StepsShot 1.0.3

StepsShot transforme des captures d’écran en un guide Word modifiable. Successeur de CapturesXHTML, sous licence MIT. Mainteneur : RauVolt.

## Un parcours en cinq étapes

1. **Donnez un nom à votre guide** : ce nom devient le titre du document.
2. **Choisissez l’écran** : sélectionnez le moniteur à capturer. Il peut être changé pendant la session.
3. **Choisissez où enregistrer** : indiquez un fichier `.docx` et son dossier. Si ce fichier existe, un remplacement est confirmé avant le démarrage.
4. **Démarrez puis capturez** avec Impr. écran, ou le raccourci configuré. Le fichier Word est créé avant la première capture, puis actualisé en arrière-plan après chaque capture.
5. **Terminez et complétez** : cliquez sur Terminer, puis Ouvrir le document. Modifiez les titres et explications dans Word ou LibreOffice Writer, déplacez ou supprimez les images.

Aucune licence Word et aucune installation de Python ne sont nécessaires pour capturer et générer le DOCX. Un logiciel capable de modifier les DOCX est nécessaire pour l’édition. Les captures sont des images : le texte à l’intérieur n’est pas converti par OCR.

## Documents Word

Chaque capture correspond à une étape avec titre éditable, date, image intégrée et paragraphe d’explication à compléter. Les images sont redimensionnées proportionnellement et ne dépendent pas de fichiers externes. Une étape commence sur une nouvelle page à partir de la deuxième capture. Le guide utilise des styles Word ordinaires, sans protection d’édition.

Pendant la session, attendez la confirmation de sauvegarde avant d’ouvrir le document. Les modifications sont à faire après Terminer. Si le fichier a été modifié ou déplacé ailleurs, StepsShot refuse de l’écraser. Si Word le verrouille, les captures restent conservées ; fermez le document pour réessayer, ou utilisez **Enregistrer une copie** vers un autre `.docx`, lorsque les captures en attente sont terminées.

Les PNG et un manifeste de session sont conservés dans `%LOCALAPPDATA%/StepsShot/Temp/session-*` jusqu’à finalisation réussie. Après une panne, la récupération est manuelle. Le dernier DOCX sauvegardé reste disponible ; la capture en cours peut ne pas avoir été intégrée. Chaque mise à jour réécrit le guide entier, ce qui convient aux sessions usuelles d’environ 50 captures.

## Raccourci et historique

Touche seule ou Ctrl / Alt / Maj + une touche ; le raccourci est réservé uniquement pendant la session. **Rétablir Impr. écran** restaure le raccourci initial. Les restrictions Windows et les autres hooks peuvent empêcher l’interception ; aucun contournement des écrans sécurisés. Les contenus protégés peuvent être noirs.

Les cinq derniers fichiers et leurs chemins restent affichés, avec un bouton vers chaque dossier. Deux zones de défilement verticales sont disponibles. Configuration et historique sont stockés localement dans `%LOCALAPPDATA%/StepsShot`. Au premier lancement, l’historique et le raccourci CapturesXHTML sont copiés si disponibles ; les documents XHTML précédents ne sont pas convertis ni supprimés.

## Installation et mise à jour

Un seul `StepsShot-1.0.3-Setup.exe`, pour Windows 10/11 x64, sans droits administrateur. Nouvelle installation dans `%LOCALAPPDATA%/Programs/StepsShot`. L’identité d’installation de CapturesXHTML est conservée pour qu’une mise à jour existante utilise son répertoire précédent et sa même entrée de désinstallation, sous le nouveau nom. L’ancien raccourci est remplacé par StepsShot. Documents, historique ancien et captures résiduelles ne sont pas supprimés.

Lorsqu’une installation existe, le Setup propose mise à jour/réinstallation, désinstallation ou annulation. Aucune désinstallation du poste utilisateur n’est effectuée automatiquement pendant les tests.

## Sources et compilation

Le dépôt historique reste [RauVolt/CapturesXHTML](https://github.com/RauVolt/CapturesXHTML). Le produit et les fichiers distribués s’appellent désormais StepsShot 1.0. Les versions de paquet et de fichier sont 1.0.3.

Sur Windows avec Python 3.12 ou 3.13 x64 (incluant Tkinter) et Inno Setup 6 :

```powershell
./build_windows.ps1 -Python 'C:/chemin/python.exe' -ISCC 'C:/chemin/Inno Setup 6/ISCC.exe'
```

Le script crée `.venv`, installe les dépendances, exécute les tests, génère l’icône, inclut le modèle DOCX et construit `installer/StepsShot-1.0.3-Setup.exe`. Internet est nécessaire pour les dépendances. Office n’est pas requis pour la compilation.

GitHub Actions compile sous Windows avec Python 3.13 et prépare une Release **brouillon** `v1.0.3`, incluant Setup, sources, rapport et empreintes SHA256. Aucune publication automatique d’une Release déjà publiée. Le lancement manuel est disponible dans Actions. Voir [VERIFICATION.md](VERIFICATION.md).

## Confidentialité et licence

Aucune télémétrie ni transfert de captures par StepsShot. Les documents et chemins choisis peuvent se trouver sur un dossier réseau ou synchronisé, qui relève du service choisi par l’utilisateur. Les documents contiennent leurs captures et dates : vérifiez leur contenu avant partage.

Code du projet sous [MIT](LICENSE), bibliothèques tierces sous leurs licences respectives. Application, installateur et désinstalleur **autosignés**, sans confiance Windows automatique. SignPath n’est pas activé ; l’acceptation éventuelle reste indépendante du choix de licence.

## Correctif installateur 1.0.1

Corrige l’erreur `TaskDialogMsgBox: Invalid ButtonLabels` lors de la détection d’une installation existante. Seuls les deux boutons d’action sont personnalisés ; Windows fournit le bouton Annuler. L’application reste StepsShot 1.0 (binaire 1.0.0), seul l’installateur passe à 1.0.1.

## Curseur visible depuis 1.0.2

Le curseur Windows visible est intégré au PNG et donc au document Word. Sa forme et sa position sont relevées juste avant la capture, avec prise en compte du point actif du curseur et de l’origine du moniteur. Il est omis si Windows le masque ou si son point actif se trouve sur un autre écran. Les curseurs flèche, texte, transparents et monochromes sont dessinés par Windows sur les pixels de l’image. La capture et le curseur reflètent le moment de traitement par le worker, pas nécessairement l’appui initial si des demandes sont en attente. Les coordonnées utilisent le contexte DPI de l’application ; les configurations physiques à DPI mixtes restent à vérifier.

## Intégrité et autosignature depuis la version 1.0.3

Le titre en en-tête est le nom du fichier sans extension lors de la génération. Le pied de page contient la date de sauvegarde à gauche et les champs natifs PAGE / NUMPAGES à droite. Word ou Writer calculent la pagination à l’ouverture et lors de la mise à jour des champs. Renommer un DOCX après la session ne réécrit pas son en-tête.

Le programme compilé vérifie au démarrage un inventaire SHA-256 signé RSA 3072 / SHA-256 avec une clé publique intégrée au programme. Un fichier absent, modifié ou ajouté dans le dossier applicatif bloque le démarrage. Les seuls fichiers exclus sont l’inventaire, sa signature et les trois fichiers de désinstallation Inno `unins000.exe`, `.dat`, `.msg`. Les documents et paramètres utilisateur sont en dehors de ce dossier. Le désinstalleur est signé Authenticode mais son hash ne fait pas partie de l’inventaire.

L’EXE, le Setup et le désinstalleur sont autosignés. Aucune autorité racine ni aucun éditeur approuvé ne sont ajoutés à Windows. Windows peut afficher un éditeur non approuvé ou SmartScreen : un certificat autosigné ne constitue pas une identité vérifiée par un tiers. Le certificat a une durée de trois ans, sans service d’horodatage. La clé privée est non exportable dans le magasin personnel Windows du compte qui compile. Le fichier `.cer` contient uniquement le certificat public ; ne distribuez jamais de PFX ou de clé privée.

Pour conserver la même identité entre versions :

```powershell
./packaging/new_signing_certificate.ps1
# Conserver le thumbprint affiché, puis :
./build_windows.ps1 -Python python -ISCC 'C:/chemin/ISCC.exe' -SigningThumbprint VOTRE_EMPREINTE
```

Sans `-SigningThumbprint`, le build crée une nouvelle identité autosignée. En CI GitHub, cette identité est éphémère et différente de celle des builds locaux : les deux ne doivent pas être considérées comme le même éditeur. Aucune clé privée locale n’est envoyée à GitHub. La clé publique intégrée est régénérée avant chaque compilation à partir du certificat choisi.

Cette vérification détecte les altérations ; une personne capable de remplacer l’exécutable peut aussi modifier ou supprimer le contrôle. Python et certaines bibliothèques sont déjà chargés avant celui-ci. Pour imposer une interdiction par Windows, il faut une politique de contrôle des applications administrée et une chaîne de confiance adaptée. Aucun contrôle local ne rend un logiciel impossible à modifier.

Pour mettre à jour, le Setup remplace le répertoire applicatif `_internal` afin d’éviter les anciennes bibliothèques résiduelles. Ne stockez pas de documents dans ce répertoire technique. Pour réparer une altération, utilisez votre installateur de confiance ; il n’existe pas de bouton de contournement du contrôle.
