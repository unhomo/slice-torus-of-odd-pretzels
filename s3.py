"""
Verify the conjecture for s_3 of odd pretzel knots.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from common import (
    Params, conjectured_formula,
    add_common_args, validate_common_args, format_seconds,
    interesting_canonical_representatives,
    load_verified, log_verified, log_mismatch,
)

try:
    from pretzel_pd import tangle_points, pretzel_pd_2
except ImportError:
    sys.exit("pretzel_pd.py not found next to s3.py")


PROJECT_DIR = Path(__file__).resolve().parent
VERIFIED_LOG = PROJECT_DIR / "verified_s3.log"
MISMATCH_LOG = PROJECT_DIR / "mismatches_s3.log"


KNOTJOB_JAR = Path(r"\KnotJob.jar") # <----- edit this path to your local copy of KnotJob.jar
JAVA = "java"


# --------------------------------------------------------------------------- #
# Computation
# --------------------------------------------------------------------------- #

def predicted(params: Params) -> int:
    return conjectured_formula(params)


def pd_string(params: Params) -> str:
    nums = list(params)
    expected = sum(abs(x) for x in nums)
    pd = pretzel_pd_2(nums, tangle_points(nums))
    if pd is None:
        raise RuntimeError("pretzel_pd_2 returned None")
    if len(pd) != expected:
        raise RuntimeError(f"PD length {len(pd)} != {expected}")
    flat = [x for tup in pd for x in tup]
    if 0 in flat:
        flat = [x + 1 for x in flat]
    cnt = Counter(flat)
    if set(cnt) != set(range(1, 2 * len(pd) + 1)) or not all(v == 2 for v in cnt.values()):
        raise RuntimeError("invalid 2-regular PD")
    return "PD[" + ", ".join(f"X[{t[0]},{t[1]},{t[2]},{t[3]}]" for t in pd) + "]"


def run_knotjob(batch, characteristic: int, timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="knotjob_") as tmp:
        tmp = Path(tmp)
        name_map = {}
        for i, (params, pd) in enumerate(batch):
            fname = f"k{i:06d}.txt"
            (tmp / fname).write_text(pd + "\n", encoding="utf-8")
            name_map[fname] = params

        args = [JAVA, "-jar", str(KNOTJOB_JAR), *name_map.keys(),
                f"-sl{characteristic}", "-nf"]
        proc = subprocess.run(args, cwd=str(tmp), capture_output=True,
                              text=True, encoding="utf-8", timeout=timeout)

        header_re = re.compile(rf"^(k\d{{6}}\.txt)_sl3s{characteristic}$")
        value_re = re.compile(
            rf"^sl_3 S-Invariant mod {characteristic}\s*:\s*(-?\d+)\s*$"
        )
        results = {}
        current = None
        for line in proc.stdout.splitlines():
            line = line.strip()
            if m := header_re.match(line):
                current = m.group(1)
            elif (m := value_re.match(line)) and current is not None:
                results[name_map[current]] = int(m.group(1))
                current = None
        return results


# --------------------------------------------------------------------------- #
# CLI and main
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    add_common_args(p)
    p.add_argument("--characteristic", type=int, default=0,
                   help="KnotJob -sl<char> (default 0)")
    p.add_argument("--batch-size", type=int, default=10,
                   help="KnotJob batch size (default 10)")
    p.add_argument("--timeout", type=int, default=600,
                   help="KnotJob timeout per batch, seconds (default 600)")
    args = p.parse_args()
    validate_common_args(p, args)
    if args.batch_size <= 0:
        p.error("--batch-size must be positive")
    if args.timeout <= 0:
        p.error("--timeout must be positive")
    return args


def main() -> None:
    args = parse_args()
    if not KNOTJOB_JAR.exists():
        sys.exit(f"KnotJob.jar not found at {KNOTJOB_JAR}")

    done = set() if args.rerun else load_verified(VERIFIED_LOG)
    print(f"characteristic={args.characteristic}, already verified: {len(done)}")

    total_checked = total_mismatch = total_fail = 0
    t_start = time.perf_counter()

    for n in range(3, args.max_blocks + 1, 2):
        t_n = time.perf_counter()
        todo = [p for p in interesting_canonical_representatives(args.max_abs, n)
                if p not in done]
        print(f"\nn = {n}: {len(todo)} to check")

        to_run = []
        for p in todo:
            try:
                to_run.append((p, pd_string(p)))
            except Exception as e:
                total_fail += 1
                log_mismatch(MISMATCH_LOG, p, None, predicted(p),
                             f"PD-gen: {type(e).__name__}: {e}")

        n_mismatch = n_fail = 0
        for i in range(0, len(to_run), args.batch_size):
            batch = to_run[i:i + args.batch_size]
            try:
                results = run_knotjob(batch, args.characteristic, args.timeout)
            except subprocess.TimeoutExpired:
                for p, _ in batch:
                    n_fail += 1
                    log_mismatch(MISMATCH_LOG, p, None, predicted(p), "timeout")
                continue

            for params, _ in batch:
                pred = predicted(params)
                real = results.get(params)
                if real is None:
                    n_fail += 1
                    log_mismatch(MISMATCH_LOG, params, None, pred, "no result")
                elif real != pred:
                    n_mismatch += 1
                    log_mismatch(MISMATCH_LOG, params, real, pred)
                    print(f"  MISMATCH: {params} -> real={real}, pred={pred}")
                else:
                    log_verified(VERIFIED_LOG, params, real)
                    done.add(params)

            print(f"  batch {i // args.batch_size}: "
                  f"{i + len(batch)}/{len(to_run)}, "
                  f"mismatches={n_mismatch}, failures={n_fail}")

        total_checked += len(to_run)
        total_mismatch += n_mismatch
        total_fail += n_fail
        print(f"  n={n}: {len(to_run)} checked, {n_mismatch} mismatches, "
              f"{n_fail} failures in {format_seconds(time.perf_counter() - t_n)}")

    print("\n=== SUMMARY ===")
    print(f"Checked:    {total_checked}")
    print(f"Mismatches: {total_mismatch}")
    print(f"Failures:   {total_fail}")
    print(f"Total time: {format_seconds(time.perf_counter() - t_start)}")


if __name__ == "__main__":
    main()