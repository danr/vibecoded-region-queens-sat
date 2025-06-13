# Region Queens SAT/SMT Solver

This project implements a region-based variant of the N-Queens problem using the Z3 theorem prover, comparing different solving approaches (SAT vs SMT) and benchmarking their performance.

## Problem Description

The **Region Queens** problem is a variant of the classic N-Queens puzzle where:
- 9 queens must be placed on a 9×9 board
- No two queens can be in the same column
- No two queens can be diagonally adjacent (one row apart)
- Exactly one queen must be placed in each colored region

The board is divided into 9 colored regions:
```
111111111  (purple: 19 squares)
112333999  (red: 12 squares, brown: 5 squares, pink: 17 squares)
122439999  (white: 7 squares)
124437799  (green: 4 squares, yellow: 5 squares, orange: 7 squares)
124666779  (blue: 5 squares)
124467799
122467899
122555889
112258899
```

## Implementation Approaches

This project implements three different solving approaches:

### 1. BitVector SMT Approach (`region_queens_bitvec.smt2`)
- Uses Z3's BitVector theory with 4-bit vectors for queen positions
- Constraints: `ULT(q_i, 9)`, `Distinct(q_0,...,q_8)`, diagonal adjacency, region constraints
- **Performance**: ~45ms (3.7× slower than SAT)

### 2. Integer SMT Approach (`region_queens_int.smt2`) 
- Uses Z3's Integer theory with integer variables for queen positions
- Constraints: `0 ≤ q_i < 9`, `Distinct(q_0,...,q_8)`, `Abs(q_i - q_{i+1}) ≠ 1`, region constraints
- **Performance**: ~45ms (3.7× slower than SAT)

### 3. SAT Approach (`region_queens_clean.dimacs`)
- BitVector constraints bit-blasted to CNF using Z3's `bit-blast` + `tseitin-cnf` tactics
- Pure Boolean satisfiability with ~160 variables and clauses
- **Performance**: ~12ms (fastest approach)

## Files Generated

The project generates the following output files:

### Input Files
- **`output/region_queens_bitvec.smt2`**: BitVector SMT-LIB2 formulation
- **`output/region_queens_int.smt2`**: Integer SMT-LIB2 formulation  
- **`output/region_queens_clean.dimacs`**: CNF SAT formulation with variable mapping

### Results
- **`output/benchmark.md`**: Comprehensive performance comparison table
- **SAT solutions**: Can be decoded back to queen positions using `--decode`

## Usage

### Basic Usage
```bash
# Solve the problem and show solution
python region_queens_bitvec.py

# Show the region layout
python region_queens_bitvec.py --test-regions

# Generate all input files
python region_queens_bitvec.py --generate-files

# Run comprehensive benchmark
python region_queens_bitvec.py --benchmark
```

### Advanced Usage
```bash
# Output SMT-LIB2 format
python region_queens_bitvec.py --smt

# Output DIMACS CNF format  
python region_queens_bitvec.py --dimacs

# Show Z3 formulas before/after bit-blasting
python region_queens_bitvec.py --show-formula

# Decode SAT solution back to queen positions
python region_queens_bitvec.py --decode /tmp/minisat_out
```

## Benchmark Results

Performance comparison using `hyperfine` (mean ± std dev):

| Solver | Time [ms] | Relative Performance |
|:-------|----------:|---------------------:|
| **Z3 (SAT mode)** | 12.0 ± 0.8 | **1.00× (fastest)** |
| **MiniSat** | 12.6 ± 0.5 | 1.05× |
| **Glucose** | 13.9 ± 0.6 | 1.16× |
| **CryptoMiniSat** | 14.4 ± 0.6 | 1.20× |
| Z3 (BitVector SMT) | 44.9 ± 18.1 | 3.74× |
| Z3 (Integer SMT) | 45.0 ± 14.7 | 3.75× |

**Key Findings**:
- SAT solvers are ~4× faster than SMT approaches for this constraint problem
- All SAT solvers perform similarly (within 20% of each other)  
- SMT provides more readable constraints but with significant performance cost

## Technical Implementation

### Constraint Encoding
The problem uses several types of constraints:

**Column Uniqueness**: `Distinct(q_0, q_1, ..., q_8)`
- Each queen must be in a different column

**Diagonal Adjacency**: `|q_i - q_{i+1}| ≠ 1`
- Queens in adjacent rows cannot be diagonally adjacent
- BitVector: `(q_i - q_{i+1} ≠ 1) ∧ (q_{i+1} - q_i ≠ 1)`
- Integer: `Abs(q_i - q_{i+1}) ≠ 1`

**Region Constraints**: `Or(q_0 = col_0, q_1 = col_1, ...) for each region`
- Exactly one queen per colored region
- Each region constraint is a disjunction over valid positions

### Z3 Type Stubs
The project includes comprehensive type stubs (`z3.pyi`) for the Z3 theorem prover library:
- Handles Z3's unique behavior where comparison operators return symbolic expressions
- Provides complete type safety for all Z3 operations used
- Eliminates all pyright type checking errors

### Bit-Blasting Process
The SAT encoding uses Z3's bit-blasting to convert BitVector constraints to CNF:
```
Z3 BitVector SMT → bit-blast → Tseitin CNF → simplify → DIMACS
```

## Dependencies

- **Python 3.12+**
- **Z3 Theorem Prover** (`pip install z3-solver`)
- **Hyperfine** (for benchmarking): `cargo install hyperfine`
- **SAT Solvers** (optional, for comparison):
  - MiniSat: `apt install minisat`
  - Glucose: `apt install glucose`  
  - CryptoMiniSat: `apt install cryptominisat`

## Expected Results

When you run the benchmark, you should see:
1. **Fast SAT solving** (~12-15ms) with all SAT solvers performing similarly
2. **Slower SMT solving** (~40-50ms) due to theory reasoning overhead
3. **Valid solutions** that satisfy all constraints when decoded
4. **Performance ranking**: SAT ≫ SMT for this constraint satisfaction problem

The results demonstrate the classical tradeoff in constraint solving:
- **SAT**: Fast but requires manual constraint encoding
- **SMT**: Expressive high-level constraints but slower solving

## References

- Inspired by "Solving LinkedIn Queens with SMT" blog post
- Demonstrates practical SAT vs SMT performance comparison
- Shows Z3's versatility across different theories (BitVector, Integer, SAT)