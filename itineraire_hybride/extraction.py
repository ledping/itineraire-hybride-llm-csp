"""Partie générative : le LLM transforme une demande ou une alerte en langage naturel
en données structurées. Il ne décide jamais du planning, c'est le rôle du solveur."""
import json
import os
from pathlib import Path

from .model import Activity, Event, Problem

EXTRACTION_PROMPT = """Tu extrais des informations pour un planificateur d'itinéraires touristiques.
Réponds uniquement en JSON valide, sans texte autour.
Pour une demande de touriste, renvoie :
{{"day_start": minutes, "day_end": minutes,
  "activities": [{{"id", "name", "place": [x, y], "duration", "opens", "closes",
                   "outdoor": bool, "preference": 1-10, "mandatory": bool}}]}}
Pour une alerte, renvoie : {{"events": [{{"kind": "rain"|"closure"|"strike", "start", "end",
  "activity_id", "travel_factor", "description"}}]}}
Les heures sont en minutes depuis minuit. N'invente aucune activité absente du catalogue.
Catalogue : {catalogue}
Texte : {text}"""


def _ask_llm(prompt: str) -> dict:
    import anthropic  # dépendance facultative, utile seulement hors mode démo

    client = anthropic.Anthropic()
    reply = client.messages.create(
        model=os.environ.get("LLM_MODEL", "claude-haiku-4-5"),
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(reply.content[0].text)


def extract(text: str, catalogue: list[dict], cached_answer: Path | None = None) -> dict:
    """Sans clé d'API, on relit une extraction enregistrée pour que la démo tourne hors ligne."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _ask_llm(EXTRACTION_PROMPT.format(catalogue=json.dumps(catalogue, ensure_ascii=False), text=text))
    if cached_answer is None:
        raise RuntimeError("Aucune clé ANTHROPIC_API_KEY et aucune extraction enregistrée.")
    return json.loads(cached_answer.read_text(encoding="utf-8"))


def to_problem(structured: dict) -> Problem:
    return Problem(
        activities=[Activity(**{**a, "place": tuple(a["place"])}) for a in structured["activities"]],
        day_start=structured["day_start"],
        day_end=structured["day_end"],
    )


def to_events(structured: dict) -> list[Event]:
    return [Event(**e) for e in structured["events"]]
