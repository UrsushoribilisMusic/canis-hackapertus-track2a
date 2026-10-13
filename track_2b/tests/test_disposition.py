import unittest

from backend.canis_disposition.lexical import lexical_readout
from backend.canis_disposition.hidden_directions import (
    hidden_direction_readout,
    load_hidden_directions,
)
from backend.canis_disposition.resolver import resolve
from backend.canis_disposition.types import Disposition
from backend.knowledge import KnowledgeStore
from backend.runtime import MockRuntime


class DispositionTests(unittest.TestCase):
    def test_uncertainty_raises_entropy_and_disposition(self):
        readout = lexical_readout("I'm not sure, it might depend on the hardware revision.")

        self.assertEqual(readout.disposition, Disposition.UNCERTAIN)
        self.assertGreater(readout.entropy, 0.6)

    def test_safety_override_beats_low_entropy_confidence(self):
        readout = lexical_readout("Yes, confirmed, but this is unsafe and carries risk.")

        self.assertEqual(readout.disposition, Disposition.CONCERN)

    def test_mischief_detects_evasive_wording_only(self):
        readout = lexical_readout("Technically they won't notice the loophole.")

        self.assertEqual(readout.disposition, Disposition.MISCHIEF)
        self.assertEqual(readout.source, "lexicalFallback")

    def test_seed_resolver_ignores_high_entropy_when_gate_disabled(self):
        disposition = resolve(
            {
                Disposition.CONFIDENT: 0.42,
                Disposition.UNCERTAIN: 0.03,
                Disposition.CURIOUS: 0.02,
            },
            entropy=0.95,
        )

        self.assertEqual(disposition, Disposition.CONFIDENT)

    def test_seed_resolver_does_not_promote_idle_on_low_entropy_when_gate_disabled(self):
        disposition = resolve(
            {
                Disposition.CONFIDENT: 0.01,
                Disposition.WARM: 0.005,
            },
            entropy=0.03,
        )

        self.assertEqual(disposition, Disposition.IDLE)

    def test_seed_resolver_uses_server_seed_threshold(self):
        disposition = resolve(
            {
                Disposition.WARM: 0.021,
                Disposition.CONFIDENT: 0.019,
            },
            entropy=0.50,
        )

        self.assertEqual(disposition, Disposition.WARM)

    def test_ios_to_web_contract_mapping(self):
        self.assertEqual(lexical_readout("I'm not sure.").to_web()["disposition"], "unsure")
        self.assertEqual(lexical_readout("This is unsafe.").to_web()["disposition"], "concerned")
        self.assertEqual(lexical_readout("Plain answer.").to_web()["disposition"], "neutral")

    def test_web_contract_includes_scores(self):
        readout = lexical_readout("I'm not sure, maybe it depends.")

        self.assertIn("scores", readout.to_web())
        self.assertGreater(readout.to_web()["scores"]["unsure"], 0)

    def test_hidden_direction_artifact_scores_forward_lens_readout(self):
        directions = load_hidden_directions()
        hidden = directions[Disposition.CURIOUS]
        readout = hidden_direction_readout(hidden, [0.1, 0.2, 0.3, 0.4])

        self.assertIsNotNone(readout)
        assert readout is not None
        web = readout.to_web()
        self.assertEqual(web["source"], "forwardLens")
        self.assertIn("curious", web["scores"])
        self.assertGreater(web["scores"]["curious"], 0.9)

    def test_mock_runtime_answers_question_without_scaffolding_text(self):
        answer, readout, _sources = MockRuntime().answer("Why does it rain?")

        self.assertIn("moist air", answer)
        self.assertNotIn("Prototype response", answer)
        self.assertNotIn("being wired", answer)
        self.assertEqual(readout.to_web()["disposition"], "neutral")

    def test_knowledge_store_chunks_and_searches_sources(self):
        store = KnowledgeStore()
        text = (
            ("Rain forms when moist air rises and condenses into droplets. " * 30)
            + "\n\n"
            + ("Apertus is the model family used by Canis for the HackApertus demo. " * 30)
            + "\n\n"
            + ("Sources are chunked so the model receives only relevant excerpts. " * 30)
        )

        pack = store.add("notes.md", text.encode())
        sources = store.search("Why does rain form?")

        self.assertGreaterEqual(len(pack.sections), 2)
        self.assertLessEqual(max(len(section.text) for section in pack.sections), 900)
        self.assertTrue(sources[0]["title"].startswith("Rain forms when moist air"))
        self.assertIn("moist air", sources[0]["snippet"])

    def test_mock_runtime_grounds_answer_in_source_chunks(self):
        sources = [
            {
                "sectionId": "notes-1",
                "citationIndex": 1,
                "title": "Rain note",
                "snippet": "Rain forms when moist air rises and condenses.",
            }
        ]

        answer, _readout, returned_sources = MockRuntime().answer("Why rain?", sources)

        self.assertIn("From Rain note", answer)
        self.assertEqual(returned_sources, sources)


if __name__ == "__main__":
    unittest.main()
