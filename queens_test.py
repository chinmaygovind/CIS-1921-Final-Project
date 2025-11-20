from queens import QueensSATSolver
import unittest

class TestQueensSATSolver(unittest.TestCase):
    def test_daily_11_20_2025(self):
        grid = [
            [1, 2, 2, 3, 4, 4, 4, 5],
            [1, 1, 2, 3, 3, 4, 4, 5],
            [6, 1, 1, 1, 1, 4, 4, 5],
            [6, 6, 1, 1, 1, 1, 4, 5],
            [7, 7, 1, 1, 1, 1, 4, 1],
            [8, 7, 1, 1, 1, 1, 1, 1],
            [8, 8, 8, 1, 1, 1, 1, 1],
            [8, 8, 8, 8, 8, 1, 1, 1]
        ]
        queens = [(0, 2), (1, 4)]
        solver = QueensSATSolver(grid, queens)
        solution = solver.solve()
        print(solution)
        self.assertIsNotNone(solution)