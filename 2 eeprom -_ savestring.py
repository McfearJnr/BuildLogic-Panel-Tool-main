import json
import time
import sys
import os
import random
import clipboard as clp
import datetime
try:
    from colorama import Fore
except:
    class _Fake:
        RED = ""
        BLUE = ""
        YELLOW = ""
        RESET = ""
    Fore = _Fake()

def log(content, t):
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

# --- NEW: Get number of saves ---
MAX_SAVES = 10
while True:
    log(f"How many save files (1 to {MAX_SAVES}) will you be including in the EEPROM?:", "")
    try:
        num_saves = int(input().strip())
        if 1 <= num_saves <= MAX_SAVES:
            break
        else:
            log(f"Please enter a number between 1 and {MAX_SAVES}.", "error")
    except ValueError:
        log("Invalid input. Please enter a whole number.", "error")

# --- MODIFIED: Dynamically generate required assets list ---
required_assets = []
for i in range(1, num_saves + 1):
    required_assets.append(f"save{i}.txt")
required_assets.append("BinaryChars.json")

# --- File Verification Loop ---
count = 0
for asset in required_assets:
    count += 1
    if os.path.exists(asset):
        log(f"Verifying file ({count}/{len(required_assets)})", "warn")
    else:
        error_msg(f"Missing or corrupted required file: {asset}")
    time.sleep(random.random() * 0.1) # Reduced sleep for faster verification

log("Are you using a 16 bit eeprom? (y/n):", "")
type16 = input().lower() in ["yes", "y"]

# --- MODIFIED: Ask for boot file based on number of saves ---
save_options = ", ".join([f"save{i}.txt ({i-1})" for i in range(1, num_saves + 1)])
log(f"Please select the Boot File (File loaded on startup). Enter the number (0 to {num_saves-1}):\nOptions: {save_options}", "")
mode_input = input().strip()

valid_modes = [str(i) for i in range(num_saves)]
if mode_input not in valid_modes:
    error_msg(f"Input was not a valid save index (0 to {num_saves-1}), unexpected.")

mode = int(mode_input) # mode is the 0-indexed boot save number

log("Encoding eeprom file, please do not exit the program.", "warn")

stages = [
    "Waiting",
    "Fetching Files",
    "Converting Input",
    "Encoding EEPROM",
    "Verifying Output",
    "Finished"
]

current_stage = 0

def next_stage():
    global current_stage
    stage = stages[current_stage]
    log(f"[{stage}]...", "")
    current_stage += 1
    time.sleep(random.random() * 0.2) # Reduced sleep

def import_files():
    save_files = []
    for i in range(1, num_saves + 1):
        filename = f"save{i}.txt"
        log(f"Importing save file: {filename}...", "warn")
        with open(filename, "r", encoding="utf-8") as f:
            save_files.append(f.read().split("\n"))

    log("Importing binary chars...", "warn")
    with open("BinaryChars.json", "r", encoding="utf-8") as f:
        Bin = json.load(f)["CharToBin"]

    return save_files, Bin

next_stage()  # Waiting
next_stage()  # Fetching Files
save_files, Bin = import_files()

next_stage()  # Converting Input

header = "#dHCAgA/" if type16 else "XDCAgA/"
Save = header

digits = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@$%?&<()"

def FlipByte(n):
    fmt = "{:016b}" if type16 else "{:08b}"
    return int(fmt.format(n)[::-1], 2)

def Base71(n):
    if n == 0:
        return "00" + ("0" if type16 else "")
    out = ""
    while n > 0:
        n, r = divmod(n, 71)
        out = digits[r] + out
    return out.rjust(2 + type16, "0")

def calc(token):
    token = token.strip()
    # ... (Keep the rest of your calc function unchanged)
    if all(c in "01" for c in token):
        return int(token, 2)

    if token.isdigit():
        return int(token)

    if "+" in token:
        total = 0
        for part in token.split("+"):
            part = part.strip()

            if len(part) == 1 and not part.isdigit():
                if part not in Bin:
                    error_msg("Character not in set")
                total += int(Bin[part], 2)

            elif part.lower().startswith("b"):
                bit = int(part[1:])
                if bit > (16 if type16 else 8):
                    error_msg("Bit too high")
                total += (1 << (bit - 1))

            elif part.lower().startswith("h"):
                total += int(part[1:], 16)

            else:
                if all(c in "01" for c in part):
                    total += int(part, 2)
                else:
                    total += int(part)

        return total

    if token.lower().startswith("h"):
        return int(token[1:], 16)

    if len(token) == 1 and token in Bin:
        return int(Bin[token], 2)

    error_msg(f"Unable to parse token: {token}")

address = 0

def encode_file(lines, save_index):
    global Save, address
    for line in lines:
        if not line or line.startswith("#"):
            continue

        try:
            value = calc(line)
        except Exception as e:
            error_msg(f"Error processing line in save{save_index+1}.txt: '{line.strip()}'. Details: {e}")

        max_val = (1 << (16 if type16 else 8)) - 1
        if value > max_val:
            error_msg(f"Value {value} is too high for the selected EEPROM type (max {max_val}).")

        Save += Base71(FlipByte(address))
        Save += Base71(FlipByte(value))

        address += 1

next_stage()  # Encoding EEPROM

# --- MODIFIED: Loop through all save files for encoding ---
for i, file_lines in enumerate(save_files):
    log(f"Encoding save{i+1}.txt...", "warn")
    encode_file(file_lines, i)
    log(f"Done encoding save{i+1}.txt.", "warn")

# The boot file mode is stored in the EEPROM at a dedicated address (255 here).
# The 'mode' variable now holds the 0-indexed save file to be booted.
mode_address = 255
Save += Base71(FlipByte(mode_address))
Save += Base71(FlipByte(mode))

Save += "=1"

clp.copy(Save)

next_stage()  # Verifying
next_stage()  # Finished

log("Encoding complete. Output copied to clipboard.", "")
log(Save, "")