# Assistant IA aux projets

MVP d'un assistant facultatif de cohérence documentaire pour les Engineering
Projects. Il aide une équipe à relier le besoin, le cadrage, les décisions, la
conception, les preuves et les productions sans se substituer au mentor, à
l'expert, au déposant ni au jury.

## Principes

- Le cadre documentaire et les contrôles déterministes fonctionnent sans IA.
- Monday reste la référence du suivi opérationnel, des actions et des échéances.
- Git porte les artefacts du projet, leur histoire et leurs relations.
- L'IA ne certifie ni la vérité métier, ni la validité scientifique ou technique.
- Toute modification proposée par l'IA doit être explicitement appliquée par un
  étudiant ; aucun changement de statut vers `valide` n'est autorisé.
- L'audit IA final est consultatif, indépendant et strictement en lecture seule.
- Aucun contenu n'est envoyé à un service d'IA sans autorisation déclarée dans
  `confidentialite.yml`.

## Installation

Python 3.11 ou plus récent est requis.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

L'assistant OpenAI est optionnel. Pour l'utiliser, définir la clé dans
l'environnement, jamais dans le dépôt :

```powershell
$env:OPENAI_API_KEY = "..."
```

Le modèle est configurable par `OPENAI_MODEL`, `--model` ou
`confidentialite.yml`. Le réglage du projet est utilisé en dernier recours.

## Démarrage rapide

Créer un projet étudiant :

```powershell
coherence init mon-projet --campus paris --title "Mon Engineering Project"
cd mon-projet
coherence check
```

Analyser l'impact d'un artefact :

```powershell
coherence impact EXG-001
```

Produire un rapport déterministe :

```powershell
coherence report --output evaluation/rapport-coherence.md
```

Après autorisation explicite de l'IA dans `confidentialite.yml` :

```powershell
coherence assist "Vérifie la cohérence du périmètre et des exigences"
coherence assist "Propose la mise à jour des critères" --apply
coherence assist "Consigne cette décision" --apply --commit
```

`--apply` est obligatoire pour écrire. `--commit` ajoute uniquement les fichiers
modifiés par la proposition et refuse de fonctionner si le dépôt était déjà sale.

Lancer l'audit documentaire indépendant :

```powershell
coherence audit --save
```

L'autorisation d'évaluation est distincte de l'autorisation d'assistance.

## Commandes

| Commande | Fonction |
| --- | --- |
| `coherence init` | Copie le modèle de projet et configure le campus |
| `coherence check` | Vérifie schémas, identifiants, références et couverture |
| `coherence impact` | Parcourt les dépendances amont et aval d'un identifiant |
| `coherence report` | Génère un rapport de cohérence sans IA |
| `coherence assist` | Analyse ou propose des modifications avec l'IA facultative |
| `coherence audit` | Produit un audit IA indépendant, en lecture seule |

## Répartition des responsabilités

| Couche | Référence |
| --- | --- |
| Actions, responsables, échéances, comptes rendus | Monday |
| Besoin, exigences, décisions, conception, preuves | Git |
| Validité métier | Déposant et experts |
| Validité technique ou scientifique | Experts |
| Contrôle continu | Mentor |
| Évaluation finale | Expert et jury humains |
| Cohérence documentaire et analyse d'impact | Outil et assistant facultatif |

Le dépôt ne doit pas servir à mesurer une contribution individuelle par le nombre
de commits. L'usage de l'IA est déclaré, mais sa fréquence n'est pas un critère de
qualité.

## Développement

```powershell
python -m compileall src
pytest
```

Le test de l'API OpenAI est volontairement simulé : les tests n'envoient aucune
donnée et ne consomment aucun crédit.

Voir [l'architecture](docs/architecture.md) et la
[politique de contribution](CONTRIBUTING.md).

