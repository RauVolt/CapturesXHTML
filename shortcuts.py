"""Shortcut configuration and deterministic keyboard event matching."""
KEYS = {'Impr. écran': 0x2C, 'Pause': 0x13, 'Arrêt défil.': 0x91}
KEYS.update({f'F{i}': 0x6F + i for i in range(1, 25)})
KEYS.update({chr(i): i for i in range(ord('A'), ord('Z') + 1)})
KEYS.update({str(i): ord(str(i)) for i in range(10)})
MODIFIERS = {'Aucune': None, 'Ctrl': 0x11, 'Alt': 0x12, 'Maj': 0x10}
DEFAULT_SHORTCUT = ('Aucune', 'Impr. écran')


def normalize(vk):
    return {0xA0: 0x10, 0xA1: 0x10, 0xA2: 0x11, 0xA3: 0x11,
            0xA4: 0x12, 0xA5: 0x12}.get(vk, vk)


def validate(modifier, key):
    if modifier not in MODIFIERS or key not in KEYS:
        raise ValueError('Choisissez une touche et éventuellement Ctrl, Alt ou Maj.')
    return modifier, key


def label(shortcut):
    modifier, key = shortcut
    return key if modifier == 'Aucune' else modifier + ' + ' + key


class ShortcutMatcher:
    def __init__(self, shortcut=DEFAULT_SHORTCUT):
        self.shortcut = validate(*shortcut)
        self.pressed = set()
        self.suppressed = set()

    def feed(self, vk, down, enabled, modifiers):
        """Return (capture, suppress). State tracks key-up even after deactivation."""
        vk = normalize(vk)
        repeated = vk in self.pressed
        modifier, key = self.shortcut
        required = set() if MODIFIERS[modifier] is None else {MODIFIERS[modifier]}
        matches = enabled and vk == KEYS[key] and set(modifiers) == required
        if down:
            self.pressed.add(vk)
            trigger = matches and not repeated
            if trigger:
                self.suppressed.add(vk)
            return trigger, vk in self.suppressed
        self.pressed.discard(vk)
        suppressed = vk in self.suppressed
        self.suppressed.discard(vk)
        # Some keyboards emit only Print Screen's release.
        release_only = matches and vk == 0x2C and not repeated and not suppressed
        return release_only, suppressed or release_only
