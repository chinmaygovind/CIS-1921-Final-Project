import random 
import numpy as np
import time
import matplotlib.pyplot as plt
from tqdm import tqdm

from queens import QueensSATSolver
from mini_sudoku import MiniSudokuSATSolver
from tango import TangoCPSATSolver
from zip import ZipCPSATSolver
# class to make sample puzzles for each of the 4 puzzles and benchmark their solvers

class Benchmark:
    MINI_SUDOKU_PIECES = range(36, 6, -1)
    QUEEN_SIZES = range(5, 25)
    TANGO_SIZES = range(5, 25)
    ZIP_SIZES = range(5, 25)
    TRIALS_PER_SIZE = 50

    # generate a mini sudoku puzzle with p pieces and exactly 1 solution
    def generate_mini_sudoku(self, p):
        solver = MiniSudokuSATSolver([[0]*6 for _ in range(6)])
        return solver.generate_mini_sudoku(p)
    
    # generate a queen puzzle of size n with q queens already given
    def generate_queens(self, n, q):
        queen_positions = []
        fails = 0
        while len(queen_positions) < n:
            remaining_valid = []
            for r in range(n):
                for c in range(n):
                    # any() and all() is my favorite function i learned from this class
                    if all(r != qr and c != qc and abs(r - qr) != abs(c - qc) for (qr, qc) in queen_positions):
                        remaining_valid.append((r, c))
            if not remaining_valid:
                queen_positions = []
                continue
            queen_positions.append(random.choice(remaining_valid))
        board = [[random.choice(range(1, n + 1)) for _ in range(n)] for _ in range(n)]
        for i, (r, c) in enumerate(queen_positions):
            board[r][c] = i + 1
        return board, queen_positions[:q]
    
    def benchmark_mini_sudoku(self):
        pieces = self.MINI_SUDOKU_PIECES
        results = np.zeros((len(pieces), self.TRIALS_PER_SIZE))
        for i, p in tqdm(enumerate(pieces), total=len(pieces), desc='Benchmarking Mini Sudoku'):
            for t in range(self.TRIALS_PER_SIZE):
                solver = MiniSudokuSATSolver([[0]*6 for _ in range(6)])
                puzzle = solver.generate_mini_sudoku(p)
                solver = MiniSudokuSATSolver(puzzle)
                start = time.time()
                solver.solve()
                elapsed = time.time() - start
                results[i, t] = elapsed
        results = np.median(results, axis=1)
        return pieces, results

    def plot_mini_sudoku(self):
        pieces, times = self.benchmark_mini_sudoku()
        plt.plot(pieces, times, label='Mini Sudoku')
        plt.xlabel('Number of Given Pieces')
        plt.ylabel('Median Solve Time (s)')
        plt.title('Puzzle Solver Benchmark')
        plt.legend()
        plt.grid(True)
        plt.show()

    def benchmark_queens(self):
        sizes = self.QUEEN_SIZES
        q = 1
        results = np.zeros(len(sizes))
        for i, n in tqdm(enumerate(sizes), total=len(sizes), desc='Benchmarking Queens'):
            for _ in range(self.TRIALS_PER_SIZE):
                grid, queens = self.generate_queens(n, q)
                solver = QueensSATSolver(grid, queens)
                start = time.time()
                solver.solve()
                elapsed = time.time() - start
                results[i] += elapsed
            results[i] /= self.TRIALS_PER_SIZE
        return sizes, results
    
    def plot_queens_zip_tango(self):
        queen_sizes, queen_times = self.benchmark_queens()
        plt.plot(queen_sizes, queen_times, label='Queens')
        # add this for zip, tango - TODO: nick
        plt.xlabel('Puzzle Size')
        plt.ylabel('Average Solve Time (s)')
        plt.title('Puzzle Solver Benchmark')
        plt.legend()
        plt.grid(True)
        plt.show()


if __name__ == "__main__":
    benchmark = Benchmark()
    benchmark.plot_mini_sudoku()