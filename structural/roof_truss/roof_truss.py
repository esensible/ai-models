#!/usr/bin/env python
"""Structural analysis of a coupled-rafter roof (rafters + collar tie + ceiling
joists) with under-purlins and a ridge beam carried on cross walls — a grillage
of several trusses coupled through the purlins/ridge. AS 1720.1 timber checks,
AS/NZS 1170 loads.

    python roof_truss.py                  # as built: 8.5 m, 27 deg, 35x105 F7, purlins/ridge on 4 m cross walls
    python roof_truss.py --all --plots    # what-if matrix + section sweep + PNGs
    python roof_truss.py --bay 0          # purlins as bracing only (no cross walls)
    python roof_truss.py --help

Units N, mm, MPa. Tabular work is polars; the stiffness solve is numpy (frame2d.py).

THIS IS AN INDICATIVE ANALYSIS, not a certified design.
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

# AS 1720.1-2010 Table H2.1 characteristic values (MPa). Oregon = unseasoned F5/F7/F8.
GRADES = {
    "F4":  dict(fb=12.0, ft=7.4, fs=1.3, fc=9.7, E=6100),
    "F5":  dict(fb=14.0, ft=8.4, fs=1.5, fc=12.0, E=6900),
    "F7":  dict(fb=18.0, ft=11.0, fs=1.7, fc=13.0, E=7900),
    "F8":  dict(fb=22.0, ft=13.0, fs=2.2, fc=18.0, E=9100),
    "F11": dict(fb=31.0, ft=18.0, fs=2.5, fc=24.0, E=10500),
}


@dataclass
class Section:
    b: float   # breadth (mm), out of the bending plane
    d: float   # depth (mm), in the bending plane
    @property
    def A(self): return self.b * self.d
    @property
    def Z(self): return self.b * self.d ** 2 / 6
    @property
    def I(self): return self.b * self.d ** 3 / 12
    def __str__(self): return f"{self.b:g}x{self.d:g}"


def parse_section(s: str) -> tuple[float, float]:
    return tuple(float(v) for v in s.lower().split("x"))


def k12_from(rho_S: float) -> float:
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


class RoofGrillage:
    """N trusses at `spacing` along Y, coupled vertically to under-purlins (at the
    collar node, both sides) and a ridge beam (at the apex), which are continuous
    beams supported on cross walls every `bay`. Each truss is a 2D frame in X-Z;
    the purlins/ridge are 2D beams in Y-Z; they share the Z DOF where they meet."""

    def __init__(self, a):
        self.a = a
        self.sec = Section(*a.section)
        self.sec_ridge = Section(*a.ridge) if a.ridge else None
        self.secs = {"rafter": Section(*a.rafter_section) if a.rafter_section else self.sec,
                     "collar": Section(*a.collar_section) if a.collar_section else self.sec,
                     "tie": Section(*a.joist_section) if a.joist_section else self.sec,
                     "purlin": Section(*a.purlin_section) if a.purlin_section else self.sec,
                     "ridge": self.sec_ridge}
        self.grade = GRADES[a.grade]
        th = math.radians(a.pitch)
        self.th = th
        half = a.span / 2
        rise = half * math.tan(th)
        yc = rise - a.collar_drop
        if yc <= 0:
            raise SystemExit("collar tie is below the wall plate — check --collar-drop")
        xc = half - yc / math.tan(th)
        self.rise, self.yc, self.xc = rise, yc, xc
        self.L_rafter = half / math.cos(th)
        self.L_lower = (half - xc) / math.cos(th)
        self.L_upper = xc / math.cos(th)
        self.L_collar = 2 * xc
        self.n1 = self.n2 = 6
        self.nt = 12

        # truss positions along the building
        if a.bay > 0:
            self.walls_y = [k * a.bay for k in range(a.bays + 1)]
            length = a.bays * a.bay
        else:
            self.walls_y = []
            length = a.spacing
        ys, y = [], a.truss_offset
        while y < length - 1e-6:
            ys.append(y); y += a.spacing
        self.truss_y = ys
        self.mid_truss = min(range(len(ys)), key=lambda i: abs(ys[i] - length / 2))

        fr = Frame()
        self.fr = fr
        self.trusses = [self._build_truss(y) for y in ys]
        self.purlin_elems, self.ridge_elems = [], []
        self.purlin_wall_nodes, self.ridge_wall_nodes = [], []
        if a.bay > 0:
            for side in ("L", "R"):
                self._build_runner([(t["y"], t["collar_" + side]) for t in self.trusses],
                                   self.yc, self.secs["purlin"], "purlin", f"under-purlin {side}",
                                   self.purlin_elems, self.purlin_wall_nodes)
            if self.sec_ridge:
                self._build_runner([(t["y"], t["apex"]) for t in self.trusses],
                                   self.rise, self.sec_ridge, "ridge", "ridge beam",
                                   self.ridge_elems, self.ridge_wall_nodes)
        self.L_joist = a.span / (a.joist_props + 1)

    # --- one truss in the X-Z plane --------------------------------------------
    def _build_truss(self, y: float) -> dict:
        a, fr = self.a, self.fr
        E = self.grade["E"]
        A, I = self.secs["rafter"].A, self.secs["rafter"].I
        Ac, Ic = self.secs["collar"].A, self.secs["collar"].I
        At, It = self.secs["tie"].A, self.secs["tie"].I
        half, rise, yc, xc = a.span / 2, self.rise, self.yc, self.xc
        n1, n2 = self.n1, self.n2
        t = dict(y=y, rafter=[], collar=None, tie=[], props=[])
        t["wall_L"] = fr.node(0, 0)
        t["wall_R"] = fr.node(a.span, 0)
        xs = [(0, 0)] + [((half - xc) * k / n1, yc * k / n1) for k in range(1, n1)] + [(half - xc, yc)]
        xs += [((half - xc) + xc * k / n2, yc + (rise - yc) * k / n2) for k in range(1, n2)] + [(half, rise)]
        nL = [t["wall_L"]] + [fr.node(x, z) for x, z in xs[1:]]
        rL = [fr.new_rot() for _ in nL]
        t["collar_L"], t["apex"], t["midlow_L"] = nL[n1], nL[-1], nL[n1 // 2]
        for i in range(len(nL) - 1):
            seg = "lower" if i < n1 else "upper"
            t["rafter"].append(fr.beam(nL[i], nL[i + 1], E, A, I, rL[i], rL[i + 1], "rafter", f"rafter L {seg}"))
        xsR = [(a.span - x, z) for x, z in reversed(xs)]
        nR = [t["apex"]] + [fr.node(x, z) for x, z in xsR[1:-1]] + [t["wall_R"]]
        rR = [fr.new_rot() for _ in nR]            # own apex rotation -> hinge between rafters
        t["collar_R"] = nR[n2]
        for i in range(len(nR) - 1):
            seg = "upper" if i < n2 else "lower"
            t["rafter"].append(fr.beam(nR[i], nR[i + 1], E, A, I, rR[i], rR[i + 1], "rafter", f"rafter R {seg}"))
        t["collar"] = fr.beam(t["collar_L"], t["collar_R"], E, Ac, Ic, fr.new_rot(), fr.new_rot(),
                              "collar", "collar tie")
        fr.fix(t["wall_L"], "x", "y")
        if a.support == "pinned":
            fr.fix(t["wall_R"], "x", "y")
        else:
            fr.fix(t["wall_R"], "y")
            if a.support == "tie":
                nt = self.nt
                tn = [t["wall_L"]] + [fr.node(a.span * k / nt, 0) for k in range(1, nt)] + [t["wall_R"]]
                rots = [fr.new_rot() for _ in tn]
                for i in range(nt):
                    t["tie"].append(fr.beam(tn[i], tn[i + 1], E, At, It, rots[i], rots[i + 1], "tie", "ceiling joist"))
                t["tie_nodes"] = tn
                if a.joist_props:
                    if nt % (a.joist_props + 1):
                        raise SystemExit("--joist-props must be 1, 2, 3, 5 or 11")
                    step = nt // (a.joist_props + 1)
                    for k in range(1, a.joist_props + 1):
                        fr.fix(tn[k * step], "y"); t["props"].append(tn[k * step])
        if a.strutted:
            fr.fix(t["collar_L"], "y"); fr.fix(t["collar_R"], "y")
        return t

    # --- a continuous beam along Y (purlin / ridge), coupled to truss nodes ------------
    def _build_runner(self, attach: list[tuple[float, int]], z: float, sec: Section,
                      group: str, tag: str, elems: list, wall_nodes: list):
        a, fr = self.a, self.fr
        E = self.grade["E"]
        pts = sorted([(y, nd, False) for y, nd in attach] + [(y, None, True) for y in self.walls_y])
        nodes = []
        for y, nd, is_wall in pts:
            n = fr.node(y, z)                     # plane coords (Y, Z)
            nodes.append(n)
            if is_wall:
                fr.fix(n, "y"); wall_nodes.append(n)
            else:
                fr.link(n, nd, "y")               # share vertical displacement with the truss
        fr.fix(nodes[0], "x")                     # along-Y rigid body freedom
        rots = [fr.new_rot() for _ in nodes]
        for i in range(len(nodes) - 1):
            if fr.nodes[nodes[i + 1]][0] - fr.nodes[nodes[i]][0] < 1e-6:
                fr.link(nodes[i + 1], nodes[i], "x"); continue
            elems.append(fr.beam(nodes[i], nodes[i + 1], E, sec.A, sec.I, rots[i], rots[i + 1], group, tag))

    # --- loads -------------------------------------------------------------------
    def load_cases(self):
        a, fr = self.a, self.fr
        sp, kpa = a.spacing, 1e-3
        G, Q, Qp, Qc = LoadCase("G"), LoadCase("Q"), LoadCase("Qp"), LoadCase("Qc")
        for idx, e in enumerate(fr.elements):
            G.w_v[idx] = -a.density * 9.81e-9 * self.secs[e.group].A   # self weight
        for t in self.trusses:
            for idx in t["rafter"]:
                G.w_v[idx] -= a.g_roof * kpa * sp                   # sheeting+battens on slope area
                Q.w_v[idx] = -a.q_roof * kpa * math.cos(self.th) * sp
            for idx in t["tie"]:
                G.w_v[idx] -= a.ceiling * kpa * sp
        tm = self.trusses[self.mid_truss]
        Qp.P[tm["midlow_L"]] = (0.0, -a.q_point)
        if tm["tie"]:
            step = self.nt // (a.joist_props + 1)
            Qc.P[tm["tie_nodes"][step // 2]] = (0.0, -a.qc_point)

        def wind(name, pL, pR):   # net pressure onto the roof surface (kPa, +down)
            w = LoadCase(name)
            for t in self.trusses:
                for i, idx in enumerate(t["rafter"]):
                    w.q_n[idx] = -(pL if i < self.n1 + self.n2 else pR) * kpa * sp
            return w
        return dict(G=G, Q=Q, Qp=Qp, Qc=Qc, Wu=wind("Wu", a.wind_up, a.wind_up),
                    Wd=wind("Wd", a.wind_down, a.wind_down), Wa=wind("Wa", *a.wind_asym))

    def combos(self):
        lc = self.load_cases()
        uls = [
            ("1.35G", lc["G"].scaled(1.35), 0.57, 0.25),
            ("1.2G+1.5Q", lc["G"].scaled(1.2) + lc["Q"].scaled(1.5), 0.94, 0.25),
            ("1.2G+1.5Qp", lc["G"].scaled(1.2) + lc["Qp"].scaled(1.5), 0.97, 0.25),
            ("1.2G+1.5Qc", lc["G"].scaled(1.2) + lc["Qc"].scaled(1.5), 0.97, 0.25),
            ("1.2G+Wd", lc["G"].scaled(1.2) + lc["Wd"], 1.0, 1.0),
            ("0.9G+Wu", lc["G"].scaled(0.9) + lc["Wu"], 1.0, 1.0),
            ("1.2G+Wa", lc["G"].scaled(1.2) + lc["Wa"], 1.0, 1.0),
            ("0.9G+Wa", lc["G"].scaled(0.9) + lc["Wa"], 1.0, 1.0),
        ]
        sls = [("G long-term", lc["G"], self.a.j2),
               ("0.7Q short-term", lc["Q"].scaled(0.7), 1.0),
               ("Ws uplift", lc["Wu"].scaled(self.a.ws_ratio), 1.0)]
        return uls, sls

    # --- per-element restraint lengths and section for k12 -----------------------------
    def member_meta(self) -> pl.DataFrame:
        a, fr = self.a, self.fr
        rows = []
        for idx, e in enumerate(fr.elements):
            L = fr.length(e)
            sec = self.secs[e.group]
            if e.group == "rafter":
                seg = self.L_lower if "lower" in e.tag else self.L_upper
                r = dict(Lay_sag=min(a.battens, seg), Lay_hog=seg, Lax_c=seg, Lay_c=min(a.battens, seg))
            elif e.group == "collar":
                Lr = self.L_collar / (a.collar_restraints + 1)
                r = dict(Lay_sag=Lr, Lay_hog=Lr, Lax_c=self.L_collar, Lay_c=Lr)
            elif e.group == "tie":
                Lj = self.L_joist
                r = dict(Lay_sag=Lj, Lay_hog=min(a.ceiling_battens, Lj), Lax_c=Lj, Lay_c=min(a.ceiling_battens, Lj))
            else:  # purlin / ridge: top edge held by the rafters at each truss, bottom edge free between walls
                r = dict(Lay_sag=a.spacing, Lay_hog=a.bay, Lax_c=a.bay, Lay_c=a.spacing)
            rows.append(dict(elem=idx, group=e.group, tag=e.tag, L=L, b=sec.b, d=sec.d,
                             A=sec.A, Z=sec.Z, **r))
        return pl.DataFrame(rows)

    def run_uls(self) -> tuple[pl.DataFrame, pl.DataFrame]:
        a, fr, g = self.a, self.fr, self.grade
        meta = self.member_meta()
        uls, _ = self.combos()
        frames, reacts = [], []
        tm = self.trusses[self.mid_truss]
        for name, lc, k1, r in uls:
            res = fr.solve(lc)
            for idx, e in enumerate(fr.elements):
                s, N, V, M = res.actions(idx, 11)
                (x1, y1), (x2, y2) = fr.nodes[e.ni], fr.nodes[e.nj]
                L = fr.length(e)
                frames.append(pl.DataFrame(dict(
                    combo=name, k1=k1, r=r, elem=idx,
                    s=s, x=x1 + (x2 - x1) * s / L, y=y1 + (y2 - y1) * s / L, N=N, V=V, M=M)))
            sup = [(tm["wall_L"], "wall L (mid truss)"), (tm["wall_R"], "wall R (mid truss)")]
            sup += [(nd, f"joist prop {k+1} (mid truss)") for k, nd in enumerate(tm["props"])]
            if a.strutted:
                sup += [(tm["collar_L"], "strut L (mid truss)"), (tm["collar_R"], "strut R (mid truss)")]
            for k, nd in enumerate(self.purlin_wall_nodes):
                sup.append((nd, f"purlin on cross wall ({'L' if k < len(self.walls_y) else 'R'} y={fr.nodes[nd][0]:.0f})"))
            for nd in self.ridge_wall_nodes:
                sup.append((nd, f"ridge on cross wall (y={fr.nodes[nd][0]:.0f})"))
            for nd, lab in sup:
                Rx, Ry = res.reaction(nd)
                reacts.append(dict(combo=name, support=lab, H_kN=Rx / 1e3, V_kN=Ry / 1e3))
        df = pl.concat(frames).join(meta, on="elem")

        phi, k4, k6, k9 = a.phi, 1.0, 1.0, a.k9
        E, fb, ft, fc, fs = g["E"], g["fb"], g["ft"], g["fc"], g["fs"]
        rb = pl.col("r").map_elements(lambda r_: rho_b(E, fb, r_, a.seasoned), return_dtype=pl.Float64)
        rc = pl.col("r").map_elements(lambda r_: rho_c(E, fc, r_, a.seasoned), return_dtype=pl.Float64)
        k12f = lambda ex: ex.map_elements(k12_from, return_dtype=pl.Float64)  # noqa: E731
        d, b = pl.col("d"), pl.col("b")
        S1 = pl.when(pl.col("M") >= 0).then(1.25 * (d / b) * (pl.col("Lay_sag") / d) ** 0.5) \
               .otherwise(1.25 * (d / b) * (pl.col("Lay_hog") / d) ** 0.5)
        df = df.with_columns([(rb * S1).alias("rhoS1"), (rc * pl.col("Lax_c") / d).alias("rhoS3"),
                              (rc * pl.col("Lay_c") / b).alias("rhoS4")]) \
               .with_columns([k12f(pl.col("rhoS1")).alias("k12b"), k12f(pl.col("rhoS3")).alias("k12cx"),
                              k12f(pl.col("rhoS4")).alias("k12cy")])
        base = phi * pl.col("k1") * k4 * k6
        df = df.with_columns([
            (base * k9 * pl.col("k12b") * fb * pl.col("Z")).alias("Md"),
            (base * ft * pl.col("A")).alias("Nt"),
            (base * pl.col("k12cx") * fc * pl.col("A")).alias("Ncx"),
            (base * pl.col("k12cy") * fc * pl.col("A")).alias("Ncy"),
            (base * fs * (2 / 3) * pl.col("A")).alias("Vd"),
        ])
        Mr = pl.col("M").abs() / pl.col("Md")
        Nc = (-pl.col("N")).clip(lower_bound=0)
        Ntn = pl.col("N").clip(lower_bound=0)
        df = df.with_columns([
            Mr.alias("u_bend"), (pl.col("V").abs() / pl.col("Vd")).alias("u_shear"),
            # cl 3.5.1 (squared term only meaningful below unity; linear once failed), cl 3.5.2
            pl.max_horizontal(pl.when(Mr > 1).then(Mr).otherwise(Mr ** 2) + Nc / pl.col("Ncy"),
                              Mr + Nc / pl.col("Ncx")).alias("u_comb_c"),
            (Mr + Ntn / pl.col("Nt")).alias("u_comb_t"),
        ]).with_columns(pl.max_horizontal("u_bend", "u_shear", "u_comb_c", "u_comb_t").alias("util"))
        return df, pl.DataFrame(reacts)

    def run_sls(self) -> pl.DataFrame:
        a, fr, th = self.a, self.fr, self.th
        _, sls = self.combos()
        tm = self.trusses[self.mid_truss]
        rows = []
        for name, lc, j2 in sls:
            res = fr.solve(lc)
            nodes = [fr.elements[tm["rafter"][0]].ni] + [fr.elements[i].nj for i in tm["rafter"][: self.n1 + self.n2]]
            (x0, z0), (xa, za) = fr.nodes[nodes[0]], fr.nodes[nodes[-1]]
            u0, ua = res.disp(nodes[0]), res.disp(nodes[-1])
            best = 0.0
            for nd in nodes[1:-1]:
                x, z = fr.nodes[nd]; ux, uz = res.disp(nd)
                tt = ((x - x0) * (xa - x0) + (z - z0) * (za - z0)) / ((xa - x0) ** 2 + (za - z0) ** 2)
                cx, cz = u0[0] + tt * (ua[0] - u0[0]), u0[1] + tt * (ua[1] - u0[1])
                dn = -(ux - cx) * math.sin(th) + (uz - cz) * math.cos(th)
                best = dn if abs(dn) > abs(best) else best
            seg = nodes[: self.n1 + 1]
            u0s, u1s, um = res.disp(seg[0]), res.disp(seg[-1]), res.disp(seg[self.n1 // 2])
            dseg = -(um[0] - (u0s[0] + u1s[0]) / 2) * math.sin(th) + (um[1] - (u0s[1] + u1s[1]) / 2) * math.cos(th)
            joist = 0.0
            if tm["tie"]:
                zs = [res.disp(nd)[1] for nd in tm["tie_nodes"]]
                joist = min(zs, key=abs) if False else (min(zs) if abs(min(zs)) > abs(max(zs)) else max(zs))
            purlin = 0.0
            if self.purlin_elems:
                zs = [res.disp(fr.elements[i].ni)[1] for i in self.purlin_elems] + \
                     [res.disp(fr.elements[i].nj)[1] for i in self.purlin_elems]
                purlin = min(zs) if abs(min(zs)) > abs(max(zs)) else max(zs)
            rows.append(dict(case=name, j2=j2, rafter_mm=best * j2, lower_seg_mm=dseg * j2,
                             collar_node_mm=res.disp(tm["collar_L"])[1] * j2,
                             apex_mm=res.disp(tm["apex"])[1] * j2,
                             spread_mm=res.disp(tm["wall_R"])[0] * j2,
                             joist_sag_mm=joist * j2, purlin_mm=purlin * j2))
        return pl.DataFrame(rows)


# ---------------------------------------------------------------------------- reporting
def md(df: pl.DataFrame, fmt: dict[str, str] | None = None) -> str:
    fmt = fmt or {}
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.iter_rows(named=True):
        out.append("| " + " | ".join(format(v, fmt.get(c, ".2f")) if isinstance(v, float) else str(v)
                                     for c, v in zip(cols, row.values())) + " |")
    return "\n".join(out)


def governing(df: pl.DataFrame) -> pl.DataFrame:
    return (df.sort("util", descending=True).group_by("group", maintain_order=True).first()
              .select(["group", "combo", "tag", "util", "M", "Md", "N", "Ncx", "Ncy", "Nt", "k12b", "k12cy"])
              .with_columns([(pl.col(c) / 1e6).alias(c) for c in ("M", "Md")]
                            + [(pl.col(c) / 1e3).alias(c) for c in ("N", "Ncx", "Ncy", "Nt")])
              .rename({"M": "M* kNm", "Md": "Md kNm", "N": "N* kN", "Ncx": "Ncx kN", "Ncy": "Ncy kN", "Nt": "Nt kN"}))


def connection_note(df: pl.DataFrame, a) -> str:
    col = df.filter(pl.col("group") == "collar")
    if col.is_empty():
        return ""
    w = col.sort(pl.col("N").abs(), descending=True).row(0, named=True)
    Ns = abs(w["N"]) / 1e3
    k17 = 1.0
    n = math.ceil(Ns / (0.8 * w["k1"] * a.nail_qk)) if Ns > 0 else 0
    k17 = 1.0 if n <= 4 else (0.94 if n <= 7 else (0.88 if n <= 11 else 0.80))
    n = math.ceil(Ns / (0.8 * w["k1"] * k17 * a.nail_qk)) if Ns > 0 else 0
    return (f"Collar-tie lap: N* = {Ns:.2f} kN ({'tension' if w['N'] > 0 else 'compression'}, {w['combo']}) "
            f"≈ {n} x 3.15 mm nails each end (Q_k {a.nail_qk} kN J4, φ 0.80, k1 {w['k1']}, k17 {k17}), or an M12 bolt.")


def plot_case(m: RoofGrillage, df: pl.DataFrame, sls: pl.DataFrame, title: str, path: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fr, a = m.fr, m.a
    tm = m.trusses[m.mid_truss]
    truss_elems = set(tm["rafter"] + [tm["collar"]] + tm["tie"])
    gov = df.filter(pl.col("elem").is_in(list(truss_elems))).sort("util", descending=True).row(0, named=True)["combo"]
    sub = df.filter(pl.col("combo") == gov)
    nrow = 3 if m.purlin_elems else 2
    fig, axes = plt.subplots(nrow, 1, figsize=(11, 4 * nrow))
    # 1. mid-bay truss BMD
    ax = axes[0]
    for idx in truss_elems:
        e = fr.elements[idx]
        (x1, y1), (x2, y2) = fr.nodes[e.ni], fr.nodes[e.nj]
        ax.plot([x1, x2], [y1, y2], color="#6b4f2a", lw=3, solid_capstyle="round")
    tsub = sub.filter(pl.col("elem").is_in(list(truss_elems)))
    Mmax = max(abs(tsub["M"].min()), abs(tsub["M"].max()), 1.0)
    scale = 600.0 / Mmax
    for idx in truss_elems:
        e = fr.elements[idx]
        rows = tsub.filter(pl.col("elem") == idx).sort("s")
        ang = fr.angle(e); nx, ny = -math.sin(ang), math.cos(ang)
        xs, ys, Ms = rows["x"].to_numpy(), rows["y"].to_numpy(), rows["M"].to_numpy()
        ax.fill(np.r_[xs, xs[::-1]], np.r_[ys, (ys - ny * Ms * scale)[::-1]], color="#d9534f", alpha=0.35, lw=0)
    for nd in (tm["wall_L"], tm["wall_R"]):
        ax.plot(*fr.nodes[nd], marker="^", ms=12, color="k")
    for nd in tm["props"]:
        ax.plot(*fr.nodes[nd], marker="^", ms=10, color="gray")
    if m.purlin_elems:
        for nd in (tm["collar_L"], tm["collar_R"]):
            ax.plot(*fr.nodes[nd], marker="s", ms=8, color="#2a8a4a")
        if m.ridge_elems:
            ax.plot(*fr.nodes[tm["apex"]], marker="s", ms=8, color="#2a8a4a")
    ax.set_aspect("equal"); ax.grid(alpha=.3)
    ax.set_title(f"{title}\nmid-bay truss (y={tm['y']:.0f}) bending moment, governing combo {gov} (|M|max {Mmax/1e6:.2f} kNm);"
                 f" green squares = purlin/ridge coupling")
    # 2. purlin + ridge elevation along Y
    if m.purlin_elems:
        ax = axes[1]
        psub = sub.filter(pl.col("elem").is_in(m.purlin_elems + m.ridge_elems))
        Mp = max(abs(psub["M"].min()), abs(psub["M"].max()), 1.0)
        for grp, col, label in (("purlin", "#2a8a4a", "under-purlin"), ("ridge", "#7a4bb0", "ridge")):
            rows = psub.filter(pl.col("group") == grp).sort(["elem", "s"])
            if rows.is_empty():
                continue
            # runner elements live in the (Y, Z) plane, so their along-building coordinate is "x"
            ax.plot(rows["x"].to_numpy(), rows["M"].to_numpy() / 1e6, color=col, lw=2, label=f"{label} M (kNm)")
        for yw in m.walls_y:
            ax.axvline(yw, color="k", ls="--", lw=1)
        for t in m.trusses:
            ax.axvline(t["y"], color="#c8812f", lw=0.8, alpha=0.6)
        ax.invert_yaxis(); ax.grid(alpha=.3); ax.legend(loc="upper right")
        ax.set_title(f"under-purlin / ridge bending along the building, {gov} (dashed = cross walls, orange = trusses)")
        ax.set_xlabel("y (mm)")
    # 3. deflected shape of the mid truss, long-term G
    ax = axes[-1]
    res = fr.solve(m.combos()[1][0][1]); j2 = a.j2; amp = 20.0
    for idx in truss_elems:
        e = fr.elements[idx]
        (x1, y1), (x2, y2) = fr.nodes[e.ni], fr.nodes[e.nj]
        ax.plot([x1, x2], [y1, y2], color="#bbb", lw=1.5)
        u1, u2 = res.disp(e.ni), res.disp(e.nj)
        ax.plot([x1 + amp * j2 * u1[0], x2 + amp * j2 * u2[0]], [y1 + amp * j2 * u1[1], y2 + amp * j2 * u2[1]],
                color="#2a6fb0", lw=2.5)
    r = sls.filter(pl.col("case") == "G long-term").row(0, named=True)
    ax.set_aspect("equal"); ax.grid(alpha=.3)
    ax.set_title(f"long-term dead-load deflection x{amp:g} (j2={j2:g}): rafter {r['rafter_mm']:.1f}, apex {r['apex_mm']:.1f}, "
                 f"collar node {r['collar_node_mm']:.1f}, joist {r['joist_sag_mm']:.1f}, purlin {r['purlin_mm']:.1f} mm")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def run_one(a, title: str, plots_dir: str | None = None, tag: str = "") -> dict:
    m = RoofGrillage(a)
    df, reacts = m.run_uls()
    sls = m.run_sls()
    gov = governing(df)
    lines = [f"### {title} — {m.sec} {a.grade}, ridge {a.ridge or 'none'}, span {a.span:g}, pitch {a.pitch:g}°, "
             f"trusses @ {a.spacing:g} c/c, cross walls @ {a.bay:g}", "",
             "Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):", "", md(gov), "",
             "Support reactions (kN; H = horizontal thrust):", "",
             md(reacts.group_by("support").agg(pl.col("H_kN").abs().max().alias("|H| max"),
                                                pl.col("V_kN").max().alias("V max (down)"),
                                                pl.col("V_kN").min().alias("V min (uplift if <0)")).sort("support")), ""]
    jl = f", joist span {m.L_joist:.0f} → {m.L_joist/300:.1f}" if a.support == "tie" else ""
    pl_ = f", purlin bay {a.bay:.0f} → {a.bay/300:.1f}" if m.purlin_elems else ""
    lines += [f"Serviceability deflections, mid-bay truss (mm; limits span/300: rafter {m.L_rafter/300:.1f}{jl}{pl_}):", "",
              md(sls, {"j2": ".0f"}), ""]
    cn = connection_note(df, a)
    if cn:
        lines += [cn, ""]
    if plots_dir:
        os.makedirs(plots_dir, exist_ok=True)
        p = os.path.join(plots_dir, f"{tag or 'case'}_{m.sec}.png")
        plot_case(m, df, sls, title, p)
        lines += [f"![{title}]({os.path.basename(p)})", ""]
    return dict(model=m, df=df, reacts=reacts, sls=sls, gov=gov, text="\n".join(lines))


def sweep(a, sections) -> pl.DataFrame:
    rows = []
    for b, d in sections:
        aa = argparse.Namespace(**vars(a)); aa.section = (b, d)
        m = RoofGrillage(aa)
        df, _ = m.run_uls(); sls = m.run_sls()
        g = governing(df)
        def u(grp):
            r = g.filter(pl.col("group") == grp)
            return r["util"][0] if r.height else float("nan")
        G = sls.filter(pl.col("case") == "G long-term").row(0, named=True)
        rows.append({"section": str(m.sec), "rafter": u("rafter"), "collar": u("collar"), "joist": u("tie"),
                     "purlin": u("purlin"), "ridge": u("ridge"),
                     "rafter δG mm": abs(G["rafter_mm"]), "purlin δG mm": abs(G["purlin_mm"])})
    return pl.DataFrame(rows)


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_argument_group("geometry (mm, deg)")
    g.add_argument("--span", type=float, default=8500, help="between wall supports")
    g.add_argument("--pitch", type=float, default=27)
    g.add_argument("--spacing", type=float, default=1200, help="truss centres")
    g.add_argument("--collar-drop", type=float, default=1000, help="collar tie below the apex (vertical)")
    g.add_argument("--section", type=parse_section, default=(35, 105), help="b x d of rafters/collar/joists/purlins")
    g.add_argument("--ridge", type=parse_section, default=(40, 190), help="ridge beam b x d; '' for none")
    g.add_argument("--rafter-section", type=parse_section, default=None, help="override for rafters only")
    g.add_argument("--collar-section", type=parse_section, default=None)
    g.add_argument("--joist-section", type=parse_section, default=None)
    g.add_argument("--purlin-section", type=parse_section, default=None)
    g.add_argument("--bay", type=float, default=3600, help="cross-wall spacing supporting purlins + ridge (3 trusses per bay, walls mid-way between trusses); 0 = none")
    g.add_argument("--bays", type=int, default=3, help="bays modelled (results reported for the middle one)")
    g.add_argument("--truss-offset", type=float, default=600, help="first truss from the first cross wall")
    g.add_argument("--support", choices=["pinned", "roller", "tie"], default="tie",
                   help="tie: ceiling joists tie the feet [default]; pinned: walls resist thrust; roller: one wall free")
    g.add_argument("--joist-props", type=int, default=3, help="props under the joists: 3 = mid wall + hanging beams at quarter points [default], 1 = mid wall only, 0 = none")
    g.add_argument("--strutted", action="store_true", help="what-if: every collar node rigidly propped")
    g.add_argument("--battens", type=float, default=900)
    g.add_argument("--ceiling-battens", type=float, default=450)
    g.add_argument("--collar-restraints", type=int, default=0)
    t = ap.add_argument_group("timber (AS 1720.1)")
    t.add_argument("--grade", choices=sorted(GRADES), default="F7")
    t.add_argument("--seasoned", action="store_true")
    t.add_argument("--density", type=float, default=550)
    t.add_argument("--phi", type=float, default=0.70)
    t.add_argument("--k9", type=float, default=1.0)
    t.add_argument("--j2", type=float, default=3.0)
    t.add_argument("--nail-qk", type=float, default=0.515)
    l = ap.add_argument_group("loads (kPa, AS/NZS 1170; wind = N1 suburban Adelaide)")
    l.add_argument("--g-roof", type=float, default=0.10)
    l.add_argument("--ceiling", type=float, default=0.12)
    l.add_argument("--q-roof", type=float, default=0.25)
    l.add_argument("--q-point", type=float, default=1400)
    l.add_argument("--qc-point", type=float, default=900)
    l.add_argument("--wind-up", type=float, default=-0.58, help="N2 = -0.8")
    l.add_argument("--wind-down", type=float, default=0.43, help="N2 = 0.6")
    l.add_argument("--wind-asym", type=lambda s: tuple(float(v) for v in s.split(",")), default=(0.36, -0.58), help="N2 = 0.5,-0.8")
    l.add_argument("--ws-ratio", type=float, default=0.58)
    o = ap.add_argument_group("output")
    o.add_argument("--all", action="store_true")
    o.add_argument("--plots", action="store_true")
    o.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "report"))
    args = ap.parse_args(argv)
    if args.ridge == () or args.ridge == ("",):
        args.ridge = None
    return args


def main(argv=None):
    a = parse(argv)
    plots = a.out if a.plots else None
    m0 = RoofGrillage(a)
    print(f"# Roof analysis — span {a.span:g} mm, pitch {a.pitch:g}°, {m0.sec} {a.grade} Oregon, trusses @ {a.spacing:g} c/c\n")
    print(f"Geometry: rise {m0.rise:.0f} mm, rafter {m0.L_rafter:.0f} on slope (wall→collar {m0.L_lower:.0f}, "
          f"collar→apex {m0.L_upper:.0f}), collar {m0.L_collar:.0f} long at {m0.yc:.0f} above the plate; "
          f"{len(m0.truss_y)} trusses modelled over {a.bays} x {a.bay:g} mm bays, results for truss at y={m0.truss_y[m0.mid_truss]:.0f}.\n")
    if not a.all:
        print(run_one(a, "as built", plots_dir=plots, tag="asbuilt")["text"])
        return
    cases = [
        (dict(), "as built: purlins + 40x190 ridge on cross walls @ 3.6 m (mid-way between trusses), joists on mid wall + hanging beams", "asbuilt"),
        (dict(joist_props=1), "what-if: joists on the mid wall only (no hanging beams)", "nobeams"),
        (dict(ridge=None), "what-if: no ridge beam", "noridge"),
        (dict(bay=0.0, bays=1), "what-if: purlins as bracing only (no cross walls)", "nowalls"),
        (dict(bay=0.0, bays=1, strutted=True), "what-if: every collar node rigidly propped", "strutted"),
        (dict(collar_restraints=2), "what-if: as built + collar braced at third points", "collarbraced"),
    ]
    for over, title, tag in cases:
        aa = argparse.Namespace(**vars(a)); aa.__dict__.update(over)
        print(run_one(aa, title, plots_dir=plots, tag=tag)["text"])
    secs = [(35, 105), (35, 140), (45, 140), (35, 190), (45, 190), (45, 240)]
    print("### Section sweep — as built (rafters/collar/joists/purlins all this section; ridge 40x190)\n")
    print(md(sweep(a, secs)), "\n")


if __name__ == "__main__":
    main()
