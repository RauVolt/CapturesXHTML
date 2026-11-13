# CapturesXHTML 1.3.0

Application Windows 10/11 x64 de capture d’un écran vers un XHTML autonome. Licence [MIT](LICENSE). Mainteneur : [RauVolt](https://github.com/RauVolt).

## Utilisation

1. Saisir le titre et sélectionner un écran.
2. Cliquer sur **Choisir le fichier et démarrer**. Choisir le nom et le dossier du XHTML. Si un fichier existe, la boîte Windows demande confirmation de son remplacement.
3. Un XHTML vide et valide est créé en arrière-plan avant l’activation de la session.
4. Appuyer sur **Impr. écran** ou sur **Capturer**. Chaque PNG est enregistré localement, puis le XHTML complet est réécrit en arrière-plan, vérifié et remplacé atomiquement. Le compteur indique les captures ; le statut indique leur sauvegarde effective.
5. **Terminer** attend les captures en cours et effectue une dernière sauvegarde. Fermer une session active propose de sauvegarder avant de quitter.

**Ouvrir le dossier** ouvre le répertoire du dernier document enregistré. Les cinq derniers titres et chemins absolus sont affichés et conservés localement dans `%LOCALAPPDATA%/CapturesXHTML/recent.json`. Un chemin déplacé ou supprimé reste dans l’historique et peut ne plus être accessible.

## Sauvegarde et récupération

Les captures sont écrites dans `%LOCALAPPDATA%/CapturesXHTML/Temp/session-*`. Un manifeste `session.json` associe les PNG au document. Ces fichiers sont supprimés après une finalisation réussie. En cas d’échec, le dernier XHTML valide reste disponible ; **Terminer** permet de réessayer en intégrant tous les PNG disponibles. Après une interruption brutale, les PNG et le manifeste restent disponibles pour récupération manuelle ; aucune reprise automatique n’est implémentée.

Une capture n’est intégrée au document qu’après confirmation de sauvegarde dans le statut. Un arrêt pendant une capture peut perdre la capture en cours. La mise à jour réécrit tout le XHTML : le fonctionnement vise les sessions d’environ 50 captures ou moins, sans limite dure à 50. Le temps dépend du contenu, du disque et des dossiers réseau/synchronisés.

## Installation, mise à jour, désinstallation

Un seul Setup, sans Python à installer pour l’utilisateur. Installation sans élévation dans `%LOCALAPPDATA%/Programs/CapturesXHTML`. L’identifiant d’installation est conservé depuis 1.2 pour permettre la mise à jour.

Si l’application est déjà installée pour ce compte, relancer le Setup propose **Mettre à jour ou réinstaller**, **Désinstaller CapturesXHTML** ou **Annuler**. Le choix de désinstallation lance le désinstalleur existant et arrête le Setup. En mode silencieux, le Setup met à jour sans afficher ce choix. La désinstallation reste également disponible dans les paramètres Windows. Documents, historique et données temporaires résiduelles sont conservés.

## Interface

Fond gris clair, cartes blanches, accent bleu, typographie Segoe UI, commandes principales regroupées et historique visible. Interface Tkinter/ttk personnalisée, sans dépendance graphique supplémentaire.

## Compilation

Sur Windows x64 avec Python/Tkinter et Inno Setup 6 :

```powershell
./build_windows.ps1 -Python 'C:/chemin/python.exe' -ISCC 'C:/chemin/Inno Setup 6/ISCC.exe'
```

Le script crée un environnement isolé, installe les dépendances fixées, exécute les tests et produit `installer/CapturesXHTML-1.3.0-Setup.exe`.

[GitHub Actions](https://github.com/RauVolt/CapturesXHTML/actions/workflows/windows.yml) compile sur Windows avec Python 3.13, publie des artefacts et prépare une Release **brouillon** v1.3.0 sur `main`. Le lot contient Setup, sources, rapport et SHA256. Les pull requests ne peuvent pas publier de Release. Une Release déjà publiée n’est pas remplacée.

## Confidentialité et limites

Aucune télémétrie et aucun envoi réseau par l’application. Les documents contiennent les images capturées et leurs dates ; leur partage relève de l’utilisateur. Un dossier réseau ou synchronisé choisi peut naturellement être traité par le service correspondant.

Le hook Impr. écran dépend des restrictions Windows et n’intercepte pas tous les contextes protégés. Le bouton Capturer reste disponible si le hook ne s’installe pas. Les captures en attente saisissent l’écran au moment de leur traitement. La validation confirme un XML bien formé, pas une conformité complète DTD/XSD ni un affichage universel. Voir [VERIFICATION.md](VERIFICATION.md).

Les bibliothèques tierces conservent leurs licences. L’application et le Setup restent **non signés** ; aucun service SignPath actif. Voir [SIGNPATH.md](SIGNPATH.md).
