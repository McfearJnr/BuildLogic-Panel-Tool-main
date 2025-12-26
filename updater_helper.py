# updater_helper.py

import os
import sys
import time
import subprocess
import shutil

MAIN_EXE_NAME = "BuildLogic Panel Suite.exe" 
TEMP_NEW_EXE_NAME = "LatestBuild.exe" 
HELPER_SCRIPT_NAME = "updater_helper.py"
# ---------------------------------------------------

def update_and_restart():
    """
    Main function to wait for the old app to close, replace it, and restart.
    """

    # 1. Define paths based on the location of this script
    # This script will be run from the same directory as the main EXE
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    current_exe_path = os.path.join(app_dir, MAIN_EXE_NAME)
    temp_new_exe_path = os.path.join(app_dir, TEMP_NEW_EXE_NAME)
    helper_script_path = os.path.join(app_dir, HELPER_SCRIPT_NAME)

    print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] Starting update process...")
    print(f"App directory: {app_dir}")

    # 2. Wait for the main executable file lock to be released
    wait_time = 0
    max_wait = 10 # seconds
    while wait_time < max_wait:
        try:
            # Try to rename the file. If successful, the file is NOT locked.
            os.rename(current_exe_path, current_exe_path + '.temp_rename')
            os.rename(current_exe_path + '.temp_rename', current_exe_path)
            break
        except OSError:
            # File is still locked by the main application process. Wait.
            time.sleep(1)
            wait_time += 1
            print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] Waiting for main app to exit... ({wait_time}s)")
    
    if wait_time >= max_wait:
        print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] Error: Main app file lock not released after {max_wait}s. Aborting update.")
        return

    # 3. Perform the replacement
    try:
        if os.path.exists(temp_new_exe_path):
            # Delete the old executable
            os.remove(current_exe_path)
            
            # Rename the new executable to the original name
            os.rename(temp_new_exe_path, current_exe_path)
            print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] Executable replaced successfully.")
            
            # 4. Clean up the helper script itself
            if os.path.exists(helper_script_path):
                 os.remove(helper_script_path)
                 print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] Cleaned up helper script.")
            
            # 5. Restart the application
            print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] Restarting application...")
            
            # --- FIX: DETACH PROCESS TO ALLOW CLEANUP ---
            if sys.platform == 'win32':
                # 0x00000008 is DETACHED_PROCESS on Windows.
                # close_fds=True ensures file handles aren't inherited.
                subprocess.Popen([current_exe_path], creationflags=0x00000008, close_fds=True)
            else:
                subprocess.Popen([current_exe_path], close_fds=True)
            # --------------------------------------------
            
        else:
            print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] Error: New executable file ...")

    except Exception as e:
        print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] FATAL ERROR during replacement: {e}")

if __name__ == "__main__":
    # Ensure this script is only run when explicitly called by the main app
    if len(sys.argv) > 1 and sys.argv[1] == "--update-trigger":
        update_and_restart()
    else:
        # Prevent accidental double-click execution of the helper script
        print(f"[{os.path.basename(HELPER_SCRIPT_NAME)}] This script is an internal helper and cannot be run directly.")
        time.sleep(3)