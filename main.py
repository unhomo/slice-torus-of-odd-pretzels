from __future__ import annotations

import argparse
import itertools
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable, Iterator

import knot_floer_homology as kfh
from pretzel_pd import tangle_points, pretzel_pd_2

Params = tuple[int, ...]


# --------------------------------------------------------------------------- #
#                              Predicted tau
# --------------------------------------------------------------------------- #

def sign(x: int) -> int:
    return 1 if x > 0 else -1


def min_abs_after_cancellation(params: Params) -> int:
    """
    Return the parameter of minimal absolute value after
    iteratively removing all pairs {t, -t} from params.
    """
    counts = Counter(params)
    survivors = (
        abs_val if counts[abs_val] > counts[-abs_val] else -abs_val
        for abs_val in {abs(a) for a in params}
        if counts[abs_val] != counts[-abs_val]
    )
    return min(survivors, key=abs)


def predicted_tau(params: Params) -> int:
    """
    Predicted tau(P(params)) by the conjecture.
    """
    sign_sum = sum(sign(a) for a in params)
    return (-sign_sum + sign(min_abs_after_cancellation(params))) // 2


# --------------------------------------------------------------------------- #
#                  Which tuples are still worth testing
# --------------------------------------------------------------------------- #

def has_adjacent_opposites(params: Params) -> bool:
    """
    True iff some cyclically adjacent pair has the form {t, -t}.
    """
    n = len(params)
    return any(params[i] == -params[(i + 1) % n] for i in range(n))


def has_both_units(params: Params) -> bool:
    """
    True iff both 1 and -1 appear in the tuple, regardless of adjacency.
    """
    return 1 in params and -1 in params


def min_abs_is_mixed(params: Params) -> bool:
    """
    True iff condition (b) of Theorem 2 fails for the original tuple:
    the parameters of minimal absolute value appear with both signs.
    """
    min_abs = min(abs(a) for a in params)
    return len({sign(a) for a in params if abs(a) == min_abs}) == 2


def is_interesting(params: Params) -> bool:
    """
    True iff params is outside the scope of Theorem 2, has no cyclically
    adjacent cancellable pair, and does not contain both 1 and -1.
    """
    return (
        not has_adjacent_opposites(params)
        and not has_both_units(params)
        and min_abs_is_mixed(params)
    )


# --------------------------------------------------------------------------- #
#                    Canonical representatives of pretzel
# --------------------------------------------------------------------------- #

def is_canonical(t: Params) -> bool:
    """
    True iff t is the lex-minimum of its orbit under
    cyclic shifts, reversal of the order, and global sign flip.
    """
    n = len(t)
    for s in (1, -1):
        st = tuple(s * x for x in t)
        for k in range(n):
            r = st[k:] + st[:k]
            if r < t or r[::-1] < t:
                return False
    return True


def interesting_canonical_representatives(
    max_abs: int, n: int
) -> Iterator[Params]:
    """
    Yield one representative per orbit among tuples satisfying
    `is_interesting`. Any canonical tuple has first entry -max|a_i|,
    so we enumerate (-k, rest) with odd k and |rest_i| <= k.
    """
    for k in range(1, max_abs + 1, 2):
        values = tuple(x for x in range(-k, k + 1) if x % 2)
        for rest in itertools.product(values, repeat=n - 1):
            t = (-k,) + rest
            if is_interesting(t) and is_canonical(t):
                yield t


# --------------------------------------------------------------------------- #
#                            Tau computation
# --------------------------------------------------------------------------- #

def compute_tau(params: Params) -> tuple[int | None, str | None]:
    """
    Return (tau, None) on success, or (None, reason) on failure.
    """
    try:
        pd_code = [tuple(x) for x in pretzel_pd_2(params, tangle_points(params))]
        return kfh.pd_to_hfk(pd_code)["tau"], None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def worker(params: Params) -> tuple[Params, int | None, str | None]:
    tau, err = compute_tau(params)
    return params, tau, err


# --------------------------------------------------------------------------- #
#                          Verification driver
# --------------------------------------------------------------------------- #

def run_verification(
    jobs: Iterable[Params],
    args: argparse.Namespace,
    log,
) -> tuple[int, int, int]:
    """
    Verify the conjecture on `jobs`.  Returns (checked, mismatches, failures).
    """
    checked = mismatches = failures = 0
    t0 = time.perf_counter()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for params, tau_real, err in executor.map(worker, jobs, chunksize=8):
            checked += 1

            if tau_real is None:
                failures += 1
                log.write(f"FAIL: {params} -- {err}\n")
                continue

            tau_pred = predicted_tau(params)
            if tau_real != tau_pred:
                mismatches += 1
                line = f"MISMATCH: {params} -> tau={tau_real}, predicted={tau_pred}\n"
                print(line, end="")
                log.write(line)
                log.flush()

            if checked % args.progress_every == 0:
                rate = checked / (time.perf_counter() - t0)
                print(f"  {checked} checked  ({rate:.0f} knots/s)")

    return checked, mismatches, failures


# --------------------------------------------------------------------------- #
#                           CLI and reporting
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--max-abs", type=int, default=17,
                   help="maximum |a_i| (odd; default 17)")
    p.add_argument("--max-blocks", type=int, default=5,
                   help="maximum number of blocks (odd; default 5)")
    p.add_argument("--workers", type=int, default=None,
                   help="worker processes (default: all cores)")
    p.add_argument("--progress-every", type=int, default=200,
                   help="print progress every N checks")
    p.add_argument("--log", type=Path, default=Path("mismatches.log"),
                   help="log file for mismatches and failures")

    args = p.parse_args()
    if args.max_abs % 2 == 0:
        p.error("--max-abs must be odd")
    if args.max_blocks % 2 == 0:
        p.error("--max-blocks must be odd")
    if args.workers is not None and args.workers <= 0:
        p.error("--workers must be a positive integer")
    if args.progress_every <= 0:
        p.error("--progress-every must be a positive integer")
    return args


def format_seconds(sec: float) -> str:
    m, s = divmod(sec, 60)
    h, m = divmod(int(m), 60)
    if h:
        return f"{h}h {m}m {s:.0f}s"
    if m:
        return f"{int(m)}m {s:.1f}s"
    return f"{s:.1f}s"


def main() -> None:
    args = parse_args()
    t_start = time.perf_counter()

    total_checked = total_mismatches = total_failures = 0

    with args.log.open("w") as log:
        try:
            for n in range(3, args.max_blocks + 1, 2):
                print(f"n = {n}")
                t_n = time.perf_counter()

                jobs = interesting_canonical_representatives(args.max_abs, n)
                checked, mismatches, failures = run_verification(jobs, args, log)

                total_checked += checked
                total_mismatches += mismatches
                total_failures += failures

                print(f"  n={n}: {checked} checked, {mismatches} mismatches, "
                      f"{failures} failures in "
                      f"{format_seconds(time.perf_counter() - t_n)}\n")
        except KeyboardInterrupt:
            print("\nInterrupted.", file=sys.stderr)

    dt_total = time.perf_counter() - t_start

    print("=== SUMMARY ===")
    print(f"Total checked:  {total_checked}")
    print(f"Mismatches:     {total_mismatches}")
    print(f"Failures:       {total_failures}")
    print(f"Total time:     {format_seconds(dt_total)}")
    if total_checked:
        print(f"Average rate:   {total_checked / dt_total:.0f} knots/s")
    print(f"Log file:       {args.log}")


if __name__ == "__main__":
    main()
