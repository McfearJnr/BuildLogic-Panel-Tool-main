import json
import sys
import re
import argparse
import time
import random
import datetime
import os 

try:
    from colorama import Fore
except:
    class _Fake:
        RED = ""
        BLUE = ""
        YELLOW = ""
        RESET = ""
    Fore = _Fake()

# --- Logging Functions ---
def log(content, t=""):
    ts = time.time()
    stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    if t == "warn":
        print(Fore.YELLOW + "[WARNING]" + Fore.BLUE + f" [{stamp}]" + Fore.RESET, content)
    elif t == "error":
        print(Fore.RED + "[ERROR]" + Fore.BLUE + f" [{stamp}]" + Fore.RESET, content)
    else:
        print(Fore.BLUE + f"[{stamp}]" + Fore.RESET, content)

def error_msg(content):
    log(content, "error")
    sys.exit()

stages = [
    "Waiting",
    "Loading Binary Map",
    "Validating Characters",
    "Reading Source",
    "Converting Lines",
    "Exporting EEPROM",
    "Finished"
]

current_stage = 0

def next_stage():
    global current_stage
    stage = stages[current_stage]
    log(f"[{stage}]...", "warn")
    current_stage += 1
    time.sleep(random.random() * 0.1) # Reduced sleep for faster execution

# --- Color Mapping and Regex ---
# 6 bits: [R1 G1 B1] [R2 G2 B2]
# R1/G1/B1 = Light RGB, R2/G2/B2 = Dark RGB
COLOR_MAP = {
    # Basic colors (example values - adjust based on your hardware)
    "black":   "000000",
    "white":   "111111",
    "gray":    "111000",
    "red":     "100100",
    "green":   "010010",
    "blue":    "001001",
    "yellow":  "110110",
    "magenta": "101101",
    "cyan":    "011011",
    
    # Brighter variations (example)
    "bright_red":   "100000",
    "bright_green": "010000",
    "bright_blue":  "001000",
    
    # Darker variations (example)
    "dark_red":     "000100",
    "dark_green":   "000010",
    "dark_blue":    "000001",
}
# Default color to use if no tag or unknown color
DEFAULT_COLOR_BITS = COLOR_MAP["black"] 
# Regex to find the color tag: //(color_name) or //(color_name -mode) at the end of a line
# Captures: 1=color_name, 2=optional_mode (e.g., " -f" or " -t")
COLOR_TAG_REGEX = re.compile(r'//\((\w+)(\s+-[ft])?\)$')


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--text-only", action="store_true", help="Ignore all colour tags")
# Removed the -o/--output argument
args = parser.parse_args()

next_stage()  # Waiting
next_stage()  # Loading Binary Map

# load 7-bit char map
try:
    with open("BinaryChars.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    error_msg("Failed to load BinaryChars.json")

CharToBin = data.get("CharToBin", {})

next_stage()  # Validating Characters

# validate characters
for ch, bits in CharToBin.items():
    if not all(c in "01" for c in bits):
        error_msg(f"BinaryChars.json invalid bits for {ch!r}")

    if len(bits) > 7:
        error_msg(f"Binary for {ch!r} too long ({len(bits)} > 7)")

    CharToBin[ch] = bits.rjust(7, "0")

BLANK = CharToBin.get(" ")
if not BLANK:
    error_msg("BinaryChars.json missing space char")

checking = True
while checking:
    check = input("confirm: use lines.txt as source? y/n\n")
    if check.upper() == "N":
        log("please import your design to lines.txt\n", "error")
        sys.exit()
    elif check.upper() == "Y":
        log("confirmed.\n")
        checking = False
    else:
        log("invalid choice.\n", "warn")

next_stage()  # Reading Source

try:
    with open("lines.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
except Exception:
    error_msg("Could not read lines.txt")

next_stage()  # Converting Lines

converted = []

# --- Helper function for color-mode logic ---
def should_apply_color(mode, is_padding, char):
    """
    Determines if color should be applied based on mode, padding status, and character type.
    """
    
    if mode == '-f':
        # Mode //(color -f): Whole line (including padding)
        return True
    
    if mode == '-t':
        # Mode //(color -t): Text and internal spaces, but NOT padding spaces
        return not is_padding
        
    # Default mode: //(color)
    # Only color actual non-space characters
    return not is_padding and (char != ' ')
# --- End Helper function ---


for line_num, line in enumerate(lines, start=1):
    original_line = line.rstrip()
    
    # 1. Extract the color tag and mode
    color_bits = DEFAULT_COLOR_BITS
    color_mode = 'default' # 'default', '-f', or '-t'
    
    match = COLOR_TAG_REGEX.search(original_line)
    
    if match:
        # Get the color name and optional mode from the captured groups
        color_name = match.group(1).lower()
        optional_mode = match.group(2)
        
        # Determine the mode
        if optional_mode:
            color_mode = optional_mode.strip()

        # Remove the tag from the line content for character conversion
        line = original_line[:match.start()].rstrip()
        
        if color_name in COLOR_MAP:
            color_bits = COLOR_MAP[color_name]
        else:
            log(f"Line {line_num}: Unknown color {color_name!r}. Using default 'black'.", "warn")
            
    else:
        # If no tag is found, process the line and remove any trailing comments
        line = re.sub(r'//\(.+\)$', '', original_line).rstrip()


    # 2. Convert characters to binary strings
    char_list = []
    text_chars = list(line) 
    
    # Check for line length constraint
    if len(text_chars) > 16:
        log(f"Line {line_num}: Line is too long ({len(text_chars)} > 16). It will be truncated.", "warn")
        text_chars = text_chars[:16]


    # Process actual text characters (up to 16)
    for ch in text_chars:
        if ch not in CharToBin:
            error_msg(f"Unknown char {ch!r} in line {line_num}")
        
        char_bits = CharToBin[ch]
        
        # Check if the line's color should be applied to this character
        if args.text_only or should_apply_color(color_mode, is_padding=False, char=ch):
            # Apply the line color
            final_color_bits = color_bits
        else:
            # Use the default black color (or whatever DEFAULT_COLOR_BITS is set to)
            final_color_bits = DEFAULT_COLOR_BITS

        # Final word format: [000][R1G1B1R2G2B2][C7 C6 C5 C4 C3 C2 C1] (16 bits total)
        final_word = "000" + final_color_bits + char_bits
        char_list.append(final_word)


    # 3. Pad the line with spaces (BLANKs) up to 16 characters
    padding_needed = 16 - len(char_list)
    
    # Determine the color for the padding blank based on the mode
    if args.text_only or should_apply_color(color_mode, is_padding=True, char=' '):
        padding_color_bits = color_bits
    else:
        padding_color_bits = DEFAULT_COLOR_BITS
    
    # Create the BLANK_WORD for padding
    BLANK_PADDING_WORD = "000" + padding_color_bits + BLANK

    # Add the necessary padding
    for _ in range(padding_needed):
        char_list.append(BLANK_PADDING_WORD)

    
    # Extend the main converted list with the 16 characters for this line
    converted.extend(char_list)

# 5. Pad the rest of the EEPROM (if needed)
# Ensure the final output is 16*16 (256) 16-bit words
# A standard blank space character with default color
BLANK_WORD = "000" + DEFAULT_COLOR_BITS + BLANK 

while len(converted) < 16*16:
    converted.append(BLANK_WORD)

next_stage()  # Exporting EEPROM

# --- LOGIC FOR INTERACTIVE FILENAME INPUT WITH OVERWRITE PROTECTION ---

def determine_default_save_file():
    """Finds the first non-existent numbered save file (e.g., save1.txt, save2.txt)."""
    i = 1
    if os.path.exists(f"save{i}.txt"):
        return f"save{i}.txt"

# Determine the suggested default filename (guaranteed not to exist yet)
default_filename = determine_default_save_file()

# Get interactive input from the user
while True:
    print("\n--- Output File Selection ---")
    print("To save as a numbered file (e.g., save1.txt, save2.txt), enter a number.")
    print("To save as the default EEPROM file, enter 'EEPROM'.")
    output_choice = input(f"Enter save name or number (default: {default_filename}): ").strip()
    
    
    # 1. Determine the target filename
    if not output_choice:
        # Use the calculated default (guaranteed not to exist)
        output_filename = default_filename
    
    # 2. Check for the explicit EEPROM option
    elif output_choice.upper() == "EEPROM":
        output_filename = "eeprom.txt"
        
    # 3. Check for numbered input
    elif output_choice.isdigit():
        output_filename = f"save{output_choice}.txt"
    
    # 4. Use the input as a custom filename
    else:
        # Ensure it ends with .txt if it's a custom name
        if not output_choice.lower().endswith('.txt'):
            output_filename = output_choice + '.txt'
        else:
            output_filename = output_choice
            
    
    # 5. Check for overwrite condition and confirm
    if os.path.exists(output_filename):
        if output_filename.lower() == "eeprom.txt":
            # Special case for eeprom.txt which is often a temporary file
            log("Warning: eeprom.txt already exists and will be overwritten.", "warn")
            break
            
        # Ask for confirmation if an existing numbered/custom save file is being overwritten
        confirm = input(Fore.YELLOW + f"Are you sure you want to over-write {output_filename}? (y/n): " + Fore.RESET)
        if confirm.lower() == 'y':
            log(f"Overwriting {output_filename} confirmed.", "warn")
            break
        else:
            log("Overwrite canceled. Please choose a different file name.", "warn")
            # Loop back to ask for input again
            continue
    else:
        # File does not exist, safe to proceed
        break

# --- END LOGIC FOR INTERACTIVE FILENAME INPUT WITH OVERWRITE PROTECTION ---

try:
    with open(output_filename, "w", encoding="utf-8") as f:
        # Each item is now a 16-bit binary string
        for item in converted:
            f.write(item + "\n")
except Exception:
    error_msg(f"Failed to write {output_filename}")

next_stage()  # Finished

log(f"Converted. output: {output_filename}", "warn")