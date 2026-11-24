# StepsShot 1.0.3

- En-tête DOCX : nom du fichier sans extension.
- Pied de page : date JJ/MM/AAAA à gauche, champs PAGE / NUMPAGES à droite.
- Contrôle d’intégrité SHA-256 de l’application compilée et de ses bibliothèques, avec inventaire signé RSA et clé publique intégrée.
- Blocage du lancement si les fichiers contrôlés ont été modifiés, supprimés ou ajoutés.
- Autosignature Authenticode de l’application, de l’installateur et du désinstalleur. Certificat autosigné : non approuvé automatiquement par Windows, sans suppression garantie de SmartScreen.
- Conservation des fonctions de capture avec curseur, sauvegarde progressive, raccourci personnalisable, écran modifiable et historique.

Le build CI utilise un certificat autosigné éphémère propre à chaque compilation. Les builds locaux peuvent réutiliser leur certificat via -SigningThumbprint. Aucune clé privée n’est publiée. Ces mécanismes détectent des modifications mais peuvent être contournés en remplaçant le programme lui-même.
