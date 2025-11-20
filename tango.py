from ortools.sat.python import cp_model

class TangoCPSATSolver:

    # n is the size of the grid (n x n), must be even
    # grid is a 2d array of ints where grid[x][y] = (1 for Sun, 0 for Moon, -1 for empty)
    # equals is a list of pairs of positions that must be equal
    # diffs is a list of pairs of positions that must be different

    def __init__(self, n, grid, equals, diffs):
        self.n = n
        self.grid = grid
        self.equals = equals
        self.diffs = diffs
        self.model = cp_model.CpModel()
        # x[r][c] = 1 (Sun), 0 (Moon)
        self.x = [[self.model.NewBoolVar(f"x_{r}_{c}") for c in range(n)]
                  for r in range(n)]
    
    #adds the given clues to the model
    def add_givens(self):
        for r in range(self.n):
            for c in range(self.n):
                if self.grid[r][c] == 1:
                    self.model.Add(self.x[r][c] == 1)
                elif self.grid[r][c] == 0:
                    self.model.Add(self.x[r][c] == 0)
    
    #adds the equality constraints to the model
    def add_equals(self):
        for (r1, c1), (r2, c2) in self.equals:
            self.model.Add(self.x[r1][c1] == self.x[r2][c2])

    #adds the difference constraints to the model   
    def add_diffs(self):
        for (r1, c1), (r2, c2) in self.diffs:
            self.model.Add(self.x[r1][c1] != self.x[r2][c2])
            
    #adds the constraint that no three adjacent cells in a row or column can be the same
    def add_no_three_adjacent(self):
        for r in range(self.n):
            for c in range(self.n):
                if r < self.n - 2:
                    self.model.Add(self.x[r][c] + self.x[r + 1][c] + self.x[r + 2][c] <= 2)
                    self.model.Add(self.x[r][c] + self.x[r + 1][c] + self.x[r + 2][c] >= 1)
                    
                if c < self.n - 2:
                    self.model.Add(self.x[r][c] + self.x[r][c + 1] + self.x[r][c + 2] <= 2)
                    self.model.Add(self.x[r][c] + self.x[r][c + 1] + self.x[r][c + 2] >= 1)
    
    #adds the constraint that each row and column must have equal number of Suns and Moons
    def add_equal_suns_moons(self):
        half_n = self.n // 2
        for r in range(self.n):
            self.model.Add(sum(self.x[r][c] for c in range(self.n)) == half_n)
        for c in range(self.n):
            self.model.Add(sum(self.x[r][c] for r in range(self.n)) == half_n)

    def solve(self):
        self.add_givens()
        self.add_equals()
        self.add_diffs()
        self.add_no_three_adjacent()
        self.add_equal_suns_moons()
        
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        
        if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
            solution = [[solver.Value(self.x[r][c]) for c in range(self.n)] for r in range(self.n)]
            #print solution with symbols
            for row in solution:
                #print sun/moon emojis with same size (the sun is curently wider than the moon)
                print("".join("☀️ " if cell == 1 else "🌙 " for cell in row))
        else:
            raise Exception("No solution found")
# Test case
n = 6
grid_test1 = [
    [-1, 0, 1, 1, 0, -1],
    [ 0, -1, -1, -1, -1,  0],
    [ 1, -1, -1, -1, -1,  0],
    [ 1, -1, -1, -1, -1,  1],
    [ 0, -1, -1, -1, -1,  1],
    [-1,  1,  0,  0,  1, -1],
]

equals_test1 = [
    ((1, 1), (2, 1)),
    ((3, 1), (3, 2)),
]

diffs_test1 = [
    ((1, 2), (2, 2)),
    ((1, 3), (1, 4)),
    ((2, 3), (2, 4)),
    ((3, 3), (4, 3)),
    ((3, 4), (4, 4)),
    ((4, 1), (4, 2)),
]

solver = TangoCPSATSolver(n, grid_test1, equals_test1, diffs_test1)
solver.solve()