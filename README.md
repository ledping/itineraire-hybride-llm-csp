# Itinéraire hybride : LLM et programmation par contraintes

Prototype d'adaptation d'un itinéraire touristique quand un événement extérieur le perturbe (pluie, fermeture d'un site, grève des transports).

Le modèle de langage ne planifie rien. Il transforme la demande du touriste et le texte de l'alerte en données structurées (activités, fenêtres d'ouverture, préférences, événements). Un solveur de contraintes (OR-Tools CP-SAT) calcule ensuite l'itinéraire. Un vérificateur indépendant contrôle le résultat, puis une mesure de similarité indique à quel point l'itinéraire adapté reste proche de l'itinéraire initial.

## Modèle

- **Activité** : lieu, durée, horaires d'ouverture, intérieur ou extérieur, poids de préférence, caractère obligatoire.
- **Contraintes** : horaires d'ouverture, temps de trajet entre deux activités consécutives, pas d'activité extérieure pendant la pluie, site fermé exclu, temps de trajet multipliés en cas de grève.
- **Planification initiale** : maximiser la somme des préférences des activités retenues.
- **Adaptation minimale** : objectif lexicographique. On garde d'abord le plus d'activités possible (pondérées par la préférence), puis on limite les inversions d'ordre, puis les décalages horaires.
- **Similarité** : 0,5 × préférences conservées + 0,25 × ordre conservé (paires concordantes) + 0,25 × horaires conservés.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```bash
python demo.py
```

Sans clé d'API, la démo relit les extractions enregistrées dans `exemples/`. Avec `ANTHROPIC_API_KEY` définie (et `pip install anthropic`), l'extraction est faite par le modèle de langage à partir des textes `exemples/demande.txt` et `exemples/alerte.txt`.

## Résultat de la démo

```

Itinéraire initial
  09h00 à 10h30  Château de Caen  (extérieur)
  10h30 à 12h00  Musée des Beaux-Arts
  12h03 à 13h03  Déjeuner au marché
  13h06 à 14h21  Abbaye aux Hommes
  14h39 à 17h09  Mémorial de Caen
  17h36 à 18h36  Balade au bord de l'Orne  (extérieur)
  Vérification : toutes les contraintes sont respectées

Alerte : Fortes pluies de 9 h 30 à 12 h 30. Fermeture exceptionnelle de l'Abbaye aux Hommes.

Itinéraire adapté
  10h15 à 11h45  Musée des Beaux-Arts
  11h48 à 12h48  Déjeuner au marché
  12h51 à 14h21  Château de Caen  (extérieur)
  14h39 à 17h09  Mémorial de Caen
  17h36 à 18h36  Balade au bord de l'Orne  (extérieur)
  Vérification : toutes les contraintes sont respectées

Similarité avec l'itinéraire initial : preferences 0.80, ordre 0.80, horaires 0.91, score 0.83
```

## Limites et suite

L'ordre est modélisé par des variables de précédence deux à deux, ce qui suffit pour une journée de quelques activités mais pas pour plusieurs jours. Les étapes suivantes sont un graphe de connaissances touristiques pour alimenter le catalogue, un raisonnement temporel qualitatif (relations d'Allen) pour les contraintes exprimées en langage naturel (« après le déjeuner », « pendant la matinée »), et une évaluation sur un jeu de scénarios de perturbation.

Auteur : Steve MBOSOP TETSING, Master recherche en informatique, LGIA, ENSET de Douala.
