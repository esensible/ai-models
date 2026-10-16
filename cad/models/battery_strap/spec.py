"""Single source of truth for the battery strap (hold-down bar).

Reverse-engineered from battery_clip.stl recovered off the printer's SD card
2026-09-09 and measured by sectioning 2026-09-10, then re-authored
parametrically. A flat bar with a raised pad at each end, a bolt hole through
each pad, and "Fuck Yeah" recessed into the face that prints against the bed.

Provenance tags (repo convention):
  [AS-BUILT]   measured off the recovered STL -- reproduces the printed part
  [CHOSEN]     our picks where the STL could not tell us the intent
  [DERIVED]    computed; no new information

=== DATUM ======================================================================
Origin at the centre of the bar's footprint; z=0 is the TEXT face (the face
that sits on the bed, and the visible face once installed). +z is up through
the bar's thickness.
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "out")  # cad/out
os.makedirs(OUT, exist_ok=True)

# === AS-BUILT (measured from the recovered mesh) =============================
LENGTH = 219.0        # [AS-BUILT] overall
WIDTH = 60.0          # [AS-BUILT]
BAR_T = 15.0          # [AS-BUILT] thickness of the flat span
PAD_T = 25.0          # [AS-BUILT] total height at the raised end pads
PAD_L = 24.5          # [AS-BUILT] length of each raised pad
HOLE_D = 8.0          # [AS-BUILT] bolt holes, through the pads
HOLE_PITCH = 189.0    # [AS-BUILT] centre to centre
PAD_CH = 1.4          # [AS-BUILT] chamfer around the top of each pad
TEXT = "Fuck Yeah"    # [AS-BUILT]
TEXT_DEPTH = 2.0      # [AS-BUILT] recess depth into the z=0 face
TEXT_W = 150.0        # [AS-BUILT] width of the text block on the original
TEXT_H = 34.2         # [CHOSEN] font size that makes Comic Neue span TEXT_W.
                      #   The original's font is NOT recoverable from a mesh
                      #   and was more condensed (same 150 width but a 31.8
                      #   tall block vs 22 here) -- matching width keeps the
                      #   proportions on the bar right; matching height would
                      #   overflow the pads.

# === CHOSEN ==================================================================
FONT = "ComicNeue-Bold.ttf"   # [CHOSEN] the repo's house font for this phrase
                              #   (canbox_slim lid used the same); the original
                              #   STL's font is not recoverable from a mesh
EDGE_R = 1.0          # [CHOSEN] softening on the bar's outline

# === DERIVED =================================================================
HOLE_X = HOLE_PITCH / 2                       # +-94.5
PAD_CTR_X = LENGTH / 2 - PAD_L / 2            # +-97.25
assert HOLE_X + HOLE_D / 2 < LENGTH / 2, "hole breaks out of the end"
assert PAD_T > BAR_T, "pads must stand above the bar"
