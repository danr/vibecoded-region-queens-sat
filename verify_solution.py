queens = [0, 5, 8, 2, 7, 4, 1, 3, 6]
print('Solution:', queens)
print('All columns distinct:', len(set(queens)) == len(queens))
print('Diagonal check:')
for i in range(len(queens)-1):
    diff = abs(queens[i] - queens[i+1])
    print(f'  |{queens[i]} - {queens[i+1]}| = {diff} (OK: {diff != 1})')