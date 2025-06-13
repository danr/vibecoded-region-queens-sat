from z3 import *
from itertools import combinations, chain, product
import sys

solver = Solver()
size = 9  # N

# queens[n] = col of queen on row n
# by construction, not on same row
queens = IntVector('q', size)

solver.add([And(0 <= i, i < size) for i in queens])
# not on same column
solver.add(Distinct(queens))

# not diagonally adjacent
for i in range(size-1):
    q1, q2 = queens[i], queens[i+1]
    solver.add(Abs(q1 - q2) != 1)

region_pattern = [
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

def parse_regions():
    colormap = ["", "purple", "red", "brown", "white", "green", "yellow", "orange", "blue", "pink"]
    regions = {color: [] for color in colormap[1:]}
    
    for row, line in enumerate(region_pattern):
        for col, char in enumerate(line):
            region_id = int(char)
            color = colormap[region_id]
            regions[color].append((row, col))
    
    return regions

regions = parse_regions()

# Sanity checks
all_squares = set(product(range(size), repeat=2))

def test_i_set_up_problem_right():
    assert all_squares == set(chain.from_iterable(regions.values()))

    for r1, r2 in combinations(regions.values(), 2):
        assert not set(r1) & set(r2), set(r1) & set(r2)

def render_regions():
    colormap = ["purple", "red", "brown", "white", "green", "yellow", "orange", "blue", "pink"]
    board = [[0 for _ in range(size)] for _ in range(size)]
    for (row, col) in all_squares:
        for color, region in regions.items():
            if (row, col) in region:
                board[row][col] = colormap.index(color)+1

    for row in board:
        print("".join(map(str, row)))

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test-regions":
        print("Regions dictionary:")
        for color, coords in regions.items():
            print(f"{color}: {coords}")
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == "--smt":
        # Region constraints
        for r in regions.values():
            solver.add(Or(
                *[queens[row] == col for (row, col) in r]
            ))
        print(solver.sexpr())
        return
    
    # Run sanity checks
    test_i_set_up_problem_right()
    render_regions()

    # Region constraints
    for r in regions.values():
        solver.add(Or(
            *[queens[row] == col for (row, col) in r]
        ))

    if solver.check() == sat:
        m = solver.model()
        print([(l, m[l]) for l in queens])
    else:
        print("No solution found")

if __name__ == "__main__":
    main()