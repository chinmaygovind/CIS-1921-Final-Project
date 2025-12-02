# heavily vibe coded the visualizer since GUI wasn't focus of the project
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import time
import os
from math import floor


from mini_sudoku import MiniSudokuSATSolver
from queens import QueensSATSolver
from tango import TangoCPSATSolver
from zip import ZipCPSATSolver


class Visualizer:
	def __init__(self, root):
		self.root = root
		self.root.title("Linkedin Games Solver")
		self.images_dir = os.path.join(os.path.dirname(__file__), 'images')
		# keep image refs to avoid GC
		self._images = {}
		self.current_frame = None
		self.create_styles()
		self.show_main_menu()

	def create_styles(self):
		style = ttk.Style()
		try:
			style.theme_use('clam')
		except Exception:
			pass
		# set default fonts to Roboto where possible
		try:
			import tkinter.font as tkfont
			default = tkfont.nametofont('TkDefaultFont')
			default.configure(family='Roboto')
			header = tkfont.nametofont('TkHeadingFont') if 'TkHeadingFont' in tkfont.names() else None
			if header:
				header.configure(family='Roboto')
		except Exception:
			# ignore if Roboto not available; fallback will use system font
			pass

	def clear_current(self):
		if self.current_frame is not None:
			self.current_frame.destroy()
			self.current_frame = None

	def load_icon(self, name, size=(64, 64)):
		path = os.path.join(self.images_dir, name)
		try:
			from PIL import Image, ImageTk
			img = Image.open(path).convert('RGBA')
			# resize with antialias
			img = img.resize(size, Image.LANCZOS)
			# composite onto white background to avoid black alpha artifacts
			bg = Image.new('RGBA', img.size, (255, 255, 255, 0))
			bg.paste(img, (0, 0), img)
			photo = ImageTk.PhotoImage(bg)
			# store reference to prevent GC
			self._images[name] = photo
			return photo
		except Exception:
			return None

	def show_main_menu(self):
		self.clear_current()
		frame = ttk.Frame(self.root, padding=16)
		self.current_frame = frame
		frame.pack(fill='both', expand=True)

		title = ttk.Label(frame, text='Linkedin Games Solver', font=(None, 24, 'bold'))
		title.pack(pady=(4, 0))
		subtitle = ttk.Label(frame, text='CIS 1921 Final Project', font=(None, 12))
		subtitle.pack()
		authors = ttk.Label(frame, text='By Chinmay Govind and Nick Tarsis', font=(None, 10))
		authors.pack(pady=(0, 12))

		buttons_frame = ttk.Frame(frame)
		buttons_frame.pack()

		# button definitions: (label, image file, callback)
		defs = [
			("Mini Sudoku", 'icon_mini_sudoku.png', self.show_mini_sudoku),
			("Queens", 'icon_queens.png', self.show_queens),
			("Tango", 'icon_tango.png', self.show_tango),
			("Zip", 'icon_zip.png', self.show_zip),
		]

		for i, (label, imgfile, cb) in enumerate(defs):
			icon = self.load_icon(imgfile)
			b = ttk.Button(buttons_frame, text=label, command=cb, compound='top')
			if icon:
				b.image = icon
				b.config(image=icon)
			b.grid(row=0, column=i, padx=8, ipadx=8, ipady=8)

	# ---------------- Mini Sudoku ----------------
	def show_mini_sudoku(self):
		self.clear_current()
		frame = ttk.Frame(self.root, padding=8)
		self.current_frame = frame
		frame.pack(fill='both', expand=True)

		header = ttk.Label(frame, text='Mini Sudoku (6x6)', font=(None, 16, 'bold'))
		header.pack()

		# Use canvas style like the Queens board so styling and hover are consistent
		self.ms_values = [[0 for _ in range(6)] for _ in range(6)]
		self.ms_user_placed = [[False for _ in range(6)] for _ in range(6)]
		self.ms_selected_number = None
		self.ms_cell_size = 48
		self.ms_canvas = tk.Canvas(frame, width=self.ms_cell_size*6, height=self.ms_cell_size*6)
		self.ms_canvas.pack(pady=8)
		self.ms_draw()
		self.ms_canvas.bind('<Motion>', self.ms_on_motion)
		self.ms_canvas.bind('<Leave>', lambda e: self.ms_canvas.delete('hover'))
		self.ms_canvas.bind('<Button-1>', self.ms_on_click)

		# number buttons (click a number then click a cell to place it)
		numbers_frame = ttk.Frame(frame)
		numbers_frame.pack(pady=6)
		for v in range(1, 7):
			b = ttk.Button(numbers_frame, text=str(v), command=lambda val=v: self.ms_select_number(val))
			b.pack(side='left', padx=4)
		blank = ttk.Button(numbers_frame, text='Blank', command=lambda: self.ms_select_number(0))
		blank.pack(side='left', padx=8)

		actions = ttk.Frame(frame)
		actions.pack(pady=6)
		solve_btn = ttk.Button(actions, text='Solve', command=self.ms_solve)
		solve_btn.pack(side='left', padx=6)
		clear_btn = ttk.Button(actions, text='Clear Board', command=self.ms_clear_board)
		clear_btn.pack(side='left', padx=6)
		back = ttk.Button(actions, text='Back', command=self.show_main_menu)
		back.pack(side='left')

		self.ms_status = ttk.Label(frame, text='Click a number, then click a cell to place it')
		self.ms_status.pack()

	def ms_draw(self):
		c = self.ms_canvas
		s = self.ms_cell_size
		c.delete('all')
		for r in range(6):
			for col in range(6):
				x0 = col * s
				y0 = r * s
				x1 = x0 + s
				y1 = y0 + s
				c.create_rectangle(x0, y0, x1, y1, fill='white', outline='black')
				val = self.ms_values[r][col]
				if val > 0:
					c.create_text(x0 + s/2, y0 + s/2, text=str(val), font=('Arial', int(s/2)))
				# user-placed highlight
				if getattr(self, 'ms_user_placed', None) and self.ms_user_placed[r][col]:
					c.create_rectangle(x0+3, y0+3, x1-3, y1-3, outline='#ff9900', width=3, tags='user-placed')

	def ms_select_number(self, val):
		self.ms_selected_number = val
		self._ms_set_status(f'Selected: {"Blank" if val==0 else val}. Click a cell to place.')

	def ms_on_motion(self, event):
		# highlight the cell under cursor
		cell = self._coord_to_cell(event.x, event.y, self.ms_cell_size, 6)
		self.ms_canvas.delete('hover')
		if cell is None:
			return
		r, c = cell
		x0 = c * self.ms_cell_size
		y0 = r * self.ms_cell_size
		x1 = x0 + self.ms_cell_size
		y1 = y0 + self.ms_cell_size
		self.ms_canvas.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline='#ff9900', width=3, tags='hover')

	def ms_on_click(self, event):
		cell = self._coord_to_cell(event.x, event.y, self.ms_cell_size, 6)
		if cell is None:
			return
		r, c = cell
		if self.ms_selected_number is None:
			# do nothing until a number is selected
			self._ms_set_status('Select a number first')
			return
		# place user number (or blank)
		self.ms_values[r][c] = self.ms_selected_number
		self.ms_user_placed[r][c] = (self.ms_selected_number != 0)
		self.ms_draw()


	def ms_solve(self):
		if MiniSudokuSATSolver is None:
			messagebox.showerror('Solver missing', 'Mini Sudoku solver not available (missing imports)')
			return

		grid = [[self.ms_values[r][c] for c in range(6)] for r in range(6)]
		start = time.time()
		try:
			solver = MiniSudokuSATSolver(grid)
			sol = solver.solve()
		except Exception as e:
			messagebox.showerror('Solve error', str(e))
			return
		elapsed = time.time() - start
		if sol is None:
			self._ms_set_status('No solution found')
			return

		# update values and redraw; highlight cells solver filled
		self._ms_last_original = [row[:] for row in grid]
		for r in range(6):
			for c in range(6):
				self.ms_values[r][c] = sol[r][c]
		self.ms_draw()
		c = self.ms_canvas
		s = self.ms_cell_size
		for r in range(6):
			for col in range(6):
				if self._ms_last_original[r][col] == 0:
					x0 = col * s
					y0 = r * s
					x1 = x0 + s
					y1 = y0 + s
					c.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline='#3b82f6', width=3, tags='solver-filled')
					# clear user highlight for solver-filled cells
					if getattr(self, 'ms_user_placed', None):
						self.ms_user_placed[r][col] = False

		self._ms_set_status(f'Solved in {elapsed:.3f} seconds')

	# ---------------- Queens ----------------
	def show_queens(self):
		self.clear_current()
		frame = ttk.Frame(self.root, padding=8)
		self.current_frame = frame
		frame.pack(fill='both', expand=True)

		header = ttk.Label(frame, text='Queens', font=(None, 16, 'bold'))
		header.pack()

		size = simpledialog.askinteger('Board size', 'Enter N for N x N board (e.g. 6):', parent=self.root, minvalue=2, maxvalue=20)
		if not size:
			self.show_main_menu()
			return
		self.qN = size
		self.q_regions = [[0 for _ in range(size)] for _ in range(size)]
		self.q_queens = set()

		canvas = tk.Canvas(frame, width=40*size, height=40*size)
		canvas.pack(pady=8)
		self.q_canvas = canvas
		self.q_cell_size = 40
		# load queen image
		self.q_queen_img = self.load_icon('queen.png', size=(int(self.q_cell_size*0.8), int(self.q_cell_size*0.8)))
		self.q_draw_grid()
		# bind hover events for queens canvas
		self.q_canvas.bind('<Motion>', self.q_on_motion)
		self.q_canvas.bind('<Leave>', lambda e: self.q_canvas.delete('hover'))

		controls = ttk.Frame(frame)
		controls.pack()
		self.q_color = 1
		colors = self.generate_colors(self.qN)
		for i, col in enumerate(colors, start=1):
			b = tk.Button(controls, text=str(i), bg=col, command=lambda v=i: self.q_set_color(v))
			b.pack(side='left', padx=2)

		queen_btn = ttk.Button(controls, text='Queen Mode', command=self.q_toggle_queen_mode)
		queen_btn.pack(side='left', padx=6)
		# support drag painting while holding left mouse button
		self.q_canvas.bind('<B1-Motion>', self.q_on_drag)
		# clear button
		clear_btn = ttk.Button(controls, text='Clear Board', command=self.q_clear_board)
		clear_btn.pack(side='left', padx=6)
		solve_btn = ttk.Button(controls, text='Solve', command=self.q_solve)
		solve_btn.pack(side='left', padx=6)
		back = ttk.Button(controls, text='Back', command=self.show_main_menu)
		back.pack(side='left', padx=6)

		self.q_mode = 'color'  # or 'queen'
		self.q_status = ttk.Label(frame, text='Click a color then click cells to paint regions. Use Queen Mode to place queens.')
		self.q_status.pack()
		canvas.bind('<Button-1>', self.q_on_click)

	def q_draw_grid(self):
		c = self.q_canvas
		n = self.qN
		s = self.q_cell_size
		c.delete('all')
		for r in range(n):
			for col in range(n):
				x0 = col * s
				y0 = r * s
				x1 = x0 + s
				y1 = y0 + s
				region = self.q_regions[r][col]
				fill = self.generate_colors(self.qN)[region-1] if region > 0 else 'white'
				c.create_rectangle(x0, y0, x1, y1, fill=fill, outline='black')
				if (r, col) in self.q_queens:
					if getattr(self, 'q_queen_img', None):
						c.create_image(x0 + s/2, y0 + s/2, image=self.q_queen_img)
					else:
						c.create_text(x0 + s/2, y0 + s/2, text='♛', fill='black', font=('Arial', int(s/2)))
		# clear any existing hover tag (drawn by motion handler)
		c.delete('hover')

	def q_on_motion(self, event):
		c = self.q_canvas
		cell = self._coord_to_cell(event.x, event.y, self.q_cell_size, self.qN)
		c.delete('hover')
		if cell is None:
			return
		r, col = cell
		x0 = col * self.q_cell_size
		y0 = r * self.q_cell_size
		x1 = x0 + self.q_cell_size
		y1 = y0 + self.q_cell_size
		c.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline='#ff9900', width=3, tags='hover')

	def q_set_color(self, v):
		self.q_color = v
		self.q_mode = 'color'
		self.q_status.config(text=f'Color mode: {v}')

	def q_toggle_queen_mode(self):
		self.q_mode = 'queen' if self.q_mode != 'queen' else 'color'
		self.q_status.config(text=f'Mode: {self.q_mode}')

	def q_on_click(self, event):
		s = self.q_cell_size
		c = floor(event.y / s)
		r = floor(event.x / s)
		# careful: inverted coords from canvas: r is col, c is row
		row = c
		col = r
		if not (0 <= row < self.qN and 0 <= col < self.qN):
			return
		if self.q_mode == 'color':
			self.q_regions[row][col] = self.q_color
		else:
			if (row, col) in self.q_queens:
				self.q_queens.remove((row, col))
			else:
				self.q_queens.add((row, col))
		self.q_draw_grid()

	def q_on_drag(self, event):
		# when dragging with button held, paint color if in color mode
		if self.q_mode != 'color':
			return
		cell = self._coord_to_cell(event.x, event.y, self.q_cell_size, self.qN)
		if cell is None:
			return
		r, col = cell
		self.q_regions[r][col] = self.q_color
		self.q_draw_grid()

	def q_clear_board(self):
		# reset queens board
		self.q_regions = [[0 for _ in range(self.qN)] for _ in range(self.qN)]
		self.q_queens = set()
		self.q_draw_grid()

	def ms_clear_board(self):
		# reset mini sudoku board
		self.ms_values = [[0 for _ in range(6)] for _ in range(6)]
		self.ms_user_placed = [[False for _ in range(6)] for _ in range(6)]
		self.ms_selected_number = None
		if getattr(self, 'ms_canvas', None):
			self.ms_draw()
		self._ms_set_status('Board cleared')

	def t_clear_board(self):
		# reset tango board
		if getattr(self, 'tN', None) is None:
			return
		self.t_grid = [[-1 for _ in range(self.tN)] for _ in range(self.tN)]
		self.t_equals = set()
		self.t_diffs = set()
		self.t_last = None
		if getattr(self, 't_canvas', None):
			self.t_draw()
		self._t_set_status('Board cleared')

	def z_clear_board(self):
		# reset zip board
		if getattr(self, 'zN', None) is None:
			return
		self.z_grid = [[0 for _ in range(self.zN)] for _ in range(self.zN)]
		self.z_walls = set()
		self.z_next_num = 1
		self.z_last = None
		self.z_solution_steps = None
		if getattr(self, 'z_canvas', None):
			self.z_draw()
		self._z_set_status('Board cleared')
	def q_solve(self):
		if QueensSATSolver is None:
			messagebox.showerror('Solver missing', 'Queens solver not available (missing imports)')
			return
		# validate regions
		regs = set()
		for r in range(self.qN):
			for c in range(self.qN):
				regs.add(self.q_regions[r][c])
		if 0 in regs:
			messagebox.showerror('Regions incomplete', 'All cells must be assigned to regions (use color buttons)')
			return
		if len(regs) != self.qN:
			messagebox.showerror('Region count', f'Number of distinct regions must equal N ({self.qN}). Currently {len(regs)}')
			return

		# map region labels to contiguous 1..N
		distinct = sorted(list(regs))
		mapping = {val: i+1 for i, val in enumerate(distinct)}
		grid = [[mapping[self.q_regions[r][c]] for c in range(self.qN)] for r in range(self.qN)]
		queens_list = list(self.q_queens)
		start = time.time()
		try:
			solver = QueensSATSolver(grid, queens_list)
			sol = solver.solve()
		except Exception as e:
			messagebox.showerror('Solve error', str(e))
			return
		elapsed = time.time() - start
		if sol is None:
			self.q_status.config(text='No solution found')
			return
		# mark result queens (sol is list of positions)
		self.q_queens = set(sol)
		self.q_draw_grid()
		self.q_status.config(text=f'Solved in {elapsed:.3f} seconds')

	# ---------------- Tango ----------------
	def show_tango(self):
		self.clear_current()
		frame = ttk.Frame(self.root, padding=8)
		self.current_frame = frame
		frame.pack(fill='both', expand=True)

		header = ttk.Label(frame, text='Tango', font=(None, 16, 'bold'))
		header.pack()

		size = simpledialog.askinteger('Board size', 'Enter even N for N x N board (e.g. 6):', parent=self.root, minvalue=2, maxvalue=20)
		if not size or size % 2 != 0:
			messagebox.showerror('Invalid size', 'Size must be an even integer')
			self.show_main_menu()
			return
		self.tN = size
		self.t_grid = [[-1 for _ in range(size)] for _ in range(size)]
		self.t_equals = set()
		self.t_diffs = set()
		self.t_mode = 'sun'  # sun, moon, equals, diff

		canvas = tk.Canvas(frame, width=40*size, height=40*size)
		canvas.pack(pady=8)
		self.t_canvas = canvas
		self.t_cell_size = 40
		# load sun/moon images
		self.t_sun_img = self.load_icon('sun.png', size=(int(self.t_cell_size*0.8), int(self.t_cell_size*0.8)))
		self.t_moon_img = self.load_icon('moon.png', size=(int(self.t_cell_size*0.64), int(self.t_cell_size*0.64)))
		self.t_draw()
		# hover bindings to show cell/edge highlight
		self.t_canvas.bind('<Motion>', self.t_on_motion)
		self.t_canvas.bind('<Leave>', lambda e: self.t_canvas.delete('hover'))

		controls = ttk.Frame(frame)
		controls.pack()
		ttk.Button(controls, text='Sun', command=lambda: self.t_set_mode('sun')).pack(side='left', padx=4)
		ttk.Button(controls, text='Moon', command=lambda: self.t_set_mode('moon')).pack(side='left', padx=4)
		ttk.Button(controls, text='Equals(edge)', command=lambda: self.t_set_mode('equals')).pack(side='left', padx=4)
		ttk.Button(controls, text='Different(edge)', command=lambda: self.t_set_mode('diff')).pack(side='left', padx=4)
		ttk.Button(controls, text='Solve', command=self.t_solve).pack(side='left', padx=6)
		clear_btn = ttk.Button(controls, text='Clear Board', command=self.t_clear_board)
		clear_btn.pack(side='left', padx=6)
		ttk.Button(controls, text='Back', command=self.show_main_menu).pack(side='left', padx=6)

		self.t_status = ttk.Label(frame, text='Click cells to place Sun/Moon; to mark an edge click two adjacent cells.')
		self.t_status.pack()
		self.t_last = None
		canvas.bind('<Button-1>', self.t_on_click)

	def t_draw(self):
		c = self.t_canvas
		n = self.tN
		s = self.t_cell_size
		c.delete('all')
		for r in range(n):
			for col in range(n):
				x0 = col * s
				y0 = r * s
				x1 = x0 + s
				y1 = y0 + s
				c.create_rectangle(x0, y0, x1, y1, fill='white', outline='black')
				val = self.t_grid[r][col]
				if val == 1:
					if getattr(self, 't_sun_img', None):
						c.create_image(x0 + s/2, y0 + s/2, image=self.t_sun_img)
					else:
						c.create_text(x0 + s/2, y0 + s/2, text='☀️', font=('Arial', int(s/2)))
				elif val == 0:
					if getattr(self, 't_moon_img', None):
						c.create_image(x0 + s/2, y0 + s/2, image=self.t_moon_img)
					else:
						c.create_text(x0 + s/2, y0 + s/2, text='🌙', font=('Arial', int(s/2)))

		# draw edge markers
		for (a, b) in self.t_equals:
			(r1, c1), (r2, c2) = a, b
			self._draw_edge_marker((r1, c1), (r2, c2), '=')
		for (a, b) in self.t_diffs:
			(r1, c1), (r2, c2) = a, b
			# use multiplication symbol for 'different'
			self._draw_edge_marker((r1, c1), (r2, c2), '✖')

	def _coord_to_cell(self, x, y, cell_size, n):
		col = int(x // cell_size)
		row = int(y // cell_size)
		if 0 <= row < n and 0 <= col < n:
			return (row, col)
		return None

	def _coord_to_edge(self, x, y, cell_size, n, threshold=8):
		# improved edge detection: consider proximity to any of the four surrounding grid lines
		col = int(x // cell_size)
		row = int(y // cell_size)
		# if outside bounds, still allow edges near border only if adjacent cell exists
		if col < 0: col = 0
		if row < 0: row = 0
		if col >= n: col = n-1
		if row >= n: row = n-1
		# fractional within cell
		fx = x - (col * cell_size)
		fy = y - (row * cell_size)
		# check left vertical edge
		if fx <= threshold and col - 1 >= 0 and (fy >= 0 and fy <= cell_size):
			return ((row, col-1), (row, col))
		# check right vertical edge
		if fx >= cell_size - threshold and col + 1 < n and (fy >= 0 and fy <= cell_size):
			return ((row, col), (row, col+1))
		# check top horizontal edge
		if fy <= threshold and row - 1 >= 0 and (fx >= 0 and fx <= cell_size):
			return ((row-1, col), (row, col))
		# check bottom horizontal edge
		if fy >= cell_size - threshold and row + 1 < n and (fx >= 0 and fx <= cell_size):
			return ((row, col), (row+1, col))
		return None

	# --- safe status setters ---
	def _ms_set_status(self, text):
		try:
			if hasattr(self, 'ms_status') and self.ms_status:
				self.ms_status.config(text=text)
				return
		except Exception:
			pass
		# if possible create the label in current frame
		if getattr(self, 'current_frame', None) is not None:
			self.ms_status = ttk.Label(self.current_frame, text=text)
			self.ms_status.pack()
		else:
			print(text)

	def _t_set_status(self, text):
		try:
			if hasattr(self, 't_status') and self.t_status:
				self.t_status.config(text=text)
				return
		except Exception:
			pass
		if getattr(self, 'current_frame', None) is not None:
			self.t_status = ttk.Label(self.current_frame, text=text)
			self.t_status.pack()
		else:
			print(text)

	def _z_set_status(self, text):
		try:
			if hasattr(self, 'z_status') and self.z_status:
				self.z_status.config(text=text)
				return
		except Exception:
			pass
		if getattr(self, 'current_frame', None) is not None:
			self.z_status = ttk.Label(self.current_frame, text=text)
			self.z_status.pack()
		else:
			print(text)

	def t_on_motion(self, event):
		c = self.t_canvas
		c.delete('hover')
		if self.t_mode in ('sun', 'moon'):
			cell = self._coord_to_cell(event.x, event.y, self.t_cell_size, self.tN)
			if cell is None:
				return
			r, col = cell
			x0 = col * self.t_cell_size
			y0 = r * self.t_cell_size
			x1 = x0 + self.t_cell_size
			y1 = y0 + self.t_cell_size
			c.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline='#ff9900', width=3, tags='hover')
		else:
			edge = self._coord_to_edge(event.x, event.y, self.t_cell_size, self.tN)
			if edge:
				(a, b) = edge
				(r1, c1), (r2, c2) = a, b
				# compute center line
				if r1 == r2:
					x = (c1 + c2 + 1) * self.t_cell_size/2
					y = (r1 + r2 + 1) * self.t_cell_size/2
					# draw thicker bold line to represent edge highlight
					c.create_line(x, y-10, x, y+10, fill='#ff9900', width=8, tags='hover')
				else:
					x = (c1 + c2 + 1) * self.t_cell_size/2
					y = (r1 + r2 + 1) * self.t_cell_size/2
					c.create_line(x-10, y, x+10, y, fill='#ff9900', width=8, tags='hover')

	def t_on_click(self, event):
		# allow single-click toggling on edge if clicked near an edge
		edge = self._coord_to_edge(event.x, event.y, self.t_cell_size, self.tN)
		if edge and self.t_mode in ('equals', 'diff'):
			pair = edge if edge[0] < edge[1] else (edge[1], edge[0])
			if self.t_mode == 'equals':
				if pair in self.t_equals:
					self.t_equals.remove(pair)
				else:
					self.t_equals.add(pair)
					if pair in self.t_diffs:
						self.t_diffs.remove(pair)
			else:
				if pair in self.t_diffs:
					self.t_diffs.remove(pair)
				else:
					self.t_diffs.add(pair)
					if pair in self.t_equals:
						self.t_equals.remove(pair)
			self.t_draw()
			return
		# fallback to previous behaviour
		s = self.t_cell_size
		col = floor(event.x / s)
		row = floor(event.y / s)
		if not (0 <= row < self.tN and 0 <= col < self.tN):
			return
		if self.t_mode in ('sun', 'moon'):
			self.t_grid[row][col] = 1 if self.t_mode == 'sun' else 0
			self.t_draw()
			self.t_last = None
			return
		# edge modes: two-click fallback
		if self.t_last is None:
			self.t_last = (row, col)
			return
		else:
			a = self.t_last
			b = (row, col)
			self.t_last = None
			if abs(a[0]-b[0]) + abs(a[1]-b[1]) != 1:
				messagebox.showerror('Invalid edge', 'Edges must be between adjacent cells')
				return
			pair = (a, b) if a < b else (b, a)
			if self.t_mode == 'equals':
				# toggle in equals
				if pair in self.t_equals:
					self.t_equals.remove(pair)
				else:
					self.t_equals.add(pair)
					if pair in self.t_diffs:
						self.t_diffs.remove(pair)
			else:
				if pair in self.t_diffs:
					self.t_diffs.remove(pair)
				else:
					self.t_diffs.add(pair)
					if pair in self.t_equals:
						self.t_equals.remove(pair)
			self.t_draw()

	def _draw_edge_marker(self, pos1, pos2, sym):
		(r1, c1) = pos1
		(r2, c2) = pos2
		s = self.t_cell_size
		x = (c1 + c2 + 1) * s/2
		y = (r1 + r2 + 1) * s/2
		self.t_canvas.create_text(x, y, text=sym, font=('Arial', 12), fill='red')

	def t_set_mode(self, m):
		self.t_mode = m
		self.t_status.config(text=f'Mode: {m}')



	def t_solve(self):
		if TangoCPSATSolver is None:
			messagebox.showerror('Solver missing', 'Tango solver not available (missing imports)')
			return
		start = time.time()
		try:
			solver = TangoCPSATSolver(self.tN, self.t_grid, list(self.t_equals), list(self.t_diffs))
			sol = solver.solve()
		except Exception as e:
			messagebox.showerror('Solve error', str(e))
			return
		elapsed = time.time() - start
		# apply solution to the board and redraw
		if sol is None:
			self._t_set_status('No solution found')
			return
		# solver returns 0/1 grid: set t_grid accordingly
		self.t_grid = [[int(sol[r][c]) for c in range(self.tN)] for r in range(self.tN)]
		if getattr(self, 't_canvas', None):
			self.t_draw()
		self._t_set_status(f'Solved in {elapsed:.3f} seconds')

	# ---------------- Zip ----------------
	def show_zip(self):
		self.clear_current()
		frame = ttk.Frame(self.root, padding=8)
		self.current_frame = frame
		frame.pack(fill='both', expand=True)

		header = ttk.Label(frame, text='Zip', font=(None, 16, 'bold'))
		header.pack()

		size = simpledialog.askinteger('Board size', 'Enter N for N x N board (e.g. 6):', parent=self.root, minvalue=2, maxvalue=20)
		if not size:
			self.show_main_menu()
			return
		self.zN = size
		self.z_grid = [[0 for _ in range(size)] for _ in range(size)]
		self.z_walls = set()
		self.z_next_num = 1
		self.z_canvas = tk.Canvas(frame, width=40*size, height=40*size)
		self.z_canvas.pack(pady=8)
		self.z_cell_size = 40
		self.z_draw()
		# hover bindings for zip canvas
		self.z_canvas.bind('<Motion>', self.z_on_motion)
		self.z_canvas.bind('<Leave>', lambda e: self.z_canvas.delete('hover'))

		controls = ttk.Frame(frame)
		controls.pack()
		ttk.Button(controls, text='Mark Number', command=lambda: setattr(self, 'z_mode', 'number')).pack(side='left', padx=4)
		ttk.Button(controls, text='Wall Mode', command=lambda: setattr(self, 'z_mode', 'wall')).pack(side='left', padx=4)
		ttk.Button(controls, text='Undo Last Number', command=self.z_undo_last).pack(side='left', padx=4)
		ttk.Button(controls, text='Solve', command=self.z_solve).pack(side='left', padx=4)
		clear_btn = ttk.Button(controls, text='Clear Board', command=self.z_clear_board)
		clear_btn.pack(side='left', padx=4)
		ttk.Button(controls, text='Back', command=self.show_main_menu).pack(side='left', padx=4)

		self.z_mode = 'number'
		self.z_status = ttk.Label(frame, text='Click cells to number in order or switch to Wall Mode to mark walls (click two adjacent cells).')
		self.z_status.pack()
		self.z_last = None
		self.z_canvas.bind('<Button-1>', self.z_on_click)

	def z_draw(self):
		c = self.z_canvas
		n = self.zN
		s = self.z_cell_size
		c.delete('all')
		for r in range(n):
			for col in range(n):
				x0 = col * s
				y0 = r * s
				x1 = x0 + s
				y1 = y0 + s
				c.create_rectangle(x0, y0, x1, y1, fill='white', outline='black')
				val = self.z_grid[r][col]
				if val > 0:
					# draw black circle with number
					radius = int(s*0.32)
					cx = x0 + s/2
					cy = y0 + s/2
					c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, fill='black', outline='')
					c.create_text(cx, cy, text=str(val), fill='white', font=('Arial', int(s*0.35)))

		# draw walls as bold edges between cells
		for (a, b) in self.z_walls:
			(r1, c1), (r2, c2) = a, b
			if r1 == r2:
				# vertical wall between columns
				row = r1
				col_left = min(c1, c2)
				x = (col_left + 1) * s
				y0 = row * s
				y1 = y0 + s
				c.create_line(x, y0, x, y1, fill='black', width=6)
			else:
				# horizontal wall
				col = c1
				row_top = min(r1, r2)
				y = (row_top + 1) * s
				x0 = col * s
				x1 = x0 + s
				c.create_line(x0, y, x1, y, fill='black', width=6)

		# draw solution path arrows if available
		# draw small solution step numbers in bottom-right if available
		if getattr(self, 'z_solution_steps', None):
			for (rr, cc), step in self.z_solution_steps.items():
				x1 = cc * s + s - 4
				y1 = rr * s + s - 4
				c.create_text(x1, y1, text=str(step), anchor='se', fill='#4b9eff', font=('Arial', int(s*0.22)))

	def z_on_motion(self, event):
		c = self.z_canvas
		c.delete('hover')
		if self.z_mode == 'number':
			cell = self._coord_to_cell(event.x, event.y, self.z_cell_size, self.zN)
			if cell is None:
				return
			r, col = cell
			x0 = col * self.z_cell_size
			y0 = r * self.z_cell_size
			x1 = x0 + self.z_cell_size
			y1 = y0 + self.z_cell_size
			c.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline='#ff9900', width=3, tags='hover')
		else:
			edge = self._coord_to_edge(event.x, event.y, self.z_cell_size, self.zN)
			if edge:
				(a, b) = edge
				(r1, c1), (r2, c2) = a, b
				if r1 == r2:
					x = (c1 + c2 + 1) * self.z_cell_size/2
					y = (r1 + r2 + 1) * self.z_cell_size/2
					c.create_line(x, y-14, x, y+14, fill='#ff9900', width=6, tags='hover')
				else:
					x = (c1 + c2 + 1) * self.z_cell_size/2
					y = (r1 + r2 + 1) * self.z_cell_size/2
					c.create_line(x-14, y, x+14, y, fill='#ff9900', width=6, tags='hover')

	def z_on_click(self, event):
		edge = self._coord_to_edge(event.x, event.y, self.z_cell_size, self.zN)
		if edge and self.z_mode == 'wall':
			pair = edge if edge[0] < edge[1] else (edge[1], edge[0])
			if pair in self.z_walls:
				self.z_walls.remove(pair)
			else:
				self.z_walls.add(pair)
			self.z_solution_steps = None
			self.z_draw()
			return
		# fallback to cell behaviour
		s = self.z_cell_size
		col = floor(event.x / s)
		row = floor(event.y / s)
		if not (0 <= row < self.zN and 0 <= col < self.zN):
			return
		if self.z_mode == 'number':
			# set next number
			self.z_grid[row][col] = self.z_next_num
			self.z_next_num += 1
			self.z_solution_steps = None
			self.z_draw()
			return
		# wall mode fallback: two-click
		if self.z_last is None:
			self.z_last = (row, col)
			return
		else:
			a = self.z_last
			b = (row, col)
			self.z_last = None
			if abs(a[0]-b[0]) + abs(a[1]-b[1]) != 1:
				messagebox.showerror('Invalid wall', 'Walls are between adjacent cells')
				return
			pair = (a, b) if a < b else (b, a)
			if pair in self.z_walls:
				self.z_walls.remove(pair)
			else:
				self.z_walls.add(pair)
			self.z_draw()

	def z_undo_last(self):
		# remove highest number
		maxn = 0
		pos = None
		for r in range(self.zN):
			for c in range(self.zN):
				if self.z_grid[r][c] > maxn:
					maxn = self.z_grid[r][c]
					pos = (r, c)
		if pos:
			self.z_grid[pos[0]][pos[1]] = 0
			self.z_next_num = max(1, maxn)
			self.z_draw()

	def z_solve(self):
		if ZipCPSATSolver is None:
			messagebox.showerror('Solver missing', 'Zip solver not available (missing imports)')
			return
		start = time.time()
		try:
			solver = ZipCPSATSolver(self.z_grid, self.z_walls)
			sol = solver.solve()
		except Exception as e:
			messagebox.showerror('Solve error', str(e))
			return
		elapsed = time.time() - start
		if sol is None:
			self._z_set_status('No solution found')
			return
		# solver returns ordered list of (r,c) path; keep user numbers and store solution steps separately
		self.z_solution_steps = {}
		for step, (r, c) in enumerate(sol, start=1):
			self.z_solution_steps[(r, c)] = step
		# redraw with solution overlay
		if getattr(self, 'z_canvas', None):
			self.z_draw()
		self._z_set_status(f'Solved in {elapsed:.3f} seconds')

	# ---------------- Helpers ----------------
	def generate_colors(self, n):
		# generate n distinct pastel colors
		import colorsys
		cols = []
		for i in range(n):
			h = i / max(1, n)
			r, g, b = colorsys.hsv_to_rgb(h, 0.5, 0.95)
			cols.append('#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255)))
		return cols


if __name__ == '__main__':
	root = tk.Tk()
	app = Visualizer(root)
	root.mainloop()