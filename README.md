# Wildlife Compedium

Ein persönliches Tierfoto-Compedium – inspiriert vom Tier-Kompendium aus Red Dead
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

Drei Dienste: `db` (PostgreSQL), `backend` (FastAPI unter Uvicorn) und
`frontend` (Vite-Build, ausgeliefert von Caddy). Caddy übernimmt dabei die Rolle
des Dev-Proxys und reicht `/api` und `/media` an das Backend durch – die App
bleibt also auch im Container einorigin. Die API ist zusätzlich direkt unter
`http://localhost:8000` erreichbar (Doku: `/docs`).

Im Container läuft immer PostgreSQL, nicht SQLite: ein Pfad, der gepflegt und
getestet wird. Die 152 Arten werden beim ersten Start wie gewohnt geseedet.

Die Referenzbilder werden **beim Bauen** von Wikipedia geladen und liegen im
Image unter `/images/original`; der erste Start macht daraus die Platten (siehe
unten). Der erste `--build` dauert dadurch ein paar Minuten – jeder weitere
greift auf den Build-Cache zurück. Wer das nicht will, baut ohne:

```bash
docker compose build --build-arg REFERENCE_IMAGES=0
```

Zwei Volumes: `wildlife-db` für die Datenbank, `wildlife-media` für die Fotos.
Ein Rebuild lässt beide unangetastet, `docker compose down -v` löscht sie – und
damit die Sammlung. Ein vollständiges, wieder einspielbares Backup gibt es in
der App ganz unten unter **Verwaltung → Backup**. Es enthält die Datenbank aller
Profile und den vollständigen Medienbestand.

Wichtig: Arten, die in der laufenden App über **Verwaltung** angelegt werden,
liegen in dieser Datenbank und werden nicht automatisch ins Git-Repository
geschrieben. Ein Update derselben Docker-Installation behält sie über das
Volume. Eine frische Installation auf einem anderen Server kennt dagegen nur
die Arten aus `seed_species.json`. Für den Umzug der kompletten Sammlung muss
das in der App gespeicherte Gesamtbackup geladen werden.

Das Passwort ist per `POSTGRES_PASSWORD` überschreibbar (Standard `wildlife`);
der Datenbank-Port wird nicht nach außen veröffentlicht.

### Docker-Installation aktualisieren

Im bereits geklonten Projektordner auf dem Server:

```bash
git pull --ff-only
docker compose up -d --build --remove-orphans
docker compose ps
```

`git pull` holt den neuen Code; `docker compose up` baut nur die nötigen Images
neu und ersetzt die Anwendungscontainer. Die Volumes `wildlife-db` und
`wildlife-media` bleiben bestehen. Vor einem größeren Update empfiehlt sich
trotzdem **Verwaltung → Backup speichern**. Niemals `docker compose down -v`
für ein normales Update verwenden.

## Was drin ist

**Profile.** Mehrere Familienmitglieder führen ihren eigenen Sammelstand in
derselben Installation. Profile sind bewusst nicht passwortgeschützt und lassen
sich oben in der Navigation direkt anlegen und wechseln. Artenkatalog und
Referenzbilder sind gemeinsam; Fotos, Begegnungen, Freischaltungen,
Auszeichnungen und Statistiken gehören jeweils zum aktiven Profil. Das
Gesamtbackup umfasst dagegen immer alle Profile.
Die Startseite zeigt außerdem einen gemeinsamen Aktivitätsverlauf mit neuen
Fotos, Sichtungen ohne Foto und von einem Profil hinzugefügten Arten.
In den Profileinstellungen kann außerdem die männliche oder weibliche Form für
Auszeichnungsnamen gewählt werden (zum Beispiel Alpenjäger/Alpenjägerin).
Beim Upgrade werden vorhandene persönliche Daten automatisch dem Profil
„Leander“ zugeordnet. Leere Profile können wieder gelöscht werden; Profile mit
Fotos oder Begegnungen schützt die App vor versehentlichem Löschen.

**Sammeln.** 152 echte Arten mit Schwerpunkt Bayern/Deutschland plus eine
„Welt & Expedition"-Kategorie. Zwei Zustände pro Art:

| Status | Bedeutung |
|---|---|
| `locked` | kein eigenes Foto – Referenzskizze wird gezeigt |
| `unlocked` | mindestens ein eigenes Foto |

**Fotos & Begegnungen** sind getrennt: Es kann eine Begegnung ohne Foto geben
(gehört, aber nicht abgelichtet). Beim Upload liest der Server Bildmaße und
EXIF-Daten aus (Kamera, Objektiv, ISO, Blende) und legt automatisch eine
Begegnung an; ein fehlendes Datum wird aus den EXIF-Daten übernommen. Thumbnails
werden serverseitig erzeugt, damit auch Rasterseiten mit tausenden Fotos schnell
bleiben. HEIC/HEIF- und TIFF-Dateien werden als Original aufbewahrt und erhalten
zusätzlich eine browserfähige JPEG-Anzeigeversion. Fehlende Anzeigeversionen und
Vorschaubilder älterer Uploads repariert das Backend beim Start. Alle lesbaren EXIF-Bereiche werden in der
Datenbank gesichert und sind über den „i“-Schalter der Fotoansicht einsehbar.
Datum, Uhrzeit, Ort und Notiz von Fotos und Begegnungen lassen sich nachträglich
bearbeiten.

**Suche** ist umlauttolerant in beide Richtungen: `maus`, `mäuse` und `maeuse`
finden alle den Mäusebussard, ebenso der wissenschaftliche Name (`Alcedo`).

**Filter** nach gesehen/nicht gesehen, Fotostatus, Tiergruppe, Region,
Lebensraum, Schwierigkeit, Familie und Tags – kombinierbar, mit Trefferzahlen.
Jede Zahl wird live aus den Daten
berechnet; nichts ist hart kodiert.

**Auszeichnungen** sind datengetrieben (`backend/app/achievements.py`,
erweiterbar über `backend/app/data/achievements.json`). Regeltypen: `count`,
`species`, `photos`, `locations`, `seasonal`.

**Backup.** Ein einziges Gesamtbackup sichert und lädt alle Profile, Arten,
Begegnungen, Fotos, Vorschaubilder, Referenzbilder und Auszeichnungsstände. Das
Backup lässt sich über die Verwaltungsseite wieder einspielen.

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

Mit Docker passiert beides von selbst, aufgeteilt auf die beiden Zeitpunkte, an
die es jeweils gehört: Der **Download** ist ein Build-Schritt (`fetch` läuft in
einer eigenen Stage, das Ergebnis landet im Image unter `/images`). Das
**Verarbeiten** kann es nicht sein, denn es schreibt Urheber und Pfade in die
Datenbank – die es zur Bauzeit noch nicht gibt. Das erledigt das Backend beim
Start selbst; mit `--missing` werden nur noch fehlende Platten ergänzt. Dadurch
bleiben genau drei laufende Dienste und es gibt keinen absichtlich beendeten
vierten Container. Neu erzeugen lassen sie sich jederzeit:

```bash
docker compose exec backend python scripts/process_reference_images.py
```

Der Downloader nimmt das kuratierte Titelbild des Wikipedia-Artikels – das ist
zuverlässig die richtige Art. `--upgrade-small PX` tauscht zu kleine Vorlagen
gegen ein größeres Bild aus demselben Artikel; eine Sperrliste hält dabei
Verbreitungskarten, Eier, Schädel und Museumspräparate heraus.

Urheber, Lizenz und Quelle jeder Aufnahme stehen in `images/credits.json` und
werden in der App unter dem Referenzbild angezeigt. Die meisten Bilder stehen
unter CC BY-SA – **die Namensnennung darf nicht entfernt werden.**

## Daten erweitern

Über **Verwaltung** im Browser oder direkt per API:

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

Beim automatischen Anlegen über einen Tiernamen wird ein Wikipedia-Treffer erst dann
akzeptiert, wenn Artikeltext und Kategorien ihn als Tierartikel bestätigen.
Begriffsklärungen werden nach dem passenden Tierlink aufgelöst. Taxonomie und
regionale Nachweisdichte werden zusätzlich mit GBIF strukturiert abgeglichen;
Lebensräume und Tags landen nur im kontrollierten App-Vokabular. Gespeichert
werden nur eine kurze deutsche Zusammenfassung und ausdrücklich genannte Maße –
unbekannte Werte bleiben leer, statt geraten zu werden. Alternativ können alle
Felder manuell gepflegt und ein eigenes Referenzbild hochgeladen werden.

## Auf 1.000+ Arten ausgelegt

- Eine Seite der Artenliste kostet eine konstante Zahl an SQL-Abfragen,
  unabhängig von Arten- und Fotomenge (Aggregat-Join statt N+1).
- Serverseitige Paginierung, Sortierung und Filterung; das Frontend lädt
  seitenweise nach.
- Referenzbild und persönliche Fotos sind getrennte Felder und getrennte
  Storage-Präfixe.
- `backend/app/storage.py` kapselt die Ablage – ein Wechsel auf S3 o. Ä. ist
  eine neue Unterklasse, kein Umbau.
- Lokal ist SQLite der Standard, im Container läuft PostgreSQL; beides hängt
  allein an `WC_DATABASE_URL`.

## Konfiguration

`backend/.env` (siehe `.env.example`):

| Variable | Standard |
|---|---|
| `WC_DATABASE_URL` | `sqlite:///./data/compendium.db` |
| `WC_STORAGE_BACKEND` | `local` |
| `WC_STORAGE_LOCAL_DIR` | `./data/media` |
| `WC_CORS_ORIGINS` | `http://localhost:5173,…` |

Die Fotos liegen unter `backend/data/media/` und werden nirgendwohin
hochgeladen. Das Gesamtbackup unter **Verwaltung** sichert Datenbank und Medien
gemeinsam und funktioniert sowohl mit der lokalen SQLite- als auch mit der
Docker-/PostgreSQL-Installation.

## Noch nicht gebaut (Phase 3)

Verbreitungskarten, Druck-/Buchansicht und PDF-Export. Die Grundlagen liegen:
`Species.distribution_map` ist vorhanden, `.no-print` und eine `@media print`-Regel
sind gesetzt.
