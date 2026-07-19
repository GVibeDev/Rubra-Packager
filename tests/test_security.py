from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rubra_packager.security import ValidationError, confine, parse_hex_color, safe_filename_stem, safe_identifier, validate_package_name


class SecurityTests(unittest.TestCase):
    def test_safe_identifier_accepts_expected_value(self):
        self.assertEqual(safe_identifier("arena-rubra_1.0"), "arena-rubra_1.0")

    def test_safe_identifier_rejects_traversal(self):
        with self.assertRaises(ValidationError):
            safe_identifier("../outside")

    def test_package_name_validation(self):
        self.assertEqual(validate_package_name("com.GB.ArenaRubra"), "com.gb.arenarubra")

    def test_invalid_package_name_rejected(self):
        with self.assertRaises(ValidationError):
            validate_package_name("Arena Rubra")

    def test_confine_rejects_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValidationError):
                confine(root, root / ".." / "other")

    def test_filename_stem(self):
        self.assertEqual(safe_filename_stem("Arena Rubra!"), "Arena_Rubra")

    def test_hex_color(self):
        self.assertEqual(parse_hex_color("#0a1b2c"), "#0A1B2C")
