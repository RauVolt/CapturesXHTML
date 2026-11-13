# Vérification locale — CapturesXHTML 1.4.0 — 13 novembre 2026

- 15 tests automatisés réussis : les 8 tests de sauvegarde/export/historique existants, 6 tests du raccourci et 1 scénario d’interface.
- Raccourci : Impr. écran, relâchement seul, maintien de touche sans répétition, touche non configurée, désactivation hors session, modificateur incorrect, relâchement du modificateur avant la touche, changement de configuration pendant un appui et normalisation Ctrl gauche/droite. Les événements sont simulés au niveau de la logique de correspondance, sans injection clavier.
- Interface : deux barres verticales, absence du bouton Capturer, changement et restauration de raccourci, chaque bouton Ouvrir associé au bon dossier par simulation de l’appel Windows, deux captures avec écrans simulés aux coordonnées distinctes (dont négatives), changement ultérieur de sélection sans modification des captures déjà demandées et finalisation du XHTML.
- Contrôle visuel local de la fenêtre 1.4 : nouvelle icône, rappel et configuration du raccourci, bouton de réinitialisation, défilement global effectif.
- Le contrôle de démarrage packagé et les journaux PyInstaller/Inno Setup sont fournis dans le lot de vérification local. Le lot GitHub contient les journaux du runner et son environnement.

## Limites des vérifications

Les tests d’interface simulent les écrans et les captures. Ils ne prouvent pas le bon fonctionnement de tous les claviers, des raccourcis réservés, du multi-écran physique, des DPI mixtes ou des contenus protégés. À vérifier manuellement : Windows 10, raccourcis physiques, défilement sur pavé tactile, cinq chemins très longs, modification d’écran réel et installation/mise à jour/désinstallation. Aucune désinstallation de l’application utilisateur existante n’a été effectuée.

La validation XHTML confirme un XML bien formé, pas une conformité DTD/XSD complète. Les sauvegardes progressives et fichiers temporaires de récupération sont conservés depuis 1.3. L’application ne transmet aucune capture au réseau. Les tests ne sont pas une garantie contre une panne matérielle ou une politique de sécurité d’entreprise.
