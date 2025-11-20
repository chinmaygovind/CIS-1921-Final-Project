from mini_sudoku import MiniSudokuSATSolver


test_board = [
    [0, 0, 3, 4, 0, 0],
    [0, 2, 0, 0, 5, 0],
    [1, 0, 0, 0, 0, 6],
    [0, 0, 5, 3, 0, 0],
    [0, 6, 0, 0, 1, 0],
    [2, 0, 0, 0, 0, 4]
]

solver = MiniSudokuSATSolver(test_board)
print(solver.solve())