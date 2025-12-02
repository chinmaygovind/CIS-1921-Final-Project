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
    
    #creates boolean variables for each step/cell combination
    def create_position_variables(self):
        self.position = {}
        for i in range(self.n_tiles):
            for r, c in self.cells_to_visit:
                self.position[(i, r, c)] = self.model.NewBoolVar(f'pos_{i}_r{r}_c{c}')

    #adds basic constraints ensuring each cell is visited once and each step has one cell
    def add_basic_constraints(self):
        # Each step has exactly one cell
        for i in range(self.n_tiles):
            self.model.Add(sum(self.position[(i, r, c)] for r, c in self.cells_to_visit) == 1)
        
        # Each cell is visited exactly once
        for r, c in self.cells_to_visit:
            self.model.Add(sum(self.position[(i, r, c)] for i in range(self.n_tiles)) == 1)
    
    #adds constraints for starting and ending positions
    def add_start_end_constraints(self):
        r1, c1 = self.numbered_cells[1]
        self.model.Add(self.position[(0, r1, c1)] == 1)
        
        rk, ck = self.numbered_cells[self.max_number]
        self.model.Add(self.position[(self.n_tiles - 1, rk, ck)] == 1)
    
    
    #adds constraints ensuring consecutive positions are adjacent and not blocked
    def add_adjacency_constraints(self):
        for i in range(self.n_tiles - 1):
            for r1, c1 in self.cells_to_visit:
                for r2, c2 in self.cells_to_visit:
                    # If not adjacent or blocked by wall, they can't be consecutive
                    if abs(r1 - r2) + abs(c1 - c2) != 1 or self.is_wall_between((r1, c1), (r2, c2)):
                        self.model.Add(self.position[(i, r1, c1)] + self.position[(i+1, r2, c2)] <= 1)
    
    
    #adds constraints ensuring numbered cells are visited in increasing order
    def add_ordering_constraints(self):
        for num in range(2, self.max_number + 1):
            r_curr, c_curr = self.numbered_cells[num]
            r_prev, c_prev = self.numbered_cells[num - 1]
            
            #find when each numbered cell is visited
            step_curr = self.model.NewIntVar(0, self.n_tiles - 1, f'step_{num}')
            step_prev = self.model.NewIntVar(0, self.n_tiles - 1, f'step_{num-1}')
            
            #link step variables to position variables
            for i in range(self.n_tiles):
                self.model.Add(step_curr == i).OnlyEnforceIf(self.position[(i, r_curr, c_curr)])
                self.model.Add(step_prev == i).OnlyEnforceIf(self.position[(i, r_prev, c_prev)])
            
            #enforce ordering
            self.model.Add(step_prev < step_curr)

    #extracts the solution path 
    def extract_solution(self, solver):
        path = []
        for i in range(self.n_tiles):
            for r, c in self.cells_to_visit:
                if solver.Value(self.position[(i, r, c)]) == 1:
                    path.append((r, c))
                    break
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
        self.add_basic_constraints()
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
