#!/usr/bin/env python3

# HID keycode reference for debugging
# Standard USB HID keycodes for letters:
hid_keycodes = {
    'A': 4, 'B': 5, 'C': 6, 'D': 7, 'E': 8, 'F': 9, 'G': 10, 'H': 11,
    'I': 12, 'J': 13, 'K': 14, 'L': 15, 'M': 16, 'N': 17, 'O': 18, 'P': 19,
    'Q': 20, 'R': 21, 'S': 22, 'T': 23, 'U': 24, 'V': 25, 'W': 26, 'X': 27,
    'Y': 28, 'Z': 29
}

print("Current CircuitPython touch zone mapping:")
print("Zone -> Keycode -> Expected Letter")
print("-" * 35)

# Current mapping from your code
current_zones = [
    ("A", 4), ("B", 5), ("C", 6), ("D", 7), ("E", 8), ("F", 9), ("G", 10), ("H", 11),
    ("I", 12), ("J", 13), ("K", 14), ("L", 15), ("M", 16), ("N", 17)
]

for letter, keycode in current_zones:
    print(f"{letter:2} -> {keycode:2} -> Should produce '{letter}'")

print("\nIf keycode 6 produces 'N', then there's an 8-keycode offset:")
print("Keycode 6 -> 'N' means keycode maps are shifted")
print("\nTo fix this, try these keycodes instead:")
print("Zone -> New Keycode")
print("-" * 20)

# If keycode 6 produces N (which is normally 17), then we need to subtract 11
offset = 17 - 6  # = 11
print(f"Detected offset: {offset}")

for letter, current_keycode in current_zones:
    target_keycode = hid_keycodes[letter]
    corrected_keycode = target_keycode - offset
    if corrected_keycode > 0:
        print(f"{letter} -> {corrected_keycode} (was {current_keycode})")
    else:
        print(f"{letter} -> Cannot fix with offset (would be {corrected_keycode})")