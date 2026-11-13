# CapturesXHTML 1.2.0 — Windows, installation par utilisateur

## Licence open source

Le code propre à CapturesXHTML est distribué sous [licence MIT](LICENSE). Elle autorise l'utilisation, la modification et la redistribution, y compris commerciale, en conservant la notice de licence. Les bibliothèques tierces restent régies par leurs licences propres ; la licence MIT du projet ne les remplace pas.

La préparation à une signature gratuite est décrite dans [SIGNPATH.md](SIGNPATH.md). Le projet est publié sur https://github.com/RauVolt/CapturesXHTML et maintenu par RauVolt. Aucune candidature SignPath n'a encore été envoyée ; l'installateur existant reste non signé.

Cette version reprend le code Python/Tkinter de CapturesXHTML v1.1. Elle ajoute le packaging Windows par utilisateur et conserve la capture de moniteur et l'export XHTML autonome.

## Disponibilité

Ce dépôt contient les sources, les scripts de build et les tests. Aucun installateur n'est encore publié dans les Releases GitHub. Pour obtenir le Setup, suivre la section Recompiler.

## Installer et utiliser

Lancer `CapturesXHTML-1.2.0-Setup.exe` avec le compte utilisateur habituel. Python n'est pas nécessaire sur le poste destinataire. Le programme est installé dans `%LOCALAPPDATA%\Programs\CapturesXHTML`, avec un raccourci dans le menu Démarrer et une entrée de désinstallation Windows. Aucun service, pilote, démarrage automatique ni changement des réglages Windows de la touche Impr. écran n'est ajouté.

Saisir le nom du document, sélectionner un écran, puis cliquer sur Démarrer. À chaque pression sur Impr. écran, l'écran choisi est capturé. Cliquer sur Terminer et choisir la destination XHTML. Les captures et l'export s'exécutent dans un worker ; la finalisation attend les captures en cours.

Chaque PNG est écrit dans `%LOCALAPPDATA%\CapturesXHTML\Temp\session-*` avant son intégration au document. Les PNG sont supprimés après un export réussi ou une fermeture confirmée. En cas d'échec d'export, on peut réessayer pendant la session. Il n'y a pas de reprise automatique après fermeture forcée ; des dossiers temporaires résiduels peuvent rester. La désinstallation ne supprime pas les documents exportés ni ces résidus.

## Changements depuis 1.1

- Installation Inno Setup en mode non administratif (`PrivilegesRequired=lowest`), sans option d'élévation ; application sans manifeste exigeant les droits administrateur.
- Distribution sous forme d'un seul installateur. PyInstaller utilise `onedir` à l'intérieur : Inno Setup regroupe tous les fichiers dans le fichier Setup unique.
- Stockage temporaire déplacé dans le profil local, sous CapturesXHTML.
- Choix explicite requis quand plusieurs écrans sont détectés.
- Numérotation des PNG indépendante des réussites/échecs, pour éviter la réutilisation d'un nom après une capture échouée.
- Contrôle de démarrage `CapturesXHTML.exe --self-test CHEMIN_ABSOLU_JSON`, qui vérifie Tk, détection d'écran et installation du hook sans activer l'interception.

Le XHTML autonome, les dates, les images PNG Base64, la validation XML en flux et le remplacement atomique de la destination sont conservés. La validation XML ne constitue pas une validation DTD/XSD complète du XHTML.

## Recompiler

Sur Windows x64, installer Python avec Tkinter et Inno Setup 6 depuis leurs sites officiels. Compilation réalisée ici avec Python 3.15.0 x64, Pillow 12.3.0, screeninfo 0.8.1, PyInstaller 6.22.3 et hooks 2026.8. Les trois dépendances principales sont fixées dans `requirements.txt` ; l'environnement complet utilisé figure dans le dossier de vérification.

Depuis le dossier des sources, dans PowerShell :

```powershell
.\build_windows.ps1 -Python 'C:\chemin\python.exe' -ISCC 'C:\chemin\Inno Setup 6\ISCC.exe'
```

Ou lancer `build_windows.bat` si Python et Inno Setup sont aux emplacements attendus. Le script crée `.venv`, installe les dépendances, lance les tests, construit l'application puis l'installateur. Il s'arrête si une étape échoue. Internet est nécessaire pour installer les dépendances. Résultat : `installer\CapturesXHTML-1.2.0-Setup.exe`. Les outils de développement ne sont pas inclus dans les sources.

## Vérifications et limites

Consulter `VERIFICATION.md` pour distinguer les tests réellement passés des essais restant à faire. L'installateur n'est pas signé : Windows peut afficher un avertissement SmartScreen. Une politique d'entreprise peut interdire l'exécution même sans demande d'administration.

Impr. écran est intercepté uniquement pendant une session et seulement lorsque Windows transmet l'événement au hook. Les écrans UAC, contenus protégés, applications élevées ou d'autres hooks peuvent empêcher cette interception. Aucun contournement de ces protections n'est réalisé. Les captures en attente saisissent l'écran au moment où le worker les traite, pas nécessairement à l'instant exact de l'appui.

Sources techniques : [Inno Setup — droits requis](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm), [PyInstaller — utilisation](https://pyinstaller.org/en/stable/usage.html), [Python Windows](https://www.python.org/downloads/windows/), [Inno Setup](https://jrsoftware.org/isdl.php).
