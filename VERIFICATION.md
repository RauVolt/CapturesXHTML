# Vérification locale — 1.3.0 — 13 novembre 2026

- 8 tests automatisés réussis : export Unicode/PNG, préservation de destination après erreur, XML mal formé, création vide puis sauvegarde après chaque capture, conservation des PNG et reprise après échec d’export, échec d’initialisation sans remplacement, historique limité à cinq chemins uniques et persistant, historique corrompu ignoré.
- Essai intégré avec interface cachée et images synthétiques : création du fichier avant capture, trois captures en attente puis Terminer, vérification des trois images intégrées, historique relu depuis disque, appel d’ouverture du bon dossier vérifié par simulation.
- Interface source ouverte sous Windows 11 et inspectée visuellement : titres, cartes, champs, commandes et zone des récents visibles.
- Lot de 50 captures : première image 1920×1080 du fichier d’exemple fourni répétée 50 fois, fichier de 15 769 436 octets, environ 0,53 s pour la dernière capture/sauvegarde et 15,92 s cumulées sur le disque local de test. Mesure indicative, sans garantie sur d’autres images ou disques. Images de test supprimées et non publiées.
- L’installateur est compilé avec Inno Setup ; le script Pascal de maintenance est vérifié par compilation. L’application est compilée avec PyInstaller. Le résultat du contrôle de démarrage packagé figure dans le rapport livré.

## À vérifier sur poste utilisateur

- Installation, mise à jour depuis 1.2, choix de désinstallation et annulation avec une installation existante. Aucune désinstallation du profil utilisateur réel n’a été exécutée pendant ces essais.
- Windows 10 et configurations multi-écrans/DPI mixtes, touche Impr. écran physique et conflit avec l’outil Windows.
- Perte d’accès à un dossier réseau, disque saturé, arrêt forcé réel pendant remplacement ; les pannes d’export sont testées par simulation.
- Affichage des cinq chemins très longs avec les réglages d’accessibilité Windows ; ouverture effective de l’Explorateur sur un dossier déplacé.

Le XML est analysé avant remplacement, sans validation DTD/XSD complète. Les fichiers temporaires permettent une récupération manuelle, pas une reprise automatique. Le binaire et le Setup sont non signés.
