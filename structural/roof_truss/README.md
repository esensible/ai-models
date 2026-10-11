# Roof truss structural analysis

Indicative structural analysis of a coupled-rafter roof — rafters, ceiling
joists tying the rafter feet (carrying a ceiling, on a mid wall and hanging
beams), a collar tie, under-purlins and a ridge beam bearing on cross walls
every ~4 m — spanning 8.5 m between wall supports at 27° pitch, trusses at
1200 c/c, 35×105 Oregon (ridge 40×190), corrugated iron roof, suburban
Adelaide (N1). Results and recommendations are in [`REPORT.md`](REPORT.md);
the full generated tables are in [`report/analysis.md`](report/analysis.md).

**This is not a certified design.** It is a transparent, parametric model you can
interrogate. Loads, grade, capacity factor and restraint assumptions are
command-line parameters — check them against the timber actually supplied and
AS 1684 / AS 1720.1 before building.

## Running it

```bash
uv venv .venv && VIRTUAL_ENV=.venv uv pip install -r structural/roof_truss/requirements.txt
.venv/bin/python structural/roof_truss/roof_truss.py            # default case
.venv/bin/python structural/roof_truss/roof_truss.py --all --plots   # support matrix + section sweep + PNGs
.venv/bin/python structural/roof_truss/roof_truss.py --bay 0                 # no cross walls
.venv/bin/python structural/roof_truss/roof_truss.py --section 45x190 --ridge 40x190
.venv/bin/python structural/roof_truss/roof_truss.py --help
```

`frame2d.py` is a ~200-line 2D Euler–Bernoulli frame solver (direct stiffness,
numpy for the linear solve only) with DOF linking so beams in different planes
can share a displacement (the grillage coupling). `roof_truss.py` builds the frame, applies
AS/NZS 1170 load combinations, and runs AS 1720.1 member checks; all the tabular
work (station actions, envelopes, utilisation, report tables) is polars.

## What is modelled

A grillage: `--bays` (3) bays of `--bay` (4000) between cross walls, with
trusses every `--spacing` (1200) starting `--truss-offset` (600) from the first
wall. Each truss is a 2D frame in its own X-Z plane; the two under-purlins and
the ridge beam are continuous 2D beams in the Y-Z plane, supported vertically on
every cross wall, and share their vertical displacement with the truss nodes
they pass (collar nodes, apex). Results are reported for the truss nearest the
middle of the middle bay.

- **Geometry** (centreline): wall supports 8500 apart, rise 2165 mm, rafter
  4770 mm on slope. Collar tie 1000 mm (vertical) below the apex → 3925 mm
  long, meeting the rafter 2567 mm up the slope from the wall.
- **Rafters**: continuous beam elements wall → collar node → apex, 6 elements
  per segment; the two rafters are hinged at the apex (no ridge-beam moment
  continuity, but the ridge supports the apex vertically).
- **Collar tie**: beam element pinned both ends (nailed/bolted lap); carries
  axial force and its own self-weight bending.
- **Ceiling joists** (`--support tie`, default): continuous 12-element beam at
  plate level pinned to the rafter feet, carrying `--ceiling` and a `--qc-point`
  load; `--joist-props N` props it at N equally spaced points (3 = mid wall +
  hanging beams at quarter points, the default; 1 = mid wall only; 0 = none).
  `pinned` / `roller` replace the joists with walls that do / don't resist thrust.
- **Under-purlins** (same section): continuous beams along the building at the
  collar node, supported on the cross walls. `--bay 0` removes the walls (purlins
  become bracing only, trusses independent). `--strutted` is the what-if where
  every collar node is rigidly propped.
- **Ridge beam** (`--ridge` 40x190, `''` for none): same, at the apex.

## Loads (kN, m; AS/NZS 1170)

| Load | Default | Note |
|---|---|---|
| Sheeting + battens `--g-roof` | 0.10 kPa on slope area | corrugated steel ~0.05 + battens; rafter/collar self-weight added automatically (550 kg/m³) |
| Roof live `--q-roof` | 0.25 kPa on plan | AS 1170.1 R2 non-trafficable, area ≥ 14 m² |
| Concentrated live `--q-point` | 1.4 kN | mid lower-rafter segment (worst position) |
| Ceiling lining `--ceiling` | 0.12 kPa on plan | plasterboard + battens, on the joists |
| Ceiling concentrated `--qc-point` | 0.9 kN | mid first joist span (AS 1684 ceiling-joist basis) |
| Wind uplift `--wind-up` | −0.58 kPa net, both slopes | N1, suburban Adelaide (q_u 0.69 kPa, leeward C_pe −0.6, C_pi +0.2); N2 = −0.8 |
| Wind down `--wind-down` | +0.43 kPa net, both slopes | conservative; N2 = 0.6 |
| Wind asymmetric `--wind-asym` | +0.36 / −0.58 kPa | windward pressure with internal suction, leeward uplift; N2 = 0.5 / −0.8 |
| Serviceability wind `--ws-ratio` | 0.58 × ultimate | (26/34)² |

Combinations: 1.35G · 1.2G+1.5Q · 1.2G+1.5Q_point · 1.2G+1.5Q_ceiling · 1.2G+W_down · 0.9G+W_up ·
1.2G+W_asym · 0.9G+W_asym. Serviceability: G long-term (×j₂ = 3, unseasoned),
0.7Q, W_s. Wind class N2 scales all wind pressures by (40/34)² ≈ 1.39, N3 by 2.16.

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
  the collar uses its full length / (`--collar-restraints` + 1); joists their
  propped span; purlins/ridge the bay (top edge held by the rafters every 1200).
- Checks per station: bending, shear, combined bending + compression
  (cl 3.5.1, both expressions), bending + tension (cl 3.5.2). `util` is the
  worst demand/capacity ratio; > 1.0 fails. Once M*/Md exceeds 1 the squared
  interaction term is replaced by the linear ratio so "times over" stays
  readable.
- Collar-tie connection: rough 3.15 mm nail count from Table 4.1(B) J4 values
  (φ 0.80, k17 for multiple nails). Bolts to be designed separately.

## Known simplifications

- Point loads placed at the nearest node; eaves overhang,
  birdsmouth notch and ridge board ignored (the notch reduces capacity at the
  heel — a real design must check it).
- No load sharing (k9 = 1.0) — at 1200 c/c the battens don't share much.
- Purlin/ridge bearing on the cross walls and the rafter-to-purlin fixings are not checked.
- One truss-plane model: no bracing / longitudinal stability check.
