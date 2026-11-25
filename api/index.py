import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INTERNAL_DIR = BASE_DIR / "_internal"
if str(INTERNAL_DIR) not in sys.path:
    sys.path.insert(0, str(INTERNAL_DIR))

# Su Vercel usa /tmp per dati demo scrivibili e precarica dati realistici
demo_dir = Path("/tmp/braaap_demo")
demo_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("BRAAAP_DATA_DIR", str(demo_dir))
os.environ.setdefault("BRAAAP_DEMO_MODE", "1")

data_file = demo_dir / "braaap_data.json"
if not data_file.exists():
    demo_dati = {
        "scuole": [
            {"id": 1, "nome": "I.C. Valle Camonica - Plesso Braone", "tipo": "Scuola Primaria", "referente": "Prof.ssa Bianchi", "telefono": "0364 000001"},
            {"id": 2, "nome": "Motoclub Sebino Off-Road", "tipo": "Associazione Sportiva", "referente": "Marco Rossi", "telefono": "333 000002"}
        ],
        "eventi": [
            {"id": 101, "data": "2026-04-18", "scuola_id": 1, "iniziativa": "Educazione Stradale & Mini-Cross", "numero_partecipanti": 85, "braccialetti": 85, "medaglie": 85, "adesivi": 120, "coppe": 3, "voci_ricavi": [{"descrizione": "Contributo Comune e Pro Loco", "importo": 1200}], "voci_costi": [{"descrizione": "Carburante e trasporto mezzi", "importo": 180}, {"descrizione": "Assicurazione giornaliera", "importo": 140}]},
            {"id": 102, "data": "2026-05-24", "scuola_id": 2, "iniziativa": "Trova il tuo Braaap - Open Day Pista", "numero_partecipanti": 110, "braccialetti": 110, "medaglie": 60, "adesivi": 150, "coppe": 6, "voci_ricavi": [{"descrizione": "Quote iscrizione partecipanti", "importo": 1650}, {"descrizione": "Sponsor locale", "importo": 500}], "voci_costi": [{"descrizione": "Ambulanza e presidio medico", "importo": 350}, {"descrizione": "Allestimento tracciato", "importo": 220}]}
        ],
        "stock": {"braccialetti": 305, "medaglie": 155, "adesivi": 530, "coppe": 21},
        "movimenti": {
            "braccialetti": [{"id": 1, "data": "2026-02-10", "tipo": "carico", "quantita": 500, "prezzo_unitario": 0.45, "motivo": "Fornitura stagione 2026"}, {"id": 2, "data": "2026-04-18", "tipo": "scarico", "quantita": 85, "evento_id": 101, "motivo": "Evento Scuola Braone"}, {"id": 3, "data": "2026-05-24", "tipo": "scarico", "quantita": 110, "evento_id": 102, "motivo": "Open Day Pista"}],
            "medaglie": [{"id": 4, "data": "2026-02-10", "tipo": "carico", "quantita": 300, "prezzo_unitario": 1.80, "motivo": "Medaglie personalizzate"}, {"id": 5, "data": "2026-04-18", "tipo": "scarico", "quantita": 85, "evento_id": 101, "motivo": "Evento Scuola Braone"}, {"id": 6, "data": "2026-05-24", "tipo": "scarico", "quantita": 60, "evento_id": 102, "motivo": "Open Day Pista"}],
            "adesivi": [{"id": 7, "data": "2026-02-10", "tipo": "carico", "quantita": 800, "prezzo_unitario": 0.15, "motivo": "Kit adesivi Braaap"}],
            "coppe": [{"id": 8, "data": "2026-02-10", "tipo": "carico", "quantita": 30, "prezzo_unitario": 12.0, "motivo": "Trofei premiazioni"}]
        },
        "inventario": [
            {"id": 1, "nome": "Minimoto Elettrica Training #1", "quantita": 2, "valore_unitario": 1450.0, "valore_totale": 2900.0, "data_acquisto": "2026-01-15", "stato": "Operativo"},
            {"id": 2, "nome": "Gazebo Paddock 4x4 Impermeabile", "quantita": 2, "valore_unitario": 380.0, "valore_totale": 760.0, "data_acquisto": "2026-02-05", "stato": "Operativo"}
        ],
        "entita": [
            {"id": 1, "nome": "Caschi Cross Junior omologati", "categoria": "Protezioni", "quantita": 12, "costo_unitario": 65.0, "data_carico": "2026-02-20", "condizione": "Nuovo"}
        ],
        "entrate": [
            {"id": 1, "data": "2026-04-18", "tipo": "evento", "descrizione": "Contributo Evento Scuola Braone", "importo": 1200.0},
            {"id": 2, "data": "2026-05-24", "tipo": "evento", "descrizione": "Quote e Sponsor Open Day Pista", "importo": 2150.0}
        ],
        "uscite": [],
        "altro": [
            {"id": 1, "data": "2026-03-10", "descrizione": "Manutenzione furgone trasporto mezzi", "importo": 290.0}
        ],
        "task": [
            {"id": 1, "titolo": "Preparare kit gadget per tappa estiva", "categoria": "Magazzino", "data_scadenza": "2026-06-15", "priorita": "Alta", "stato": "Da fare"}
        ],
        "rubrica": [], "postit": [], "note_calendario": [], "liste": [], "note_vocali": [], "portafoglio": []
    }
    data_file.write_text(json.dumps(demo_dati, ensure_ascii=False, indent=2), encoding="utf-8")

from app import create_app
app = create_app()

_flask_app = app
def app(environ, start_response):
    qs = environ.get("QUERY_STRING", "")
    if "__path=" in qs:
        from urllib.parse import parse_qs, urlencode
        q = parse_qs(qs, keep_blank_values=True)
        p = q.pop("__path", [""])[0]
        environ["PATH_INFO"] = "/" + p.lstrip("/")
        environ["QUERY_STRING"] = urlencode(q, doseq=True)
    return _flask_app(environ, start_response)