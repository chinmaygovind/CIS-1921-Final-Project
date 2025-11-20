import pycosat
from collections import defaultdict

class QueensSATSolver:


    # takes in a grid (2d array) and a list of queen positions. grid should have numbers 1-n, where each number represents a region
    def __init__(self, grid, queens):
        self.grid = grid
        self.size = len(grid)
        self.regions = defaultdict(list)
        for r in range(len(grid)):
            for c in range(len(grid)):
                region = grid[r][c]
                self.regions[region].append((r, c))
        if self.size != len(self.regions.keys()):
            raise ValueError("Number of regions must equal grid size")
        self.queens = queens
        self.clauses = []
    
    def x(self, r, c):
        # variable number for cell (r, c). false if no queen, true if queen
        return r * self.size + c + 1
    
    # enforce given queens in the grid
    def add_givens(self):    
        for queen in self.queens:
            r, c = queen
            self.clauses.append([self.x(r, c)])

    def add_rows_cols_constraints(self):
        for i in range(self.size):
            # at least one queen in each row
            self.clauses.append([self.x(i, c) for c in range(self.size)])
            # at most one queen in each row
            for c1 in range(self.size):
                for c2 in range(c1 + 1, self.size):
                    self.clauses.append([-self.x(i, c1), -self.x(i, c2)])
            # at least one queen in each column
            self.clauses.append([self.x(r, i) for r in range(self.size)])
            # at most one queen in each column
            for r1 in range(self.size):
                for r2 in range(r1 + 1, self.size):
                    self.clauses.append([-self.x(r1, i), -self.x(r2, i)])
    
    def add_regions_constraints(self):
        # exactly one queen in each region
        for region_cells in self.regions.values():
            # at least one queen in the region
            self.clauses.append([self.x(r, c) for (r, c) in region_cells])
            # at most one queen in the region
            for i in range(len(region_cells)):
                for j in range(i + 1, len(region_cells)):
                    r1, c1 = region_cells[i]
                    r2, c2 = region_cells[j]
                    self.clauses.append([-self.x(r1, c1), -self.x(r2, c2)])
    
    def solve(self):
        self.add_givens()
        self.add_rows_cols_constraints()
        self.add_regions_constraints()
        
        solution = pycosat.solve(self.clauses)
        if solution == 'UNSAT':
            return None
        
        result_queens = []
        for r in range(self.size):
            for c in range(self.size):
                if solution[self.x(r, c) - 1] > 0:
                    result_queens.append((r, c))
        return result_queens