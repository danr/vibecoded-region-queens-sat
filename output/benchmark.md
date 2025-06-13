| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `z3 -dimacs output/region_queens_clean.dimacs >/dev/null 2>&1` | 12.0 ± 0.8 | 9.8 | 15.3 | 1.00 |
| `minisat output/region_queens_clean.dimacs /tmp/minisat_out >/dev/null 2>&1` | 12.6 ± 0.5 | 12.0 | 14.2 | 1.05 ± 0.08 |
| `glucose -model output/region_queens_clean.dimacs >/dev/null 2>&1` | 13.9 ± 0.6 | 13.3 | 16.2 | 1.16 ± 0.09 |
| `cryptominisat5 output/region_queens_clean.dimacs >/dev/null 2>&1` | 14.4 ± 0.6 | 13.7 | 17.0 | 1.20 ± 0.09 |
| `z3 output/region_queens_bitvec.smt2 >/dev/null 2>&1` | 44.9 ± 18.1 | 25.2 | 69.2 | 3.74 ± 1.53 |
| `z3 output/region_queens_int.smt2 >/dev/null 2>&1` | 45.0 ± 14.7 | 21.8 | 61.6 | 3.75 ± 1.25 |
