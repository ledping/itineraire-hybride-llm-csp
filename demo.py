"""Démonstration : demande en langage naturel, itinéraire initial, alerte, itinéraire adapté."""
from pathlib import Path

from itineraire_hybride.extraction import extract, to_events, to_problem
from itineraire_hybride.similarity import similarity
from itineraire_hybride.solver import check, solve

EXAMPLES = Path(__file__).parent / "exemples"


def hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}h{minutes % 60:02d}"


def show(title, problem, itinerary):
    acts = problem.by_id()
    print(f"\n{title}")
    for v in sorted(itinerary.visits, key=lambda v: v.start):
        a = acts[v.activity_id]
        print(f"  {hhmm(v.start)} à {hhmm(v.end(acts))}  {a.name}{'  (extérieur)' if a.outdoor else ''}")
    violations = check(problem, itinerary)
    print("  Vérification : " + ("toutes les contraintes sont respectées" if not violations else "; ".join(violations)))


def main():
    request = (EXAMPLES / "demande.txt").read_text(encoding="utf-8")
    problem = to_problem(extract(request, [], EXAMPLES / "demande.extraction.json"))
    initial = solve(problem)
    show("Itinéraire initial", problem, initial)

    alert = (EXAMPLES / "alerte.txt").read_text(encoding="utf-8")
    problem.events = to_events(extract(alert, [], EXAMPLES / "alerte.extraction.json"))
    print("\nAlerte : " + " ".join(e.description for e in problem.events))
    adapted = solve(problem, initial=initial)
    if adapted is None:
        print("Aucune adaptation ne respecte les contraintes obligatoires.")
        return
    show("Itinéraire adapté", problem, adapted)

    scores = similarity(problem, initial, adapted)
    print("\nSimilarité avec l'itinéraire initial : " + ", ".join(f"{k} {v:.2f}" for k, v in scores.items()))


if __name__ == "__main__":
    main()
