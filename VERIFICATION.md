# Vérification StepsShot 1.0 — 16 novembre 2026

## Vérifié localement

- 17 tests automatisés réussis sous Python 3.12 : génération/relecture DOCX avec titre Unicode et PNG intégré inchangé, dimensions proportionnelles, ajout de texte et réenregistrement, rejet d’archive corrompue, maintien de l’ancien fichier en cas de panne ou verrou simulé, création vide et sauvegardes progressives, préservation des modifications externes, historique limité à cinq documents, raccourcis et scénario d’interface avec changement d’écran simulé.
- Nouvelle interface ouverte et inspectée visuellement sous Windows 11 : marque StepsShot, cinq étapes, nouvelle palette, champs et commandes de création.
- DOCX d’essai produit avec deux captures synthétiques et relu sans Office. Aucun fichier utilisateur utilisé pour ce test.
- Contrôle de démarrage du binaire packagé : Tk chargé, moniteur détecté, hook installé, création et validation d’un DOCX incluant une image ; résultat JSON et journaux livrés.
- Compilation PyInstaller et Inno Setup effectuée sous Windows. Le rapport de la CI indique séparément le commit et l’environnement du runner.

## Non vérifié

- Rendu visuel du DOCX dans Word/LibreOffice : le renderer ne dispose pas de LibreOffice et l’utilisateur a demandé de poursuivre sans étape Word. Les tests sont structurels et ne constituent pas une vérification visuelle dans ces logiciels.
- Installation réelle, migration depuis CapturesXHTML, remplacement de raccourci et désinstallation sur le profil de l’utilisateur. Le script est compilé ; aucune installation existante n’a été désinstallée pendant les vérifications.
- Windows 10, raccourcis physiques sur tous les claviers, configurations multi-écrans/DPI mixtes et contenus protégés.
- Pannes matérielles réelles et stockage réseau. Les conflits/verrous sont simulés dans les tests ; les captures temporaires permettent une récupération manuelle.

La mise en page utilise des styles Word ordinaires, des images intégrées et une taille proportionnelle plafonnée. Les titres et paragraphes sont éditables ; le contenu pixel des captures ne l’est pas. L’installateur et le programme ne sont pas signés.

## Correctif installateur 1.0.1

Le même dialogue de maintenance a été exécuté dans un Setup de test compilé avec `MaintenanceDialogTest`, qui affiche le dialogue puis s’arrête sans installer ni désinstaller. Les trois boutons Mettre à jour ou réinstaller, Désinstaller StepsShot et Annuler sont présents ; Annuler ferme le programme sans erreur. Le Setup de production est compilé séparément sans ce symbole. Le démarrage du Setup de production a aussi été vérifié puis annulé avant installation. La mise à jour et la désinstallation réelles du profil utilisateur restent non exécutées.

## Version 1.0.2

23 tests réussis, dont six nouveaux tests du curseur : géométrie des moniteurs à coordonnées négatives, omission hors écran, point actif et bord supérieur/gauche, curseur masqué, dessin natif des curseurs Windows flèche et texte sur fond clair/sombre, rognage au bord de l’image. Ces essais utilisent des pixels synthétiques sans déplacer le pointeur utilisateur. Le contrôle du binaire packagé exerce la récupération du curseur, la capture sur pixels de test et l’export DOCX. Les écrans physiques à DPI mixtes et les curseurs animés restent à vérifier ; aucune installation existante n’a été modifiée pendant les tests.
