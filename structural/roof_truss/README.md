# Roof truss structural analysis

Indicative structural analysis of a coupled-rafter roof "truss" — two rafters,
a collar tie, under-purlins at the collar node — spanning 8.5 m between wall
supports at 27° pitch, trusses at 1200 c/c, all members 35×105 Oregon, corrugated
iron roof. Results and recommendations are in [`REPORT.md`](REPORT.md); the
full generated tables are in [`report/analysis.md`](report/analysis.md).

**This is not a certified design.** It is a transparent, parametric model you can
interrogate. Wind pressures, timber grade, capacity factor and restraint
assumptions are command-line parameters — check them against the site wind
class, the timber actually supplied and AS 1684 / AS 1720.1 before building.

## Running it

```bash
uv venv .venv && VIRTUAL_ENV=.venv uv pip install -r structural/roof_truss/requirements.txt
.venv/bin/python structural/roof_truss/roof_truss.py            # default case
.venv/bin/python structural/roof_truss/roof_truss.py --all --plots   # support matrix + section sweep + PNGs
.venv/bin/python structural/roof_truss/roof_truss.py --support tie --strutted --section 35x140
.venv/bin/python structural/roof_truss/roof_truss.py --help
```

`frame2d.py` is a ~200-line 2D Euler–Bernoulli frame solver (direct stiffness,
numpy for the linear solve only). `roof_truss.py` builds the frame, applies
AS/NZS 1170 load combinations, and runs AS 1720.1 member checks; all the tabular
work (station actions, envelopes, utilisation, report tables) is polars.

## What is modelled

- **Geometry** (centreline): wall supports 8500 apart, rise = 4250·tan 27° =
  2165 mm, rafter 4770 mm on slope. Collar tie 1000 mm (vertical) below the
  apex → 3925 mm long, meeting the rafter 2567 mm up the slope from the wall.
- **Rafters**: continuous beam elements wall → collar node → apex, 6 elements
  per segment. The two rafters are **hinged at the apex** (no ridge-beam
  bending continuity).
- **Collar tie**: beam element pinned both ends (nailed/bolted lap carries no
  moment); it carries axial force and its own self-weight bending.
- **Under-purlins**: run along the building at the collar node. Unless
  `--strutted`, they are assumed to be carried *by* the trusses (lateral
  restraint only, no vertical support). With `--strutted` the collar node is
  propped vertically (purlin strutted to a wall / strutting beam below).
- **Supports** (`--support`):
  - `pinned` — both walls resist the horizontal thrust (masonry, or walls
    braced/tied some other way). The reported `|H|` is what each wall must take.
  - `roller` — one wall is free to spread: what happens if nothing takes the
    thrust and only the collar tie holds the frame together.
  - `tie` — a 35×105 bottom tie (ceiling joist) at wall-plate level, pinned, takes
    the thrust in tension. Its own 8.5 m self-weight sag is reported too.

## Loads (kN, m; AS/NZS 1170)

| Load | Default | Note |
|---|---|---|
| Sheeting + battens `--g-roof` | 0.10 kPa on slope area | corrugated steel ~0.05 + battens; rafter/collar self-weight added automatically (550 kg/m³) |
| Roof live `--q-roof` | 0.25 kPa on plan | AS 1170.1 R2 non-trafficable, area ≥ 14 m² |
| Concentrated live `--q-point` | 1.4 kN | mid lower-rafter segment (worst position) |
| Wind uplift `--wind-up` | −0.8 kPa net, both slopes | indicative N2 (q_u 0.96 kPa, leeward C_pe −0.6, C_pi +0.2) |
| Wind down `--wind-down` | +0.6 kPa net, both slopes | conservative |
| Wind asymmetric `--wind-asym` | +0.5 / −0.8 kPa | windward pressure with internal suction, leeward uplift; **governs** |
| Serviceability wind `--ws-ratio` | 0.42 × ultimate | (26/40)² |

Combinations: 1.35G · 1.2G+1.5Q · 1.2G+1.5Q_point · 1.2G+W_down · 0.9G+W_up ·
1.2G+W_asym · 0.9G+W_asym. Serviceability: G long-term (×j₂ = 3, unseasoned),
0.7Q, W_s. Site wind class N3 scales all wind pressures by (50/40)² ≈ 1.56.

## Timber checks (AS 1720.1)

- Grade default **F7** (unseasoned Oregon; F5 / F8 selectable). Table H2.1
  values: f'b 18, f't 11, f's 1.7, f'c 13 MPa, E 7900 MPa.
- φ = 0.70 (Table 2.1, visually graded F-grade sawn timber, category 2 —
  primary members in a house). k1 per combination (0.57 / 0.94 / 0.97 / 1.0),
  k4 = k6 = k9 = 1.0.
- k12 bending stability: sagging → compression edge restrained by battens at
  `--battens` 900; hogging / uplift → compression edge restrained only at the
  wall, collar/purlin node and apex. Unseasoned ρ_b, ρ_c with r = 0.25 (gravity)
  or 1.0 (wind).
- Compression: S3 = segment length / d, S4 = batten spacing / b for rafters;
  collar and tie use their full length / (restraints + 1).
- Checks per station: bending, shear, combined bending + compression
  (cl 3.5.1, both expressions), bending + tension (cl 3.5.2). `util` is the
  worst demand/capacity ratio; > 1.0 fails.
- Collar-tie connection: rough 3.15 mm nail count from Table 4.1(B) J4 values
  (φ 0.80, k17 for multiple nails). Bolts to be designed separately.

## Known simplifications

- Point load placed at the nearest node (mid lower segment); eaves overhang,
  birdsmouth notch and ridge board ignored (the notch reduces capacity at the
  heel — a real design must check it).
- No load sharing (k9 = 1.0) — at 1200 c/c the battens don't share much.
- The under-purlin is not checked as a beam between struts; see REPORT.md.
- One truss-plane model: no bracing / longitudinal stability check.
