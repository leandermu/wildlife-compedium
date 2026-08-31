# Referenzbilder

Dieser Ordner bleibt im Repository **leer** – die Bilder stammen aus Wikipedia
bzw. Wikimedia Commons und werden nicht mitgeliefert. Sie lassen sich jederzeit
nachladen:

```bash
cd backend
python scripts/fetch_reference_images.py       # → images/original/ + credits.json
python scripts/process_reference_images.py     # → S/W-Platten + Datenbankeinträge
```

`credits.json` ist versioniert und dokumentiert zu jeder Art Urheber, Lizenz und
Quelle. Die Lizenzen sind überwiegend CC BY-SA; die Namensnennung wird in der App
unter dem Referenzbild angezeigt und darf nicht entfernt werden.

Eigene Fotos landen nie hier, sondern unter `backend/data/media/` – und damit
außerhalb der Versionskontrolle.
