"""Interprete AI basato su Groq per il parsing intelligente del testo."""
from __future__ import annotations
import json
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODELLO_LLM


SYSTEM_PROMPT = """Sei un assistente intelligente per un'app di gestione eventi e magazzino chiamata Braaap.
Il tuo compito e' analizzare il testo dell'utente e restituire un JSON strutturato con le azioni da intraprendere.

Le azioni possibili sono:
- "movimento_magazzino": per carichi/scarichi di materiale (braccialetti, medaglie, adesivi, coppe)
  Specifica: categoria, tipo_movimento ('carico' o 'scarico'), quantita
- "evento": per la creazione di un nuovo evento
  Specifica: iniziativa, data (YYYY-MM-DD), scuola, numero_partecipanti
- "task": per un promemoria o un'azione da fare
  Specifica: titolo, scadenza (YYYY-MM-DD)
- "proposta": se l'utente fa un'affermazione che implica un'azione automatica
  Esempio: "consegno gadget a tutti" -> proponi scarico di braccialetti e medaglie per il numero di partecipanti
  Specifica: descrizione, movimenti (array)

Restituisci SEMPRE un JSON valido con questa struttura:
{
  "success": true,
  "azioni": [
    { "tipo": "evento", "iniziativa": "...", "data": "2026-11-15", "scuola": "...", "numero_partecipanti": 50 },
    { "tipo": "movimento_magazzino", "categoria": "braccialetti", "tipo_movimento": "scarico", "quantita": 50, "motivo": "..." },
    { "tipo": "task", "titolo": "...", "scadenza": "2026-11-14" }
  ],
  "chiarimenti": [ "Domanda di chiarimento se il testo e' ambiguo" ]
}

Se il testo e' chiaro, "chiarimenti" e' un array vuoto.
Se il testo e' ambiguo, usa "chiarimenti" per fare domande.
Sii conciso e restituisci solo JSON.
"""


def interpreta_con_groq(testo: str, contesto: dict = None) -> dict:
    """Invia il testo a Groq per un'interpretazione strutturata."""
    if not GROQ_API_KEY:
        return {
            'success': False,
            'azioni': [],
            'chiarimenti': ['GROQ_API_KEY non configurata nel .env'],
        }

    client = Groq(api_key=GROQ_API_KEY)

    messaggio_utente = testo
    if contesto:
        messaggio_utente = f"Contesto: {json.dumps(contesto, ensure_ascii=False)}\n\nTesto: {testo}"

    try:
        risposta = client.chat.completions.create(
            model=GROQ_MODELLO_LLM,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": messaggio_utente},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1024,
        )

        risultato = json.loads(risposta.choices[0].message.content)
        return risultato

    except json.JSONDecodeError as e:
        return {
            'success': False,
            'azioni': [],
            'chiarimenti': [f'Errore nel parsing della risposta Groq: {e}'],
        }
    except Exception as e:
        return {
            'success': False,
            'azioni': [],
            'chiarimenti': [f'Errore Groq: {e}'],
        }