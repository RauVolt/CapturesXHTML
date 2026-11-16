StepsShot 1.0.2 — curseur visible dans les captures

- Le pointeur Windows est intégré aux captures PNG et aux images du document Word.
- Position corrigée selon l’origine de l’écran et le point actif du curseur ; formes et transparence dessinées par Windows.
- Le curseur est omis lorsqu’il est masqué ou placé sur un autre écran. Au bord du moniteur, le dessin est rogné aux limites de la capture.
- Correctif du dialogue de maintenance 1.0.1 conservé.

23 tests automatisés réussis localement : export Word, sauvegarde progressive, raccourcis, historique, changement d’écran simulé et six tests du curseur, dont le dessin natif flèche/texte sur fonds clair et sombre. Les configurations physiques à DPI mixtes et les curseurs animés ne sont pas entièrement vérifiés. La position correspond au moment de capture dans le worker.

Installateur Windows x64 par utilisateur, non signé. Sources MIT, rapport et SHA256SUMS.txt joints. La Release reste en brouillon.
