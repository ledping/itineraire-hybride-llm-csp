"""Mesure de similarité entre l'itinéraire initial et l'itinéraire adapté (valeur dans [0, 1])."""
from .model import Itinerary, Problem


def similarity(problem: Problem, initial: Itinerary, adapted: Itinerary) -> dict[str, float]:
    acts = problem.by_id()
    init_ids, new_ids = set(initial.starts()), set(adapted.starts())
    kept = init_ids & new_ids

    # Conservation pondérée par les préférences : perdre l'activité favorite coûte plus cher.
    total_pref = sum(acts[i].preference for i in init_ids) or 1
    preference_kept = sum(acts[i].preference for i in kept) / total_pref

    init_order = [i for i in initial.order() if i in kept]
    new_order = [i for i in adapted.order() if i in kept]
    pairs = [(x, y) for k, x in enumerate(init_order) for y in init_order[k + 1:]]
    order_kept = 1.0 if not pairs else sum(new_order.index(x) < new_order.index(y) for x, y in pairs) / len(pairs)

    horizon = problem.day_end - problem.day_start
    shifts = [abs(initial.starts()[i] - adapted.starts()[i]) for i in kept]
    time_kept = 1.0 - (sum(shifts) / len(shifts) / horizon if shifts else 0.0)

    score = 0.5 * preference_kept + 0.25 * order_kept + 0.25 * time_kept
    return {"preferences": preference_kept, "ordre": order_kept, "horaires": time_kept, "score": score}
