"""Live quality audit for the automatic species importer.

The script deliberately uses preview mode: no database rows or media files are
written. It covers 200 familiar species across mammals, birds, reptiles,
amphibians, fish and insects.

Usage:
    python scripts/audit_species_import.py --workers 8
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from app.wikipedia import import_species_automatically


SPECIES_BY_GROUP: dict[str, list[str]] = {
    "mammal": [
        "Wolf", "Rotfuchs", "Polarfuchs", "Fennek", "Goldschakal",
        "Braunbär", "Eisbär", "Waschbär", "Dachs", "Fischotter",
        "Baummarder", "Hermelin", "Löwe", "Tiger", "Leopard", "Gepard",
        "Jaguar", "Puma", "Eurasischer Luchs", "Afrikanischer Elefant",
        "Asiatischer Elefant", "Giraffe", "Steppenzebra", "Breitmaulnashorn",
        "Flusspferd", "Wildschwein", "Rothirsch", "Reh", "Elch", "Rentier",
        "Gämse", "Alpensteinbock", "Wisent", "Kaffernbüffel",
        "Rotes Riesenkänguru", "Koala", "Nacktnasenwombat",
        "Braunkehl-Faultier", "Westlicher Gorilla", "Schimpanse", "Bonobo",
        "Borneo-Orang-Utan", "Mantelpavian", "Erdmännchen", "Alpenmurmeltier",
        "Eichhörnchen", "Europäischer Biber", "Feldhase", "Wildkaninchen",
        "Braunbrustigel", "Maulwurf", "Zwergfledermaus", "Blauwal", "Orca",
        "Seehund",
    ],
    "bird": [
        "Amsel", "Rotkehlchen", "Haussperling", "Feldsperling", "Blaumeise",
        "Kohlmeise", "Buchfink", "Grünfink", "Stieglitz", "Gimpel",
        "Zaunkönig", "Star", "Elster", "Eichelhäher", "Rabenkrähe",
        "Kolkrabe", "Mauersegler", "Rauchschwalbe", "Mehlschwalbe", "Kuckuck",
        "Buntspecht", "Grünspecht", "Eisvogel", "Wiedehopf", "Bienenfresser",
        "Weißstorch", "Schwarzstorch", "Graureiher", "Silberreiher",
        "Höckerschwan", "Graugans", "Stockente", "Mandarinente", "Blässhuhn",
        "Teichhuhn", "Kranich", "Kiebitz", "Austernfischer", "Lachmöwe",
        "Silbermöwe", "Basstölpel", "Papageitaucher", "Kaiserpinguin", "Strauß",
        "Rosaflamingo", "Uhu", "Waldkauz", "Schleiereule", "Mäusebussard",
        "Rotmilan", "Seeadler", "Steinadler", "Wanderfalke", "Turmfalke", "Habicht",
    ],
    "reptile": [
        "Ringelnatter", "Schlingnatter", "Kreuzotter", "Äskulapnatter",
        "Königspython", "Königskobra", "Grüne Mamba", "Komodowaran",
        "Zauneidechse", "Mauereidechse", "Blindschleiche",
        "Grüne Meeresschildkröte", "Lederschildkröte",
        "Griechische Landschildkröte", "Mississippi-Alligator", "Nilkrokodil",
        "Pantherchamäleon", "Grüner Leguan", "Leopardgecko",
        "Streifenköpfige Bartagame",
    ],
    "amphibian": [
        "Grasfrosch", "Europäischer Laubfrosch", "Erdkröte", "Kreuzkröte",
        "Wechselkröte", "Knoblauchkröte", "Feuersalamander", "Alpensalamander",
        "Teichmolch", "Bergmolch", "Nördlicher Kammmolch", "Axolotl",
        "Goldbaumsteiger", "Nordamerikanischer Ochsenfrosch", "Moorfrosch",
    ],
    "fish": [
        "Hecht", "Zander", "Flussbarsch", "Karpfen", "Europäischer Wels",
        "Bachforelle", "Atlantischer Lachs", "Europäischer Aal", "Hering",
        "Kabeljau", "Makrele", "Atlantischer Blauflossen-Thunfisch", "Weißer Hai",
        "Großer Hammerhai", "Riesenmanta", "Echter Clownfisch",
        "Langschnäuziges Seepferdchen", "Japanischer Kugelfisch", "Mondfisch",
        "Schwertfisch",
    ],
    "insect": [
        "Westliche Honigbiene", "Dunkle Erdhummel", "Deutsche Wespe",
        "Europäische Hornisse", "Rote Waldameise", "Siebenpunkt-Marienkäfer",
        "Feldmaikäfer", "Nashornkäfer", "Hirschkäfer", "Kartoffelkäfer",
        "Gemeiner Mistkäfer", "Grünes Heupferd", "Feldgrille",
        "Europäische Gottesanbeterin", "Indische Stabschrecke",
        "Gemeine Skorpionsfliege", "Gemeine Florfliege", "Silberfischchen",
        "Gemeiner Ohrwurm", "Gemeine Stechmücke",
    ],
    "butterfly": [
        "Tagpfauenauge", "Admiral", "Distelfalter", "Zitronenfalter",
        "Schwalbenschwanz", "Kleiner Fuchs", "Großer Fuchs", "C-Falter",
        "Aurorafalter", "Hauhechel-Bläuling", "Schachbrettfalter", "Kaisermantel",
        "Totenkopfschwärmer", "Taubenschwänzchen", "Ligusterschwärmer",
    ],
}


LATIN_FAMILY = re.compile(r"(?:idae|inae)$", re.IGNORECASE)
LATIN_ORDER = re.compile(
    r"(?:formes|ptera|poda|carnivora|primates|rodentia|lagomorpha|artiodactyla|cetacea)$",
    re.IGNORECASE,
)


@dataclass
class AuditResult:
    requested: str
    expected_group: str
    returned: str = ""
    scientific: str = ""
    family: str = ""
    order: str = ""
    regions: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()


def audit_one(expected_group: str, name: str) -> AuditResult:
    try:
        imported = import_species_automatically(name, save_reference=False)
    except Exception as exc:
        return AuditResult(name, expected_group, issues=(f"FEHLER: {exc}",))

    issues: list[str] = []
    if imported.group != expected_group:
        issues.append(f"Gruppe {imported.group!r} statt {expected_group!r}")
    if not imported.scientific_name:
        issues.append("wissenschaftlicher Name fehlt")
    if not imported.family:
        issues.append("Familie fehlt")
    elif LATIN_FAMILY.search(imported.family):
        issues.append(f"Familie nicht deutsch: {imported.family}")
    if not imported.order_name:
        issues.append("Ordnung fehlt")
    elif LATIN_ORDER.search(imported.order_name):
        issues.append(f"Ordnung nicht deutsch: {imported.order_name}")
    if not imported.reference_image:
        issues.append("Referenzbild fehlt")
    if not imported.regions:
        issues.append("Region fehlt")
    return AuditResult(
        requested=name,
        expected_group=expected_group,
        returned=imported.common_name,
        scientific=imported.scientific_name,
        family=imported.family,
        order=imported.order_name,
        regions=tuple(imported.regions),
        issues=tuple(issues),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--all", action="store_true", help="Auch fehlerfreie Ergebnisse ausgeben")
    parser.add_argument("--names", nargs="*", help="Optional nur diese Artnamen prüfen")
    args = parser.parse_args()

    cases = [(group, name) for group, names in SPECIES_BY_GROUP.items() for name in names]
    if len(cases) != 200:
        raise RuntimeError(f"Audit-Liste muss 200 Arten enthalten, enthält aber {len(cases)}")
    if args.names:
        requested = {name.casefold() for name in args.names}
        cases = [(group, name) for group, name in cases if name.casefold() in requested]
        found = {name.casefold() for _group, name in cases}
        if missing := requested - found:
            raise RuntimeError(f"Nicht in der Audit-Liste: {', '.join(sorted(missing))}")
    total = len(cases)

    results: dict[str, AuditResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as executor:
        futures = {
            executor.submit(audit_one, group, name): name for group, name in cases
        }
        for index, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results[result.requested] = result
            state = "OK" if not result.issues else "AUFFÄLLIG"
            print(f"[{index:03}/{total:03}] {state}: {result.requested}", flush=True)

    issue_count = 0
    print("\nDETAILS")
    for _group, name in cases:
        result = results[name]
        if not args.all and not result.issues:
            continue
        issue_count += bool(result.issues)
        detail = "; ".join(result.issues) or "OK"
        print(
            f"{result.requested}\t{result.returned}\t{result.scientific}\t"
            f"{result.order}\t{result.family}\t{','.join(result.regions)}\t{detail}"
        )

    print("\nZUSAMMENFASSUNG")
    print(f"Geprüft: {total}")
    print(f"Ohne Auffälligkeit: {total - issue_count}")
    print(f"Mit Auffälligkeit: {issue_count}")
    print("Gruppen:", dict(Counter(group for group, _name in cases)))


if __name__ == "__main__":
    main()
