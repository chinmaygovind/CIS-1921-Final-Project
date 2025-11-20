import pycosat

class MiniSudokuSATSolver:

    # grid is a 6x6 list of lists with integers 0-6, 0 = empty
    def __init__(self, grid):
        self.grid = grid
        # grid should be 6x6
        if len(grid) != 6 or any(len(row) != 6 for row in grid):
            raise ValueError("Grid must be 6x6")
        self.clauses = []

    def x(self, r, c, v):
        # variable number for cell (r, c) with value v (1-6)
        return r * 36 + c * 6 + v

    # enforce given values in the grid
    def add_givens(self):    
        for r in range(6):
            for c in range(6):
                v = self.grid[r][c]
                if v > 0:
                    # cell (r, c) is given as value v
                    self.clauses.append([self.x(r, c, v)])
    
    # each cell has exactly one value
    def add_cell_constraints(self):
        for r in range(6):
            for c in range(6):
                # each cell must have at least one value
                self.clauses.append([self.x(r, c, v) for v in range(1, 7)])
                # each cell must have at most one value
                for v1 in range(1, 7):
                    for v2 in range(v1 + 1, 7):
                        self.clauses.append([-self.x(r, c, v1), -self.x(r, c, v2)])

    def add_row_col_subgrid_constraints(self):
        for i in range(6):
            for v in range(1, 7):
                # each value appears exactly once in each row
                self.clauses.append([self.x(i, c, v) for c in range(6)])
                for c1 in range(6):
                    for c2 in range(c1 + 1, 6):
                        self.clauses.append([-self.x(i, c1, v), -self.x(i, c2, v)])
                
                # each value appears exactly once in each column
                self.clauses.append([self.x(r, i, v) for r in range(6)])
                for r1 in range(6):
                    for r2 in range(r1 + 1, 6):
                        self.clauses.append([-self.x(r1, i, v), -self.x(r2, i, v)])
        # each value appears exactly once in each 2x3 subgrid
        for cellr in range(0, 6, 2):
            for cellc in range(0, 6, 3):
                for v in range(1, 7):
                    # at least once in the subgrid
                    self.clauses.append([self.x(r, c, v) 
                                            for r in range(cellr, cellr + 2) 
                                            for c in range(cellc, cellc + 3)])
                    # at most once in the subgrid
                    positions = [(r, c) 
                                 for r in range(cellr, cellr + 2) 
                                 for c in range(cellc, cellc + 3)]
                    for i1 in range(len(positions)):
                        for i2 in range(i1 + 1, len(positions)):
                            r1, c1 = positions[i1]
                            r2, c2 = positions[i2]
                            self.clauses.append([-self.x(r1, c1, v), -self.x(r2, c2, v)])

    def solve(self):
        self.add_givens()
        self.add_cell_constraints()
        self.add_row_col_subgrid_constraints()
        
        solution = pycosat.solve(self.clauses)
        if solution == 'UNSAT':
            return None
        
        result_grid = [[0 for _ in range(6)] for _ in range(6)]
        for r in range(6):
            for c in range(6):
                for v in range(1, 7):
                    if solution[self.x(r, c, v) - 1] > 0:
                        result_grid[r][c] = v
                        break
        return result_grid  