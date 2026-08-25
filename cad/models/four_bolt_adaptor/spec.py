"""Single source of truth for the four-bolt fixture adaptor.

An adaptor plate joining two 4-bolt fixtures: 10 mm thick, 50 mm bore, two
4-hole bolt patterns (8 holes total), adaptor holes Ø6 mm.

Fixture A measured 2026-08-18: the pattern is an IRREGULAR quadrilateral
(top/bottom pitches differ, diagonals differ by 7 mm) -- solved from all six
pairwise hole distances by trilateration, never assumed symmetric.

Provenance tags (repo convention):
  [GROUND TRUTH]  design decisions everything derives from
  [DATUM]         coordinate-frame definition
  [MEASURED]      raw caliper readings off the physical fixtures, recorded
                  verbatim -- coordinates are DERIVED, never typed in
  [CHOSEN]        our picks (clearances, margins); comment says what constrains
  [DERIVED]       computed from the above; no new information

=== DATUM ======================================================================
Pattern A frame: top-left hole centre at the origin, +x through the top-right
hole centre, +y toward the bottom holes. Bore position in this frame is TBD
(awaiting how the 50 mm bore must align to the fixtures); provisionally the
centroid of pattern A's four holes.

=== MEASUREMENT PROTOCOL (calipers only) =======================================
All pair readings are OUTSIDE edge to OUTSIDE edge; centre-to-centre derives
by subtracting one measured hole diameter. Six pairs per fixture (4 sides +
2 diagonals) over-determine the quad by one distance; the solver checks the
residual against PAIR_TOL.
"""
import math, os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "out")  # cad/out
os.makedirs(OUT, exist_ok=True)

# === GROUND TRUTH =============================================================
THICKNESS = 10.0      # [GROUND TRUTH] plate thickness (user spec)
BORE_DIA = 50.0       # [GROUND TRUTH] plate's central through-bore (user spec;
                      #   the fixtures' 22/33 inner holes were measured only to
                      #   LOCATE their centres, not to size this hole)
HOLE_DIA = 6.0        # [GROUND TRUTH] adaptor bolt holes, all 8 (user spec)
                      #   NOTE: fixture A's holes measure 6.2; if the bolts
                      #   are M6, 6.0 printed holes will bind -- flagged, see
                      #   conversation

# === MEASURED: fixture A raw caliper readings (user, 2026-08-18) ==============
A_HOLE = 6.2          # [MEASURED] bolt-hole diameter, inside jaws
A_TOP_OO = 69.5       # [MEASURED] top pair, outside-outside (re-measured)
A_BOT_OO = 81.0       # [MEASURED] bottom pair, outside-outside (re-measured)
A_TLBR_OO = 99.0      # [MEASURED] diagonal, top-left to bottom-right
A_TRBL_OO = 92.0      # [MEASURED] diagonal, top-right to bottom-left
A_LEFT_OO = 61.5      # [MEASURED] left pair, outside-outside
A_RIGHT_OO = 65.0     # [MEASURED] right pair, outside-outside
A_INNER_DIA = 22.0    # [MEASURED] fixture A central hole diameter
A_TR_BORE_OO = 58.5   # [MEASURED] top-right hole outside edge, across the
                      #   inner circle, to its far edge
A_TL_BORE_OO = 54.9   # [MEASURED] top-left hole outside edge, across the
                      #   inner circle, to its far edge
A_BL_BORE_OO = None   # [MEASURED] same from bottom-left -- cross-check, FILL IN

# === MEASURED: fixture B (user, 2026-08-18) ===================================
# ALIGNMENT [GROUND TRUTH]: fixture B's central hole is coincident with
# fixture A's bore centre. Relative clocking of the two patterns: TBD.
B_INNER_DIA = 33.0    # [MEASURED] fixture B central hole diameter
B_HOLE = 6.0          # [MEASURED] bolt-hole diameter
B_TOP_OO = 84.3       # [MEASURED] top pair, outside-outside (re-read, decimals)
B_BOT_OO = 97.0       # [MEASURED] bottom pair, outside-outside
B_LEFT_OO = 76.0      # [MEASURED] left pair (first read 16 -- transposed digits)
                      # NOTE closure residual 0.91 > 0.5 with these readings;
                      # left/right/bottom being re-read with decimals
B_RIGHT_OO = 76.8     # [MEASURED] right pair, outside-outside
B_TLBR_OO = 121.0     # [MEASURED] diagonal, top-left to bottom-right
B_TRBL_OO = 111.0     # [MEASURED] diagonal, top-right to bottom-left
B_TL_BORE_OO = 73.0   # [MEASURED] top-left hole outside edge, across the
                      #   33mm hole, to its far edge
B_TR_BORE_OO = 70.9   # [MEASURED] top-right hole outside edge, same protocol
B_BL_BORE_OO = None   # [MEASURED] cross-check from bottom-left -- not taken

# === CHOSEN ===================================================================
EDGE_MARGIN = 5.0     # [GROUND TRUTH] outer wall clearance around the holes
                      #   (user spec)
CB_DEPTH = 5.0        # [GROUND TRUTH] A-hole recess depth (user spec)
CB_SIDE_A = True      # [GROUND TRUTH] v2 (user): recesses cut from the A
                      #   mating face (z=0), not the B face
BUTTON_HEAD_DIA = 10.4  # [STANDARD] ISO 7380 M6 button head diameter (h 3.3)
CB_DIA = 10.0         # [GROUND TRUTH] v2 (user): recess diameter reduced 1mm
                      #   from the Ø11 v1. NOTE: smaller than an ISO 7380 M6
                      #   button head (10.4) -- user directed; their hardware
PAIR_TOL = 0.7        # [CHOSEN] max residual between the redundant sixth
                      #   distance and the solved quad. Raised from 0.5 at the
                      #   user's direction to accept fixture B's 0.56 residual
                      #   -- implies up to ~0.6mm pattern uncertainty; bolt
                      #   clearance must absorb it

# === DERIVED: pattern A hole centres by trilateration =========================
def solve_quad(hole, top, bot, tlbr, trbl, left, right, tol):
    """Solve TL,TR,BL,BR centre coords from six outside-outside readings.

    Datum: TL at origin, TR on +x. BL/BR placed from (left, trbl) and
    (right, tlbr); the bottom reading is the redundant check.
    Returns dict of centre coords. Raises if the quad doesn't close.
    """
    c = lambda oo: oo - hole                     # outside-outside -> centre-centre
    def _tri(d_from_tl, d_from_tr, tr_x):
        # intersect circles about TL(0,0) r=d_from_tl and TR(tr_x,0) r=d_from_tr
        x = (d_from_tl**2 - d_from_tr**2 + tr_x**2) / (2 * tr_x)
        y2 = d_from_tl**2 - x**2
        assert y2 > 0, "readings do not form a valid quad (circle miss)"
        return (x, math.sqrt(y2))                # +y = downward, toward bottom row
    TL = (0.0, 0.0)
    TR = (c(top), 0.0)
    BL = _tri(c(left), c(trbl), TR[0])
    BR = _tri(c(tlbr), c(right), TR[0])
    got_bot = math.dist(BL, BR)
    resid = abs(got_bot - c(bot))
    assert resid <= tol, (
        f"quad does not close: solved bottom pitch {got_bot:.2f} vs measured "
        f"{c(bot):.2f} (residual {resid:.2f} > {tol}) -- re-measure")
    return {"TL": TL, "TR": TR, "BL": BL, "BR": BR, "residual": resid}

if None not in (A_LEFT_OO, A_RIGHT_OO):
    A_QUAD = solve_quad(A_HOLE, A_TOP_OO, A_BOT_OO, A_TLBR_OO, A_TRBL_OO,
                        A_LEFT_OO, A_RIGHT_OO, PAIR_TOL)      # [DERIVED]
    A_CENTROID = tuple(sum(A_QUAD[k][i] for k in ("TL", "TR", "BL", "BR")) / 4
                       for i in (0, 1))                        # [DERIVED]

# === DERIVED: bore centres ====================================================
# Span readings run hole outside edge -> far edge of the inner circle, so
# centre-to-centre = reading - hole_dia/2 - inner_dia/2.
def solve_bore(quad, hole, inner, tl_oo, tr_oo, bl_oo, tol):
    off = hole / 2 + inner / 2
    r_tl, r_tr = tl_oo - off, tr_oo - off
    tr_x = quad["TR"][0]
    x = (r_tl**2 - r_tr**2 + tr_x**2) / (2 * tr_x)
    y2 = r_tl**2 - x**2
    assert y2 > 0, "bore readings do not intersect"
    ctr = (x, math.sqrt(y2))    # +y solution: bore sits between the hole rows
    if bl_oo is not None:
        err = abs(math.dist(ctr, quad["BL"]) - (bl_oo - off))
        assert err <= tol, (
            f"bore cross-check from BL disagrees by {err:.2f}mm -- re-measure")
    return ctr

A_BORE_CTR = solve_bore(A_QUAD, A_HOLE, A_INNER_DIA,
                        A_TL_BORE_OO, A_TR_BORE_OO, A_BL_BORE_OO, PAIR_TOL)

# === DERIVED: pattern B (once its hole diameter + left pair are in) ===========
if None not in (B_HOLE, B_LEFT_OO):
    B_QUAD = solve_quad(B_HOLE, B_TOP_OO, B_BOT_OO, B_TLBR_OO, B_TRBL_OO,
                        B_LEFT_OO, B_RIGHT_OO, PAIR_TOL)      # [DERIVED]
    B_BORE_CTR = solve_bore(B_QUAD, B_HOLE, B_INNER_DIA,
                            B_TL_BORE_OO, B_TR_BORE_OO, B_BL_BORE_OO, PAIR_TOL)

# === DERIVED: both patterns in the PLATE frame ================================
# Plate frame = pattern A's frame, viewed from fixture A's side.
# [GROUND TRUTH] MIRROR_B=False, user-confirmed: B's readings describe its
# pattern as seen from fixture A's side, so patterns combine unmirrored.
# (Cross-evidence: mirrored placement puts A-BR and B-BL 0.07mm apart --
# bolts would collide inside the plate.)
# [GROUND TRUTH] clocking per user: top-pair lines parallel, no rotation.
MIRROR_B = False
if None not in (B_HOLE, B_LEFT_OO):
    def _b_to_plate(p):
        x, y = p
        if MIRROR_B:
            x = 2 * B_BORE_CTR[0] - x
        return (x - B_BORE_CTR[0] + A_BORE_CTR[0],
                y - B_BORE_CTR[1] + A_BORE_CTR[1])
    B_HOLES_PLATE = {k: _b_to_plate(B_QUAD[k]) for k in ("TL", "TR", "BL", "BR")}
    ALL_HOLES_PLATE = {("A", k): A_QUAD[k] for k in ("TL", "TR", "BL", "BR")} | \
                      {("B", k): B_HOLES_PLATE[k] for k in B_HOLES_PLATE}
    # no two holes may merge or leave a sub-1mm wall between them
    for (n1, p1) in ALL_HOLES_PLATE.items():
        for (n2, p2) in ALL_HOLES_PLATE.items():
            if n1 < n2:
                gap = math.dist(p1, p2) - HOLE_DIA
                assert gap >= 1.0, (
                    f"holes {n1} and {n2} are {math.dist(p1, p2):.2f}mm apart "
                    f"(wall {gap:.2f}mm) -- patterns collide; check MIRROR_B "
                    f"/ clocking assumptions")
