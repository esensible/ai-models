"""Minimal 2D Euler-Bernoulli frame solver (direct stiffness) — numpy only.

Conventions
  * plane coordinates (x, y) in mm, y up; rotations positive anticlockwise.
  * Each node has 2 translational DOFs. Each ELEMENT END owns a rotation DOF id;
    rigid joints share one id, a hinge gives each member end its own id. That is
    how pins/releases are modelled without any stiffness tricks.
  * Element local x runs node i -> node j; local y = x rotated +90 deg.
  * Member loads: uniform in global vertical (w_v, N/mm, +up) and uniform in
    local y (q_n, N/mm, + towards local +y). Nodal point loads in global.
  * Internal actions along a member: N (tension +), V, M (sagging about local
    y = tension on the local -y face is +).

Units: N, mm, MPa throughout.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class Element:
    ni: int
    nj: int
    E: float
    A: float
    I: float
    rot_i: int          # rotation DOF id at end i
    rot_j: int          # rotation DOF id at end j
    group: str          # label used for reporting/checks
    tag: str = ""       # free text (e.g. "rafter L lower")


@dataclass
class LoadCase:
    name: str
    w_v: dict = field(default_factory=dict)     # element idx -> N/mm global vertical (+up)
    q_n: dict = field(default_factory=dict)     # element idx -> N/mm local +y
    P: dict = field(default_factory=dict)       # node -> (Fx, Fy) N

    def scaled(self, f: float, name: str | None = None) -> "LoadCase":
        return LoadCase(name or f"{f}*{self.name}",
                        {k: f * v for k, v in self.w_v.items()},
                        {k: f * v for k, v in self.q_n.items()},
                        {k: (f * v[0], f * v[1]) for k, v in self.P.items()})

    def __add__(self, o: "LoadCase") -> "LoadCase":
        out = LoadCase(f"{self.name}+{o.name}", dict(self.w_v), dict(self.q_n), dict(self.P))
        for k, v in o.w_v.items():
            out.w_v[k] = out.w_v.get(k, 0.0) + v
        for k, v in o.q_n.items():
            out.q_n[k] = out.q_n.get(k, 0.0) + v
        for k, v in o.P.items():
            px, py = out.P.get(k, (0.0, 0.0))
            out.P[k] = (px + v[0], py + v[1])
        return out


class Frame:
    def __init__(self):
        self.nodes: list[tuple[float, float]] = []
        self.elements: list[Element] = []
        self.fixed: set[tuple[int, str]] = set()   # (node, 'x'|'y')
        self.links: list[tuple[int, int]] = []     # (slave dof, master dof): equal displacement
        self._nrot = 0

    # --- model building -------------------------------------------------
    def node(self, x: float, y: float) -> int:
        self.nodes.append((float(x), float(y)))
        return len(self.nodes) - 1

    def new_rot(self) -> int:
        self._nrot += 1
        return self._nrot - 1

    def beam(self, ni, nj, E, A, I, rot_i, rot_j, group, tag="") -> int:
        self.elements.append(Element(ni, nj, E, A, I, rot_i, rot_j, group, tag))
        return len(self.elements) - 1

    def fix(self, node: int, *dirs: str):
        for d in dirs:
            self.fixed.add((node, d))

    def link(self, slave: int, master: int, d: str):
        """Make node `slave`'s displacement in direction d equal node `master`'s.
        This is how elements in different planes (a grillage) share a DOF."""
        k = 0 if d == 'x' else 1
        self.links.append((2 * slave + k, 2 * master + k))

    # --- geometry helpers ------------------------------------------------
    def length(self, e: Element) -> float:
        (x1, y1), (x2, y2) = self.nodes[e.ni], self.nodes[e.nj]
        return float(np.hypot(x2 - x1, y2 - y1))

    def angle(self, e: Element) -> float:
        (x1, y1), (x2, y2) = self.nodes[e.ni], self.nodes[e.nj]
        return float(np.arctan2(y2 - y1, x2 - x1))

    def dofs(self, e: Element) -> list[int]:
        nt = 2 * len(self.nodes)
        return [2 * e.ni, 2 * e.ni + 1, nt + e.rot_i, 2 * e.nj, 2 * e.nj + 1, nt + e.rot_j]

    @staticmethod
    def _T(c, s):
        T = np.zeros((6, 6))
        for k in (0, 3):
            T[k, k] = c; T[k, k + 1] = s
            T[k + 1, k] = -s; T[k + 1, k + 1] = c
        T[2, 2] = T[5, 5] = 1.0
        return T

    def _k_local(self, e: Element, L: float):
        EA_L = e.E * e.A / L
        EI = e.E * e.I
        k = np.array([
            [EA_L, 0, 0, -EA_L, 0, 0],
            [0, 12 * EI / L**3, 6 * EI / L**2, 0, -12 * EI / L**3, 6 * EI / L**2],
            [0, 6 * EI / L**2, 4 * EI / L, 0, -6 * EI / L**2, 2 * EI / L],
            [-EA_L, 0, 0, EA_L, 0, 0],
            [0, -12 * EI / L**3, -6 * EI / L**2, 0, 12 * EI / L**3, -6 * EI / L**2],
            [0, 6 * EI / L**2, 2 * EI / L, 0, -6 * EI / L**2, 4 * EI / L],
        ])
        return k

    def _local_udl(self, e_idx: int, lc: LoadCase):
        """Uniform load on element in local axes (p along x, q along y), N/mm."""
        e = self.elements[e_idx]
        a = self.angle(e)
        c, s = np.cos(a), np.sin(a)
        wv = lc.w_v.get(e_idx, 0.0)
        qn = lc.q_n.get(e_idx, 0.0)
        # global vertical w (y) -> local: p = w*s, q = w*c
        p = wv * s
        q = wv * c + qn
        return p, q

    # --- solve -------------------------------------------------------------
    def solve(self, lc: LoadCase) -> "Result":
        nt = 2 * len(self.nodes)
        ndof = nt + self._nrot
        K = np.zeros((ndof, ndof))
        F = np.zeros(ndof)
        mp = np.arange(ndof)                      # dof -> master dof
        for slave, master in self.links:
            while mp[master] != master:
                master = mp[master]
            mp[slave] = master
        mp = mp[mp]                               # resolve chains
        for idx, e in enumerate(self.elements):
            L = self.length(e)
            a = self.angle(e)
            T = self._T(np.cos(a), np.sin(a))
            k = T.T @ self._k_local(e, L) @ T
            d = mp[self.dofs(e)]
            np.add.at(K, (d[:, None], d[None, :]), k)   # add.at: repeated ids accumulate
            p, q = self._local_udl(idx, lc)
            feq = np.array([p * L / 2, q * L / 2, q * L**2 / 12, p * L / 2, q * L / 2, -q * L**2 / 12])
            np.add.at(F, d, T.T @ feq)
        for n, (fx, fy) in lc.P.items():
            F[mp[2 * n]] += fx
            F[mp[2 * n + 1]] += fy
        fixed = {mp[2 * n + (0 if d == 'x' else 1)] for n, d in self.fixed}
        slaves = {i for i in range(ndof) if mp[i] != i}
        free = [i for i in range(ndof) if i not in fixed and i not in slaves]
        u = np.zeros(ndof)
        Kff = K[np.ix_(free, free)]
        cond = np.linalg.cond(Kff)
        if not np.isfinite(cond) or cond > 1e14:
            raise RuntimeError(f"stiffness matrix singular/ill-conditioned (cond={cond:.2e}): mechanism?")
        u[free] = np.linalg.solve(Kff, F[free])
        R = K @ u - F
        u = u[mp]                                 # slaves follow their masters
        R = R[mp]
        return Result(self, lc, u, R)


class Result:
    def __init__(self, frame: Frame, lc: LoadCase, u: np.ndarray, R: np.ndarray):
        self.frame, self.lc, self.u, self.R = frame, lc, u, R

    def reaction(self, node: int) -> tuple[float, float]:
        return float(self.R[2 * node]), float(self.R[2 * node + 1])

    def disp(self, node: int) -> tuple[float, float]:
        return float(self.u[2 * node]), float(self.u[2 * node + 1])

    def end_forces_local(self, e_idx: int) -> np.ndarray:
        fr = self.frame
        e = fr.elements[e_idx]
        L = fr.length(e)
        a = fr.angle(e)
        T = fr._T(np.cos(a), np.sin(a))
        ul = T @ self.u[fr.dofs(e)]
        p, q = fr._local_udl(e_idx, self.lc)
        feq = np.array([p * L / 2, q * L / 2, q * L**2 / 12, p * L / 2, q * L / 2, -q * L**2 / 12])
        return fr._k_local(e, L) @ ul - feq   # forces acting ON the element ends

    def actions(self, e_idx: int, n: int = 11):
        """Return s (mm from node i), N, V, M arrays along the element."""
        fr = self.frame
        e = fr.elements[e_idx]
        L = fr.length(e)
        f = self.end_forces_local(e_idx)
        p, q = fr._local_udl(e_idx, self.lc)
        s = np.linspace(0.0, L, n)
        N = -f[0] - p * s
        V = f[1] + q * s
        M = -f[2] + f[1] * s + q * s**2 / 2   # sagging (compression on local +y face) +
        return s, N, V, M

    def member_envelope(self, e_idx: int, n: int = 21):
        s, N, V, M = self.actions(e_idx, n)
        return dict(Nmax=N.max(), Nmin=N.min(), Vabs=np.abs(V).max(),
                    Mmax=M.max(), Mmin=M.min())
