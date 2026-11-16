StepsShot 1.0.1 — correctif de l’installateur

Corrige l’erreur « TaskDialogMsgBox: Invalid ButtonLabels » qui empêchait le lancement du Setup lorsqu’une installation existante était détectée.

Le dialogue conserve Mettre à jour ou réinstaller, Désinstaller StepsShot et Annuler. Les deux boutons d’action sont personnalisés ; Windows fournit Annuler. L’application reste StepsShot 1.0 (binaire 1.0.0) ; ce correctif concerne uniquement le Setup.

Le dialogue a été exécuté dans un Setup de test sans installation/désinstallation, puis annulé avec succès. Le Setup de production est compilé séparément sans le mode de test. Voir VERIFICATION.md pour les limites. Aucune désinstallation de l’application utilisateur n’a été effectuée.

Installeur Windows x64 par utilisateur, sans élévation. Non signé. Sources MIT et journaux joints. Ce correctif remplace le Setup 1.0.0.
