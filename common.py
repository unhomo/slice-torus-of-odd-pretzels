from __future__ import annotations

import argparse
import itertools
import re
import time
from collections import Counter
from pathlib import Path
from typing import Iterator


Params = tuple[int, ...]


# --------------------------------------------------------------------------- #
#                                    Formula
# --------------------------------------------------------------------------- #

def sign(x: int) -> int:
    return 1 if x > 0 else -1


def min_abs_after_cancellation(params: Params) -> int:
    """
    Return the parameter of minimal absolute value after 
    iteratively removing all pairs {t, -t} from `params`.
    """
    counts = Counter(params)
    survivors = (
        abs_val if counts[abs_val] > counts[-abs_val] else -abs_val
        for abs_val in {abs(a) for a in params}
        if counts[abs_val] != counts[-abs_val]
    )
    return min(survivors, key=abs)


def conjectured_formula(params: Params) -> int:
    sign_sum = sum(sign(a) for a in params)
    return -sign_sum + sign(min_abs_after_cancellation(params))


# --------------------------------------------------------------------------- #
#                                   Filters
# --------------------------------------------------------------------------- #

def has_adjacent_opposites(params: Params) -> bool:
    """
    True iff some cyclically adjacent pair has the form {t, -t}.
    """
    n = len(params)
    return any(params[i] == -params[(i + 1) % n] for i in range(n))


def min_abs_is_mixed(params: Params) -> bool:
    """
    True iff condition (b) of Theorem 2 fails for the original tuple:
    the parameters of minimal absolute value appear with both signs.
    """
    min_abs = min(abs(a) for a in params)
    return len({sign(a) for a in params if abs(a) == min_abs}) == 2


def is_interesting(params: Params) -> bool:
    """
    True iff `params` is outside the scope of Theorem 2, 
    has no cyclically adjacent cancellable pair.
    """
    return (
        not has_adjacent_opposites(params)
        and min_abs_is_mixed(params)
    )

# --------------------------------------------------------------------------- #
#                           Canonical representatives
# --------------------------------------------------------------------------- #

def is_canonical(t: Params) -> bool:
    """
    True iff `t` is the lex-minimum of its orbit under cyclic shifts,
    reversal of the order, and global sign flip.
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
    for k in range(3, max_abs + 1, 2):
        values = tuple(x for x in range(-k, k + 1) if x % 2 and abs(x) > 1)
        for rest in itertools.product(values, repeat=n - 1):
            t = (-k,) + rest
            if is_interesting(t) and is_canonical(t):
                yield t


# --------------------------------------------------------------------------- #
#                                   Logs
# --------------------------------------------------------------------------- #

_OK_RE = re.compile(r"^OK:\s*\(([^)]*)\)\s*->\s*(-?\d+)\s*$")


def load_verified(path: Path) -> set[Params]:
    """
    Return the set of tuples recorded as verified in `path`.
    """
    done: set[Params] = set()
    if not path.exists():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _OK_RE.match(line.strip())
        if not m:
            continue
        params = tuple(int(x.strip()) for x in m.group(1).split(",") if x.strip())
        done.add(params)
    return done


def log_verified(path: Path, params: Params, value: int) -> None:
    """
    Append one verified tuple and its computed invariant to `path`.
    """
    with path.open("a", encoding="utf-8") as f:
        f.write(f"OK: {params} -> {value}\n")


def log_mismatch(path: Path, params: Params, real, pred, reason: str = "") -> None:
    """
    Append a failure or a mismatch to `path`
    """
    with path.open("a", encoding="utf-8") as f:
        if real is None:
            f.write(f"FAILURE: {params} -> predicted={pred} {reason}\n")
        else:
            f.write(f"MISMATCH: {params} -> real={real}, predicted={pred}\n")


# --------------------------------------------------------------------------- #
#                               CLI helpers
# --------------------------------------------------------------------------- #

def add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--max-abs", type=int, default=17,
                   help="maximum |a_i| (odd; default 17)")
    p.add_argument("--max-blocks", type=int, default=5,
                   help="maximum number of blocks (odd; default 5)")
    p.add_argument("--rerun", action="store_true",
                   help="ignore verified.log and recheck everything")


def validate_common_args(p: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.max_abs % 2 == 0:
        p.error("--max-abs must be odd")
    if args.max_blocks % 2 == 0:
        p.error("--max-blocks must be odd")


def format_seconds(sec: float) -> str:
    m, s = divmod(sec, 60)
    h, m = divmod(int(m), 60)
    if h:
        return f"{h}h {m}m {s:.0f}s"
    if m:
        return f"{int(m)}m {s:.1f}s"
    return f"{s:.1f}s"
