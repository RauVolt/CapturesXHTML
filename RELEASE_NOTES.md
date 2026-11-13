CapturesXHTML crée un document XHTML autonome à partir de captures d'un écran Windows sélectionné.

- Installation par utilisateur dans `%LOCALAPPDATA%\Programs\CapturesXHTML`, sans élévation administrateur et sans Python à installer.
- Choix explicite du moniteur en configuration multi-écrans.
- Captures PNG enregistrées progressivement sur disque ; capture et export en arrière-plan.
- Dates et images intégrées au XHTML ; vérification XML avant remplacement de la destination.
- Sources sous licence MIT, scripts PyInstaller/Inno Setup et tests inclus.

**Version de pré-diffusion non signée.** SmartScreen peut afficher un avertissement. Aucun soutien ou service de signature SignPath actif.

Fichiers : Setup Windows x64, sources, rapport de compilation et `SHA256SUMS.txt`. Les fichiers joints sont générés ensemble depuis le commit indiqué dans le rapport de compilation.

La compilation automatique exécute les tests d'export et construit le programme et son installateur. Elle ne teste pas la capture d'un bureau interactif, l'installation/désinstallation ni l'interception physique de la touche Impr. écran. Windows 10, les configurations multi-écrans et les parcours manuels restent à vérifier ; voir `VERIFICATION.md` pour les essais locaux antérieurs.

La touche Impr. écran dépend des restrictions Windows ; les contenus protégés peuvent être noirs. La validation XML n'est pas une validation complète DTD/XSD du XHTML.
