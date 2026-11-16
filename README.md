# StepsShot 1.0

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

Un seul `StepsShot-1.0.0-Setup.exe`, pour Windows 10/11 x64, sans droits administrateur. Nouvelle installation dans `%LOCALAPPDATA%/Programs/StepsShot`. L’identité d’installation de CapturesXHTML est conservée pour qu’une mise à jour existante utilise son répertoire précédent et sa même entrée de désinstallation, sous le nouveau nom. L’ancien raccourci est remplacé par StepsShot. Documents, historique ancien et captures résiduelles ne sont pas supprimés.

Lorsqu’une installation existe, le Setup propose mise à jour/réinstallation, désinstallation ou annulation. Aucune désinstallation du poste utilisateur n’est effectuée automatiquement pendant les tests.

## Sources et compilation

Le dépôt historique reste [RauVolt/CapturesXHTML](https://github.com/RauVolt/CapturesXHTML). Le produit et les fichiers distribués s’appellent désormais StepsShot 1.0. Les versions de paquet et de fichier sont 1.0.0.

Sur Windows avec Python 3.12 ou 3.13 x64 (incluant Tkinter) et Inno Setup 6 :

```powershell
./build_windows.ps1 -Python 'C:/chemin/python.exe' -ISCC 'C:/chemin/Inno Setup 6/ISCC.exe'
```

Le script crée `.venv`, installe les dépendances, exécute les tests, génère l’icône, inclut le modèle DOCX et construit `installer/StepsShot-1.0.0-Setup.exe`. Internet est nécessaire pour les dépendances. Office n’est pas requis pour la compilation.

GitHub Actions compile sous Windows avec Python 3.13 et prépare une Release **brouillon** `v1.0.0`, incluant Setup, sources, rapport et empreintes SHA256. Aucune publication automatique d’une Release déjà publiée. Le lancement manuel est disponible dans Actions. Voir [VERIFICATION.md](VERIFICATION.md).

## Confidentialité et licence

Aucune télémétrie ni transfert de captures par StepsShot. Les documents et chemins choisis peuvent se trouver sur un dossier réseau ou synchronisé, qui relève du service choisi par l’utilisateur. Les documents contiennent leurs captures et dates : vérifiez leur contenu avant partage.

Code du projet sous [MIT](LICENSE), bibliothèques tierces sous leurs licences respectives. Application et installateur **non signés**. SignPath n’est pas activé ; l’acceptation éventuelle reste indépendante du choix de licence.
