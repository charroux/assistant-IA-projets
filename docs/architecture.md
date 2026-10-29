# Architecture

## Séparation des systèmes

```text
Monday                     Git                        IA optionnelle
actions                    besoin                     analyse transversale
responsables               exigences                  questions
échéances                  décisions                  propositions
comptes rendus             conception                 audit documentaire
alertes institutionnelles  preuves
```

L'application ne synchronise pas Monday. Elle peut produire une synthèse que les
étudiants reportent eux-mêmes dans les outils institutionnels.

## Flux d'autorité

```text
besoin → exigences → conception → réalisation → preuves → productions
```

## Flux de découverte

```text
observation → écart → examen humain → décision → mise à jour → nouveau contrôle
```

Une couche aval peut révéler un problème, mais ne modifie jamais silencieusement
le statut d'une couche amont.

## Parcours d'utilisation

```text
start (sans IA)
  ↓
ask (IA en lecture seule)
  ↓ optionnel
propose (IA, écrit une proposition locale)
  ↓ examen humain
apply (sans IA, applique et vérifie)
```

Une IA disposant déjà d'un accès autorisé au dépôt peut également utiliser
`PROMPT_DEMARRAGE.md`. La CLI ajoute une liste blanche de fichiers, la détection
de secrets et des sorties structurées ; elle n'est pas l'unique interface possible.

## Modules

- `repository.py` lit les artefacts Markdown et YAML.
- `checks.py` exécute les règles déterministes.
- `graph.py` calcule les impacts amont et aval.
- `guidance.py` oriente l'étudiant sans appel IA.
- `security.py` applique les autorisations et filtre le contexte IA.
- `ai.py` appelle l'API Responses avec une sortie JSON structurée.
- `reports.py` produit les rapports lisibles.
- `gitops.py` limite les commits aux fichiers effectivement modifiés.

## Frontière de confiance

Le contenu d'un dépôt étudiant est une donnée non fiable. Les instructions
trouvées dans les documents sont traitées comme du contenu du projet, jamais
comme des instructions système. Les chemins proposés par un modèle sont résolus
et contrôlés avant écriture. Les suppressions ne sont pas prises en charge.

L'audit utilise un prompt distinct et ne reçoit ni la conversation d'assistance,
ni ses conclusions antérieures.

