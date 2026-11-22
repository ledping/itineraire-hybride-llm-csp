"""Planification et adaptation d'itinéraires par programmation par contraintes (CP-SAT)."""
from ortools.sat.python import cp_model

from .model import Itinerary, Problem, Visit

# Poids lexicographiques : garder une activité compte plus que tout décalage horaire,
# et un décalage reste préférable à une inversion d'ordre que le touriste remarquerait.
KEEP_WEIGHT = 10_000
ORDER_CHANGE_WEIGHT = 120
SHIFT_WEIGHT = 1


def solve(problem: Problem, initial: Itinerary | None = None, time_limit: float = 10.0) -> Itinerary | None:
    """Sans itinéraire initial : maximise les préférences.
    Avec itinéraire initial : cherche l'adaptation minimale qui respecte les nouvelles contraintes."""
    activities = problem.activities
    model = cp_model.CpModel()
    chosen, start, interval = {}, {}, {}

    for a in activities:
        chosen[a.id] = model.NewBoolVar(f"chosen_{a.id}")
        lo = max(a.opens, problem.day_start)
        hi = min(a.closes, problem.day_end) - a.duration
        if hi < lo:
            model.Add(chosen[a.id] == 0)
            hi = lo
        start[a.id] = model.NewIntVar(lo, hi, f"start_{a.id}")
        interval[a.id] = model.NewOptionalFixedSizeIntervalVar(start[a.id], a.duration, chosen[a.id], f"iv_{a.id}")
        if a.mandatory:
            model.Add(chosen[a.id] == 1)

    for e in problem.events:
        if e.kind == "closure" and e.activity_id in chosen:
            model.Add(chosen[e.activity_id] == 0)
        if e.kind == "rain":
            rain = model.NewFixedSizeIntervalVar(e.start, e.end - e.start, "rain")
            for a in activities:
                if a.outdoor:
                    model.AddNoOverlap([interval[a.id], rain])

    # Ordre deux à deux avec temps de trajet : suffisant pour une journée de quelques activités.
    before = {}
    for i, a in enumerate(activities):
        for b in activities[i + 1:]:
            ab = model.NewBoolVar(f"{a.id}_before_{b.id}")
            before[(a.id, b.id)] = ab
            both = [chosen[a.id], chosen[b.id]]
            model.Add(start[b.id] >= start[a.id] + a.duration + problem.travel_minutes(a, b)).OnlyEnforceIf(both + [ab])
            model.Add(start[a.id] >= start[b.id] + b.duration + problem.travel_minutes(b, a)).OnlyEnforceIf(both + [ab.Not()])

    if initial is None:
        model.Maximize(sum(a.preference * chosen[a.id] for a in activities))
    else:
        init_start = initial.starts()
        objective = []
        for a in activities:
            if a.id not in init_start:
                model.Add(chosen[a.id] == 0)  # l'adaptation n'ajoute que si on le demande explicitement
                continue
            objective.append(KEEP_WEIGHT * a.preference * chosen[a.id])
            shift = model.NewIntVar(0, 24 * 60, f"shift_{a.id}")
            model.AddAbsEquality(shift, start[a.id] - init_start[a.id])
            objective.append(-SHIFT_WEIGHT * shift)
        for (x, y), lit in before.items():
            if x in init_start and y in init_start:
                was_before = init_start[x] < init_start[y]
                changed = model.NewBoolVar(f"changed_{x}_{y}")
                model.Add(lit != was_before).OnlyEnforceIf(changed)
                model.Add(lit == was_before).OnlyEnforceIf(changed.Not())
                kept_pair = model.NewBoolVar(f"pair_{x}_{y}")
                model.AddBoolAnd([chosen[x], chosen[y]]).OnlyEnforceIf(kept_pair)
                model.AddBoolOr([chosen[x].Not(), chosen[y].Not()]).OnlyEnforceIf(kept_pair.Not())
                penalized = model.NewBoolVar(f"pen_{x}_{y}")
                model.AddBoolAnd([changed, kept_pair]).OnlyEnforceIf(penalized)
                model.AddBoolOr([changed.Not(), kept_pair.Not()]).OnlyEnforceIf(penalized.Not())
                objective.append(-ORDER_CHANGE_WEIGHT * penalized)
        model.Maximize(sum(objective))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return Itinerary([Visit(a.id, solver.Value(start[a.id])) for a in activities if solver.Value(chosen[a.id])])


def check(problem: Problem, itinerary: Itinerary) -> list[str]:
    """Vérification indépendante du solveur : la garantie ne repose pas sur le seul modèle."""
    acts = problem.by_id()
    violations = []
    visits = sorted(itinerary.visits, key=lambda v: v.start)
    for v in visits:
        a = acts[v.activity_id]
        if v.start < max(a.opens, problem.day_start) or v.end(acts) > min(a.closes, problem.day_end):
            violations.append(f"{a.name} hors horaires d'ouverture")
        for e in problem.events:
            if e.kind == "closure" and e.activity_id == a.id:
                violations.append(f"{a.name} est fermé")
            if e.kind == "rain" and a.outdoor and v.start < e.end and v.end(acts) > e.start:
                violations.append(f"{a.name} en extérieur pendant la pluie")
    for v, w in zip(visits, visits[1:]):
        if v.end(acts) + problem.travel_minutes(acts[v.activity_id], acts[w.activity_id]) > w.start:
            violations.append(f"trajet impossible entre {acts[v.activity_id].name} et {acts[w.activity_id].name}")
    return violations
