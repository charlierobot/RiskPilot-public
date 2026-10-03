#RiskPilot


RiskPilot è un prototipo Django locale per dimostrare un caso d’uso tipico della consulenza: ricevere un dataset, verificarne la qualità, applicare controlli ripetibili e comunicare i risultati in modo leggibile a un decisore.

Il progetto non pretende di sostituire un sistema GRC o un modello antifrode in produzione. Il suo obiettivo è rendere visibile il percorso completo **input → qualità → regole → rischio → reporting**.

## 2. Utente e flusso

1. L’utente apre la dashboard.
2. Carica un CSV oppure usa il dataset demo.
3. RiskPilot verifica intestazioni, tipi, campi obbligatori e valori.
4. Se il dataset è valido, salva l’upload e crea un’analisi
5. Il motore applica regole esplicite a ogni record.
6. Ogni record riceve score, livello e motivazioni
7. La dashboard mostra KPI e distribuzione del rischio.
8. Il report permette di filtrare i risultati e capire il “perché” di ogni segnalazione.

## 3. Stack e motivazioni

- **Python 3.11+**: linguaggio accessibile e diffuso nella data analysis
- **Django 5.x**: framework full-stack con form, template e test integrati
- **SQLite**: database locale senza configurazione esterna, adeguato al prototipo
- **HTML/CSS + Bootstrap via CDN**: interfaccia leggibile con JavaScript
- **Pandas**: parsing CSV e controlli tabellari: è una dipendenza intenzionale perché rende i controlli comprensibili e testabili.


## 4. Moduli

```text
riskpilot/
├── manage.py
├── config/                 # settings, root URLs, WSGI
├── analysis/               # modello dati, form, viste e URL del dominio
│   ├── services/           # validazione CSV e risk engine
│   ├── templates/          # dashboard, upload, report, dettaglio
│   └── tests/              # test di dominio e view
├── templates/              # layout comune
├── static/                 # CSS, logo, manifest route
├── sample_data/            # CSV demo validi e non validi
├── requirements.txt
├── README.md
└── .env.example
```

## 5. Modello dati

- `DatasetUpload`: nome file, timestamp, righe, stato, errori di validazione.
- `Analysis`: relazione 1-a-1 con upload, timestamp e contatori KPI
- `RiskRecord`: valori normalizzati del record, score, livello e motivazioni JSON

La persistenza dei risultati rende il report riproducibile senza ricaricare il CSV a ogni pagina.

## 6. Contratto CSV

Colonne obbligatorie:

- `transaction_id`
- `date`
- `amount`
- `vendor`
- `country`
- `approved_by`
- `category`

Regole principali:

- ID non vuoto e univoco;
- data in formato ISO `YYYY-MM-DD`;
- importo numerico non negativo;
- paese in codice a due lettere;
- approvatore non vuoto;
- categoria non vuota.

## 7. Risk engine

Il motore è deterministico e spiegabile. Regole iniziali:

- importo oltre soglia: +35 punti
- importo molto alto: +20 punti aggiuntivi.
- paese in lista di attenzione: +25 punti
- record non approvato: +20 punti
- categoria sensibile: +15 punti
- weekend: +10 punti.

Classificazione:

- `0–29`: basso
- `30–59`: medio
- `60+`: alto

La somma è troncata a 100. 

## 8. Route applicative

- `/` — dashboard dell’ultima analisi
- `/upload/` — upload e validazione CSV
- `/demo/` — avvio analisi del dataset demo
- `/analysis/<id>/` — dashboard di una specifica analisi
- `/analysis/<id>/report/` — report filtrabile
- `/analysis/<id>/record/<id>/` — dettaglio del record;
- `/manus-routes.json` — manifest richiesto dall’ambiente Webdev.

Le route sono server-rendered e non richiedono una separazione frontend/backend. In produzione il container Django serve HTML e asset statici, le risposte private e i report non devono essere condivisi in cache.

## 9. Qualità e sicurezza

- limite dimensione file;
- estensione CSV controllata;
- encoding gestito in modo esplicito;
- nessun secret nel repository;
- CSRF sui form Django;
- escape HTML lasciato ai template Django;
- validazione server-side, non solo nel browser;
- dataset demo anonimizzato.
