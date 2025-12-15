import customtkinter as ctk
from PIL import Image, ImageTk
#macos scaling (affect on windows not yet tested [!])
ctk.set_widget_scaling(1)
ctk.set_window_scaling(1)
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
# Try cross-platform defaults first, then Segoe UI.
try:
    # Use a standard font like 'Arial' or 'Helvetica' as a fallback base
    FONT_FAMILY = "Helvetica" 
    
    # Try loading Segoe UI if available (Windows)
    ctk.FontManager.load_font("C:/Windows/Fonts/segoeui.ttf")
    FONT_FAMILY = "Segoe UI"
except Exception:
    # Fallback remains 'Helvetica' or 'Roboto'
    pass

# Ensure your constants use the finalized FONT_FAMILY

THEME = {
    "bg": "#0f0f0f",
    "surface": "#1a1a1a",     # Primary container/card background
    "surface_2": "#202020",   # Secondary container/sidebar background
    "border": "#2a2a2a",
    
    # Text colors
    "text": "#e5e5e5",        # High contrast text
    "muted": "#9ca3af",       # Secondary/placeholder text
    
    # Primary Accent (Bright Green)
    "accent": "#0e75c4",   
    "accent_hover": "#135f9a",
    
    # Semantic Colors
    "danger": "#dc2626",      # For clear grid
    "error": "#dc2626",       # Red for error messages/remove buttons
    "error_hover": "#ae1919",
    "info": "#0e75c4",        # Blue for info/saving
    "info_hover": "#135f9a",
    "success": "#16a34a",     # Darker green for COMPILING button (good contrast)
    "success_hover": "#0f7534",
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

BTN_STYLE_HM = {
    #"height": 34, # Slightly reduced for better spacing - no height mod for buttons which have custom heights
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
        try:
            # Load the PNG image using Pillow
            icon_image = ImageTk.PhotoImage(Image.open("icon.png")) 
            
            # Set the icon for the window (macOS preferred method)
            # The 'True' flag makes this the icon for all windows
            self.iconphoto(True, icon_image) 
            
        except FileNotFoundError:
            print("Warning: icon.png not found. Window will use default icon.")
        except Exception as e:
            # Fallback for Windows or other errors (not strictly needed on Mac)
            self.iconbitmap("icon.ico") 
            print(f"Icon loading error: {e}")
        self.minsize(1800, 1200) 
        
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
        # ------------------ ROOT GRID CONFIG ------------------
        self.tab_designer.grid_columnconfigure(0, weight=1) # Drawing Area (Left)
        self.tab_designer.grid_columnconfigure(1, weight=0, minsize=350) # Sidebar (Right)
        self.tab_designer.grid_rowconfigure(0, weight=1)

        # ------------------ LEFT SIDE: DRAWING AREA (Column 0) ------------------
        container = ctk.CTkFrame(self.tab_designer, fg_color=THEME["surface_2"], corner_radius=10) 
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # Drawing Area (Center) - Ensures the grid is centered
        draw_frame = tk.Frame(container, bg=THEME["surface_2"])
        draw_frame.grid(row=0, column=0, sticky="nsew")
        
        # Centering the grid within the frame
        self.grid_inner = tk.Frame(draw_frame, bg="#202020")
        self.grid_inner.pack(expand=True, padx=20, pady=20) 
        
        # Grid initialization (kept mostly the same for functionality)
        self.cells = {}
        # Assuming GRID_SIZE, UI_COLORS, and relevant commands are defined elsewhere
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = tk.Label(self.grid_inner, text=" ", width=6, height=3, # Slightly more compact grid
                                font=("Courier New", 12, "bold"), bg=UI_COLORS["black"],
                                fg="white", relief="flat", bd=1)
                cell.grid(row=r, column=c, padx=1, pady=1)
                
                cell.bind("<Button-1>", lambda e, row=r, col=c: self.on_cell_down(e, row, col))
                cell.bind("<B1-Motion>", self.on_cell_drag)
                cell.bind("<ButtonRelease-1>", self.on_cell_up)
                
                # New: Bind hover event for live info display
                cell.bind("<Enter>", lambda e, row=r, col=c: self.update_cell_info(row, col))
                cell.bind("<Leave>", lambda e: self.clear_cell_info())
                
                self.cells[cell] = (r, c)
        
        self.refresh_grid_ui()
                
        # ------------------ RIGHT SIDE: SIDEBAR (Column 1) ------------------
        sidebar = ctk.CTkFrame(self.tab_designer, width=350, fg_color=THEME["surface"], corner_radius=10)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Use a scrollable frame for the sidebar if tools/actions get too long
        scroll_sidebar = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        scroll_sidebar.pack(fill="both", expand=True, padx=5, pady=5)


        # --- 1. TOOL SELECTION ---
        self.create_sidebar_heading(scroll_sidebar, "🔧 Drawing Tools")
        tool_frame = ctk.CTkFrame(scroll_sidebar, fg_color=THEME["surface_2"], corner_radius=8)
        tool_frame.pack(fill="x", padx=10, pady=(0, 10))
        tool_frame.grid_columnconfigure(0, weight=1) # Make column 0 expandable
        
        # Standardized radio button layout
        ctk.CTkRadioButton(tool_frame, text="Paint (Click/Drag)", variable=self.tool_var, value="paint", command=self.sync_tools, font=(FONT_FAMILY, 11, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=4)
        ctk.CTkRadioButton(tool_frame, text="Text (Sequential Type)", variable=self.tool_var, value="text", command=self.sync_tools, font=(FONT_FAMILY, 11, "bold")).grid(row=1, column=0, sticky="w", padx=15, pady=4)
        ctk.CTkRadioButton(tool_frame, text="Line (Start & End Click)", variable=self.tool_var, value="line", command=self.sync_tools, font=(FONT_FAMILY, 11, "bold")).grid(row=2, column=0, sticky="w", padx=15, pady=4)
        ctk.CTkRadioButton(tool_frame, text="Fill (Bucket)", variable=self.tool_var, value="fill", command=self.sync_tools, font=(FONT_FAMILY, 11, "bold")).grid(row=3, column=0, sticky="w", padx=15, pady=4)
        # Selector tool is hidden: ctk.CTkRadioButton(tool_frame, text="Select (Box Drag)", variable=self.tool_var, value="select", command=self.sync_tools, font=(FONT_FAMILY, 11)).grid(row=4, column=0, sticky="w", padx=5, pady=2)
        
        
        # --- 2. COLOR PALETTE ---
        self.create_sidebar_heading(scroll_sidebar, "🎨 Color Palette")
        palette_box = ctk.CTkFrame(scroll_sidebar, fg_color=THEME["surface_2"], corner_radius=8)
        palette_box.pack(fill="x", padx=10, pady=(0, 10))
        
        palette_grid = ctk.CTkFrame(palette_box, fg_color="transparent")
        palette_grid.pack(pady=10, padx=10)
        
        # Dynamic Palette Layout
        row, col = 0, 0
        max_cols = 5
        for name, hex_val in UI_COLORS.items():
            ctk.CTkButton(palette_grid, text=" ", width=45, height=45, fg_color=hex_val, 
                          hover_color=hex_val, corner_radius=6, 
                          command=lambda c=name: self.select_color(c)).grid(row=row, column=col, padx=4, pady=4)
            col += 1
            if col >= max_cols: col = 0; row += 1
        
        # Selected Color Info
        self.lbl_selected = ctk.CTkLabel(palette_box, text="Current Color: RED", font=(FONT_FAMILY, 12, "bold"), anchor="center")
        self.lbl_selected.pack(fill="x", pady=(0, 10))


        # --- 3. TRANSFORM & ACTIONS ---
        self.create_sidebar_heading(scroll_sidebar, "🔄 Grid Transformations")
        action_frame = ctk.CTkFrame(scroll_sidebar, fg_color=THEME["surface_2"], corner_radius=8)
        action_frame.pack(fill="x", padx=10, pady=(0, 10))
        action_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Transformation Tools (kept same structure)
        btn_h = 35
        ctk.CTkButton(action_frame, text="Flip Horizontal", height=btn_h, **BTN_STYLE_HM, command=lambda: self.transform_grid('flip_h')).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="ew")
        
        # New Row for Rotate and Flip V
        ctk.CTkButton(action_frame, text="Flip Vertical", height=btn_h, **BTN_STYLE_HM, command=lambda: self.transform_grid('flip_v')).grid(row=1, column=0, columnspan=2, padx=(10, 5), pady=5, sticky="ew")
        ctk.CTkButton(action_frame, text="Rotate ↻", height=btn_h, **BTN_STYLE_HM, command=lambda: self.transform_grid('rotate')).grid(row=1, column=2, padx=(5, 10), pady=5, sticky="ew")


        # --- 4. DATA PREVIEW ---
        self.create_sidebar_heading(scroll_sidebar, "📊 Cell Data Preview")
        preview_frame = ctk.CTkFrame(scroll_sidebar, fg_color=THEME["surface_2"], corner_radius=8)
        preview_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Live Info Label (Improved readability)
        self.lbl_cell_info = ctk.CTkLabel(preview_frame, text="Hover over a cell to see data.", justify="left", 
                                          font=("Consolas", 11), padx=10, anchor="w")
        self.lbl_cell_info.pack(fill="x", padx=10, pady=10)
        
        # Clear Grid Button (High visibility, kept the danger color)
        ctk.CTkButton(preview_frame, text="WIPE ENTIRE GRID", fg_color=THEME["danger"], hover_color="#b91c1c", 
                      height=40, font=(FONT_FAMILY, 14, "bold"), command=lambda: self.clear_grid(confirm=True)).pack(fill="x", padx=10, pady=(5, 10))


        # --- 5. PROJECT & I/O ---
        self.create_sidebar_heading(scroll_sidebar, "💾 Project I/O")
        io_frame = ctk.CTkFrame(scroll_sidebar, fg_color=THEME["surface_2"], corner_radius=8)
        io_frame.pack(fill="x", padx=10, pady=(0, 15))
        io_frame.grid_columnconfigure((0, 1), weight=1)

        # Load/Save Project (for internal state)
        ctk.CTkButton(io_frame, text="LOAD PROJECT (.json)", height=35, **BTN_STYLE_HM, command=self.load_project).grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="ew")
        ctk.CTkButton(io_frame, text="SAVE PROJECT (.json)", height=35, **BTN_STYLE_HM, command=self.save_project).grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="ew")
        
        # Import/Export .TXT (for encoder compatibility)
        ctk.CTkButton(io_frame, text="IMPORT TXT (File)", height=35, **BTN_STYLE_HM, command=self.import_designer_file).grid(row=1, column=0, padx=(10, 5), pady=(5, 5), sticky="ew")
        ctk.CTkButton(io_frame, text="EXPORT TXT (File)", height=35, **BTN_STYLE_HM, command=self.export_designer_file).grid(row=1, column=1, padx=(5, 10), pady=(5, 5), sticky="ew")


        # --- 6. ENCODER INTEGRATION ---
        self.create_sidebar_heading(scroll_sidebar, "🔗 Integration")
        ctk.CTkButton(
            scroll_sidebar,
            text="SEND DESIGN TO ENCODER",
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            height=50,
            font=(FONT_FAMILY, 15, "bold"),
            command=self.send_to_encoder,
        ).pack(fill="x", padx=15, pady=(5, 15))

    def update_cell_info(self, row, col):
        # Assuming you have a design_grid_data structure holding the raw color values (0-7, or hex/name)
        # Assuming your UI_COLORS dictionary maps names to hex, and you have a reverse map to binary.
        
        # Calculate Address: 4-bit Location (0) + 8-bit Pixel (r*N + c)
        pixel_address = (row * GRID_SIZE) + col 
        
        # The 16-bit EEPROM address (Location 0, Pixel X)
        eeprom_address = pixel_address # Simplification: Assuming Location 0
        
        # Fetch the data stored in the pixel (You must implement how data is stored, e.g., self.pixel_data[row][col])
        # Example data structure: (RGB1_Value, RGB2_Value, Character_Value)
        # For simplicity, let's assume you fetch the stored color name or RGB value.
        
        # Placeholder for actual data retrieval
        # pixel_color_name = self.pixel_data[row][col].color_name
        # pixel_combined_val = self.get_combined_value(row, col) # A function to get the final 16-bit value
        
        # For demonstration, use address and row/col info:
        info_text = (
            f"Address: 0x00{eeprom_address:02X} (L0:P{pixel_address})\n"
            f"Pixel: ({row}, {col})\n"
            f"DEC Value: 0\n" # Replace 0 with the actual DEC value
            f"BIN Value: 000 000 000 0000000" # Replace with actual 16-bit binary
        )
        self.lbl_cell_info.configure(text=info_text)

    def clear_cell_info(self):
        self.lbl_cell_info.configure(text="Hover over a cell to see data.")

    # --- ADD THIS METHOD TO YOUR CLASS (If missing) ---
    def create_sidebar_heading(self, parent, text):
        # FIX: Remove pady from the CTkLabel constructor and place it in .pack()
        ctk.CTkLabel(parent, text=text, font=(FONT_FAMILY, 16, "bold"), padx=10, anchor="w").pack(fill="x", padx=5, pady=(15, 5))
        ctk.CTkFrame(parent, height=1, fg_color="gray40").pack(fill="x", padx=15, pady=5)

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
        
        # ------------------ ROOT GRID CONFIG ------------------
        self.tab_encoder.grid_columnconfigure(0, weight=1, minsize=350) # File Manager
        self.tab_encoder.grid_columnconfigure(1, weight=1, minsize=450) # Settings & Console
        self.tab_encoder.grid_rowconfigure(0, weight=1)

        # ------------------ LEFT SIDE: FILE MANAGER (Column 0) ------------------
        left = ctk.CTkFrame(self.tab_encoder, corner_radius=10, fg_color=THEME["surface_2"])
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(left, text="📂 File Order & Management", font=(FONT_FAMILY, 18, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=10)

        # Listbox
        self.file_listbox = tk.Listbox(left, bg=THEME["surface"], fg="white", borderwidth=0, 
                                   highlightthickness=0, font=("Consolas", 11), selectmode=tk.SINGLE,
                                   relief="flat", bd=0)
        self.file_listbox.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))

        # --- File Add/Remove Buttons ---
        btn_f = ctk.CTkFrame(left, fg_color="transparent")
        btn_f.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 5))
        btn_f.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_f, text="+ Add File", **BTN_STYLE, command=self.add_encoder_file).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(btn_f, text="- Remove", fg_color=THEME["error"], hover_color=THEME["error_hover"], 
                      **Legacy_BTN_STYLE, command=self.remove_encoder_file).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # --- Reordering Buttons ---
        reorder_f = ctk.CTkFrame(left, fg_color="transparent")
        reorder_f.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 15))
        reorder_f.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(reorder_f, text="Move Up ⇧", **BTN_STYLE, command=self.move_file_up).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(reorder_f, text="Move Down ⇩", **BTN_STYLE, command=self.move_file_down).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # --- Virtual File Management ---
        ctk.CTkButton(left, text="💾 SAVE VIRTUAL FILES AS .TXT", 
                      fg_color=THEME["info"], hover_color=THEME["info_hover"],
                      **BTN_STYLE, command=self.save_virtual_files).grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 15))


        # ------------------ RIGHT SIDE: SETTINGS & CONSOLE (Column 1) ------------------
        right = ctk.CTkFrame(self.tab_encoder, corner_radius=10, fg_color=THEME["surface_2"])
        right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        # We need to increase the weight of the console row, which will now be row 6
        right.grid_rowconfigure(6, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(right, text="⚙️ Compiler Options & Output", font=(FONT_FAMILY, 18, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=10)

        # --- Group 1: Core Settings (Row 1) ---
        settings_box = ctk.CTkFrame(right, fg_color=THEME["surface"], corner_radius=8)
        settings_box.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # 16-bit Mode
        ctk.CTkSwitch(settings_box, text="16-bit Data Mode (Unchecked is 8-bit)", variable=self.is_16bit, font=(FONT_FAMILY, 11, "bold")).pack(pady=(10, 5), padx=15, anchor="w")

        # NEW FEATURE: Data Integrity Checkbox
        self.check_integrity = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(settings_box, text="High Integrity Check (Disable for speed)", variable=self.check_integrity, 
                      font=(FONT_FAMILY, 11), onvalue=True, offvalue=False).pack(pady=(5, 10), padx=15, anchor="w")

        
        # --- Group 1.5: EEPROM Usage Dashboard (NEW - Row 2) ---
        usage_box = ctk.CTkFrame(right, fg_color=THEME["surface"], corner_radius=8)
        usage_box.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(usage_box, text="📊 EEPROM Usage Dashboard", font=(FONT_FAMILY, 14, "bold"), anchor="w").pack(fill="x", padx=15, pady=(8, 4))
        
        # 1. Total Usage Progress Bar
        self.lbl_total_usage = ctk.CTkLabel(usage_box, text="Total Memory Used: 0 / 4096 Addresses (0.0%)", font=(FONT_FAMILY, 11), anchor="w")
        self.lbl_total_usage.pack(fill="x", padx=15, pady=(0, 2))
        
        self.progress_total = ctk.CTkProgressBar(usage_box, height=10, corner_radius=5, fg_color="#333333", progress_color="#3498db")
        self.progress_total.set(0.0)
        self.progress_total.pack(fill="x", padx=15, pady=(0, 8))
        
        # 2. File Saturation Details (Scrollable List)
        ctk.CTkLabel(usage_box, text="File Saturation (Max 256 addresses per file):", font=(FONT_FAMILY, 11, "bold"), anchor="w").pack(fill="x", padx=15, pady=(4, 2))
        
        self.file_usage_scroll = ctk.CTkScrollableFrame(usage_box, height=100, fg_color="#2b2b2b", corner_radius=6)
        self.file_usage_scroll.pack(fill="x", padx=15, pady=(0, 10))
        
        # Placeholder Label - This will be replaced by dynamic labels in run_encoder
        self.lbl_file_usage_placeholder = ctk.CTkLabel(self.file_usage_scroll, text="Run compiler to calculate usage...", font=(FONT_FAMILY, 10), text_color="#aaaaaa")
        self.lbl_file_usage_placeholder.pack(padx=10, pady=5)

        
        # --- Group 2: Boot & Output Settings (Row 3 - BUMPED) ---
        boot_output_box = ctk.CTkFrame(right, fg_color=THEME["surface"], corner_radius=8)
        boot_output_box.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10)) # OLD ROW 2
        
        # Boot Index
        boot_f = ctk.CTkFrame(boot_output_box, fg_color="transparent")
        boot_f.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(boot_f, text="Boot File Index (0-15)", anchor="w", font=(FONT_FAMILY, 12, "bold")).pack(fill="x", pady=(0, 2))
        self.opt_boot = ctk.CTkOptionMenu(boot_f, variable=self.boot_index, values=["0"], font=(FONT_FAMILY, 11), height=35)
        self.opt_boot.pack(fill="x")

        # NEW FEATURE: Output Type Selection
        self.output_mode = ctk.StringVar(value="Clipboard")
        ctk.CTkLabel(boot_output_box, text="Output Destination", anchor="w", font=(FONT_FAMILY, 12, "bold")).pack(fill="x", padx=10, pady=(5, 2))
        ctk.CTkSegmentedButton(boot_output_box, variable=self.output_mode, 
                               values=["Clipboard", "Save File (.dat)"], font=(FONT_FAMILY, 11), height=35).pack(fill="x", padx=10, pady=(0, 10))


        # --- Compile Button (Row 4 - BUMPED) ---
        ctk.CTkButton(right, text="🚀 COMPILE & EXPORT", font=(FONT_FAMILY, 16, "bold"), 
                      fg_color=THEME["success"], hover_color=THEME["success_hover"], 
                      command=self.run_encoder, height=50).grid(row=4, column=0, sticky="ew", padx=15, pady=(10, 20)) # OLD ROW 3

        # --- Console Output (Row 5 - BUMPED) ---
        ctk.CTkLabel(right, text="🖥️ Console Log", font=(FONT_FAMILY, 14, "bold")).grid(row=5, column=0, sticky="w", padx=15, pady=(0, 5)) # OLD ROW 4
        
        # Console Textbox (Row 6 - BUMPED)
        self.console = ctk.CTkTextbox(right, font=("Consolas", 10), corner_radius=8, fg_color=THEME["surface"])
        self.console.grid(row=6, column=0, sticky="nsew", padx=15, pady=(0, 15)) # OLD ROW 5
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
            # Check if file path is already tracked
           if p not in self.files_to_encode:
                # 1. Add the full path to the internal list (most important)
                self.files_to_encode.append(p)

                # 2. Prepare the display string: Name (Full Path)
                short_name = os.path.basename(p)
                # Use os.path.normpath to clean up path separators
                display_path = os.path.normpath(p) 
            
                # 3. Insert the formatted string into the Listbox
                # We add the index number in the listbox for clarity
                listbox_index = len(self.file_listbox.get(0, "end"))
            
                # Formatting the output string (using tabs or spaces for alignment)
                formatted_entry = f"📄 ({listbox_index}) Name: {short_name:<25} (Source: {display_path})" 
            
                self.file_listbox.insert("end", formatted_entry)
            
                self.log(f"Added file: {short_name} at index {listbox_index}.", "info")
            
        self.update_boot_options()

    def remove_encoder_file(self):
        sel = self.file_listbox.curselection()
        if not sel: return
        
        idx = sel[0]
        
        # 1. Handle Virtual File Cleanup
        name = self.files_to_encode[idx]
        if name.startswith("Virtual_Design_") and name in self.virtual_files: 
            del self.virtual_files[name]
        
        # 2. Remove the file path and listbox entry
        self.files_to_encode.pop(idx)
        self.file_listbox.delete(idx)
        
        self.log(f"Removed file at index {idx}.", "warn")
        
        # 3. Re-index and refresh the subsequent entries in the listbox (Crucial for visual consistency)
        self._refresh_listbox_indices(idx)

        self.update_boot_options()

    def _refresh_listbox_indices(self, start_idx=0):
        """
        Helper method to re-insert the [Index] prefix after a move or removal.
        """
        for i in range(start_idx, len(self.files_to_encode)):
            # The full path is always stored in self.files_to_encode
            p = self.files_to_encode[i]
            short_name = os.path.basename(p)
            display_path = os.path.normpath(p)
            
            formatted_entry = f"📄 ({i}) Name: {short_name:<25} (Source: {display_path})"
            
            # Delete the old entry and insert the new, correctly indexed entry
            self.file_listbox.delete(i)
            self.file_listbox.insert(i, formatted_entry)

    # --- FEATURE: Encoder File Reordering ---
    def move_file(self, direction):
        sel = self.file_listbox.curselection()
        if not sel: return
        idx = sel[0]
        new_idx = idx + direction
        
        if 0 <= new_idx < len(self.files_to_encode):
            
            # 1. Swap the paths in the internal list
            self.files_to_encode[idx], self.files_to_encode[new_idx] = self.files_to_encode[new_idx], self.files_to_encode[idx]
            
            # 2. Swap the display strings in the Listbox and fix indexing
            self.file_listbox.delete(idx)
            self.file_listbox.delete(new_idx - 1 if new_idx > idx else new_idx) # Delete the other item after the first delete shifts indices
            
            # Use the helper function to re-insert the items with correct new indices
            self._refresh_listbox_indices(min(idx, new_idx))
            
            # 3. Re-select the moved item
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
        
    def update_usage_dashboard(self, total_written, file_counts):
        # Constants
        TOTAL_MAX = 4096 # 16 Locations * 256 Pixels
        FILE_MAX = 256   # Max pixels per file/location
        
        # --- Update Total Usage ---
        percentage = total_written / TOTAL_MAX if TOTAL_MAX > 0 else 0
        self.progress_total.set(percentage)
        self.lbl_total_usage.configure(text=f"Total Memory Used: {total_written} / {TOTAL_MAX} Addresses ({percentage*100:.1f}%)")
        
        # --- Clear and Update File Usage Details ---
        
        # Remove old placeholder/labels in the scrollable frame
        for widget in self.file_usage_scroll.winfo_children():
            widget.destroy()
            
        # Add new labels for each file
        if not file_counts:
             ctk.CTkLabel(self.file_usage_scroll, text="No files encoded.", font=(FONT_FAMILY, 10), text_color="#aaaaaa").pack(padx=10, pady=5)
             return
             
        for i, count in enumerate(file_counts):
            file_name = os.path.basename(self.files_to_encode[i])
            file_percentage = count / FILE_MAX
            
            # Use red/warning color if the file is over 80% full
            color = "#27ae60" # Green
            #if file_percentage >= 0.8:
            #    color = "#f39c12" # Orange
            #if file_percentage == 1.0:
            #    color = "#c0392b" # Red (Full)

            # File usage line (e.g., "File 0 (Boot): 256/256 (100.0%)")
            file_text = f"File {i} ({file_name}): {count} / {FILE_MAX} ({file_percentage*100:.1f}%)"
            
            lbl = ctk.CTkLabel(self.file_usage_scroll, text=file_text, font=(FONT_FAMILY, 10, "bold"), text_color=color, anchor="w")
            lbl.pack(fill="x", padx=10, pady=1)

            # Optional: Add a small progress bar for the file usage in the scrollable frame
            progress = ctk.CTkProgressBar(self.file_usage_scroll, height=5, corner_radius=3, fg_color="#333333", progress_color=color)
            progress.set(file_percentage)
            progress.pack(fill="x", padx=10, pady=(0, 4))

    def update_boot_options(self):
        options = [f"File {i}: {os.path.basename(p)}" for i, p in enumerate(self.files_to_encode)] if self.files_to_encode else ["0"]
        self.opt_boot.configure(values=options)
        if self.boot_index.get() not in options and options: self.boot_index.set(options[0])

    # --- Encoder Logic ---
    
    def get_boot_file_index(self):
        # Extract index from the dropdown string "File 0: name.txt" -> 0
        selected_str = self.boot_index.get()
        if "File " in selected_str:
            try:
                return int(selected_str.split(":")[0].replace("File ", ""))
            except ValueError:
                return 0 # Should not happen
        return 0

    def run_encoder(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        
        if not self.files_to_encode:
            self.log("No files selected!", "error")
            return
        if not self.binary_chars:
            self.log("BinaryChars.json not loaded. Cannot encode.", "error")
            return

        # Check file count limit (4-bit Location field limit)
        num_files = len(self.files_to_encode)
        if num_files > 16:
            self.log(f"FATAL ERROR: Maximum number of save files is 16 (0-15), but {num_files} were selected.", "error")
            return

        try:
            # 1. Setup & Helper Functions
            type16 = self.is_16bit.get() # Should be True (16-bit data word)
            header = "#dHCAgA/" if type16 else "XDCAgA/"
            output_string = header
            digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@$%?&<()"
            total_addresses_written = 0
            file_addresses_written = []
            
            # Helper functions remain the same: flip_byte, base71, calc_val

            def flip_byte(n):
                # Flips 16 bits if type16 is True
                fmt = "{:016b}" if type16 else "{:08b}"
                return int(fmt.format(n)[::-1], 2)

            def base71(n):
                # Encodes 16-bit word into 3 base71 chars
                if n == 0: return "00" + ("0" if type16 else "")
                out = ""
                while n > 0:
                    n, r = divmod(n, 71)
                    out = digits[r] + out
                return out.rjust(2 + type16, "0")

            def calc_val(token):
                # ... (calc_val logic from previous response) ...
                token = token.strip()
                if not token: return 0
                if all(c in "01" for c in token) and len(token) > 2: return int(token, 2)
                if token.isdigit(): return int(token)
                if token.lower().startswith("h"): return int(token[1:], 16)
                if len(token) == 1 and token in self.binary_chars: return int(self.binary_chars[token], 2)
                if "+" in token:
                    total = 0
                    for part in token.split("+"):
                        part = part.strip()
                        if not part: continue
                        if part.lower().startswith("b"): total += (1 << (int(part[1:]) - 1))
                        else: total += calc_val(part)
                    return total
                raise ValueError(f"Unknown token: {token}")

            
            # 2. Sequential File Encoding
            
            # We don't need a single global address counter. We iterate through files
            # (Location 0 to 15) and for each file, we use the local pixel address (0 to 255).
            
            # This will store the final EEPROM address before flipping/encoding
            eeprom_address = 0 
            
            # 3. Encode File Data
            
            for file_index, filepath_or_name in enumerate(self.files_to_encode):
                
                # The file_index is the 4-bit Location field
                location_bits = file_index 

                is_virtual = filepath_or_name in self.virtual_files
                filename = os.path.basename(filepath_or_name) if not is_virtual else filepath_or_name
                self.log(f"Encoding File {file_index} (Location {location_bits}) : {filename}...", "info")
                
                if is_virtual:
                    lines = self.virtual_files[filepath_or_name].splitlines()
                else:
                    try:
                        with open(filepath_or_name, "r", encoding="utf-8") as f:
                            lines = f.read().splitlines()
                    except FileNotFoundError:
                        self.log(f"File not found: {filename}. Skipping.", "error")
                        continue
                
                local_pixel_address = 0 
                current_file_address_count = 0 # NEW: Counter for the current file
                
                max_val = (1 << 16) - 1 # 16-bit max value (65535)

                for line_num, line in enumerate(lines):
                    
                    # --- Local Address Check ---
                    if local_pixel_address > 255:
                        self.log(f"WARN: File {file_index} ({filename}) truncated after 256 addresses (Pixel 0xFF).", "warn")
                        break # Stop processing this file's lines

                    clean_line = line.split("//")[0].strip()
                    if not clean_line or clean_line.startswith("#"): 
                        continue # Skip empty/comment lines

                    try:
                        val = calc_val(clean_line)
                        if val > max_val:
                            self.log(f"Line {line_num+1}: Value {val} too high for 16-bit EEPROM word.", "error")
                            return

                        # Construct the 16-bit EEPROM address:
                        eeprom_address = (location_bits << 8) | local_pixel_address

                        # Write the encoded data
                        output_string += base71(flip_byte(eeprom_address)) # Address word
                        output_string += base71(flip_byte(val))            # Data word
                        
                        local_pixel_address += 1

                        # NEW: Increment file and total counters
                        if val != 0:
                            current_file_address_count += 1
                            total_addresses_written += 1

                    except Exception as e:
                        self.log(f"Error in {filename} line {line_num+1} ({clean_line}): {e}", "error")
                        return

            file_addresses_written.append(current_file_address_count)

            # --- 4. Write Header to High Addresses (0xFFFC to 0xFFFF) ---
            self.update_usage_dashboard(total_addresses_written, file_addresses_written)
            header_start_addr = (15 << 8) | 252 # Location 15 (0xF), Pixel 252 (0xFC) = 0xFFFC
            current_addr = header_start_addr
            
            self.log(f"Writing system header to high addresses (0x{header_start_addr:04X} to 0xFFFF)...", "info")

            # Address 0xFFFC: Number of Files
            output_string += base71(flip_byte(current_addr)) + base71(flip_byte(num_files))
            current_addr += 1

            # Address 0xFFFD: Boot File Index
            boot_index_val = self.get_boot_file_index()
            output_string += base71(flip_byte(current_addr)) + base71(flip_byte(boot_index_val))
            current_addr += 1

            # Address 0xFFFE, 0xFFFF: Reserved/Unused (Set to 0)
            output_string += base71(flip_byte(current_addr)) + base71(flip_byte(0))
            current_addr += 1
            output_string += base71(flip_byte(current_addr)) + base71(flip_byte(0))
            # current_addr is now 0x10000, outside the 16-bit range.

            # --- 5. FINAL MARKER AND COPY ---
            
            # Add the final end marker
            output_string += "=1"

            # Copy the entire encoded string to the clipboard
            self.clipboard_clear()
            self.clipboard_append(output_string)
            self.log("--------------------------------")
            self.log(f"SUCCESS! Output copied to clipboard.", "warn")
            self.log(f"Encoded {num_files} files. Final Header Address: 0xFFFF.", "warn")
            
        except Exception as e:
            self.log(f"Critical Error: {e}", "error")
            messagebox.showerror("Encoding Error", f"A critical error occurred during encoding: {e}")

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