# Todos

## Als Nächstes
- [x] Referenzbilder für alle 152 Arten (Wikipedia → S/W-Platte, mit Lizenznachweis)
- [ ] Artenliste von 152 auf ~1.000 erweitern (CSV-Import steht bereit)
- [ ] Echte Fotos von Mama einpflegen, erste Runde gemeinsam durchgehen

## Phase 3
- [ ] Verbreitungskarten — Feld `distribution_map` existiert, erst statische SVGs, später GeoJSON
- [ ] Print/Book View — druckbare Seite je Art (`.no-print` und `@media print` liegen schon)
- [ ] PDF-/Fotobuch-Export aus der Buchansicht

## Später
- [ ] Zeitliche Quests mit Start-/Enddatum (`starts_on`/`ends_on` sind im Schema, UI fehlt)
- [ ] Fotostatistiken: Kamera, Objektiv, Brennweite (EXIF wird bereits gespeichert)
- [ ] Karten-Ansicht aller Fundorte (GPS-Felder sind da)
- [ ] Privates Hosting + einfacher Passwortschutz
- [ ] Pflanzen/Pilze als weitere Module

## Offene Entscheidungen
- [ ] `mastered` wird schon bei 2 Fotos erreicht (erstes Foto wird automatisch „bestes") —
      Schwelle in `backend/app/queries.py:MASTERED_MIN_PHOTOS` anpassbar
- [ ] Backup-Rhythmus festlegen (ZIP-Export oder `backend/data/` kopieren)
