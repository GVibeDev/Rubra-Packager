from __future__ import annotations

import unittest

from rubra_packager.profiles import ProfileRegistry


class ProfileTests(unittest.TestCase):
    def test_builtin_profiles_load(self):
        registry = ProfileRegistry()
        ids = {profile.profile_id for profile in registry.list()}
        self.assertTrue({"arena-rubra", "generic-web-game", "generic-html-app"}.issubset(ids))

    def test_arena_default_is_full(self):
        profile = ProfileRegistry().get("arena-rubra")
        self.assertEqual(profile.default_variant, "full")
        self.assertEqual(profile.variant("lite").variant_id, "lite")
