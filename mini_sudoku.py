import pycosat
import random

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
    
    # generate a mini sudoku puzzle with p pieces and exactly 1 solution a la homework 1
    def generate_mini_sudoku(self, p):
        # implement this algorithm by generating a full solution and removing numbers, and using our sat model to ensure uniqueness
        board = [list(range(1, 7)) for _ in range(6)]
        # randomly shuffle rows and columns within their groups
        num_shuffles = 50
        for _ in range(num_shuffles):
            # shuffle rows within row groups
            for rg in range(3):
                r1 = random.randint(0, 1) + rg * 2
                r2 = random.randint(0, 1) + rg * 2
                board[r1], board[r2] = board[r2], board[r1]
            # shuffle columns within column groups
            for cg in range(2):
                c1 = random.randint(0, 2) + cg * 3
                c2 = random.randint(0, 2) + cg * 3
                for r in range(6):
                    board[r][c1], board[r][c2] = board[r][c2], board[r][c1]

        # remove numbers until only p pieces remain, ensuring uniqueness
        cells = [(r, c) for r in range(6) for c in range(6)]
        random.shuffle(cells)
        num_remaining = 36
        fails = 0
        to_try = 0
        while num_remaining > p:
            r, c = cells[to_try]
            original_value = board[r][c]
            board[r][c] = 0
            self.grid = board
            self.clauses = []
            self.add_givens()
            self.add_cell_constraints()
            self.add_row_col_subgrid_constraints()
            solution = pycosat.solve(self.clauses)
            # check if solution is unique by adding constraints to exclude the original solution
            new_constraint = [-self.x(r, c, v) for r in range(6) for c in range(6) for v in range(1, 7) if board[r][c] == v]
            self.clauses.append(new_constraint)
            second_solution = pycosat.solve(self.clauses)
            if second_solution != 'UNSAT':
                # not unique, restore the value
                board[r][c] = original_value
                to_try += 1
                if to_try >= len(cells):
                    return self.generate_mini_sudoku(p)
            else:
                # solution unique, removal successful
                cells.remove((r, c))
                num_remaining -= 1
                to_try = 0
        return board