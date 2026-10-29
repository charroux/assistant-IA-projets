# Projet étudiant

Ce dépôt est le dépôt du projet étudiant. L'outil `assistant-IA-projets` est un
logiciel séparé : son code source et son environnement Python ne doivent pas être
copiés ici.

Monday reste la référence pour les actions, responsables, échéances, comptes
rendus et alertes. Git conserve le besoin, les exigences, décisions, éléments de
conception, preuves autorisées et productions documentaires.

## Commencer sans IA

```text
coherence start
coherence check
```

`coherence start` explique les prochaines étapes. `coherence check` vérifie les
identifiants et relations. Ces commandes ne transmettent aucune donnée à une IA.

Ordre de travail recommandé :

1. Lire `00_guide_etudiant.md` et compléter `projet.yml`.
2. Faire valider les règles de `confidentialite.yml` avant tout usage de Git ou d'IA.
3. Décrire le besoin, le périmètre, les exigences, risques et critères.
4. Exécuter `coherence check` avant la validation du cahier des charges.
5. Relier les décisions, composants et preuves pendant la réalisation.
6. Dériver le rapport et la soutenance des artefacts du projet.

Un contrôle réussi ne vaut ni validation métier, ni validation technique.

## Utiliser une IA en lecture seule

Après autorisation explicite dans `confidentialite.yml` :

```text
coherence ask "Je suis un étudiant qui commence. Par où commencer ?"
```

Cette commande appelle une IA mais ne modifie aucun fichier. Une IA ayant déjà
accès au dépôt peut aussi recevoir le texte de `PROMPT_DEMARRAGE.md`, sans passer
par la CLI.

## Proposer puis appliquer une modification

```text
coherence propose "Structure le besoin initial"
coherence apply "ecarts/propositions/proposition-....json"
```

La première commande appelle une IA et enregistre une proposition locale. La
seconde n'appelle pas d'IA : elle applique un fichier déjà examiné, contrôle le
résultat et annule l'opération en cas d'erreur déterministe.

## Ce qui est partagé dans Git

À partager, sous réserve des autorisations : cadrage, conception, décisions,
index des preuves, écarts relus, sources Quarto et déclaration synthétique des
usages IA.

À ne pas partager : `.venv`, `.env`, clés API, caches, données personnelles,
données d'entreprise non autorisées, preuves brutes confidentielles et rapports
IA non relus. Le fichier `.gitignore` protège les éléments locaux courants, mais
ne remplace pas la vigilance de l'équipe.

