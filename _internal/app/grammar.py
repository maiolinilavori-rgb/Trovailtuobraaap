from __future__ import annotations
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODELLO_LLM

SYSTEM_PROMPT = (
    "Sei un correttore ortografico per l'italiano. "
    "Correggi SOLO errori di ortografia e refusi di battitura. "
    "NON rispondere alla domanda dell'utente, NON spiegare, NON aggiungere nulla. "
    "Restituisci ESCLUSIVAMENTE il testo corretto, identico nella forma ma senza errori. "
    "Se il testo e gia corretto, restituiscilo invariato."
)


def correggi_testo(testo: str) -> str:
    if not testo or not testo.strip():
        return testo

    client = Groq(api_key=GROQ_API_KEY)

    risposta = client.chat.completions.create(
        model=GROQ_MODELLO_LLM,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": testo},
        ],
        temperature=0.1,
        max_tokens=min(2048, len(testo) * 2 + 50),
    )

    return risposta.choices[0].message.content.strip()