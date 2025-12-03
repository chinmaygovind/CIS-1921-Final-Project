from ortools.sat.python import cp_model
import time

class ZipCPSATSolver:

    # grid is a 2D array of ints where 0 is blank cell, 1,2,...,K are numbered cells that have to be visited in order
    # walls is a set of position pairs indicating walls between cells

    def __init__(self, grid, walls=None):

        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        
        if walls is None:
            walls = set()
        
        #makes it so that (a,b) and (b,a) are treated the same
        self.walls = set((min(c1, c2), max(c1, c2)) for edge in walls for c1, c2 in [edge])
        
        self.numbered_cells = {}
        self.cells_to_visit = []
        
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells_to_visit.append((r, c))
                if self.grid[r][c] > 0:  # Numbered cell
                    self.numbered_cells[self.grid[r][c]] = (r, c)
        
        self.n_tiles = len(self.cells_to_visit)
        self.max_number = max(self.numbered_cells.keys())
    
    #checks if there's a wall between two adjacent cells
    def is_wall_between(self, pos1, pos2):
        edge = (min(pos1, pos2), max(pos1, pos2))
        return edge in self.walls
    
    #creates integer variables for the step/time at each cell
    def create_position_variables(self):
        # time[r][c] = step when cell (r,c) is visited (0 to n_tiles-1)
        self.time = {}
        for r, c in self.cells_to_visit:
            self.time[(r, c)] = self.model.NewIntVar(0, self.n_tiles - 1, f'time_{r}_{c}')
        
        # All cells must be visited at different times (ensures Hamiltonian path)
        self.model.AddAllDifferent([self.time[(r, c)] for r, c in self.cells_to_visit])

    
    #adds constraints for starting and ending positions
    def add_start_end_constraints(self):
        r1, c1 = self.numbered_cells[1]
        self.model.Add(self.time[(r1, c1)] == 0)
        
        rk, ck = self.numbered_cells[self.max_number]
        self.model.Add(self.time[(rk, ck)] == self.n_tiles - 1)
    
    
    #adds constraints ensuring consecutive positions are adjacent and not blocked
    def add_adjacency_constraints(self):
        neighbors = {}
        for r, c in self.cells_to_visit:
            nb = []
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if not self.is_wall_between((r, c), (nr, nc)):
                        nb.append((nr, nc))
            neighbors[(r, c)] = nb

        for r, c in self.cells_to_visit:
            nb = neighbors[(r, c)]

            if not nb:
                self.model.Add(self.time[(r, c)] == self.n_tiles - 1)
                continue

            is_last = self.model.NewBoolVar(f"is_last_{r}_{c}")
            self.model.Add(self.time[(r, c)] == self.n_tiles - 1).OnlyEnforceIf(is_last)
            self.model.Add(self.time[(r, c)] <  self.n_tiles - 1).OnlyEnforceIf(is_last.Not())

            succ_bools = []
            for nr, nc in nb:
                b = self.model.NewBoolVar(f"succ_{r}_{c}_to_{nr}_{nc}")
                self.model.Add(self.time[(nr, nc)] == self.time[(r, c)] + 1).OnlyEnforceIf(b)
                self.model.Add(self.time[(nr, nc)] != self.time[(r, c)] + 1).OnlyEnforceIf(b.Not())
                succ_bools.append(b)

            self.model.AddBoolOr([is_last] + succ_bools)
    
    
    #adds constraints ensuring numbered cells are visited in increasing order
    def add_ordering_constraints(self):
        for num in range(2, self.max_number + 1):
            r_curr, c_curr = self.numbered_cells[num]
            r_prev, c_prev = self.numbered_cells[num - 1]
            
            # Simply enforce time ordering
            self.model.Add(self.time[(r_prev, c_prev)] < self.time[(r_curr, c_curr)])

    #extracts the solution path 
    def extract_solution(self, solver):
        # Create a map from time to position
        time_to_pos = {}
        for r, c in self.cells_to_visit:
            t = solver.Value(self.time[(r, c)])
            time_to_pos[t] = (r, c)
        
        # Build path in order
        path = [time_to_pos[i] for i in range(self.n_tiles)]
        return path
    
    def print_solution(self, path):
        if not path:
            print("No solution found")
            return
        
        # Create a grid showing the path order
        path_grid = [[-1 for _ in range(self.cols)] for _ in range(self.rows)]
        for step, (r, c) in enumerate(path):
            path_grid[r][c] = step
        
        
        for r in range(self.rows):
            # Print cell row
            row_str = ""
            for c in range(self.cols):
                step = path_grid[r][c]
                row_str += f"{step:3d} "
                
                # Check for vertical wall to the right
                if c < self.cols - 1:
                    if self.is_wall_between((r, c), (r, c + 1)):
                        row_str += "|"
                    else:
                        row_str += " "
            print(row_str)
            
            # Print horizontal walls below this row
            if r < self.rows - 1:
                wall_str = ""
                for c in range(self.cols):
                    if self.is_wall_between((r, c), (r + 1, c)):
                        wall_str += "----"
                    else:
                        wall_str += "    "
                    if c < self.cols - 1:
                        wall_str += " "
                if wall_str.strip():
                    print(wall_str)
        
    
    def solve(self):
        self.model = cp_model.CpModel()
        self.create_position_variables()
        self.add_start_end_constraints()
        self.add_adjacency_constraints()
        self.add_ordering_constraints()
        
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return self.extract_solution(solver)
        
        return None

if __name__ == "__main__":
    grid = [
        [1, 0, 0, 0, 0, 0],  
        [0, 2, 0, 0, 0, 0],  
        [0, 0, 0, 0, 0, 0], 
        [0, 0, 0, 3, 0, 0],  
        [0, 0, 0, 0, 0, 0],  
        [4, 0, 0, 0, 0, 0],  
    ]

    walls = {
        ((0, 0), (1, 0)),
        ((0, 2), (1, 2)),
        ((1, 1), (2, 1)),
        ((2, 0), (3, 0)),
        ((2, 3), (3, 3)),
        ((3, 2), (4, 2)),
        ((3, 5), (4, 5)),
        ((4, 0), (5, 0)),
        ((4, 3), (5, 3)),
        ((4, 4), (5, 4)),
    }

    solver = ZipCPSATSolver(grid, walls)
    solution = solver.solve()
    if solution:
        solver.print_solution(solution)
    else:
        print("No solution found")
