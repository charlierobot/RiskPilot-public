# RiskPilot

## Compliance & Risk Dashboard in Django

RiskPilot è un prototipo che simula un piccolo flusso di controllo aziendale. Parte da un file CSV contenente transazioni o controlli, verifica la qualità del dato, applica regole di rischio deterministiche e presenta i risultati in una dashboard leggibile.

Il progetto non vuole dimostrare di aver costruito un prodotto enterprise completo: vuole dimostrare di saper trasformare un problema in un flusso software comprensibile, verificabile e documentato.

----

## 1. Cosa fa l’applicazione

L’utente può scegliere tra due percorsi:

1. **Dataset demo:** apre subito una base dati anonimizzata con record a rischio basso, medio e alto.
2. **Upload CSV:** carica un file proprio, che viene validato sul server prima di entrare nel motore di analisi.

Dopo la validazione RiskPilot:

- salva l’upload e l’analisi in SQLite;
- valuta ogni riga con regole esplicite;
- assegna uno score da 0 a 100;
- assegna il livello `Basso`, `Medio` o `Alto`;
- salva una lista delle motivazioni;
- mostra KPI, distribuzione e coda di priorità;
- permette di filtrare il report per livello, ID o vendor;
- mostra il dettaglio del singolo record.

----

## 2. Utilità del progetto in Consulenza

Un’azienda di consulenza non valuta soltanto se una pagina “funziona”. 
Valuta anche se chi l’ha costruita sa:

- definire un requisito non tecnico;
- tradurlo in un flusso dati;
- separare validazione, logica di dominio e presentazione;
- motivare i trade-off;
- testare i casi normali e quelli di errore;
- comunicare limiti e rischi senza nasconderli;
- lasciare un repository che un’altra persona possa eseguire.

RiskPilot rende visibili tutti questi aspetti in un progetto 

----

## 3. Stack tecnico

| Tecnologia | Ruolo | Motivo della scelta |
|---|---|---|
| Python 3.11+ | Linguaggio | Semplice da leggere, molto usato in automazione e data analysis |
| Django 5 | Web framework | Include routing, ORM, form, CSRF, template e test |
| SQLite | Database locale | Non richiede un server database separato |
| Pandas | Parsing e controlli CSV | Rende esplicite le operazioni sulle colonne |
| Bootstrap 5 CDN | Base responsive | Riduce il CSS infrastrutturale |
| CSS custom | Identità visiva | Comunica un prodotto interno da control room |


## 4. Struttura del repository

```text
riskpilot/
├── analysis/
│   ├── migrations/                 # Schema database generato da Django
│   ├── services/
│   │   ├── analyzer.py             # Orchestrazione upload → analisi → salvataggio
│   │   ├── csv_validator.py        # Contratto e controlli del CSV
│   │   └── risk_engine.py          # Regole deterministiche di rischio
│   ├── templates/analysis/         # Pagine del dominio
│   ├── tests/
│   │   ├── test_services.py        # Validator, engine e persistenza
│   │   └── test_views.py           # Flussi HTTP principali
│   ├── forms.py                    # Form upload
│   ├── models.py                   # DatasetUpload, Analysis, RiskRecord
│   ├── urls.py                     # Route applicative
│   └── views.py                    # Controller Django
├── config/
│   ├── settings.py                 # Configurazione Django e SQLite
│   ├── urls.py                     # Root URL configuration
│   └── wsgi.py                     # Entry point WSGI
├── sample_data/
│   ├── demo_transactions.csv      # Dataset demo funzionante
│   └── invalid_missing_columns.csv # Dataset per mostrare un errore
├── static/
│   ├── manus-routes.json           # Manifest route richiesto dall’ambiente
│   ├── riskpilot-logo.svg          # Logo vettoriale
│   ├── riskpilot-logo.png          # Favicon/logo PNG
│   └── riskpilot.css               # Stile control room
├── templates/base.html              # Layout comune e navigazione
├── PROJECT_PLAN.md                  # Piano tecnico e decisioni
├── ideas.md                         # Design brief e direzione visiva
├── Dockerfile                       # Avvio opzionale in container
├── Makefile                         # Comandi abbreviati
├── requirements.txt                 # Dipendenze
└── manage.py                        # CLI Django
```

---

## 5. Contratto del file CSV

Colonne del file:

| Colonna | Tipo atteso | Significato |
|---|---|---|
| `transaction_id` | testo univoco | Identificativo del record |
| `date` | `YYYY-MM-DD` | Data dell’operazione |
| `amount` | numero non negativo | Importo della transazione |
| `vendor` | testo | Controparte o fornitore |
| `country` | due lettere | Paese, ad esempio `IT` o `DE` |
| `approved_by` | testo | Persona o stato dell’approvazione |
| `category` | testo | Categoria operativa |

Il validatore controlla anche:

- estensione `.csv`;
- dimensione massima di 5 MB;
- codifica UTF-8;
- file non vuoto;
- colonne mancanti;
- ID vuoti o duplicati;
- date non interpretabili;
- importi non numerici o negativi;
- vendor, approvatore e categoria non vuoti;
- paesi non formattati come codici di due lettere.

Le colonne aggiuntive non bloccano l’analisi, ma vengono riportate come warning e ignorate dal motore.

### Esempio minimo

```csv
transaction_id,date,amount,vendor,country,approved_by,category
TX-0001,2026-09-01,125.50,Alfa Office SRL,IT,Mario Rossi,Office
```

---

## 6. Come funziona il motore di rischio

Il motore è nel file `analysis/services/risk_engine.py`. La funzione principale riceve i campi già validati e restituisce una struttura composta da `score`, `level` e `reasons`.

| Segnale | Punti |
|---|---:|
| Importo superiore a 5.000 € | +35 |
| Importo superiore a 10.000 € | +20 aggiuntivi |
| Paese demo in watchlist (`RU`, `IR`, `KP`) | +25 |
| Approvazione vuota, `pending` o `non approvato` | +20 |
| Categoria sensibile (`consulting`, `gifts`, `cash`, `crypto`) | +15 |
| Operazione nel fine settimana | +10 |

La somma viene limitata a 100. La classificazione finale è:

| Intervallo | Livello | Interpretazione |
|---:|---|---|
| 0–29 | Basso | Nessun segnale significativo nelle regole attive |
| 30–59 | Medio | Richiede una revisione mirata |
| 60–100 | Alto | Priorità alta nella coda di controllo |

## 7. Modello dati

### `DatasetUpload`

Rappresenta il file ricevuto. Conserva nome, data di importazione, numero di righe, stato e messaggi di validazione.

### `Analysis`

Rappresenta una sessione di analisi collegata a un upload. Conserva i contatori già aggregati per alimentare velocemente la dashboard.

### `RiskRecord`

Rappresenta il record normalizzato e analizzato. Conserva i valori principali, score, livello e motivazioni in un campo JSON.

----
