from z3 import *
from itertools import combinations, chain, product
import sys
import subprocess
import os
import argparse
from typing import *

# Type aliases for Z3 types  
Z3Solver = Solver
Z3BitVec = BitVecRef
Z3ExprRef = ExprRef
Z3Goal = Goal
Z3Tactic = Tactic
Z3ApplyResult = ApplyResult
Z3Model = Model
Z3CheckSatResult = CheckSatResult

size: int = 9  # N
bits_per_queen: int = 4  # ceil(log2(9))

region_pattern: List[str] = [
    "111111111",
    "112333999",
    "122439999",
    "124437799",
    "124666779",
    "124467799",
    "122467899",
    "122555889",
    "112258899"
]

def parse_regions() -> Dict[str, List[Tuple[int, int]]]:
    colormap = ["", "purple", "red", "brown", "white", "green", "yellow", "orange", "blue", "pink"]
    regions: Dict[str, List[Tuple[int, int]]] = {color: [] for color in colormap[1:]}

    for row, line in enumerate(region_pattern):
        for col, char in enumerate(line):
            region_id = int(char)
            color = colormap[region_id]
            regions[color].append((row, col))

    return regions

regions: Dict[str, List[Tuple[int, int]]] = parse_regions()

def solve_with_bitvectors() -> Tuple[Z3Solver, List[Z3BitVec]]:
    solver: Z3Solver = Solver()

    # queens[n] = col of queen on row n (as bitvectors)
    queens: List[Z3BitVec] = [BitVec(f'q_{i}', bits_per_queen) for i in range(size)]

    # Constrain each queen to valid column positions [0, size)
    for i, q in enumerate(queens):
        solver.add(ULT(q, size))  # Unsigned less than

    # Not on same column - all queens must have different column values
    solver.add(Distinct(queens))
    # Not diagonally adjacent
    for i in range(size-1):
        q1, q2 = queens[i], queens[i+1]
        # |q1 - q2| != 1
        # This is tricky with bitvectors - we need to handle both q1-q2 and q2-q1
        diff1: Z3ExprRef = q1 - q2
        diff2: Z3ExprRef = q2 - q1
        solver.add(And(diff1 != 1, diff2 != 1))
    # Region constraints - exactly one queen per region
    for r in regions.values():
        # Create a constraint that exactly one position in the region has a queen
        region_constraints: List[BoolRef] = []
        for (row, col) in r:
            region_constraints.append(queens[row] == col)
        solver.add(Or(region_constraints))
    return solver, queens

def generate_all_files() -> None:
    """Generate all input files needed for benchmarking"""
    # Create output directory if it doesn't exist
    output_dir: str = "output"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating input files for 9x9 problem in ./{output_dir}/...")

    # Generate DIMACS file with comments
    print("- Generating DIMACS file with variable mapping...")
    solver, queens = solve_with_bitvectors()
    goal: Z3Goal = Goal()
    for assertion in solver.assertions():
        goal.add(assertion)
    tactic: Z3Tactic = Then('bit-blast', 'tseitin-cnf', 'simplify')
    result: Z3ApplyResult = tactic(goal)
    with open(f'{output_dir}/region_queens_clean.dimacs', 'w') as f:
        for subgoal in result:
            dimacs_str: str = subgoal.dimacs()
            f.write(dimacs_str)
    # Generate BitVector SMT file
    print("- Generating BitVector SMT file...")
    with open(f'{output_dir}/region_queens_bitvec.smt2', 'w') as f:
        sexpr_str: str = solver.sexpr()
        f.write(sexpr_str + '\n')
        f.write('(check-sat)\n')
        f.write('(get-model)\n')

    # Generate Integer SMT file
    print("- Generating Integer SMT file...")
    # Create integer solver directly here
    int_solver: Z3Solver = Solver()
    int_queens: List[Any] = IntVector('q', size)

    # Add constraints
    int_solver.add([And(0 <= i, i < size) for i in int_queens])
    int_solver.add(Distinct(int_queens))
    # Diagonal adjacency
    for i in range(size-1):
        q1, q2 = int_queens[i], int_queens[i+1]
        int_solver.add(Abs(q1 - q2) != 1)
    # Region constraints
    for r in regions.values():
        int_solver.add(Or(*[int_queens[row] == col for (row, col) in r]))
    with open(f'{output_dir}/region_queens_int.smt2', 'w') as f:
        int_sexpr_str: str = int_solver.sexpr()
        f.write(int_sexpr_str + '\n')
        f.write('(check-sat)\n')
        f.write('(get-model)\n')

    print("All files generated successfully!")

def run_benchmark() -> None:
    """Run comprehensive benchmark using hyperfine"""
    output_dir: str = "output"

    print("Running comprehensive benchmark for 9x9 problem...")

    # Define all commands to benchmark
    commands: List[str] = [
        f"z3 -dimacs {output_dir}/region_queens_clean.dimacs >/dev/null 2>&1",
        f"minisat {output_dir}/region_queens_clean.dimacs /tmp/minisat_out >/dev/null 2>&1",
        f"glucose -model {output_dir}/region_queens_clean.dimacs >/dev/null 2>&1",
        f"cryptominisat5 {output_dir}/region_queens_clean.dimacs >/dev/null 2>&1",
        f"z3 {output_dir}/region_queens_bitvec.smt2 >/dev/null 2>&1",
        f"z3 {output_dir}/region_queens_int.smt2 >/dev/null 2>&1"
    ]

    # Build hyperfine command
    hyperfine_cmd: List[str] = [
        "hyperfine",
        "--ignore-failure",
        "--warmup", "3",
        "--min-runs", "10",
        "--export-markdown", f"{output_dir}/benchmark.md"
    ] + commands

    print("Running hyperfine benchmark...")
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            hyperfine_cmd, capture_output=True, text=True, check=False
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)

        # Display the markdown table
        benchmark_file: str = f'{output_dir}/benchmark.md'
        if os.path.exists(benchmark_file):
            print("\nBenchmark results:")
            with open(benchmark_file, 'r') as f:
                content: str = f.read()
                print(content)

    except FileNotFoundError:
        print("Error: hyperfine not found. Please install hyperfine first.")
    except Exception as e:
        print(f"Error running benchmark: {e}")

def decode_sat_solution(sat_assignment_file: str) -> Optional[List[int]]:
    """Decode a SAT assignment back to queen positions using DIMACS variable mapping"""
    print("Decoding SAT solution...")

    # First, read the DIMACS file to get variable mapping
    print("- Reading DIMACS variable mapping...")
    var_mapping: Dict[int, str] = {}

    # Try both output directory and current directory for backwards compatibility
    dimacs_paths: List[str] = ["output/region_queens_clean.dimacs", "region_queens_clean.dimacs"]
    dimacs_file: Optional[str] = None

    for path in dimacs_paths:
        if os.path.exists(path):
            dimacs_file = path
            break

    if not dimacs_file:
        print("Error: region_queens_clean.dimacs not found in output/ or current directory. Run --generate-files first.")
        return None

    try:
        with open(dimacs_file, 'r') as f:
            for line in f:
                if line.startswith('c ') and 'k!' in line:
                    # Parse lines like "c 1 k!0"
                    parts: List[str] = line.strip().split()
                    if len(parts) >= 3:
                        dvar: int = int(parts[1])
                        zvar: str = parts[2]
                        var_mapping[dvar] = zvar
                        print(f"  Variable {dvar} -> {zvar}")
    except FileNotFoundError:
        print(f"Error: {dimacs_file} not found. Run --generate-files first.")
        return None

    # Read the SAT assignment
    print("- Reading SAT assignment...")
    try:
        with open(sat_assignment_file, 'r') as f:
            content: str = f.read().strip()
            if content.startswith('SAT'):
                # MiniSat format
                assignment_line: str = content.split('\n')[-1]
            else:
                assignment_line = content

            # Parse assignment
            literals: List[int] = [int(x) for x in assignment_line.split() if x != '0']

    except FileNotFoundError:
        print(f"Error: {sat_assignment_file} not found.")
        return None

    # Create assignment dict
    assignment: Dict[int, bool] = {}
    for lit in literals:
        if lit > 0:
            assignment[lit] = True
        else:
            assignment[abs(lit)] = False

    print("- Decoding BitVector variables...")
    queens_positions: List[int] = []

    # Look for k!0 through k!35 (4 bits × 9 queens)
    for queen_idx in range(9):
        bits: List[bool] = []
        for bit_idx in range(4):
            # Find the Z3 variable name
            z3_var_name: str = f"k!{queen_idx * 4 + bit_idx}"

            # Find corresponding DIMACS variable
            dimacs_var: Optional[int] = None
            for dvar, zvar in var_mapping.items():
                if zvar == z3_var_name:
                    dimacs_var = dvar
                    break

            if dimacs_var is not None:
                bit_value: bool = assignment.get(dimacs_var, False)
                bits.append(bit_value)
                print(f"  Queen {queen_idx}, bit {bit_idx}: {z3_var_name} (DIMACS {dimacs_var}) = {bit_value}")
            else:
                bits.append(False)
                print(f"  Queen {queen_idx}, bit {bit_idx}: {z3_var_name} not found")

        # Convert 4 bits to column position (LSB first)
        col: int = sum(bit * (2**j) for j, bit in enumerate(bits))
        queens_positions.append(col)
        print(f"  -> Queen {queen_idx} at column {col}")

    print(f"\nDecoded solution: {queens_positions}")

    # Verify the solution
    print("\nVerifying solution...")
    if verify_queens_solution(queens_positions):
        print("✅ Solution is valid!")
    else:
        print("❌ Solution is invalid!")

    return queens_positions

def verify_queens_solution(queens: List[int]) -> bool:
    """Verify that a queen solution is valid"""
    positions: List[Tuple[int, int]] = [(i, col) for i, col in enumerate(queens)]
    print(f"Queen positions: {positions}")

    # Check column bounds
    if any(col >= size or col < 0 for col in queens):
        print("ERROR: Queen out of bounds!")
        return False

    # Check if all columns are different (distinct constraint)
    if len(set(queens)) != len(queens):
        print("ERROR: Queens on same column!")
        print(f"Columns: {queens}")
        return False

    # Check diagonal adjacency
    for i in range(len(queens)-1):
        if abs(queens[i] - queens[i+1]) == 1:
            print(f"ERROR: Queens {i} and {i+1} are diagonally adjacent!")
            return False

    # Check region constraints
    print("Checking region constraints...")
    for color, region_coords in regions.items():
        queens_in_region: int = 0
        for row, col in enumerate(queens):
            coord: Tuple[int, int] = (row, col)
            if coord in region_coords:
                queens_in_region += 1
                print(f"  Queen at ({row}, {col}) is in {color} region")

        if queens_in_region != 1:
            print(f"ERROR: {color} region has {queens_in_region} queens (should be 1)!")
            return False
        else:
            print(f"  ✓ {color} region has exactly 1 queen")

    print("✅ All constraints satisfied!")
    return True

def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Region Queens Solver - BitVector Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python region_queens_bitvec.py                        # Solve 9x9 and show solution
  python region_queens_bitvec.py --benchmark            # Run benchmark on 9x9
  python region_queens_bitvec.py --generate-files       # Generate files
  python region_queens_bitvec.py --decode minisat_output.txt  # Decode SAT solution
        """
    )

    parser.add_argument('--test-regions', action='store_true',
                       help='Show the regions dictionary')
    parser.add_argument('--benchmark', action='store_true',
                       help='Generate all files and run comprehensive benchmark')
    parser.add_argument('--generate-files', action='store_true',
                       help='Generate all input files (DIMACS, SMT)')
    parser.add_argument('--smt', action='store_true',
                       help='Output BitVector SMT-LIB format')
    parser.add_argument('--dimacs', action='store_true',
                       help='Output DIMACS CNF format')
    parser.add_argument('--show-formula', action='store_true',
                       help='Show Z3 formula and bit-blasted version')
    parser.add_argument('--decode', metavar='SAT_FILE',
                       help='Decode SAT assignment file back to queen positions')

    args: argparse.Namespace = parser.parse_args()

    if args.test_regions:
        print("Regions dictionary for 9x9 problem:")
        for color, coords in regions.items():
            print(f"{color}: {len(coords)} squares")
        return

    if args.benchmark:
        generate_all_files()
        run_benchmark()
        return

    if args.generate_files:
        generate_all_files()
        return

    if args.decode:
        decode_sat_solution(args.decode)
        return

    if args.smt:
        solver, queens = solve_with_bitvectors()
        print(solver.sexpr())
        return

    if args.show_formula:
        solver, queens = solve_with_bitvectors()
        formula_str: str = solver.sexpr()
        print("Z3 formula for 9x9 problem before bit-blasting:")
        print(formula_str)

        # Try to get bit-blasted version
        print("\nTrying to get bit-blasted version...")

        # Set bit-blasting tactics
        goal: Z3Goal = Goal()
        for assertion in solver.assertions():
            goal.add(assertion)
        # Apply bit-blasting tactic
        tactic: Z3Tactic = Tactic('bit-blast')
        result: Z3ApplyResult = tactic(goal)
        print("Bit-blasted formula:")
        for subgoal in result:
            bit_formula_str: str = subgoal.sexpr()
            print(bit_formula_str)
        return

    if args.dimacs:
        solver, queens = solve_with_bitvectors()

        # Try to convert to DIMACS
        goal: Z3Goal = Goal()
        for assertion in solver.assertions():
            goal.add(assertion)
        # Apply tactics to convert to CNF
        tactic: Z3Tactic = Then('bit-blast', 'tseitin-cnf', 'simplify')
        result: Z3ApplyResult = tactic(goal)
        for subgoal in result:
            dimacs_str: str = subgoal.dimacs()
            # Remove comment lines and header for cleaner DIMACS
            lines: List[str] = dimacs_str.split('\n')
            for line in lines:
                if not line.startswith('c ') and line.strip() and not line.startswith('CNF formula'):
                    print(line)
        return

    # Default: solve the problem
    print("Solving 9x9 region queens problem...")
    solver, queens = solve_with_bitvectors()

    check_result: Z3CheckSatResult = solver.check()
    if check_result == sat:
        m: Z3Model = solver.model()
        solution: List[Tuple[str, Any]] = [(f"q_{i}", m[q]) for i, q in enumerate(queens)]
        print("Solution found:")
        print(solution)
    else:
        print("No solution found")

if __name__ == "__main__":
    main()
