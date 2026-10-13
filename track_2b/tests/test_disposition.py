import unittest

from backend.canis_disposition.lexical import lexical_readout
from backend.canis_disposition.resolver import resolve
from backend.canis_disposition.types import Disposition


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


if __name__ == "__main__":
    unittest.main()
