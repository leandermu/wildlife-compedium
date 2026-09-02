import unittest
from unittest.mock import patch

from app.wikipedia import (
    _gbif_enrichment,
    _german_taxon_name,
    _is_species_article,
    _regions_from_article,
    _title_matches_request,
)
from app.vocab import group_from_taxonomy, normalize_species_metadata


class WikipediaMatchingTest(unittest.TestCase):
    def test_species_rank_accepts_correct_article_and_rejects_sculpture(self) -> None:
        fennek_page = {
            "pageprops": {"wikibase_item": "Qfennek"},
            "extract": "Der Fennek ist eine Fuchsart und der kleinste aller Wildhunde.",
            "categories": [{"title": "Kategorie:Hunde"}],
        }
        taxon = {
            "claims": {
                "P225": [{"mainsnak": {"datavalue": {"value": "Vulpes zerda"}}}],
                "P105": [{"mainsnak": {"datavalue": {"value": {"id": "Q7432"}}}}],
            }
        }
        sculpture_page = {
            "pageprops": {"wikibase_item": "Qsculpture"},
            "extract": "Die Steinskulptur eines Elchs ist ein archäologischer Fund.",
            "categories": [{"title": "Kategorie:Steinskulptur"}],
        }
        with patch("app.wikipedia._wikidata_entity", side_effect=[taxon, {"claims": {}}]):
            self.assertTrue(_is_species_article(fennek_page))
            self.assertFalse(_is_species_article(sculpture_page))

    def test_fuzzy_title_must_still_match_requested_name(self) -> None:
        self.assertTrue(_title_matches_request("Fennek (Tier)", "Fennek"))
        self.assertTrue(_title_matches_request("Erdmännchen", "Erdmännchen"))
        self.assertTrue(_title_matches_request("Gemeiner Schimpanse", "Schimpanse"))
        self.assertTrue(_title_matches_request("Atlantischer Hering", "Hering"))
        self.assertFalse(_title_matches_request("Bengalfuchs", "Fennek"))
        self.assertFalse(_title_matches_request("Alunda-Elch", "Elch"))

    def test_german_fish_class_overrides_unreliable_text_fallback(self) -> None:
        self.assertEqual(
            group_from_taxonomy("Strahlenflosser", "Barschartige", "mammal"),
            "fish",
        )
        self.assertEqual(
            group_from_taxonomy("Knorpelfische", "Grundhaie", "other"),
            "fish",
        )
        normalized = normalize_species_metadata(
            group="mammal",
            class_name="Actinopteri",
            order_name="Barschartige",
            habitats=[],
            regions=[],
            tags=[],
            activity="diurnal",
        )
        self.assertEqual(normalized["group"], "fish")
        self.assertEqual(normalized["class_name"], "Actinopterygii")

    def test_latin_fallback_taxa_are_translated(self) -> None:
        self.assertEqual(_german_taxon_name("Equidae"), "Pferde")
        self.assertEqual(_german_taxon_name("Pelecaniformes"), "Ruderfüßer")
        self.assertEqual(_german_taxon_name("Salmoniformes"), "Lachsartige")

    def test_native_regions_come_from_article_not_occurrence_records(self) -> None:
        self.assertEqual(
            _regions_from_article("Das Erdmännchen lebt im südlichen Afrika."),
            ["africa"],
        )
        self.assertEqual(
            _regions_from_article(
                "Der Elch lebt in Nordeuropa, Nordasien und Nordamerika."
            ),
            ["europe", "asia", "north_america"],
        )
        self.assertEqual(
            _regions_from_article(
                "Der Fennek bewohnt die Sandwüsten Nordafrikas.\n"
                "Ein verwandter Fuchs kommt auch in Nordamerika vor."
            ),
            ["africa"],
        )

    def test_gbif_taxonomy_is_german_and_does_not_invent_germany(self) -> None:
        gbif_match = {
            "confidence": 99,
            "matchType": "EXACT",
            "canonicalName": "Suricata suricatta",
            "class": "Mammalia",
            "family": "Herpestidae",
            "order": "Carnivora",
            "usageKey": 1,
        }
        with patch("app.wikipedia._json_api", return_value=gbif_match):
            result = _gbif_enrichment(
                "Suricata suricatta",
                "Das Erdmännchen bewohnt trockene Gebiete im südlichen Afrika.",
                "mammal",
            )
        self.assertEqual(result["regions"], ["africa"])
        self.assertEqual(result["countries"], [])
        self.assertEqual(result["family"], "Mangusten")
        self.assertEqual(result["order_name"], "Raubtiere")


if __name__ == "__main__":
    unittest.main()
