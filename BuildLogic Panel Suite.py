import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import sys

# --- Utility Functions ---

def resource_path(relative):
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, relative)

# --- CONFIGURATION & CONSTANTS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Attempt to load Segoe UI font (may fail on non-Windows/non-standard setups)
try:
    ctk.FontManager.load_font("C:/Windows/Fonts/segoeui.ttf")
    FONT_FAMILY = "Segoe UI"
except Exception:
    FONT_FAMILY = "Roboto"

THEME = {
    "bg": "#0f0f0f",
    "surface": "#1a1a1a",
    "surface_2": "#202020",
    "border": "#2a2a2a",
    "accent": "#268f07",
    "accent_hover": "#226b0c",
    "danger": "#dc2626",
    "success": "#16a34a",
    "text": "#e5e5e5",
    "muted": "#9ca3af",
}

Legacy_BTN_STYLE = {
    "height": 34, # Slightly reduced for better spacing
    "corner_radius": 6, # Slightly reduced corner radius
    "font": (FONT_FAMILY, 11),
    #"fg_color": "#2cbe00" - dont include cus some buttons do it themself
}

BTN_STYLE = {
    "height": 34, # Slightly reduced for better spacing
    "corner_radius": 6, # Slightly reduced corner radius
    "font": (FONT_FAMILY, 11),
    #"fg_color": "#268f07" - lowk looks shit rn, todo: pick new color :cool_guy:
}

GRID_SIZE = 16

COLOR_MAP = {
    "black": "000000", "white": "111111", "gray": "111000", "red": "100100",
    "green": "010010", "blue": "001001", "yellow": "110110", "magenta": "101101",
    "cyan": "011011", "bright_red": "100111", "bright_green": "010000",
    "bright_blue": "001000", "dark_red": "000100", "dark_green": "000010", "dark_blue": "000001",
}

UI_COLORS = {
    "black": "#1a1a1a", "white": "#FFFFFF", "gray": "#888888", "red": "#FF0000",
    "green": "#00FF00", "blue": "#0000FF", "yellow": "#FFFF00", "magenta": "#FF00FF",
    "cyan": "#00FFFF", "bright_red": "#FF5555", "bright_green": "#55FF55",
    "bright_blue": "#5555FF", "dark_red": "#880000", "dark_green": "#008800", "dark_blue": "#000088",
}

REVERSE_COLOR_MAP = {v: k for k, v in COLOR_MAP.items()}

class CombinedEEPROMApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.configure(fg_color=THEME["bg"])
        self.title("BuildLogic Panel Studio Pro")
        self.minsize(1500, 1100) # Increased min size to fit new layout
        
        # --- Resources ---
        self.binary_chars = self.load_char_map()
        self.reverse_char_map = {v.rjust(7, "0"): k for k, v in self.binary_chars.items()}
        
        # --- State ---
        self.grid_data = [[{'char': ' ', 'color': 'black'} for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.cells = {} # Dictionary mapping widget to (r, c)
        self.current_tool = "paint"
        self.selected_color = "red"
        self.focused_cell = None
        self.selection_start = None
        self.selection_end = None
        self.selection_area = None # (r1, c1, r2, c2)
        self.files_to_encode = [] 
        self.virtual_files = {} 
        self.is_16bit = ctk.BooleanVar(value=True)
        self.boot_index = ctk.StringVar(value="0") 
        
        self.tool_var = ctk.StringVar(value="paint") # FIX: Initialized tool variable

        # --- Clipboard for Selection ---
        self.selection_clipboard = None
        
        # --- UI Layout ---
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=THEME["surface"],
            segmented_button_fg_color=THEME["surface_2"],
            segmented_button_selected_color=THEME["accent"],
            segmented_button_selected_hover_color=THEME["accent_hover"],
            segmented_button_unselected_color=THEME["surface_2"],
        )
        # Added overall padding to the tabview
        self.tabview.pack(fill="both", expand=True, padx=12, pady=12) 
        
        self.tab_designer = self.tabview.add("Pixel Designer")
        self.tab_encoder = self.tabview.add("EEPROM Encoder")
        self.tab_charmap = self.tabview.add("Char Map")
        
        self.setup_designer_tab()
        self.setup_encoder_tab()
        self.setup_charmap_tab()
        self.bind("<Key>", self.handle_keypress)
        self.clear_grid(confirm=False) 

    def load_char_map(self):
        try:
            # Load the application's local binary map file
            with open(resource_path("BinaryChars.json"), "r", encoding="utf-8") as f:
                return json.load(f).get("CharToBin", {})
        except Exception:
            # Fallback to hardcoded defaults
            return {
                " ": "0000000", "A": "1000000", "B": "1000001", "C": "1000010",
                "D": "1000011", "E": "1000100", "F": "1000101", "G": "1000110",
                "H": "1000111", "I": "1001000", "J": "1001001", "K": "1001010",
                "L": "1001011", "M": "1001100", "N": "1001101", "O": "1001110",
                "P": "1001111", "Q": "1010000", "R": "1010001", "S": "1010010",
                "T": "1010011", "U": "1010100", "V": "1010101", "W": "1010110",
                "X": "1010111", "Y": "1011000", "Z": "1011001", "0": "1100000",
                "1": "1100001", "2": "1100010", "3": "1100011", "4": "1100100",
                "5": "1100101", "6": "1100110", "7": "1100111", "8": "1101000",
                "9": "1101001", ".": "1110000", "!": "1110001", "?": "1110010",
                ":": "1110011", ",": "1110100", "'": "1110101", "-": "1110110",
            }
    
    def save_char_map(self):
        data = {"CharToBin": self.binary_chars}
        try:
            with open(resource_path("BinaryChars.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.log("Character map saved.", "info")
        except Exception as e:
            self.log(f"Error saving char map: {e}", "error")

    # --- DESIGNER LOGIC ---
    def setup_designer_tab(self):
        self.tab_designer.grid_columnconfigure(0, weight=1)
        self.tab_designer.grid_columnconfigure(1, weight=0)
        self.tab_designer.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self.tab_designer, fg_color=THEME["surface"], corner_radius=8) # Smaller corner radius
        container.grid(row=0, column=0, sticky="nsew", padx=8, pady=8) # Reduced container padding
        container.grid_columnconfigure(0, weight=1)

        # Drawing Area (Center)
        draw_frame = tk.Frame(container, bg=THEME["surface"])
        draw_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Centering the grid within the frame
        self.grid_inner = tk.Frame(draw_frame, bg="#2B2B2B")
        self.grid_inner.pack(expand=True, padx=20, pady=20) 
        
        # Ensure cells are cleared and redrawn on fresh setup, necessary for refresh_grid_ui
        self.cells = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = tk.Label(self.grid_inner, text=" ", width=6, height=3, # Reduced size for better fit
                                font=("Courier New", 11, "bold"), bg=UI_COLORS["black"],
                                fg="white", relief="flat", bd=1)
                cell.grid(row=r, column=c, padx=1, pady=1)
                
                cell.bind("<Button-1>", lambda e, row=r, col=c: self.on_cell_down(e, row, col))
                cell.bind("<B1-Motion>", self.on_cell_drag)
                cell.bind("<ButtonRelease-1>", self.on_cell_up)
                self.cells[cell] = (r, c)
        
        self.refresh_grid_ui()
                
        # Designer Sidebar (Right)
        sidebar = ctk.CTkFrame(self.tab_designer, width=320, fg_color=THEME["surface_2"], corner_radius=8) # Moved sidebar definition here for proper padding/container use
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        
        # --- TOOLS ---
        ctk.CTkLabel(sidebar, text="TOOLS", font=(FONT_FAMILY, 16, "bold")).pack(pady=(12, 4))
        tool_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        tool_frame.pack(fill="x", padx=15, pady=(0, 8))
        
        # Standardized radio button layout
        ctk.CTkRadioButton(tool_frame, text="Paint (Click/Drag)", variable=self.tool_var, value="paint", command=self.sync_tools, font=(FONT_FAMILY, 11)).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkRadioButton(tool_frame, text="Text (Sequential Type)", variable=self.tool_var, value="text", command=self.sync_tools, font=(FONT_FAMILY, 11)).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkRadioButton(tool_frame, text="Line (Start & End Click)", variable=self.tool_var, value="line", command=self.sync_tools, font=(FONT_FAMILY, 11)).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkRadioButton(tool_frame, text="Fill (Bucket)", variable=self.tool_var, value="fill", command=self.sync_tools, font=(FONT_FAMILY, 11)).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        #ctk.CTkRadioButton(tool_frame, text="Select (Box Drag)", variable=self.tool_var, value="select", command=self.sync_tools, font=(FONT_FAMILY, 11)).grid(row=4, column=0, sticky="w", padx=5, pady=2)
        
        ctk.CTkFrame(sidebar, height=1, fg_color="gray40").pack(fill="x", padx=15, pady=10)

        # --- PALETTE ---
        ctk.CTkLabel(sidebar, text="COLOR PALETTE", font=(FONT_FAMILY, 14, "bold")).pack(pady=(0, 5))
        palette = ctk.CTkFrame(sidebar, fg_color="transparent")
        palette.pack(pady=5, padx=10)
        row, col = 0, 0
        for name, hex_val in UI_COLORS.items():
            ctk.CTkButton(palette, text="", width=30, height=30, fg_color=hex_val, # Standardized palette buttons
                          hover_color=hex_val, corner_radius=4, command=lambda c=name: self.select_color(c)).grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 4: col = 0; row += 1

        self.lbl_selected = ctk.CTkLabel(sidebar, text="Color: RED", font=(FONT_FAMILY, 11, "bold"))
        self.lbl_selected.pack(pady=4)
        
        # --- LIVE INFO ---
        ctk.CTkFrame(sidebar, height=1, fg_color="gray40").pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(sidebar, text="CELL DATA PREVIEW", font=(FONT_FAMILY, 14, "bold")).pack(pady=(0, 4))
        self.lbl_cell_info = ctk.CTkLabel(sidebar, text="Addr: --\nBIN: --\nDEC: --", justify="left", font=("Consolas", 10))
        self.lbl_cell_info.pack(fill="x", padx=15, pady=(0, 8))

        # --- GRID ACTIONS ---
        ctk.CTkFrame(sidebar, height=1, fg_color="gray40").pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(sidebar, text="GRID ACTIONS", font=(FONT_FAMILY, 14, "bold")).pack(pady=(0, 5))
        
        # Selection Tools Frame
        action_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        action_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        # Standardized button height/style
        btn_w = 85
        #ctk.CTkButton(action_frame, text="Copy", width=btn_w, **BTN_STYLE, command=self.copy_selection).grid(row=0, column=0, padx=2, pady=2)
        #ctk.CTkButton(action_frame, text="Paste", width=btn_w, **BTN_STYLE, command=self.paste_selection).grid(row=0, column=1, padx=2, pady=2)
        #ctk.CTkButton(action_frame, text="Cut", width=btn_w, **BTN_STYLE, command=self.cut_selection).grid(row=0, column=2, padx=2, pady=2)
        
        # Shift Frame
        #shift_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        #shift_frame.pack(fill="x", padx=15, pady=(5, 10))
        #ctk.CTkLabel(shift_frame, text="Shift:", font=(FONT_FAMILY, 11)).pack(side="left", padx=(0, 5))
        
        #shift_btn_style = {"width": 30, "height": 30, "corner_radius": 4, "font": (FONT_FAMILY, 10, "bold")}
        #ctk.CTkButton(shift_frame, text="⇦", **shift_btn_style, command=lambda: self.shift_selection(0, -1)).pack(side="left", padx=1)
        #ctk.CTkButton(shift_frame, text="⇨", **shift_btn_style, command=lambda: self.shift_selection(0, 1)).pack(side="left", padx=1)
        #ctk.CTkButton(shift_frame, text="⇧", **shift_btn_style, command=lambda: self.shift_selection(-1, 0)).pack(side="left", padx=1)
        #ctk.CTkButton(shift_frame, text="⇩", **shift_btn_style, command=lambda: self.shift_selection(1, 0)).pack(side="left", padx=1)

        # Transformation Tools
        ctk.CTkButton(action_frame, text="Flip H", width=btn_w, **BTN_STYLE, command=lambda: self.transform_grid('flip_h')).grid(row=1, column=0, padx=8, pady=2)
        ctk.CTkButton(action_frame, text="Flip V", width=btn_w, **BTN_STYLE, command=lambda: self.transform_grid('flip_v')).grid(row=1, column=1, padx=8, pady=2)
        ctk.CTkButton(action_frame, text="Rotate ↻", width=btn_w, **BTN_STYLE, command=lambda: self.transform_grid('rotate')).grid(row=1, column=2, padx=8, pady=2)

        ctk.CTkButton(sidebar, text="CLEAR GRID", fg_color=THEME["danger"], hover_color="#b91c1c", 
                      height=40, font=(FONT_FAMILY, 12, "bold"), command=lambda: self.clear_grid(confirm=True)).pack(fill="x", padx=15, pady=(10, 8))
        
        # --- FILE/PROJECT ACTIONS ---
        ctk.CTkFrame(sidebar, height=1, fg_color="gray40").pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(sidebar, text="PROJECT MANAGER", font=(FONT_FAMILY, 14, "bold")).pack(pady=(0, 15))
        
        file_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        file_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        ctk.CTkButton(file_frame, text="LOAD PROJECT", **BTN_STYLE, command=self.load_project).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(file_frame, text="SAVE PROJECT", **BTN_STYLE, command=self.save_project).pack(side="left", expand=True, padx=2)
        
        ctk.CTkLabel(sidebar, text="SAVES", font=(FONT_FAMILY, 14, "bold")).pack(pady=(10, 15))

        ctk.CTkButton(sidebar, text="IMPORT .TXT SAVE", **BTN_STYLE, command=self.import_designer_file).pack(fill="x", padx=15, pady=(5, 2))
        ctk.CTkButton(sidebar, text="EXPORT .TXT SAVE", **BTN_STYLE, command=self.export_designer_file).pack(fill="x", padx=15, pady=2)
        
        # --- INTEGRATION ---
        ctk.CTkButton(
            sidebar,
            text="SEND TO ENCODER",
            fg_color=THEME["success"],
            hover_color="#15803d",
            height=45,
            font=(FONT_FAMILY, 13, "bold"),
            command=self.send_to_encoder,
        ).pack(fill="x", padx=15, pady=(15, 12))


    def sync_tools(self):
        self.current_tool = self.tool_var.get()
        self.clear_focus()
        self.clear_selection()

    def select_color(self, color):
        self.selected_color = color
        self.lbl_selected.configure(text=f"Color: {color.upper()}")
        self.tool_var.set("paint")
        self.sync_tools()

    def on_cell_down(self, event, r, c):
        if self.current_tool == "paint": 
            self.paint_cell(r, c)
        elif self.current_tool == "text": 
            self.set_text_focus(r, c)
        elif self.current_tool == "line":
            if not self.focused_cell:
                self.set_text_focus(r, c)
                self.log(f"Line Start: ({r}, {c}). Select end point.", "info")
            else:
                r1, c1 = self.focused_cell
                self.draw_line_bresenham(r1, c1, r, c, self.selected_color)
                self.clear_focus()
                self.log(f"Drew line from ({r1}, {c1}) to ({r}, {c}).", "warn")
        elif self.current_tool == "fill":
            self.flood_fill(r, c, self.grid_data[r][c]['color'], self.selected_color)
            self.log(f"Filled area starting at ({r}, {c}) with {self.selected_color}.", "warn")
        elif self.current_tool == "select":
            self.selection_start = (r, c)
            self.clear_selection()
            self.update_selection_box(r, c)
            
    def on_cell_drag(self, event):
        x, y = event.x_root, event.y_root
        target = self.winfo_containing(x, y)
        if target in self.cells:
            r, c = self.cells[target]
            
            # Live Preview
            addr = r * GRID_SIZE + c
            cell = self.grid_data[r][c]
            char_bin = self.binary_chars.get(cell['char'], "0000000").rjust(7, "0")
            color_bin = COLOR_MAP[cell['color']]
            # Use the is_16bit setting for the preview's leading bits
            leading_bits = "111" if self.is_16bit.get() else "000"
            full_bin = leading_bits + color_bin + char_bin
            
            self.lbl_cell_info.configure(text=f"Addr: {addr} (R{r}, C{c})\nBIN: {full_bin}\nDEC: {int(full_bin, 2)}")
            
            if self.current_tool == "paint":
                self.paint_cell(r, c)
            elif self.current_tool == "select" and self.selection_start:
                self.update_selection_box(r, c)
                
    def on_cell_up(self, event):
        if self.current_tool == "select" and self.selection_start:
            x, y = event.x_root, event.y_root
            target = self.winfo_containing(x, y)
            if target in self.cells:
                self.selection_end = self.cells[target]
                self.update_selection_box(self.selection_end[0], self.selection_end[1], final=True)

    def paint_cell(self, r, c, color=None):
        color = color if color else self.selected_color
        self.grid_data[r][c]['color'] = color
        
        # Update UI
        fg = "black" if color in ["white", "yellow", "cyan", "bright_green", "bright_red", "bright_blue"] else "white"
        for widget, coords in self.cells.items():
            if coords == (r, c):
                widget.config(bg=UI_COLORS[color], fg=fg)
                self.update_selection_highlight(widget, (r, c)) 
                break

    def set_text_focus(self, r, c):
        self.clear_focus()
        self.focused_cell = (r, c)
        
        # Update focus highlight & Live Info
        for widget, coords in self.cells.items():
            if coords == (r, c):
                widget.config(relief="solid", bd=2)
                
                # Live Preview update on focus
                addr = r * GRID_SIZE + c
                cell = self.grid_data[r][c]
                char_bin = self.binary_chars.get(cell['char'], "0000000").rjust(7, "0")
                color_bin = COLOR_MAP[cell['color']]
                leading_bits = "111" if self.is_16bit.get() else "000"
                full_bin = leading_bits + color_bin + char_bin
                self.lbl_cell_info.configure(text=f"Addr: {addr} (R{r}, C{c})\nBIN: {full_bin}\nDEC: {int(full_bin, 2)}")
                break

    def clear_focus(self):
        if self.focused_cell:
            r, c = self.focused_cell
            for widget, coords in self.cells.items():
                if coords == (r, c):
                    widget.config(relief="flat", bd=1)
                    self.update_selection_highlight(widget, (r, c))
                    break
            self.focused_cell = None
        self.lbl_cell_info.configure(text="Addr: --\nBIN: --\nDEC: --")

    def clear_selection(self):
        if self.selection_area:
            r1, c1, r2, c2 = self.selection_area
            min_r, max_r = min(r1, r2), max(r1, r2)
            min_c, max_c = min(c1, c2), max(c1, c2)
            
            for r in range(min_r, max_r + 1):
                for c in range(min_c, max_c + 1):
                    for widget, coords in self.cells.items():
                        if coords == (r, c):
                            if self.focused_cell == (r, c):
                                widget.config(relief="solid", bd=2)
                            else:
                                widget.config(relief="flat", bd=1)
                            break
                            
        self.selection_start = None
        self.selection_end = None
        self.selection_area = None

    def update_selection_box(self, r_current, c_current, final=False):
        if not self.selection_start: return
        r1, c1 = self.selection_start
        r2, c2 = r_current, c_current
        
        self.clear_selection()
        
        min_r, max_r = min(r1, r2), max(r1, r2)
        min_c, max_c = min(c1, c2), max(c1, c2)
        
        # Highlight new selection
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                for widget, coords in self.cells.items():
                    if coords == (r, c):
                        if (r, c) != self.focused_cell: 
                            widget.config(relief="solid", bd=2, highlightthickness=0, highlightbackground=THEME["accent"])
                        break

        if final:
            self.selection_area = (r1, c1, r2, c2)
            self.log(f"Selection made: R{min_r}-R{max_r}, C{min_c}-C{max_c}", "info")
    
    def update_selection_highlight(self, widget, coords):
        if self.selection_area and coords != self.focused_cell:
            r, c = coords
            r1, c1, r2, c2 = self.selection_area
            min_r, max_r = min(r1, r2), max(r1, r2)
            min_c, max_c = min(c1, c2), max(c1, c2)
            
            if min_r <= r <= max_r and min_c <= c <= max_c:
                widget.config(relief="solid", bd=2)
            else:
                widget.config(relief="flat", bd=1)
        elif coords != self.focused_cell:
            widget.config(relief="flat", bd=1)


    # --- FEATURE: Sequential Typing ---
    def handle_keypress(self, event):
        if self.tabview.get() != "Pixel Designer" or self.current_tool != "text" or not self.focused_cell:
            return
        
        key = event.char
        r, c = self.focused_cell
        
        if event.keysym == "BackSpace": 
            key = " "
            
        
        if len(key) == 1 and (key in self.binary_chars or key == " "):
            
            # 1. Update the current cell's character
            self.grid_data[r][c]['char'] = key
            for widget, coords in self.cells.items():
                if coords == (r, c):
                    widget.config(text=key)
                    break
            
            # 2. Sequential movement logic
            self.clear_focus()
            
            next_c, next_r = c, r
            
            if event.keysym == "BackSpace":
                # Backspace moves left
                next_c -= 1
                if next_c < 0: # Wrap up
                    next_c = GRID_SIZE - 1
                    next_r -= 1
            else:
                # Typing moves right
                next_c += 1
                if next_c >= GRID_SIZE: # Wrap down
                    next_c = 0
                    next_r += 1
            
            # 3. Set focus on the next cell (if within bounds)
            if 0 <= next_r < GRID_SIZE and 0 <= next_c < GRID_SIZE:
                self.set_text_focus(next_r, next_c)
            else:
                self.focused_cell = None


    def clear_grid(self, confirm=True):
        if confirm and not messagebox.askyesno("Confirm", "Clear entire grid?"): return
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.grid_data[r][c] = {'char': ' ', 'color': 'black'}
        
        self.refresh_grid_ui()
        self.clear_focus()
        self.clear_selection()

    # --- FEATURE: Flood Fill ---
    def flood_fill(self, r, c, target_color, fill_color):
        if target_color == fill_color or r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE:
            return
        if self.grid_data[r][c]['color'] != target_color:
            return

        stack = [(r, c)]
        while stack:
            curr_r, curr_c = stack.pop()
            
            if curr_r < 0 or curr_r >= GRID_SIZE or curr_c < 0 or curr_c >= GRID_SIZE:
                continue
            if self.grid_data[curr_r][curr_c]['color'] != target_color:
                continue
            
            self.paint_cell(curr_r, curr_c, fill_color)

            # Check neighbors
            stack.append((curr_r + 1, curr_c))
            stack.append((curr_r - 1, curr_c))
            stack.append((curr_r, curr_c + 1))
            stack.append((curr_r, curr_c - 1))

    # --- FEATURE: Line Tool (Bresenham's) ---
    def draw_line_bresenham(self, r1, c1, r2, c2, color):
        dr = abs(r2 - r1)
        dc = abs(c2 - c1)
        sr = 1 if r1 < r2 else -1
        sc = 1 if c1 < c2 else -1
        err = dr - dc

        curr_r, curr_c = r1, c1
        while True:
            self.paint_cell(curr_r, curr_c, color)
            if curr_r == r2 and curr_c == c2: break
            
            e2 = 2 * err
            if e2 > -dc:
                err -= dc
                curr_r += sr
            if e2 < dr:
                err += dr
                curr_c += sc

    # --- FEATURE: Grid Transformations (Mirror/Flip/Rotate) ---
    def transform_grid(self, action):
        new_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        if not messagebox.askyesno("Confirm", f"Apply '{action.replace('_', ' ').title()}' to the entire grid?"): return

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = self.grid_data[r][c]
                
                if action == 'flip_h':
                    new_grid[r][GRID_SIZE - 1 - c] = cell
                elif action == 'flip_v':
                    new_grid[GRID_SIZE - 1 - r][c] = cell
                elif action == 'rotate':
                    # Transpose (c, r) then flip horizontal (for 90 degree clockwise rotation)
                    new_grid[c][GRID_SIZE - 1 - r] = cell 

        self.grid_data = new_grid
        self.refresh_grid_ui()
        self.log(f"Grid transformed: {action}", "warn")
        self.clear_focus()
        self.clear_selection()

    def refresh_grid_ui(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = self.grid_data[r][c]
                color = cell['color']
                char = cell['char']
                fg = "black" if color in ["white", "yellow", "cyan", "bright_green", "bright_red", "bright_blue"] else "white"
                
                for w, coords in self.cells.items():
                    if coords == (r, c):
                        w.config(text=char, bg=UI_COLORS[color], fg=fg)
                        # Ensure selection/focus highlights are also reapplied after refresh
                        if self.focused_cell == (r, c):
                             w.config(relief="solid", bd=2)
                        else:
                            self.update_selection_highlight(w, coords)
                        break
    
    # --- FEATURE: Selection & Clipboard ---
    def get_selection_data(self):
        if not self.selection_area: return None
        r1, c1, r2, c2 = self.selection_area
        min_r, max_r = min(r1, r2), max(r1, r2)
        min_c, max_c = min(c1, c2), max(c1, c2)
        
        data = []
        for r in range(min_r, max_r + 1):
            row_data = []
            for c in range(min_c, max_c + 1):
                row_data.append(self.grid_data[r][c].copy())
            data.append(row_data)
        
        return data

    def copy_selection(self):
        self.selection_clipboard = self.get_selection_data()
        if self.selection_clipboard:
            self.log(f"Copied selection of size {len(self.selection_clipboard)}x{len(self.selection_clipboard[0])}", "warn")
        else:
            self.log("No selection to copy.", "error")
            
    def cut_selection(self):
        if not self.selection_area: return self.log("No selection to cut.", "error")
        self.selection_clipboard = self.get_selection_data()
        
        r1, c1, r2, c2 = self.selection_area
        min_r, max_r = min(r1, r2), max(r1, r2)
        min_c, max_c = min(c1, c2), max(c1, c2)
        
        # Clear the cut area
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                self.grid_data[r][c] = {'char': ' ', 'color': 'black'}
                
        self.refresh_grid_ui()
        self.clear_selection()
        self.log("Cut selection and cleared area.", "warn")

    def paste_selection(self):
        if not self.selection_clipboard: return self.log("Clipboard is empty.", "error")
        if not self.focused_cell: return self.log("Select the top-left paste anchor.", "error")
        
        r_anchor, c_anchor = self.focused_cell
        rows = len(self.selection_clipboard)
        cols = len(self.selection_clipboard[0])
        
        # Check bounds
        if r_anchor + rows > GRID_SIZE or c_anchor + cols > GRID_SIZE:
            return self.log("Paste area exceeds grid boundaries.", "error")
        
        # Paste data
        for r_offset in range(rows):
            for c_offset in range(cols):
                new_r = r_anchor + r_offset
                new_c = c_anchor + c_offset
                
                self.grid_data[new_r][new_c] = self.selection_clipboard[r_offset][c_offset].copy()
                self.paint_cell(new_r, new_c, self.grid_data[new_r][new_c]['color']) 
                self.refresh_grid_ui()
                
        self.log(f"Pasted selection at R{r_anchor}, C{c_anchor}.", "warn")

    def shift_selection(self, dr, dc):
        if not self.selection_area: return self.log("No selection to shift.", "error")
        
        r1, c1, r2, c2 = self.selection_area
        min_r, max_r = min(r1, r2), max(r1, r2)
        min_c, max_c = min(c1, c2), max(c1, c2)
        
        data = self.get_selection_data()
        
        # Clear the old selection area
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                self.grid_data[r][c] = {'char': ' ', 'color': 'black'}

        # Calculate new area bounds
        new_min_r, new_max_r = min_r + dr, max_r + dr
        new_min_c, new_max_c = min_c + dc, max_c + dc

        rows = len(data)
        cols = len(data[0])
        
        for r_offset in range(rows):
            for c_offset in range(cols):
                new_r = min_r + dr + r_offset
                new_c = min_c + dc + c_offset
                
                if 0 <= new_r < GRID_SIZE and 0 <= new_c < GRID_SIZE:
                    self.grid_data[new_r][new_c] = data[r_offset][c_offset].copy()

        # Update the UI and selection area
        self.selection_area = (new_min_r, new_min_c, new_max_r, new_max_c)
        self.refresh_grid_ui()
        self.update_selection_box(r2 + dr, c2 + dc, final=True)
        self.log(f"Shifted selection by ({dr}, {dc}).", "warn")
        

    def get_grid_as_text(self):
        lines = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = self.grid_data[r][c]
                char_bin = self.binary_chars.get(cell['char'], "0000000").rjust(7, "0")
                color_bin = COLOR_MAP[cell['color']]
                
                # Check 16-bit setting to determine leading bits
                leading_bits = "111" if self.is_16bit.get() else "000"
                lines.append(leading_bits + color_bin + char_bin)
        
        while len(lines) < GRID_SIZE * GRID_SIZE:
            lines.append("0000000000000") # 13 bits total
            
        return "\n".join(lines)

    def send_to_encoder(self):
        content = self.get_grid_as_text()
        v_name = f"Virtual_Design_{len(self.virtual_files) + 1}"
        # Ensure unique name
        i = 1
        while v_name in self.virtual_files or v_name in self.files_to_encode:
            v_name = f"Virtual_Design_{i}"
            i += 1
            
        self.virtual_files[v_name] = content
        self.files_to_encode.append(v_name)
        self.file_listbox.insert("end", f"[Live] {v_name}")
        self.update_boot_options()
        self.tabview.set("EEPROM Encoder")
        self.log(f"Sent current design to encoder as {v_name}", "warn")

    def export_designer_file(self):
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if fp:
            try:
                with open(fp, "w", encoding="utf-8") as f: f.write(self.get_grid_as_text())
                messagebox.showinfo("Exported", "File saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")

    def import_designer_file(self):
        fp = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not fp: return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                lines = [l.rstrip("\n") for l in f if l.strip()]
            if len(lines) < GRID_SIZE * GRID_SIZE:
                raise ValueError(f"File must contain at least {GRID_SIZE*GRID_SIZE} lines.")
        
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    idx = r * GRID_SIZE + c
                    line = lines[idx].ljust(13, "0")

                    # Note: We rely on the stored char map to correctly decode the character bits
                    color_bin = line[3:9].rjust(6, "0")
                    char_bin = line[9:16].rjust(7, "0")
                    color = REVERSE_COLOR_MAP.get(color_bin, "black")
                    char = self.reverse_char_map.get(char_bin, " ")

                    self.grid_data[r][c] = {'char': char, 'color': color}

            self.refresh_grid_ui()
            messagebox.showinfo("Imported", "File loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- FEATURE: Project Save/Load ---
    def save_project(self):
        fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Project", "*.json")])
        if not fp: return
        
        project_data = {
            "version": "1.0",
            "grid_data": self.grid_data,
            "virtual_files": self.virtual_files,
            "files_to_encode": self.files_to_encode,
            "is_16bit": self.is_16bit.get(),
            # Include the current binary chars in the project for stability
            "binary_chars": self.binary_chars 
        }
        
        try:
            with open(fp, "w") as f:
                json.dump(project_data, f, indent=4)
            self.log("Project saved successfully.", "warn")
        except Exception as e:
            self.log(f"Error saving project: {e}", "error")

    def load_project(self):
        fp = filedialog.askopenfilename(filetypes=[("JSON Project", "*.json")])
        if not fp: return
        
        try:
            with open(fp, "r") as f:
                project_data = json.load(f)
            
            self.grid_data = project_data.get("grid_data", self.grid_data)
            self.virtual_files = project_data.get("virtual_files", {})
            self.files_to_encode = project_data.get("files_to_encode", [])
            self.is_16bit.set(project_data.get("is_16bit", True))
            
            # Load custom binary chars from project if available
            if "binary_chars" in project_data:
                self.binary_chars = project_data["binary_chars"]
                self.reverse_char_map = {v.rjust(7, "0"): k for k, v in self.binary_chars.items()}

            self.refresh_grid_ui()
            self.setup_charmap_tab() # Refresh charmap UI in case chars changed
            
            self.file_listbox.delete(0, "end")
            for p in self.files_to_encode:
                name = os.path.basename(p) if os.path.exists(p) else f"[Live] {p}"
                self.file_listbox.insert("end", name)
                
            self.update_boot_options()
            self.log("Project loaded successfully.", "warn")
            
        except Exception as e:
            self.log(f"Error loading project: {e}", "error")

    # --- ENCODER LOGIC ---
    def setup_encoder_tab(self):
        self.tab_encoder.grid_columnconfigure(0, weight=1)
        self.tab_encoder.grid_columnconfigure(1, weight=1)
        self.tab_encoder.grid_rowconfigure(0, weight=1)

        # Left: File Manager (Column 0)
        left = ctk.CTkFrame(self.tab_encoder)
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Active Files (File 0 is first)", font=(FONT_FAMILY, 16, "bold")).grid(row=0, column=0, columnspan=2, pady=8)
        self.file_listbox = tk.Listbox(left, bg="#2b2b2b", fg="white", borderwidth=0, highlightthickness=0, font=("Consolas", 11), selectmode=tk.SINGLE)
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        # Add/Remove buttons
        btn_f = ctk.CTkFrame(left, fg_color="transparent")
        btn_f.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        ctk.CTkButton(btn_f, text="+ Add File", **BTN_STYLE, command=self.add_encoder_file).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(btn_f, text="- Remove", fg_color="#c0392b", **Legacy_BTN_STYLE, command=self.remove_encoder_file).pack(side="left", expand=True, fill="x", padx=2)

        # Reordering buttons
        reorder_f = ctk.CTkFrame(left, fg_color="transparent")
        reorder_f.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        ctk.CTkButton(reorder_f, text="Move Up ⇧", **BTN_STYLE, command=self.move_file_up).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(reorder_f, text="Move Down ⇩", **BTN_STYLE, command=self.move_file_down).pack(side="left", expand=True, fill="x", padx=2)
        
        # Right: Output (Column 1)
        right = ctk.CTkFrame(self.tab_encoder)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        right.grid_rowconfigure(5, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Compiler Settings", font=(FONT_FAMILY, 16, "bold")).grid(row=0, column=0, pady=8)
        settings_box = ctk.CTkFrame(right, fg_color="#2b2b2b", corner_radius=6)
        settings_box.grid(row=1, column=0, sticky="ew", padx=10)

        ctk.CTkSwitch(settings_box, text="16-bit Mode (Unchecked is 8-bit)", variable=self.is_16bit, font=(FONT_FAMILY, 11)).pack(pady=10, padx=10, anchor="w")
        
        # Boot index group
        boot_f = ctk.CTkFrame(settings_box, fg_color="transparent")
        boot_f.pack(pady=(0, 10), padx=10, fill="x")
        ctk.CTkLabel(boot_f, text="Boot Index (Not used in current output)", anchor="w", font=(FONT_FAMILY, 10)).pack(fill="x", pady=(0, 2))
        self.opt_boot = ctk.CTkOptionMenu(boot_f, variable=self.boot_index, values=["0"], font=(FONT_FAMILY, 11), height=30)
        self.opt_boot.pack(fill="x")
        
        # Save Virtual Files Button
        ctk.CTkButton(right, text="SAVE VIRTUAL FILES AS .TXT", **BTN_STYLE, command=self.save_virtual_files).grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

        ctk.CTkButton(right, text="COMPILE TO CLIPBOARD", font=(FONT_FAMILY, 14, "bold"), 
                      fg_color="#27ae60", hover_color="#219150", command=self.run_encoder).grid(row=3, column=0, sticky="ew", padx=10, pady=(10, 20))

        ctk.CTkLabel(right, text="Console Output", font=(FONT_FAMILY, 12, "bold")).grid(row=4, column=0, sticky="w", padx=10, pady=(0, 5))
        self.console = ctk.CTkTextbox(right, font=("Consolas", 10))
        self.console.grid(row=5, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.console.configure(state="disabled")

    def log(self, message, type="info"):
        self.console.configure(state="normal")
        prefix = "[ERROR] " if type=="error" else "[WARN]  " if type=="warn" else "[INFO]  "
        self.console.insert("end", prefix + message + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def add_encoder_file(self):
        fps = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt")])
        for p in fps:
            if p not in self.files_to_encode:
                self.files_to_encode.append(p)
                self.file_listbox.insert("end", os.path.basename(p))
        self.update_boot_options()

    def remove_encoder_file(self):
        sel = self.file_listbox.curselection()
        if sel:
            idx = sel[0]
            name = self.files_to_encode[idx]
            
            if name.startswith("Virtual_Design_") and name in self.virtual_files: del self.virtual_files[name]
                
            self.file_listbox.delete(idx)
            self.files_to_encode.pop(idx)
            self.update_boot_options()

    # --- FEATURE: Encoder File Reordering ---
    def move_file(self, direction):
        sel = self.file_listbox.curselection()
        if not sel: return
        idx = sel[0]
        new_idx = idx + direction
        
        if 0 <= new_idx < len(self.files_to_encode):
            self.files_to_encode[idx], self.files_to_encode[new_idx] = self.files_to_encode[new_idx], self.files_to_encode[idx]
            
            temp_name = self.file_listbox.get(idx)
            self.file_listbox.delete(idx)
            self.file_listbox.insert(new_idx, temp_name)
            self.file_listbox.selection_set(new_idx)
            
            self.update_boot_options()
            self.log(f"Moved file index {idx} to {new_idx}.", "info")

    def move_file_up(self):
        self.move_file(-1)

    def move_file_down(self):
        self.move_file(1)

    # --- FEATURE: Save Virtual Files ---
    def save_virtual_files(self):
        if not self.virtual_files: return self.log("No virtual files to save.", "error")
        
        target_dir = filedialog.askdirectory()
        if not target_dir: return

        for name, content in self.virtual_files.items():
            file_path = os.path.join(target_dir, f"{name}.txt")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                self.log(f"Failed to save {name}: {e}", "error")

        self.log(f"Saved {len(self.virtual_files)} virtual files to {target_dir}.", "warn")
        
    def update_boot_options(self):
        options = [f"File {i}: {os.path.basename(p)}" for i, p in enumerate(self.files_to_encode)] if self.files_to_encode else ["0"]
        self.opt_boot.configure(values=options)
        if self.boot_index.get() not in options and options: self.boot_index.set(options[0])

    def run_encoder(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
    
        if not self.files_to_encode:
            return self.log("No files selected!", "error")

        try:
            type16 = self.is_16bit.get()
            out = "#dHCAgA/" if type16 else "XDCAgA/"
            digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@$%?&<()"

            def flip_byte(n):
                fmt = "{:016b}" if type16 else "{:08b}"
                return int(fmt.format(n)[::-1], 2)

            def base71(n):
                if n == 0:
                    return "00" + ("0" if type16 else "")
                s = ""
                while n > 0:
                    n, r = divmod(n, 71)
                    s = digits[r] + s
                # The length is 2 (8-bit) or 3 (16-bit). Base 71 encodes two 8-bit bytes 
                # or one 16-bit word, which should result in 2 or 3 chars respectively
                return s.rjust(2 + type16, "0")

            def calc_val(token):
                token = token.strip()
                if not token: return 0
                if all(c in "01" for c in token) and len(token) > 2: return int(token, 2)
                if token.isdigit(): return int(token)
                if token.lower().startswith("h"): return int(token[1:], 16)
                if len(token) == 1 and token in self.binary_chars: 
                    # Convert the 7-bit binary string to an integer
                    return int(self.binary_chars[token], 2)
                if "+" in token:
                    total = 0
                    for part in token.split("+"):
                        p = part.strip()
                        if not p: continue
                        if p.lower().startswith("b"): total += (1 << (int(p[1:]) - 1))
                        else: total += calc_val(p)
                    return total
                raise ValueError(f"Unknown token: {token}")

            address = 0
            for i, item in enumerate(self.files_to_encode):
                
                is_virtual = item.startswith("Virtual_Design_") or item in self.virtual_files
                
                self.log(f"Processing: {os.path.basename(item) if not is_virtual else item}...", "info")
                
                lines = []
                if is_virtual and item in self.virtual_files:
                    lines = self.virtual_files[item].splitlines()
                elif os.path.exists(item):
                    with open(item, "r") as f: # Use 'r' only for standard text files
                        lines = f.read().splitlines()
                else:
                    self.log(f"File not found or virtual content missing: {item}. Skipping.", "error")
                    continue
                
                for line in lines:
                    if address > 255: # Stop after address 255 (the last pixel)
                        self.log(f"File {i} finished/truncated after 256 addresses.", "warn")
                        break
                    
                    line = line.strip()
                    if not line or line.startswith(("#", "//")):
                        val = 0
                    else:
                        max_val = 65535 if type16 else 255
                        # If the line is 13 bits (our custom format), parse it directly
                        if len(line) == 13 and all(c in "01" for c in line):
                             val = int(line, 2)
                        else: # Assume it's a raw integer/hex/token expression
                            val = min(calc_val(line.split("//")[0]), max_val)
                        
                    out += base71(flip_byte(address)) + base71(flip_byte(val))
                    address += 1

            self.clipboard_clear()
            self.clipboard_append(out)
            self.log("SUCCESS! Encoded string copied to clipboard.", "warn")

        except Exception as e:
            self.log(f"Error: {e}", "error")

    # --- FEATURE: Character Map Editor ---
    def setup_charmap_tab(self):
        # Clear existing widgets from the tab (needed for refresh)
        for widget in self.tab_charmap.winfo_children():
            widget.destroy()

        self.tab_charmap.grid_columnconfigure(0, weight=1)
        self.tab_charmap.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.tab_charmap, text="Character to Binary Map Editor (7-bit encoding)", font=(FONT_FAMILY, 16, "bold")).grid(row=0, column=0, pady=8)
        
        map_frame = ctk.CTkScrollableFrame(self.tab_charmap, fg_color=THEME["surface_2"], corner_radius=6)
        map_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.char_entries = {}
        sorted_chars = sorted(self.binary_chars.keys())
        
        col_count = 6 
        
        for i, char in enumerate(sorted_chars):
            r = i // col_count
            c = i % col_count
            
            map_frame.grid_columnconfigure(c, weight=1)
            
            char_frame = ctk.CTkFrame(map_frame, fg_color=THEME["surface"], corner_radius=4)
            char_frame.grid(row=r, column=c, padx=5, pady=5, sticky="ew")
            
            ctk.CTkLabel(char_frame, text=f"Char: '{char}'", font=("Consolas", 11, "bold")).pack(pady=(5, 0), padx=5)
            
            entry = ctk.CTkEntry(char_frame, width=100, placeholder_text="7-bit binary", 
                                 font=("Consolas", 11), validate="all", 
                                 validatecommand=(self.register(self.validate_7bit), '%P'))
            entry.insert(0, self.binary_chars[char])
            entry.pack(pady=(0, 5), padx=5)
            
            self.char_entries[char] = entry
            
        # --- BUTTON FRAME ---
        action_frame = ctk.CTkFrame(self.tab_charmap, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        
        # New: Import Button
        ctk.CTkButton(
            action_frame, 
            text="IMPORT BUILDLOGIC CHARS", 
            fg_color="#3498db", 
            hover_color="#2980b9", 
            height=40, 
            font=(FONT_FAMILY, 12, "bold"), 
            command=self.import_binary_chars
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        # Existing: Apply & Save Button
        ctk.CTkButton(
            action_frame, 
            text="APPLY & SAVE MAP", 
            fg_color=THEME["success"], 
            hover_color="#15803d", 
            height=40, 
            font=(FONT_FAMILY, 12, "bold"), 
            command=self.apply_and_save_charmap
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))


    def validate_7bit(self, new_text):
        if not new_text:
            return True
        if len(new_text) > 7 or not all(c in '01' for c in new_text):
            return False
        return True

    def apply_and_save_charmap(self):
        new_map = {}
        for char, entry in self.char_entries.items():
            binary_str = entry.get().strip()
            if len(binary_str) != 7 or not all(c in '01' for c in binary_str):
                self.log(f"Char '{char}' has invalid 7-bit value: '{binary_str}'. Aborting save.", "error")
                return
            new_map[char] = binary_str
        
        self.binary_chars = new_map
        self.reverse_char_map = {v: k for k, v in new_map.items()}
        self.save_char_map()
        self.log("New character map applied and saved to file.", "warn")

    # --- FEATURE: Import Binary Chars ---
    def import_binary_chars(self):
        fp = filedialog.askopenfilename(
            title="Import BuildLogic Char Map",
            filetypes=[("JSON Files", "*.json")]
        )
        if not fp:
            return

        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            new_map = data.get("CharToBin")
            if not new_map or not isinstance(new_map, dict):
                raise ValueError("JSON file is missing the 'CharToBin' dictionary.")

            valid_entries = {}
            for char, binary_str in new_map.items():
                if isinstance(binary_str, str) and len(binary_str) == 7 and all(c in '01' for c in binary_str):
                    valid_entries[char] = binary_str
                else:
                    self.log(f"Skipping invalid entry in file: Char '{char}' with value '{binary_str}'", "error")

            if not valid_entries:
                raise ValueError("No valid 7-bit character entries found in the file.")
                
            # Update internal state
            self.binary_chars = valid_entries
            self.reverse_char_map = {v: k for k, v in valid_entries.items()}
            
            # Save the new map to the application's local file for persistence
            self.save_char_map() 

            # Refresh the UI to show the imported values
            self.setup_charmap_tab() 

            self.log(f"Successfully imported {len(valid_entries)} character entries from {os.path.basename(fp)}. Remember to re-export any design files to update their header.", "warn")

        except json.JSONDecodeError:
            self.log("Error: Imported file is not a valid JSON format.", "error")
        except Exception as e:
            self.log(f"Failed to import character map: {e}", "error")


if __name__ == "__main__":
    app = CombinedEEPROMApp()
    app.mainloop()