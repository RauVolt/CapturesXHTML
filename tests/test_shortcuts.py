import unittest
from shortcuts import ShortcutMatcher, validate, normalize, label


class ShortcutTests(unittest.TestCase):
    def test_default_single_capture_no_repeat_and_keyup_consumed(self):
        matcher = ShortcutMatcher()
        self.assertEqual(matcher.feed(0x2C, True, True, set()), (True, True))
        self.assertEqual(matcher.feed(0x2C, True, True, set()), (False, True))
        self.assertEqual(matcher.feed(0x2C, False, True, set()), (False, True))

    def test_print_screen_release_only(self):
        self.assertEqual(ShortcutMatcher().feed(0x2C, False, True, set()), (True, True))

    def test_disabled_and_other_shortcuts_pass_through(self):
        matcher = ShortcutMatcher(('Ctrl', 'F8'))
        self.assertEqual(matcher.feed(0x77, True, False, {0x11}), (False, False))
        matcher.feed(0x77, False, False, set())
        self.assertEqual(matcher.feed(0x77, True, True, set()), (False, False))
        matcher.feed(0x77, False, True, set())
        self.assertEqual(matcher.feed(0x77, True, True, {0x11, 0x12}), (False, False))

    def test_modifier_released_first_does_not_leak_keyup(self):
        matcher = ShortcutMatcher(('Ctrl', 'F8'))
        self.assertEqual(matcher.feed(0x77, True, True, {0x11}), (True, True))
        self.assertEqual(matcher.feed(0x77, False, True, set()), (False, True))

    def test_reconfigure_during_hold_preserves_suppression(self):
        matcher = ShortcutMatcher()
        matcher.feed(0x2C, True, True, set())
        matcher.shortcut = ('Alt', 'F9')
        self.assertEqual(matcher.feed(0x2C, False, False, set()), (False, True))
        self.assertEqual(matcher.feed(0x78, True, True, {0x12}), (True, True))

    def test_validation_and_sided_modifier_names(self):
        self.assertEqual(normalize(0xA3), 0x11)
        self.assertEqual(label(('Ctrl', 'F8')), 'Ctrl + F8')
        with self.assertRaises(ValueError):
            validate('Win', 'L')
