#!/usr/bin/env python
"""Structural analysis of a coupled-rafter "truss" (2 rafters + collar tie) with
under-purlins at the collar node — AS 1720.1 timber checks, AS/NZS 1170 loads.

    python roof_truss.py                       # default case: 8.5 m, 27 deg, 35x105 F7 Oregon
    python roof_truss.py --all                 # support-condition matrix + section sweep
    python roof_truss.py --support tie --strutted --section 45x140
    python roof_truss.py --help

Outputs a plain-text/markdown report to stdout; --plots writes BMD / deflection
PNGs to --out. Tabular work is polars; the stiffness solve is numpy (frame2d.py).

THIS IS AN INDICATIVE ANALYSIS, not a certified design. Wind pressures, grade,
capacity factor and restraint assumptions are parameters — check them against
the site (wind class), the timber actually supplied, and AS 1684 / AS 1720.1.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass

import numpy as np
import polars as pl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame2d import Frame, LoadCase  # noqa: E402

# ----------------------------------------------------------------------------
# Materials — AS 1720.1-2010 Table H2.1 characteristic values (MPa).
# Oregon (Douglas fir) is sold unseasoned, visually graded F5/F7/F8 (F8 = select).
# ----------------------------------------------------------------------------
GRADES = {
    #        f'b    f't   f's   f'c    E
    "F4":  dict(fb=12.0, ft=7.4, fs=1.3, fc=9.7, E=6100),
    "F5":  dict(fb=14.0, ft=8.4, fs=1.5, fc=12.0, E=6900),
    "F7":  dict(fb=18.0, ft=11.0, fs=1.7, fc=13.0, E=7900),
    "F8":  dict(fb=22.0, ft=13.0, fs=2.2, fc=18.0, E=9100),
    "F11": dict(fb=31.0, ft=18.0, fs=2.5, fc=24.0, E=10500),
}


@dataclass
class Section:
    b: float   # breadth (mm) — across the truss
    d: float   # depth (mm) — in the plane of bending

    @property
    def A(self): return self.b * self.d
    @property
    def Z(self): return self.b * self.d ** 2 / 6
    @property
    def I(self): return self.b * self.d ** 3 / 12
    def __str__(self): return f"{self.b:g}x{self.d:g}"


def k12_from(rho_S: float) -> float:
    """AS 1720.1 cl 3.2.4 / 3.3.3 stability factor from rho*S."""
    if rho_S <= 10:
        return 1.0
    if rho_S <= 20:
        return 1.5 - 0.05 * rho_S
    return 200.0 / rho_S ** 2


def rho_b(E, fb, r, seasoned):
    return (11.39 * (E / fb) ** -0.408 * r ** -0.074 if seasoned
            else 14.71 * (E / fb) ** -0.480 * r ** -0.061)


def rho_c(E, fc, r, seasoned):
    return (11.39 * (E / fc) ** -0.408 * r ** -0.074 if seasoned
            else 9.29 * (E / fc) ** -0.367 * r ** -0.146)


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------
class RoofTruss:
    def __init__(self, a):
        self.a = a
        self.sec = Section(*a.section)
        self.grade = GRADES[a.grade]
        th = math.radians(a.pitch)
        self.th = th
        half = a.span / 2
        rise = half * math.tan(th)
        yc = rise - a.collar_drop
        if yc <= 0:
            raise SystemExit("collar tie is below the wall plate — check --collar-drop")
        xc = half - yc / math.tan(th)         # horizontal half-length of collar (from centre)
        self.rise, self.yc, self.xc = rise, yc, xc
        self.L_rafter = half / math.cos(th)
        self.L_lower = (half - xc) / math.cos(th)   # wall -> collar node
        self.L_upper = xc / math.cos(th)            # collar node -> apex
        self.L_collar = 2 * xc

        fr = Frame()
        E, A, I = self.grade["E"], self.sec.A, self.sec.I
        n1, n2 = 6, 6                                   # elements per rafter segment (even)
        self.wall_L = fr.node(0, 0)
        self.wall_R = fr.node(a.span, 0)

        def rafter(x0, y0, x1, y1, n, rot_start, label):
            """chain of n beam elements from (x0,y0) to (x1,y1); returns (end node, end rot)"""
            prev, rot = None, rot_start
            ids = []
            for k in range(1, n + 1):
                nd = fr.node(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) if k < n else None
                ids.append(nd)
            return ids

        # left rafter: wall -> collar -> apex (continuous)
        self.rafter_elems = {"L": [], "R": []}
        xs = [(0, 0)] + [((half - xc) * k / n1, yc * k / n1) for k in range(1, n1)] + [(half - xc, yc)]
        xs += [((half - xc) + xc * k / n2, yc + (rise - yc) * k / n2) for k in range(1, n2)] + [(half, rise)]
        nodes_L = [self.wall_L] + [fr.node(x, y) for x, y in xs[1:]]
        rots_L = [fr.new_rot() for _ in nodes_L]          # one rotation per node: continuous rafter
        self.collar_L = nodes_L[n1]
        self.apex = nodes_L[-1]
        self.midlow_L = nodes_L[n1 // 2]
        for i in range(len(nodes_L) - 1):
            seg = "lower" if i < n1 else "upper"
            self.rafter_elems["L"].append(
                fr.beam(nodes_L[i], nodes_L[i + 1], E, A, I, rots_L[i], rots_L[i + 1],
                        "rafter", f"rafter L {seg}"))
        # right rafter: apex -> collar -> wall; its own apex rotation = hinge between the rafters
        xs_R = [(a.span - x, y) for x, y in reversed(xs)]   # apex ... wall R
        nodes_R = [self.apex] + [fr.node(x, y) for x, y in xs_R[1:-1]] + [self.wall_R]
        rots_R = [fr.new_rot() for _ in nodes_R]
        self.collar_R = nodes_R[n2]
        for i in range(len(nodes_R) - 1):
            seg = "upper" if i < n2 else "lower"
            self.rafter_elems["R"].append(
                fr.beam(nodes_R[i], nodes_R[i + 1], E, A, I, rots_R[i], rots_R[i + 1],
                        "rafter", f"rafter R {seg}"))
        # collar tie: pinned both ends (nailed/bolted lap — no moment continuity)
        self.collar_elem = fr.beam(self.collar_L, self.collar_R, E, A, I,
                                   fr.new_rot(), fr.new_rot(), "collar", "collar tie")
        self.tie_elems: list[int] = []
        self.tie_nodes: list[int] = []
        self.prop_nodes: list[int] = []
        # supports
        fr.fix(self.wall_L, "x", "y")
        if a.support == "pinned":
            fr.fix(self.wall_R, "x", "y")
        else:
            fr.fix(self.wall_R, "y")
            if a.support == "tie":
                # ceiling joist: continuous beam wall->wall, pinned to the rafter feet,
                # optionally propped at a.joist_props equally spaced points
                nt = 12
                self.tie_nodes = [self.wall_L] + [fr.node(a.span * k / nt, 0) for k in range(1, nt)] + [self.wall_R]
                rots = [fr.new_rot() for _ in self.tie_nodes]
                for i in range(nt):
                    self.tie_elems.append(fr.beam(self.tie_nodes[i], self.tie_nodes[i + 1], E, A, I,
                                                  rots[i], rots[i + 1], "tie", "ceiling joist"))
                if a.joist_props:
                    if nt % (a.joist_props + 1):
                        raise SystemExit("--joist-props must be 1, 2, 3, 5 or 11 (12 joist elements)")
                    step = nt // (a.joist_props + 1)
                    for k in range(1, a.joist_props + 1):
                        nd = self.tie_nodes[k * step]
                        fr.fix(nd, "y")
                        self.prop_nodes.append(nd)
                self.L_joist = a.span / (a.joist_props + 1)
        if a.strutted:                       # under-purlin strutted down to a wall/beam
            fr.fix(self.collar_L, "y")
            fr.fix(self.collar_R, "y")
        self.fr = fr
        self.n1, self.n2 = n1, n2

    # ---- loads (N, mm) ----------------------------------------------------
    def load_cases(self):
        a, fr = self.a, self.fr
        sp = a.spacing
        kpa = 1e-3                                   # kPa -> N/mm^2
        sw = a.density * 9.81e-9 * self.sec.A        # N/mm self weight
        G = LoadCase("G")
        for idx in range(len(fr.elements)):
            G.w_v[idx] = -sw
        for side in "LR":
            for idx in self.rafter_elems[side]:
                G.w_v[idx] -= a.g_roof * kpa * sp    # sheeting+battens, on slope area
        for idx in self.tie_elems:
            G.w_v[idx] -= a.ceiling * kpa * sp           # ceiling lining on plan area
        Q = LoadCase("Q")
        for side in "LR":
            for idx in self.rafter_elems[side]:
                Q.w_v[idx] = -a.q_roof * kpa * math.cos(self.th) * sp   # plan-area load
        Qp = LoadCase("Qp", P={self.midlow_L: (0.0, -a.q_point)})
        Qc = LoadCase("Qc")                              # ceiling maintenance point load
        if self.tie_elems:
            step = 12 // (a.joist_props + 1)
            Qc.P[self.tie_nodes[step // 2]] = (0.0, -a.qc_point)   # mid first joist span

        def wind(name, p_left, p_right):            # net pressure onto roof surface (kPa, +down)
            w = LoadCase(name)
            for idx in self.rafter_elems["L"]:
                w.q_n[idx] = -p_left * kpa * sp      # local +y is the outward normal
            for idx in self.rafter_elems["R"]:
                w.q_n[idx] = -p_right * kpa * sp
            return w
        Wu = wind("Wu", a.wind_up, a.wind_up)
        Wd = wind("Wd", a.wind_down, a.wind_down)
        Wa = wind("Wa", a.wind_asym[0], a.wind_asym[1])
        return dict(G=G, Q=Q, Qp=Qp, Qc=Qc, Wu=Wu, Wd=Wd, Wa=Wa)

    def combos(self):
        lc = self.load_cases()
        rs = self.a.ws_ratio
        uls = [  # name, loadcase, k1, r (temporary/total load ratio for rho)
            ("1.35G", lc["G"].scaled(1.35), 0.57, 0.25),
            ("1.2G+1.5Q", lc["G"].scaled(1.2) + lc["Q"].scaled(1.5), 0.94, 0.25),
            ("1.2G+1.5Qp", lc["G"].scaled(1.2) + lc["Qp"].scaled(1.5), 0.97, 0.25),
            ("1.2G+1.5Qc", lc["G"].scaled(1.2) + lc["Qc"].scaled(1.5), 0.97, 0.25),
            ("1.2G+Wd", lc["G"].scaled(1.2) + lc["Wd"], 1.0, 1.0),
            ("0.9G+Wu", lc["G"].scaled(0.9) + lc["Wu"], 1.0, 1.0),
            ("1.2G+Wa", lc["G"].scaled(1.2) + lc["Wa"], 1.0, 1.0),
            ("0.9G+Wa", lc["G"].scaled(0.9) + lc["Wa"], 1.0, 1.0),
        ]
        sls = [  # name, loadcase, j2 creep factor applied to the whole case
            ("G long-term", lc["G"], self.a.j2),
            ("0.7Q short-term", lc["Q"].scaled(0.7), 1.0),
            ("Ws uplift", lc["Wu"].scaled(rs), 1.0),
        ]
        return uls, sls

    # ---- analysis ------------------------------------------------------------
    def member_meta(self) -> pl.DataFrame:
        """Per-element restraint lengths used for k12 (mm)."""
        a, fr = self.a, self.fr
        rows = []
        for idx, e in enumerate(fr.elements):
            L = fr.length(e)
            if e.group == "rafter":
                seg = self.L_lower if "lower" in e.tag else self.L_upper
                rows.append(dict(elem=idx, group=e.group, tag=e.tag, L=L,
                                 Lay_sag=min(a.battens, seg),   # top (compression) edge: battens
                                 Lay_hog=seg,                   # bottom edge: nodes only
                                 Lax_c=seg, Lay_c=min(a.battens, seg)))
            elif e.group == "collar":
                Lr = self.L_collar / (a.collar_restraints + 1)
                rows.append(dict(elem=idx, group=e.group, tag=e.tag, L=L,
                                 Lay_sag=Lr, Lay_hog=Lr, Lax_c=self.L_collar, Lay_c=Lr))
            else:  # ceiling joist: top edge restrained only at props, bottom edge by ceiling battens
                Lj = self.L_joist
                rows.append(dict(elem=idx, group=e.group, tag=e.tag, L=L,
                                 Lay_sag=Lj, Lay_hog=min(a.ceiling_battens, Lj),
                                 Lax_c=Lj, Lay_c=min(a.ceiling_battens, Lj)))
        return pl.DataFrame(rows)

    def run_uls(self) -> tuple[pl.DataFrame, pl.DataFrame]:
        """Returns (station-level actions+checks, reactions) for all ULS combos."""
        a, fr, g, sec = self.a, self.fr, self.grade, self.sec
        meta = self.member_meta()
        uls, _ = self.combos()
        frames, reacts = [], []
        for name, lc, k1, r in uls:
            res = fr.solve(lc)
            for idx, e in enumerate(fr.elements):
                s, N, V, M = res.actions(idx, 11)
                (x1, y1), (x2, y2) = fr.nodes[e.ni], fr.nodes[e.nj]
                L = fr.length(e)
                frames.append(pl.DataFrame(dict(
                    combo=name, k1=k1, r=r, elem=idx,
                    s=s, x=x1 + (x2 - x1) * s / L, y=y1 + (y2 - y1) * s / L,
                    N=N, V=V, M=M)))
            for nd, lab in ([(self.wall_L, "wall L"), (self.wall_R, "wall R"),
                             (self.collar_L, "strut L"), (self.collar_R, "strut R")]
                            + [(nd, f"joist prop {k+1}") for k, nd in enumerate(self.prop_nodes)]):
                Rx, Ry = res.reaction(nd)
                if abs(Rx) > 1e-6 or abs(Ry) > 1e-6:
                    reacts.append(dict(combo=name, support=lab, H_kN=Rx / 1e3, V_kN=Ry / 1e3))
        df = pl.concat(frames).join(meta, on="elem")

        # --- AS 1720.1 capacities, row-wise (vectorised with polars) -------------
        phi, k4, k6, k9 = a.phi, 1.0, 1.0, a.k9
        seas = a.seasoned
        E, fb, ft, fc, fs = g["E"], g["fb"], g["ft"], g["fc"], g["fs"]
        rb = pl.col("r").map_elements(lambda r_: rho_b(E, fb, r_, seas), return_dtype=pl.Float64)
        rc = pl.col("r").map_elements(lambda r_: rho_c(E, fc, r_, seas), return_dtype=pl.Float64)
        k12f = lambda expr: expr.map_elements(k12_from, return_dtype=pl.Float64)  # noqa: E731
        d, b = sec.d, sec.b
        S1_sag = 1.25 * (d / b) * (pl.col("Lay_sag") / d) ** 0.5
        S1_hog = 1.25 * (d / b) * (pl.col("Lay_hog") / d) ** 0.5
        S1 = pl.when(pl.col("M") >= 0).then(S1_sag).otherwise(S1_hog)
        S3 = pl.col("Lax_c") / d
        S4 = pl.col("Lay_c") / b
        df = df.with_columns([
            (rb * S1).alias("rhoS1"), (rc * S3).alias("rhoS3"), (rc * S4).alias("rhoS4"),
        ]).with_columns([
            k12f(pl.col("rhoS1")).alias("k12b"),
            k12f(pl.col("rhoS3")).alias("k12cx"),
            k12f(pl.col("rhoS4")).alias("k12cy"),
        ])
        base = phi * pl.col("k1") * k4 * k6
        df = df.with_columns([
            (base * k9 * pl.col("k12b") * fb * sec.Z).alias("Md"),
            (base * ft * sec.A).alias("Nt"),
            (base * pl.col("k12cx") * fc * sec.A).alias("Ncx"),
            (base * pl.col("k12cy") * fc * sec.A).alias("Ncy"),
            (base * fs * (2 / 3) * sec.A).alias("Vd"),
        ])
        Mr = pl.col("M").abs() / pl.col("Md")
        Nc = (-pl.col("N")).clip(lower_bound=0)
        Ntn = pl.col("N").clip(lower_bound=0)
        df = df.with_columns([
            Mr.alias("u_bend"),
            (pl.col("V").abs() / pl.col("Vd")).alias("u_shear"),
            # cl 3.5.1 combined bending + compression (both expressions), cl 3.5.2 bending + tension
            pl.max_horizontal(Mr ** 2 + Nc / pl.col("Ncy"), Mr + Nc / pl.col("Ncx")).alias("u_comb_c"),
            (Mr + Ntn / pl.col("Nt")).alias("u_comb_t"),
        ]).with_columns(
            pl.max_horizontal("u_bend", "u_shear", "u_comb_c", "u_comb_t").alias("util")
        )
        return df, pl.DataFrame(reacts)

    def run_sls(self) -> pl.DataFrame:
        a, fr = self.a, self.fr
        _, sls = self.combos()
        rows = []
        th = self.th
        for name, lc, j2 in sls:
            res = fr.solve(lc)
            # rafter deflection normal to the wall->apex chord, left rafter
            nL = [e for e in self.rafter_elems["L"]]
            nodes = [fr.elements[nL[0]].ni] + [fr.elements[i].nj for i in nL]
            x0, y0 = fr.nodes[nodes[0]]
            ux0, uy0 = res.disp(nodes[0])
            xa, ya = fr.nodes[nodes[-1]]
            uxa, uya = res.disp(nodes[-1])
            best = 0.0
            for nd in nodes[1:-1]:
                x, y = fr.nodes[nd]
                ux, uy = res.disp(nd)
                t = ((x - x0) * (xa - x0) + (y - y0) * (ya - y0)) / ((xa - x0) ** 2 + (ya - y0) ** 2)
                # chord displacement interpolated between the deformed ends
                cx, cy = ux0 + t * (uxa - ux0), uy0 + t * (uya - uy0)
                dn = -(ux - cx) * math.sin(th) + (uy - cy) * math.cos(th)   # normal (outward +)
                best = dn if abs(dn) > abs(best) else best
            # lower-segment mid-point relative to its own ends (strutted case)
            seg_nodes = nodes[: self.n1 + 1]
            xs0, ys0 = fr.nodes[seg_nodes[0]]; u0 = res.disp(seg_nodes[0])
            xs1, ys1 = fr.nodes[seg_nodes[-1]]; u1 = res.disp(seg_nodes[-1])
            um = res.disp(seg_nodes[self.n1 // 2])
            cmx, cmy = (u0[0] + u1[0]) / 2, (u0[1] + u1[1]) / 2
            dseg = -(um[0] - cmx) * math.sin(th) + (um[1] - cmy) * math.cos(th)
            apex = res.disp(self.apex)[1]
            spread = res.disp(self.wall_R)[0]
            cl, cr = res.disp(self.collar_L), res.disp(self.collar_R)
            collar_sag = 0.0
            if self.collar_elem is not None:
                # mid-span sag of the pinned collar under its own weight (closed form on the member)
                p, q = fr._local_udl(self.collar_elem, lc)
                Lc = self.L_collar
                collar_sag = 5 * q * Lc ** 4 / (384 * self.grade["E"] * self.sec.I)
            tie_sag = 0.0
            if self.tie_elems:  # worst vertical joist displacement (props/walls are at 0)
                ys = [res.disp(nd)[1] for nd in self.tie_nodes]
                tie_sag = min(ys) if abs(min(ys)) > abs(max(ys)) else max(ys)
            rows.append(dict(case=name, j2=j2,
                             rafter_mm=best * j2, lower_seg_mm=dseg * j2, apex_mm=apex * j2,
                             spread_mm=spread * j2, collar_shorten_mm=(cr[0] - cl[0]) * j2,
                             collar_sag_mm=collar_sag * j2, joist_sag_mm=tie_sag * j2))
        return pl.DataFrame(rows)


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------
def md(df: pl.DataFrame, fmt: dict[str, str] | None = None) -> str:
    """polars DataFrame -> markdown table."""
    fmt = fmt or {}
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.iter_rows(named=True):
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                cells.append(format(v, fmt.get(c, ".2f")))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def summarise(df: pl.DataFrame) -> pl.DataFrame:
    """Worst utilisation per member group x combo."""
    return (df.group_by(["group", "combo"])
              .agg(pl.col("util").max().alias("util"),
                   (pl.col("M").abs().max() / 1e6).alias("|M| kNm"),
                   (pl.col("N").max() / 1e3).alias("N max kN"),
                   (pl.col("N").min() / 1e3).alias("N min kN"),
                   (pl.col("Md").min() / 1e6).alias("Md kNm"),
                   pl.col("k12b").min().alias("k12b min"),
                   pl.col("k12cy").min().alias("k12cy"))
              .sort(["group", "combo"]))


def governing(df: pl.DataFrame) -> pl.DataFrame:
    return (df.sort("util", descending=True)
              .group_by("group", maintain_order=True).first()
              .select(["group", "combo", "tag", "x", "util", "u_bend", "u_comb_c", "u_comb_t",
                       "M", "N", "Md", "Ncx", "Ncy", "Nt", "k12b", "k12cx", "k12cy"])
              .with_columns([(pl.col("M") / 1e6).alias("M"), (pl.col("N") / 1e3).alias("N"),
                             (pl.col("Md") / 1e6).alias("Md"), (pl.col("Ncx") / 1e3).alias("Ncx"),
                             (pl.col("Ncy") / 1e3).alias("Ncy"), (pl.col("Nt") / 1e3).alias("Nt")]))


def connection_note(df: pl.DataFrame, a) -> str:
    """Rough nail count for the collar-tie lap from the worst axial force."""
    col = df.filter(pl.col("group") == "collar")
    if col.is_empty():
        return ""
    worst = col.sort(pl.col("N").abs(), descending=True).row(0, named=True)
    Nstar = abs(worst["N"]) / 1e3
    Qk, phi_n = a.nail_qk, 0.80
    n = math.ceil(Nstar / (phi_n * worst["k1"] * Qk)) if Nstar > 0 else 0
    k17 = 1.0 if n <= 4 else (0.94 if n <= 7 else (0.88 if n <= 11 else 0.80))
    n = math.ceil(Nstar / (phi_n * worst["k1"] * k17 * Qk)) if Nstar > 0 else 0
    kind = "tension" if worst["N"] > 0 else "compression"
    return (f"Collar-tie lap connection: N* = {Nstar:.2f} kN ({kind}, {worst['combo']}). "
            f"With 3.15 mm nails in J4 Oregon (Q_k ≈ {Qk} kN, φ = 0.80, k1 = {worst['k1']}, "
            f"k17 = {k17}) that is ≈ {n} nails each end; or design an M12 bolt + washers.")


def plot_case(model: RoofTruss, df: pl.DataFrame, sls: pl.DataFrame, title: str, path: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fr = model.fr
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    # frame + BMD for the governing combo
    gov = df.sort("util", descending=True).row(0, named=True)["combo"]
    sub = df.filter(pl.col("combo") == gov)
    ax = axes[0]
    for e in fr.elements:
        (x1, y1), (x2, y2) = fr.nodes[e.ni], fr.nodes[e.nj]
        ax.plot([x1, x2], [y1, y2], color="#6b4f2a", lw=3, solid_capstyle="round")
    Mmax = max(abs(sub["M"].min()), abs(sub["M"].max()), 1.0)
    scale = 600.0 / Mmax
    for idx, e in enumerate(fr.elements):
        rows = sub.filter(pl.col("elem") == idx).sort("s")
        ang = fr.angle(e)
        nx, ny = -math.sin(ang), math.cos(ang)
        xs = rows["x"].to_numpy(); ys = rows["y"].to_numpy(); Ms = rows["M"].to_numpy()
        # draw M on the tension side: sagging (+) -> below (local -y)
        ax.fill(np.r_[xs, xs[::-1]], np.r_[ys, (ys - ny * Ms * scale)[::-1]],
                color="#d9534f", alpha=0.35, lw=0)
    for nd, lab in ((model.wall_L, "wall"), (model.wall_R, "wall")):
        x, y = fr.nodes[nd]
        ax.plot(x, y, marker="^", ms=12, color="k")
    if model.a.strutted:
        for nd in (model.collar_L, model.collar_R):
            x, y = fr.nodes[nd]
            ax.plot([x, x], [y, 0], ls="--", color="gray"); ax.plot(x, 0, marker="^", ms=10, color="gray")
    for nd in model.prop_nodes:
        x, y = fr.nodes[nd]
        ax.plot(x, y, marker="^", ms=10, color="gray", clip_on=False)
    ax.set_aspect("equal"); ax.set_title(f"{title}\nbending moment, governing ULS combo: {gov} "
                                         f"(|M|max = {Mmax/1e6:.2f} kNm)")
    ax.set_xlabel("mm"); ax.set_ylabel("mm"); ax.grid(alpha=.3)
    # deflected shape (long-term G)
    ax = axes[1]
    lc = model.combos()[1][0][1]
    res = fr.solve(lc)
    j2 = model.a.j2
    amp = 20.0
    for e in fr.elements:
        (x1, y1), (x2, y2) = fr.nodes[e.ni], fr.nodes[e.nj]
        ax.plot([x1, x2], [y1, y2], color="#bbb", lw=1.5)
        u1, u2 = res.disp(e.ni), res.disp(e.nj)
        ax.plot([x1 + amp * j2 * u1[0], x2 + amp * j2 * u2[0]],
                [y1 + amp * j2 * u1[1], y2 + amp * j2 * u2[1]], color="#2a6fb0", lw=2.5)
    r = sls.filter(pl.col("case") == "G long-term").row(0, named=True)
    ax.set_aspect("equal"); ax.grid(alpha=.3)
    ax.set_title(f"long-term dead-load deflection x{amp:g} (j2={j2:g}): rafter {r['rafter_mm']:.1f} mm, "
                 f"apex {r['apex_mm']:.1f} mm, wall spread {r['spread_mm']:.1f} mm, joist {r['joist_sag_mm']:.1f} mm")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def run_one(a, title: str | None = None, plots_dir: str | None = None, tag: str = "") -> dict:
    m = RoofTruss(a)
    df, reacts = m.run_uls()
    sls = m.run_sls()
    gov = governing(df)
    title = title or f"{a.support} supports{' + strutted purlins' if a.strutted else ''}"
    lines = [f"### {title} — {m.sec} {a.grade}, span {a.span:g}, pitch {a.pitch:g}°, "
             f"trusses @ {a.spacing:g} c/c", ""]
    lines += ["Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):", "",
              md(gov.select(["group", "combo", "tag", "util", "M", "Md", "N", "Ncx", "Ncy", "Nt",
                             "k12b", "k12cy"])
                 .rename({"M": "M* kNm", "Md": "Md kNm", "N": "N* kN", "Ncx": "Ncx kN",
                          "Ncy": "Ncy kN", "Nt": "Nt kN"})), ""]
    lines += ["Support reactions per truss (kN; H = horizontal thrust the wall must resist):", "",
              md(reacts.group_by("support").agg(
                  pl.col("H_kN").abs().max().alias("|H| max"),
                  pl.col("V_kN").max().alias("V max (down)"),
                  pl.col("V_kN").min().alias("V min (uplift if <0)")).sort("support")), ""]
    lim = m.L_rafter / 300
    jl = f", ceiling joist span {m.L_joist:.0f} mm → {m.L_joist/300:.1f} mm" if m.tie_elems else ""
    lines += [f"Serviceability deflections (mm; rafter limit span/300 = {lim:.1f} mm on the "
              f"{m.L_rafter:.0f} mm slope length, lower segment {m.L_lower/300:.1f} mm{jl}):", "",
              md(sls, {"j2": ".0f"}), ""]
    cn = connection_note(df, a)
    if cn:
        lines += [cn, ""]
    if plots_dir:
        os.makedirs(plots_dir, exist_ok=True)
        p = os.path.join(plots_dir, f"{tag or a.support}{'_strutted' if a.strutted else ''}_{m.sec}.png")
        for old in [f for f in os.listdir(plots_dir) if f == os.path.basename(p)]:
            os.remove(os.path.join(plots_dir, old))
        plot_case(m, df, sls, title, p)
        lines += [f"![{title}]({os.path.basename(p)})", ""]
    return dict(model=m, df=df, reacts=reacts, sls=sls, gov=gov, text="\n".join(lines),
                util=gov["util"].max())


def sweep(a, sections: list[tuple[float, float]]) -> pl.DataFrame:
    rows = []
    for b, d in sections:
        aa = argparse.Namespace(**vars(a)); aa.section = (b, d)
        m = RoofTruss(aa)
        df, reacts = m.run_uls(); sls = m.run_sls()
        g = governing(df)
        raf = g.filter(pl.col("group") == "rafter").row(0, named=True)
        col = g.filter(pl.col("group") == "collar").row(0, named=True)
        G = sls.filter(pl.col("case") == "G long-term").row(0, named=True)
        tie = g.filter(pl.col("group") == "tie")
        rows.append({"section": str(m.sec), "rafter util": raf["util"], "rafter combo": raf["combo"],
                     "collar util": col["util"],
                     "joist util": tie["util"][0] if tie.height else float("nan"),
                     "rafter δG mm": abs(G["rafter_mm"]), "joist δG mm": abs(G["joist_sag_mm"]),
                     "H wall kN": reacts["H_kN"].abs().max()})
    return pl.DataFrame(rows)


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_argument_group("geometry (mm, deg)")
    g.add_argument("--span", type=float, default=8500, help="between wall supports")
    g.add_argument("--pitch", type=float, default=27)
    g.add_argument("--spacing", type=float, default=1200, help="truss centres")
    g.add_argument("--collar-drop", type=float, default=1000, help="collar tie below the apex (vertical)")
    g.add_argument("--section", type=lambda s: tuple(float(v) for v in s.lower().split("x")),
                   default=(35, 105), help="b x d, e.g. 35x105 (all members)")
    g.add_argument("--support", choices=["pinned", "roller", "tie"], default="tie",
                   help="tie: ceiling joists (same section) tie the rafter feet [default]; "
                        "pinned: both walls resist thrust; roller: one wall free to spread")
    g.add_argument("--joist-props", type=int, default=0,
                   help="intermediate vertical supports under the ceiling joists (internal wall / "
                        "hanging beam): 1 = mid-span, 2 = third points, 3 = quarter points")
    g.add_argument("--ceiling-battens", type=float, default=450, help="ceiling batten spacing (joist bottom-edge restraint)")
    g.add_argument("--strutted", action="store_true", help="under-purlins strutted to a wall/beam below")
    g.add_argument("--battens", type=float, default=900, help="batten spacing (top-edge restraint)")
    g.add_argument("--collar-restraints", type=int, default=0, help="intermediate lateral restraints on collar")
    t = ap.add_argument_group("timber (AS 1720.1)")
    t.add_argument("--grade", choices=sorted(GRADES), default="F7")
    t.add_argument("--seasoned", action="store_true", help="use seasoned rho_b/rho_c (default unseasoned Oregon)")
    t.add_argument("--density", type=float, default=550, help="kg/m3")
    t.add_argument("--phi", type=float, default=0.70, help="capacity factor (Table 2.1, F-grade sawn, category 2)")
    t.add_argument("--k9", type=float, default=1.0)
    t.add_argument("--j2", type=float, default=3.0, help="creep factor for long-term deflection (unseasoned)")
    t.add_argument("--nail-qk", type=float, default=0.515, help="kN, 3.15 mm nail, J4 (Table 4.1(B))")
    l = ap.add_argument_group("loads (kPa, AS/NZS 1170)")
    l.add_argument("--g-roof", type=float, default=0.10, help="sheeting+battens on slope area (timber SW added)")
    l.add_argument("--ceiling", type=float, default=0.12, help="ceiling lining on the joists (plan; plasterboard+battens)")
    l.add_argument("--qc-point", type=float, default=900, help="N, concentrated load on a ceiling joist (AS 1684 basis)")
    l.add_argument("--q-roof", type=float, default=0.25, help="roof live load on plan (R2, ≥14 m2)")
    l.add_argument("--q-point", type=float, default=1400, help="N, concentrated roof live load")
    l.add_argument("--wind-up", type=float, default=-0.8, help="net ULS pressure onto roof, both slopes (N2 indicative)")
    l.add_argument("--wind-down", type=float, default=0.6)
    l.add_argument("--wind-asym", type=lambda s: tuple(float(v) for v in s.split(",")), default=(0.5, -0.8),
                   help="windward,leeward net pressures")
    l.add_argument("--ws-ratio", type=float, default=0.42, help="serviceability/ultimate wind pressure ratio")
    o = ap.add_argument_group("output")
    o.add_argument("--all", action="store_true", help="run the support matrix + section sweep")
    o.add_argument("--plots", action="store_true")
    o.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "report"))
    o.add_argument("--detail", action="store_true", help="also print the per-combo member table")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse(argv)
    pl.Config.set_tbl_rows(100); pl.Config.set_tbl_cols(30); pl.Config.set_tbl_width_chars(220)
    plots = a.out if a.plots else None
    m0 = RoofTruss(a)
    print(f"# Roof truss analysis — span {a.span:g} mm, pitch {a.pitch:g}°, {m0.sec} {a.grade} Oregon, "
          f"trusses @ {a.spacing:g} c/c\n")
    print(f"Geometry: rise {m0.rise:.0f} mm, rafter {m0.L_rafter:.0f} mm on slope "
          f"(wall→collar {m0.L_lower:.0f}, collar→apex {m0.L_upper:.0f}), "
          f"collar tie {m0.L_collar:.0f} mm long at {m0.yc:.0f} mm above the plate.\n")
    if not a.all:
        r = run_one(a, plots_dir=plots)
        print(r["text"])
        if a.detail:
            print(md(summarise(r["df"])))
        return
    cases = [  # (support, strutted, joist props, title)
        ("tie", False, 0, "ceiling joists tie the feet, joists unsupported, purlins not strutted"),
        ("tie", False, 1, "ceiling joists tie the feet, joists propped mid-span, purlins not strutted"),
        ("tie", True, 1, "ceiling joists propped mid-span + under-purlins strutted"),
        ("tie", True, 2, "ceiling joists propped at third points + under-purlins strutted"),
        ("pinned", False, 0, "no joists: walls resist thrust"),
        ("roller", False, 0, "no joists: one wall free to spread"),
    ]
    for support, strutted, props, title in cases:
        aa = argparse.Namespace(**vars(a)); aa.support = support; aa.strutted = strutted
        aa.joist_props = props
        r = run_one(aa, title=title, plots_dir=plots, tag=f"{support}_p{props}")
        print(r["text"])
        if a.detail:
            print(md(summarise(r["df"])), "\n")
    secs = [(35, 105), (35, 140), (45, 140), (35, 190), (45, 190), (45, 240)]
    print("### Section sweep — joists propped mid-span, purlins NOT strutted\n")
    aa = argparse.Namespace(**vars(a)); aa.support = "tie"; aa.strutted = False; aa.joist_props = 1
    print(md(sweep(aa, secs)), "\n")
    print("### Section sweep — joists propped mid-span + purlins strutted\n")
    aa.strutted = True
    print(md(sweep(aa, secs)), "\n")


if __name__ == "__main__":
    main()
