# Wildlife Compendium

Ein persönliches Tierfoto-Kompendium – inspiriert vom Tier-Kompendium aus Red Dead
Redemption 2. Jede Tierart ist eine Sammelkarte mit Steckbrief und Referenzskizze.
**Erst das eigene Foto schaltet eine Art frei.**

```
leander/
├── backend/    FastAPI + SQLAlchemy (Python)
└── frontend/   React Router + Tailwind (TypeScript, Vite)
```

## Starten

Zwei Terminals:

```bash
# 1) Backend  →  http://127.0.0.1:8000  (API-Doku: /docs)
cd backend
uv venv && uv pip install -e .          # nur beim ersten Mal
.venv/bin/python -m app.seed            # 152 Arten anlegen
.venv/bin/uvicorn app.main:app --reload

# 2) Frontend →  http://localhost:5173
cd frontend
npm install                             # nur beim ersten Mal
npm run dev
```

Das Frontend leitet `/api` und `/media` automatisch an das Backend weiter.

### Mit Docker

Ein Befehl, kein Python und kein Node auf dem Rechner nötig:

```bash
docker compose up --build     #  →  http://localhost:8080
```

Zwei Images: `backend` (FastAPI unter Uvicorn) und `frontend` (Vite-Build,
ausgeliefert von nginx). nginx übernimmt dabei die Rolle des Dev-Proxys und
reicht `/api` und `/media` an das Backend durch – die App bleibt also auch im
Container einorigin. Die API ist zusätzlich direkt unter
`http://localhost:8000` erreichbar (Doku: `/docs`).

Datenbank und Fotos liegen im Volume `wildlife-data` (im Container
`/app/data`); ein Rebuild lässt die Sammlung unangetastet. Wer sie stattdessen
im Dateisystem sehen will, ersetzt in `docker-compose.yml`:

```yaml
    volumes:
      - ./backend/data:/app/data
```

`docker compose down -v` löscht das Volume – und damit die Sammlung.

## Was drin ist

**Sammeln.** 152 echte Arten mit Schwerpunkt Bayern/Deutschland plus eine
„Welt & Expedition"-Kategorie. Drei Zustände pro Art:

| Status | Bedeutung |
|---|---|
| `locked` | kein eigenes Foto – Referenzskizze wird gezeigt |
| `unlocked` | mindestens ein eigenes Foto |
| `mastered` | mehrere Fotos und ein ausgewähltes „Bestes Foto" |

**Fotos & Begegnungen** sind getrennt: Es kann eine Begegnung ohne Foto geben
(gehört, aber nicht abgelichtet). Beim Upload liest der Server Bildmaße und
EXIF-Daten aus (Kamera, Objektiv, ISO, Blende) und legt automatisch eine
Begegnung an; ein fehlendes Datum wird aus den EXIF-Daten übernommen. Thumbnails
werden serverseitig erzeugt, damit auch Rasterseiten mit tausenden Fotos schnell
bleiben.

**Suche** ist umlauttolerant in beide Richtungen: `maus`, `mäuse` und `maeuse`
finden alle den Mäusebussard, ebenso der wissenschaftliche Name (`Alcedo`).

**Filter** nach Status, Tiergruppe, Region, Lebensraum, Schwierigkeit, Familie
und Tags – kombinierbar, mit Trefferzahlen. Jede Zahl wird live aus den Daten
berechnet; nichts ist hart kodiert.

**Auszeichnungen & Quests** sind datengetrieben (`backend/app/achievements.py`,
erweiterbar über `backend/app/data/achievements.json`). Regeltypen: `count`,
`species`, `photos`, `locations`, `seasonal`.

**Export.** JSON, CSV und ein vollständiges ZIP mit allen Originalfotos, nach
Art sortiert – die Sammlung hängt nie an dieser App.

## Referenzbilder

Gesperrte Arten zeigen ein Referenzbild als entsättigte Tinte-auf-Papier-Platte:
Man sieht, was zu finden ist – aber es sieht sichtbar noch nicht nach der eigenen
Sammlung aus. Das eigene Foto erscheint danach in voller Farbe.

Die Bilder liegen **nicht** im Repository, sondern werden nachgeladen:

```bash
cd backend
python scripts/fetch_reference_images.py     # Wikipedia → images/original/ + credits.json
python scripts/process_reference_images.py   # → S/W-Platten + Einträge in der Datenbank
```

Der Downloader nimmt das kuratierte Titelbild des Wikipedia-Artikels – das ist
zuverlässig die richtige Art. `--upgrade-small PX` tauscht zu kleine Vorlagen
gegen ein größeres Bild aus demselben Artikel; eine Sperrliste hält dabei
Verbreitungskarten, Eier, Schädel und Museumspräparate heraus.

Urheber, Lizenz und Quelle jeder Aufnahme stehen in `images/credits.json` und
werden in der App unter dem Referenzbild angezeigt. Die meisten Bilder stehen
unter CC BY-SA – **die Namensnennung darf nicht entfernt werden.**

## Daten erweitern

Über **Verwaltung** im Browser (Formular oder CSV/JSON-Upload) oder direkt:

```bash
curl -X POST http://127.0.0.1:8000/api/species/import/file -F "file=@arten.csv"
```

CSV-Spalten entsprechen den Feldern von `Species`; Mehrfachwerte per Komma:

```csv
common_name;scientific_name;group;family;size;habitats;regions;difficulty
Bienenfresser;Merops apiaster;bird;Bienenfresser;27-29 cm;"field,heath";"bavaria,germany";4
```

Bestehende Arten werden am Slug erkannt und aktualisiert. Die Startdaten liegen
in `backend/app/data/seed_species.json`; erzeugt wird sie aus
`_build_seed.py` (`python app/data/_build_seed.py`).

## Auf 1.000+ Arten ausgelegt

- Eine Seite der Artenliste kostet eine konstante Zahl an SQL-Abfragen,
  unabhängig von Arten- und Fotomenge (Aggregat-Join statt N+1).
- Serverseitige Paginierung, Sortierung und Filterung; das Frontend lädt
  seitenweise nach.
- Referenzbild und persönliche Fotos sind getrennte Felder und getrennte
  Storage-Präfixe.
- `backend/app/storage.py` kapselt die Ablage – ein Wechsel auf S3 o. Ä. ist
  eine neue Unterklasse, kein Umbau.
- SQLite ist Standard; `WC_DATABASE_URL` auf PostgreSQL umzustellen genügt
  (`uv pip install -e ".[postgres]"`).

## Konfiguration

`backend/.env` (siehe `.env.example`):

| Variable | Standard |
|---|---|
| `WC_DATABASE_URL` | `sqlite:///./data/compendium.db` |
| `WC_STORAGE_BACKEND` | `local` |
| `WC_STORAGE_LOCAL_DIR` | `./data/media` |
| `WC_CORS_ORIGINS` | `http://localhost:5173,…` |

Die Fotos liegen unter `backend/data/media/` und werden nirgendwohin
hochgeladen. Für ein Backup genügt der ZIP-Export oder ein Kopieren von
`backend/data/`.

## Noch nicht gebaut (Phase 3)

Verbreitungskarten, Druck-/Buchansicht und PDF-Export. Die Grundlagen liegen:
`Species.distribution_map` ist vorhanden, `.no-print` und eine `@media print`-Regel
sind gesetzt.
