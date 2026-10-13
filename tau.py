"""
Verify the conjecture for tau of odd pretzel knots.
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from common import (
    Params, conjectured_formula,
    add_common_args, validate_common_args, format_seconds,
    interesting_canonical_representatives,
    load_verified, log_verified, log_mismatch,
)

try:
    import knot_floer_homology as kfh
except ImportError:
    sys.exit("knot_floer_homology not installed "
             "(pip install knot_floer_homology)")

try:
    from pretzel_pd import tangle_points, pretzel_pd_2
except ImportError:
    sys.exit("pretzel_pd.py not found next to tau.py")


PROJECT_DIR = Path(__file__).resolve().parent
VERIFIED_LOG = PROJECT_DIR / "verified_tau.log"
MISMATCH_LOG = PROJECT_DIR / "mismatches_tau.log"


# --------------------------------------------------------------------------- #
#                               Computation
# --------------------------------------------------------------------------- #

def predicted(params: Params) -> int:
    return conjectured_formula(params) // 2


def compute(params: Params) -> tuple[int | None, str | None]:
    try:
        pd_code = [tuple(x) for x in pretzel_pd_2(params, tangle_points(params))]
        return kfh.pd_to_hfk(pd_code)["tau"], None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def worker(params: Params):
    tau, err = compute(params)
    return params, tau, err


# --------------------------------------------------------------------------- #
#                               CLI and main
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    add_common_args(p)
    p.add_argument("--workers", type=int, default=None,
                   help="worker processes (default: all cores)")
    p.add_argument("--progress-every", type=int, default=200)
    args = p.parse_args()
    validate_common_args(p, args)
    if args.workers is not None and args.workers <= 0:
        p.error("--workers must be a positive integer")
    if args.progress_every <= 0:
        p.error("--progress-every must be a positive integer")
    return args


def main() -> None:
    args = parse_args()
    done = set() if args.rerun else load_verified(VERIFIED_LOG)

    print(f"already verified: {len(done)}")
    total_checked = total_mismatch = total_fail = 0
    t_start = time.perf_counter()

    for n in range(3, args.max_blocks + 1, 2):
        t_n = time.perf_counter()
        jobs = interesting_canonical_representatives(args.max_abs, n)
        jobs = (t for t in jobs if t not in done)
        print(f"\nn = {n}")

        checked = mismatch = fail = 0
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            for params, tau_real, err in executor.map(worker, jobs, chunksize=8):
                checked += 1
                pred = predicted(params)
                if tau_real is None:
                    fail += 1
                    log_mismatch(MISMATCH_LOG, params, None, pred, err or "")
                elif tau_real != pred:
                    mismatch += 1
                    log_mismatch(MISMATCH_LOG, params, tau_real, pred)
                    print(f"  MISMATCH: {params} -> real={tau_real}, pred={pred}")
                else:
                    log_verified(VERIFIED_LOG, params, tau_real)
                    done.add(params)
                if checked % args.progress_every == 0:
                    rate = checked / (time.perf_counter() - t_n)
                    print(f"  {checked} checked ({rate:.0f} knots/s)")

        total_checked += checked
        total_mismatch += mismatch
        total_fail += fail
        print(f"  n={n}: {checked} checked, {mismatch} mismatches, "
              f"{fail} failures in {format_seconds(time.perf_counter() - t_n)}")

    print("\n=== SUMMARY ===")
    print(f"Checked:    {total_checked}")
    print(f"Mismatches: {total_mismatch}")
    print(f"Failures:   {total_fail}")
    print(f"Total time: {format_seconds(time.perf_counter() - t_start)}")


if __name__ == "__main__":
    main()