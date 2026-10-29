"""Check Jubjub against pinned external parameters, without HLS or network access."""
import json
from pathlib import Path
import unittest

import yaml

from tessera.structs.field import get_field


ROOT = Path(__file__).resolve().parents[1]


class JubjubParametersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((ROOT / "test/vectors/jubjub.json").read_text())
        cls.curve = yaml.safe_load((ROOT / "reference/curves.yaml").read_text())["bls12_381_ed"]
        cls.q = int(cls.reference["base_modulus"])
        cls.a = cls.q - 1
        cls.d = (-10240 * pow(10241, -1, cls.q)) % cls.q

    def test_field_identity(self):
        for field, expected in (("base", self.q),
                                ("scalar", int(self.reference["scalar_modulus"]))):
            with self.subTest(field=field):
                self.assertEqual(int(self.curve[field]["q"], 16), expected)
                self.assertEqual(self.curve[field]["bitwidth"], expected.bit_length())

    def test_coefficients(self):
        self.assertEqual(self.curve["form"], "TwistedEdwards")
        for name, expected in (("a", self.a), ("d", self.d), ("k", 2 * self.d % self.q)):
            with self.subTest(coefficient=name):
                self.assertEqual(int(self.curve[name], 16), expected)

    def test_published_generator_is_on_configured_curve(self):
        x, y = map(int, self.reference["generator"])
        self.assertNotEqual(x, 0)  # The identity would not detect wrong coefficients.
        a, d = (int(self.curve[name], 16) for name in ("a", "d"))
        self.assertEqual((a * x * x + y * y - 1 - d * x * x * y * y) % self.q, 0)

    def test_generated_field_coefficients(self):
        get_field.cache_clear()
        field = get_field("bls12_381_ed_base")
        montgomery_radix = 1 << self.q.bit_length()
        for name, expected in (("a", self.a), ("d", self.d), ("k", 2 * self.d % self.q)):
            with self.subTest(coefficient=name):
                self.assertEqual(int(field[name]["val"], 16), expected)
                self.assertEqual(int(field[name + "_mont"]["val"], 16),
                                 expected * montgomery_radix % self.q)


if __name__ == "__main__":
    unittest.main()
