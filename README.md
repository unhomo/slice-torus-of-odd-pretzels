# slice-torus-of-odd-pretzels

Numerical verification of the conjectured formula

$$
2\nu(\text{P}(a_{1}, \ldots, a_{n})) = -\sum_{i}\text{sign}(a_{i}) + \text{sign}(a_{\min})
$$

for slice-torus invariants $\tau$ and $\frac{1}{2}s_{3}$ of odd pretzel
knots. Here $a_{\min}$ is the parameter of minimal absolute value in
the multiset obtained from the multiset $\lbrace a_{1}, \ldots, a_{n} \rbrace$ by
iteratively removing pairs of the form $\lbrace t, -t \rbrace$ until
no such pair remains.

Companion code for the paper *Explicit formula for the Rasmussen invariant of
odd pretzel knots* by Yury Belousov and Vadim Stepaniuk.

## Scripts

- `tau.py` — verifies the conjecture for the Ozsváth–Szabó tau-invariant,
  using [`knot_floer_homology`](https://github.com/3-manifolds/knot_floer_homology).
- `s3.py` — verifies the conjecture for the sl(3) Rasmussen invariant,
  using [`KnotJob`](https://maths.dur.ac.uk/users/dirk.schuetz/knotjob.html).

Both scripts enumerate one representative per orbit of pretzel parameters
under cyclic shifts, reversal, and global sign change, skip tuples already
covered by Theorem 2 of the paper, and compare the computed invariant to
the conjectured formula.  Already verified tuples are stored in log files
and skipped on reruns.

## Requirements

- `python 3.10+`
- [`knot_floer_homology`](https://github.com/3-manifolds/knot_floer_homology) — for `tau.py`
- `java` and [`KnotJob`](https://maths.dur.ac.uk/users/dirk.schuetz/knotjob.html) — for `s3.py`

## Setup

For `tau.py`, no extra setup is needed beyond the Python dependencies.

For `s3.py`, edit the constant `KNOTJOB_JAR` at the top of the file to point
to your local copy of `KnotJob.jar`.

## Usage

    python tau.py --max-abs 17 --max-blocks 5
    python s3.py  --max-abs 9  --max-blocks 7

Both scripts accept `--max-abs`, `--max-blocks` and some other options.
Run with `--help` for the full list.

## Results

| invariant | max-abs | max-blocks | checked | mismatches |
|-----------|---------|------------|---------|------------|
| tau       | 19      | 5          | 5220    | 0          |
| tau       | 9       | 7          | 9354    | 0          |
| s3        | 7       | 5          | 39      | 0          |

The log files `verified_tau.log`, `verified_s3.log` from these runs
are in the repository root.

## License

MIT — see `LICENSE`.
