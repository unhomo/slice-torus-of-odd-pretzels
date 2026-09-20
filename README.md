# tau-odd-pretzel

Numerical verification of the conjectured formula

$$
2\tau(\text{P}(a_{1}, \ldots, a_{n})) = -\sum_{i}\text{sign}(a_{i}) + \text{sign}(a_{\min})
$$

for the Ozsváth–Szabó tau-invariant of odd pretzel knots, where
$a_{\min}$ is the parameter of minimal absolute value in the multiset
obtained from the multiset $\lbrace a_{1}, \ldots, a_{n} \rbrace$ by iteratively removing
pairs of the form $\lbrace t, -t \rbrace$ until no such pair remains.

Companion code for the paper *Explicit formula for the Rasmussen invariant of
odd pretzel knots* by Yury Belousov and Vadim Stepaniuk.

## How it works

The script enumerates odd pretzel parameters not covered by Theorem 2,
one representative per orbit under cyclic shifts, reversal, and global
sign change, skipping tuples that contain both $1$ and $-1$ (such blocks
cancel in pairs by isotopy). For each tuple it builds the PD code
using `pretzel_pd.py` by [Ashley Alfaro](https://github.com/ashley-alf/pretzel_pd),
computes tau via `knot_floer_homology`, and compares the result to the
conjectured formula.

## Requirements

- `python 3.10+`
- [`knot_floer_homology`](https://github.com/3-manifolds/knot_floer_homology)

## Usage

    python main.py --max-abs 17 --max-blocks 5
    python main.py --help

## Results

| max-abs | max-blocks | checked | mismatches |
|---------|------------|---------|------------|
| 17      | 5          | 3164    | 0          |
| 9       | 7          | 9354    | 0          |

## License

MIT — see `LICENSE`.
