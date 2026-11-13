# Préparation à SignPath — candidature non envoyée

Le choix d'une licence open source ne donne pas automatiquement droit à la signature gratuite. SignPath exige notamment un projet publié, maintenu, documenté, une compilation vérifiable depuis le dépôt public et une réputation vérifiable pour les applications exécutables. Un nouveau projet peut donc ne pas être accepté immédiatement.

## État actuel

- Sources du projet placées sous licence MIT ; les dépendances gardent leurs licences respectives.
- Dépôt public : https://github.com/RauVolt/CapturesXHTML ; mainteneur : RauVolt. Aucune candidature SignPath envoyée.
- Aucune signature SignPath active. L'installateur livré reste non signé et n'a pas été reconstruit pour cette modification documentaire.
- Aucun soutien de SignPath ne doit être annoncé avant acceptation.

## Étapes restantes

1. Sources et documentation publiées dans le dépôt public. Publier ensuite une version téléchargeable ; ne pas publier de captures personnelles ni de documents utilisateurs.
2. Identifier le mainteneur par son compte public ; activer l'authentification multifacteur et désigner auteurs, relecteurs et approbateurs.
3. Le workflow `.github/workflows/windows.yml` compile sous Windows, exécute les tests et prépare une Release brouillon avec sources, Setup, rapport et empreintes. Vérifier le run 1.3 ; l'intégration de la signature SignPath reste à configurer après acceptation.
4. Les métadonnées de nom et de version sont définies dans `packaging/version_info.txt` ; configurer leur contrôle dans SignPath après acceptation.
5. Candidater sur https://signpath.org/ et attendre l'accord. Les identifiants et jetons de signature doivent rester dans les secrets de la plateforme de compilation.
6. Après acceptation, publier une « Code signing policy » indiquant les comptes responsables et la mention d'attribution demandée par SignPath ; configurer la signature de l'application puis celle du Setup et du désinstalleur. Chaque version doit recevoir l'approbation manuelle prévue par SignPath.

## Confidentialité

CapturesXHTML n'envoie pas les captures, les documents ou des données de télémétrie à un service réseau. Les captures sont stockées localement pendant la session, puis intégrées au document choisi par l'utilisateur. Le document contient les images et leurs dates : son partage relève de l'utilisateur. Les chemins sur un dossier réseau ou synchronisé choisis par l'utilisateur peuvent naturellement être traités par les services correspondants.

Conditions officielles : https://signpath.org/terms
