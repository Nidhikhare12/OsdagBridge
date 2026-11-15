"""
pso.py
------
Particle Swarm Optimisation (PSO) for the OsdagBridge plate-girder optimiser
(see optimiser.py).

Design vector (per girder):

    x = [D, bf_top, bf_bot, tf_top, tf_bot, tw, s_stiffener, t_stiffener]

The class itself only cares about the length of the bounds arrays, so it
works unchanged if the stiffener terms are re-enabled later.

Features aimed at optimiser.py
-------------------------------
* Infeasible designs are signalled by the objective returning ``np.inf``
  (slender section, DCR FAIL). The swarm re-samples at init until a usable
  fraction is feasible, and never stops early while every particle found so
  far is still infeasible.
* ``repair`` hook: snap a continuous position onto the real design grid
  (SAIL plate thicknesses, depth/width in multiples of 50/10 mm) *before* it
  is evaluated, so the design returned is exactly the one that was checked -
  matches the ``snap`` function already used in optimiser.py.
* Evaluation cache, keyed on the snapped design: after snapping, many
  particles land on identical designs, and the capacity + DCR calculation
  (``IRC22CapacityCalculator`` / ``DCREngine``) is not cheap.
* Exceptions raised inside the objective are treated as infeasible instead
  of crashing the run (``catch_errors=True``).
* ``extra_seeds`` lets you seed the swarm with known-reasonable designs
  (e.g. the upper-bound vector, which is usually feasible).
* No history tracking - ``optimize()`` just returns ``(best_x, best_f)``.

Objective signature: ``f(x: np.ndarray) -> float`` (minimised). Bind extra
arguments with a lambda/closure, as optimiser.py does:

    optimizer = PSO(
        objective_function=lambda x: objective_function(g_demand, g_config, x),
        design_vector=initial_vector,
        lower_bounds=lower_bound_vector,
        upper_bounds=upper_bound_vector,
        repair=snap,
        extra_seeds=[upper_bound_vector],
    )
    best_x, best_f = optimizer.optimize()
"""

from __future__ import annotations

import math
import warnings
from typing import Callable, Optional, Sequence, Tuple

import numpy as np

class PSO:
    """Bounded, continuous-space PSO with optional grid snapping."""

    def __init__(
        self,
        objective_function: Callable[[np.ndarray], float],
        design_vector: np.ndarray,
        lower_bounds: np.ndarray,
        upper_bounds: np.ndarray,
        n_particles: int = 40,
        max_iter: int = 200,
        gname = "G1",
        w_max: float = 0.9,
        w_min: float = 0.2,
        c1: float = 1.5,
        c2: float = 1.5,
        v_max_frac: float = 0.2,
        repair: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        extra_seeds: Optional[Sequence[np.ndarray]] = None,
        min_feasible_frac: float = 0.25,
        max_init_resamples: int = 10,
        tol: float = 1,
        stall_iter: int = 25,
        catch_errors: bool = False,
        seed: Optional[int] = None,
        verbose: bool = False,
        run: int = 1
    ):
        """
        Parameters
        ----------
        objective_function : f(x) -> float, minimised; np.inf = infeasible.
        design_vector      : initial guess; seeds particle 0 (clipped to bounds).
        lower_bounds, upper_bounds : per-variable bounds (lower <= upper).
        n_particles, max_iter      : swarm size / iteration cap.
        w_max, w_min       : inertia weight, linearly annealed w_max -> w_min.
        c1, c2             : cognitive / social acceleration coefficients.
        v_max_frac         : velocity cap as a fraction of each variable's range.
        repair             : optional x -> x' snapping to the real design grid.
                             Applied before every evaluation (result is clipped
                             back into the bounds afterwards).
        extra_seeds        : additional starting designs (e.g. the upper-bound
                             vector, which is usually feasible).
        min_feasible_frac  : at start, re-sample infeasible random particles
                             until this fraction of the swarm is feasible.
        max_init_resamples : max number of such re-sampling rounds.
        tol                : relative improvement threshold for the stall test.
        stall_iter          : stop after this many iterations without a
                             significant improvement (only once feasible).
        catch_errors       : treat exceptions in the objective as infeasible
                             (e.g. a degenerate section that IRC22CapacityCalculator
                             can't classify).
        seed               : RNG seed.
        verbose            : print progress each iteration.
        """
        self.f = objective_function
        self.x0 = np.asarray(design_vector, dtype=float)
        self.lb = np.asarray(lower_bounds, dtype=float)
        self.ub = np.asarray(upper_bounds, dtype=float)
        self.run = run

        if not (self.x0.shape == self.lb.shape == self.ub.shape) or self.x0.ndim != 1:
            raise ValueError(
                "design_vector, lower_bounds and upper_bounds must be 1D arrays of "
                f"equal length (got {self.x0.shape}, {self.lb.shape}, {self.ub.shape})"
            )
        # if np.any(self.ub < self.lb):
        #     bad = np.where(self.ub < self.lb)[0].tolist()
        #     raise ValueError(f"upper_bounds < lower_bounds at indices {bad}")
        self.ub = np.maximum(self.ub, self.lb)

        self.dim = self.x0.size
        self.n_particles = int(n_particles)
        self.g_name = gname
        self.max_iter = int(max_iter)
        self.w_max, self.w_min = w_max, w_min
        self.c1, self.c2 = c1, c2
        self.v_max = v_max_frac * (self.ub - self.lb)
        self.repair = repair
        self.extra_seeds = [np.asarray(s, dtype=float) for s in (extra_seeds or [])]
        self.min_feasible_frac = min_feasible_frac
        self.max_init_resamples = max_init_resamples
        self.tol = tol
        self.stall_iter = stall_iter
        self.catch_errors = catch_errors
        self.verbose = verbose
        self.rng = np.random.default_rng(seed)

        # diagnostics (no history array is kept)
        self._cache: dict = {}
        self.n_evals = 0      # actual objective calls (cache misses)
        self.n_errors = 0     # exceptions swallowed inside the objective

    # ------------------------------------------------------------------
    def _prepare(self, x: np.ndarray) -> np.ndarray:
        """Clip -> repair (grid snap) -> clip."""
        x = np.clip(np.asarray(x, dtype=float), self.lb, self.ub)
        if self.repair is not None:
            x = np.clip(np.asarray(self.repair(x.copy()), dtype=float), self.lb, self.ub)
        return x

    def _evaluate(self, x: np.ndarray) -> Tuple[np.ndarray, float]:
        """Return (snapped design, fitness). Infeasible/invalid -> inf."""
        x = self._prepare(x)
        key = tuple(np.round(x, 6))
        if key in self._cache:
            return x, self._cache[key]

        self.n_evals += 1
        try:
            f = float(self.f(x.copy()))
        except Exception as exc:
            if not self.catch_errors:
                raise
            self.n_errors += 1
            if self.verbose and self.n_errors <= 3:
                print(f"  [PSO] objective raised {type(exc).__name__}: {exc} -> infeasible")
            f = math.inf
        if not math.isfinite(f):        # inf, -inf, nan
            f = math.inf

        self._cache[key] = f
        return x, f

    # ------------------------------------------------------------------
    def _init_swarm(self):
        n = self.n_particles
        pos = self.rng.uniform(self.lb, self.ub, size=(n, self.dim))
        seeds = ([self.x0] + self.extra_seeds)[:n]
        for i, s in enumerate(seeds):
            pos[i] = s
        pos[0] = self.x0        # initial design vector loaded onto the particle swarm
        n_seeds = len(seeds)

        vel = self.rng.uniform(-self.v_max, self.v_max, size=(n, self.dim))
        fit = np.empty(n)
        for i in range(n):
            pos[i], fit[i] = self._evaluate(pos[i])

        # make sure the swarm starts with some feasible particles
        needed = math.ceil(self.min_feasible_frac * n)
        for _ in range(self.max_init_resamples):
            feasible = np.isfinite(fit)
            if feasible.sum() >= needed:
                break
            for i in range(n_seeds, n):
                if not feasible[i]:
                    cand = self.rng.uniform(self.lb, self.ub)
                    pos[i], fit[i] = self._evaluate(cand)
        return pos, vel, fit

    # ------------------------------------------------------------------
    def optimize(self) -> Tuple[np.ndarray, float]:
        """
        Run PSO.

        Returns
        -------
        best_x : best (snapped) design vector found.
        best_f : its objective value (np.inf => no feasible design was found).
        """
        pos, vel, fit = self._init_swarm()
        file_path = r"E:\Osdag\OsdagBridge\src\osdagbridge\core\bridge_types\plate_girder\pso_results.csv"
        data = []
        pbest_pos = pos.copy()
        pbest_fit = fit.copy()
        g = int(np.argmin(pbest_fit))
        gbest_pos = pbest_pos[g].copy()
        gbest_fit = float(pbest_fit[g])

        if self.verbose:
            print(f"init: {int(np.isfinite(fit).sum())}/{self.n_particles} feasible, best f = {gbest_fit:.6g}")

        stall = 0

        for it in range(self.max_iter):
            w = self.w_max - (self.w_max - self.w_min) * it / max(1, self.max_iter - 1)
            r1 = self.rng.random((self.n_particles, self.dim))
            r2 = self.rng.random((self.n_particles, self.dim))

            vel = (w * vel
                   + self.c1 * r1 * (pbest_pos - pos)
                   + self.c2 * r2 * (gbest_pos - pos))
            vel = np.clip(vel, -self.v_max, self.v_max)
            pos = pos + vel

            out = (pos < self.lb) | (pos > self.ub)
            pos = np.clip(pos, self.lb, self.ub)
            vel[out] = 0.0

            for i in range(self.n_particles):
                snapped, f = self._evaluate(pos[i])
                if f < pbest_fit[i]:
                    pbest_fit[i] = f
                    pbest_pos[i] = snapped

            g = int(np.argmin(pbest_fit))
            cand = float(pbest_fit[g])
            if cand < gbest_fit:
                significant = (not math.isfinite(gbest_fit)) or \
                              (gbest_fit - cand) > self.tol * max(1.0, abs(gbest_fit))
                stall = 0 if significant else stall + 1
                gbest_fit = cand
                gbest_pos = pbest_pos[g].copy()
            else:
                stall += 1
            
            data.append([self.g_name, self.run, it, gbest_fit])

            if not math.isfinite(gbest_fit):
                stall = 0   # never stop while still infeasible

            if self.verbose:
                print(f"iter {it+1:4d}/{self.max_iter}  w={w:.3f}  best f = {gbest_fit:.6g}  evals = {self.n_evals}")

            if stall >= self.stall_iter:
                if self.verbose:
                    print(f"Converged: no significant improvement for {self.stall_iter} iterations.")
                break
        
        import csv
        with open(file = file_path, mode="a", newline="", encoding="utf-8") as file:
            
            writer = csv.writer(file)
            writer.writerows(data)
            
        if not math.isfinite(gbest_fit):
            warnings.warn(
                "PSO found no feasible design (objective was inf/raised for every "
                "evaluation). Check bounds / seeds, or increase n_particles / max_iter.",
                RuntimeWarning,
            )
        return gbest_pos, gbest_fit
