import random 
import numpy as np
import time
import matplotlib.pyplot as plt
from tqdm import tqdm

from queens import QueensSATSolver
from mini_sudoku import MiniSudokuSATSolver
from tango import TangoCPSATSolver
from zip_integer import ZipCPSATSolver
# class to make sample puzzles for each of the 4 puzzles and benchmark their solvers

class Benchmark:
    MINI_SUDOKU_PIECES = range(36, 6, -1)
    QUEEN_SIZES = range(5, 25)
    TANGO_SIZES = range(6, 25, 2)
    ZIP_SIZES = range(5, 11)
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
    
    def generate_tango(self, n):
        grid = [[-1] * n for _ in range(n)]
        equals = []
        diffs = []
        
        solver = TangoCPSATSolver(n, grid, equals, diffs)
        solution = solver.solve()
        
        # create a puzzle by removing some cells
        puzzle = [[-1] * n for _ in range(n)]
        num_givens = max(2, n * n // 5)
        given_positions = random.sample([(r, c) for r in range(n) for c in range(n)], num_givens)
        
        for r, c in given_positions:
            puzzle[r][c] = solution[r][c]
        
        # add some equals and diffs constraints
        num_constraints = max(1, n // 2)
        all_positions = [(r, c) for r in range(n) for c in range(n)]
        
        for _ in range(num_constraints):
            pos1, pos2 = random.sample(all_positions, 2)
            r1, c1 = pos1
            r2, c2 = pos2
            
            if solution[r1][c1] == solution[r2][c2]:
                equals.append((pos1, pos2))
            else:
                diffs.append((pos1, pos2))
        
        return puzzle, equals, diffs
    
    def benchmark_tango(self):
        sizes = self.TANGO_SIZES
        results = np.zeros(len(sizes))
        for i, n in tqdm(enumerate(sizes), total=len(sizes), desc='Benchmarking Tango'):
            for _ in range(self.TRIALS_PER_SIZE):
                grid, equals, diffs = self.generate_tango(n)
                solver = TangoCPSATSolver(n, grid, equals, diffs)
                start = time.time()
                solver.solve()
                elapsed = time.time() - start
                results[i] += elapsed
            results[i] /= self.TRIALS_PER_SIZE  
        return sizes, results
    
    def generate_zip(self, size):
        rows = cols = size
        grid = [[0] * cols for _ in range(rows)]
        
        # generates simple snake path
        path = []
        for r in range(rows):
            if r % 2 == 0:
                for c in range(cols):
                    path.append((r, c))
            else:
                for c in range(cols - 1, -1, -1):
                    path.append((r, c))
        
        # place random number of numbered cells along the path
        k = random.randint(4, max(5, size // 2))
        k = min(k, len(path))
        step_interval = len(path) // k
        numbered_positions = [path[i * step_interval] for i in range(k)]
        
        for num, (r, c) in enumerate(numbered_positions, 1):
            grid[r][c] = num
        
        # add walls that don't break the Hamiltonian path
        walls = set()
        path_edges = set()
        for i in range(len(path) - 1):
            edge = (min(path[i], path[i+1]), max(path[i], path[i+1]))
            path_edges.add(edge)
        
        all_edges = []
        for r in range(rows):
            for c in range(cols):
                if c < cols - 1:
                    all_edges.append((min((r, c), (r, c+1)), max((r, c), (r, c+1))))
                if r < rows - 1:
                    all_edges.append((min((r, c), (r+1, c)), max((r, c), (r+1, c))))
        
        available_edges = [e for e in all_edges if e not in path_edges]
        if available_edges:
            num_walls = min(len(available_edges) // 5, len(available_edges))
            if num_walls > 0:
                walls = set(random.sample(available_edges, num_walls))
        
        return grid, walls
    
    def benchmark_zip(self):
        sizes = self.ZIP_SIZES
        results = np.zeros(len(sizes))
        for i, n in tqdm(enumerate(sizes), total=len(sizes), desc='Benchmarking Zip'):
            for _ in range(self.TRIALS_PER_SIZE):
                grid, walls = self.generate_zip(n)
                solver = ZipCPSATSolver(grid, walls)
                start = time.time()
                solver.solve()
                elapsed = time.time() - start
                results[i] += elapsed
            results[i] /= self.TRIALS_PER_SIZE
        return sizes, results
    
    def plot_queens_zip_tango(self):
        #queen_sizes, queen_times = self.benchmark_queens()
        #tango_sizes, tango_times = self.benchmark_tango()
        zip_sizes, zip_times = self.benchmark_zip()
        
        #plt.plot(queen_sizes, queen_times, label='Queens')
        #plt.plot(tango_sizes, tango_times, label='Tango')
        plt.plot(zip_sizes, zip_times, label='Zip')
        
        plt.xlabel('Puzzle Size')
        plt.ylabel('Average Solve Time (s)')
        plt.title('Puzzle Solver Benchmark')
        plt.legend()
        plt.grid(True)
        plt.show()


if __name__ == "__main__":
    benchmark = Benchmark()
    benchmark.plot_queens_zip_tango()