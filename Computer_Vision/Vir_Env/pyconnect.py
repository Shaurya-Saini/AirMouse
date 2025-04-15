import time
import threading
from pynput import mouse
import sys # For flushing print output
import platform

# --- Try importing the gesture logic ---
try:
    import gesture_logic
except ImportError:
    print("❌ Error: gesture_logic.py not found.")
    print("Ensure gesture_logic.py is in the same directory.")
    sys.exit(1)

# --- Configuration ---
MIDDLE_CLICK_THRESHOLD = 0.20 # Max seconds between clicks (tune this!)
MIDDLE_CLICK_COUNT_TARGET = 3 # Number of rapid clicks to detect

# --- Global State ---
is_cv_mode_active = False # Start in Air Mouse mode (Python perspective)
gesture_processing_thread = None # Thread object for CV task
cv_stop_event = threading.Event() # Event to signal CV thread to stop

# --- Variables for Click Detection ---
last_middle_click_time = 0
middle_click_count = 0

# --- Core Functions ---

def start_cv_processing():
    """Starts the gesture recognition thread if not already running."""
    global gesture_processing_thread, cv_stop_event
    if gesture_processing_thread is None or not gesture_processing_thread.is_alive():
        print("\n--- Starting GESTURE RECOGNITION Thread ---", flush=True)
        cv_stop_event.clear() # Ensure stop event is cleared before starting
        # Create and start the thread, running the function from gesture_logic.py
        gesture_processing_thread = threading.Thread(
            target=gesture_logic.run_gesture_control,
            args=(cv_stop_event,), # Pass the stop event to the function
            daemon=True # Allows main program to exit even if this thread is stuck
        )
        gesture_processing_thread.start()
    else:
        print("Gesture processing thread already running.", flush=True)

def stop_cv_processing():
    """Signals the gesture recognition thread to stop and waits for it."""
    global gesture_processing_thread, cv_stop_event
    if gesture_processing_thread and gesture_processing_thread.is_alive():
        print("Signalling Gesture Processing thread to stop...", flush=True)
        cv_stop_event.set() # <<< Signal the loop in gesture_logic.py to stop
        gesture_processing_thread.join(timeout=3.0) # Wait max 3 seconds for thread to finish
        if gesture_processing_thread.is_alive():
            print("⚠️ Warning: Gesture processing thread did not stop cleanly after timeout.", flush=True)
            # You might consider more forceful termination if needed, but it's risky
        else:
             print("Gesture Processing thread stopped.", flush=True)
        gesture_processing_thread = None # Clear the thread object
        cv_stop_event.clear() # Clear event for next time (optional, handled in start)
    else:
         print("Gesture Processing thread not running or already stopped.", flush=True)


def on_click(x, y, button, pressed):
    """Callback executed when a mouse button is clicked."""
    global is_cv_mode_active, last_middle_click_time, middle_click_count

    # We only care about the press event for detection
    if button == mouse.Button.middle and pressed:
        current_time = time.time()
        time_diff = current_time - last_middle_click_time

        # Check if this click is close enough to the previous one
        if time_diff < MIDDLE_CLICK_THRESHOLD:
            middle_click_count += 1
            print(f"Middle click #{middle_click_count} (Interval: {time_diff:.3f}s)", flush=True) # Debug
        else:
            # Reset counter if the click is too far apart in time
            # print(f"Middle click reset (Interval too long: {time_diff:.3f}s)", flush=True) # Debug
            middle_click_count = 1 # This click is the start of a new potential sequence

        last_middle_click_time = current_time # Update time of the last middle click

        # Check if we reached the target number of clicks
        if middle_click_count >= MIDDLE_CLICK_COUNT_TARGET:
            print(f"\n*** Detected {MIDDLE_CLICK_COUNT_TARGET} rapid middle clicks! ***", flush=True)

            # Toggle the mode state
            is_cv_mode_active = not is_cv_mode_active

            if is_cv_mode_active:
                print("🟢 Switching to GESTURE MODE", flush=True)
                # Stop any previous instance cleanly before starting a new one (important!)
                stop_cv_processing()
                time.sleep(0.2) # Small delay to ensure resources are released
                # Start the CV processing in its thread
                start_cv_processing()
            else:
                print("🔵 Switching back to default mouse mode (or stopping gestures)", flush=True)
                # Stop the CV processing thread
                stop_cv_processing()

            # IMPORTANT: Reset click count and time immediately after detection and mode switch
            middle_click_count = 0
            last_middle_click_time = 0


def start_mouse_listener():
    """Starts the pynput mouse listener."""
    print("Starting mouse listener...", flush=True)
    # Setup the listener in the main thread or a dedicated thread
    # Running in main thread here, as main loop below just waits
    try:
        # Use 'with' statement for proper cleanup
        with mouse.Listener(on_click=on_click) as listener:
            listener.join() # Blocks until the listener stops
    except Exception as e:
         # Permissions errors often occur here on Linux/macOS
         print(f"\n###### ERROR starting mouse listener: {e} ######", flush=True)
         if "failed to acquire" in str(e).lower() or "permission" in str(e).lower():
              print("###### This often means another program is capturing mouse events exclusively,")
              print("###### or you lack permissions (e.g., macOS Accessibility, Linux input group/sudo).")
         else:
              import traceback
              traceback.print_exc()
         print("###### Exiting due to listener error. ######", flush=True)
         # Attempt to stop CV thread if it somehow started before listener error
         stop_cv_processing()
         sys.exit(1) # Exit if listener fails

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Hybrid Mouse/Gesture Client Starting ---", flush=True)
    print(f"Platform: {platform.system()}", flush=True)
    print(f"Listening for {MIDDLE_CLICK_COUNT_TARGET} middle clicks within {MIDDLE_CLICK_THRESHOLD*1000:.0f}ms intervals to toggle Gesture Mode.", flush=True)
    print("Initially in default mouse mode.")
    print("Press Ctrl+C in the console to exit.", flush=True)
    print("--------------------------------------------------", flush=True)

    # Run the mouse listener in the main thread. It will block here.
    # The gesture logic runs in a separate thread when activated.
    try:
        start_mouse_listener()
    except KeyboardInterrupt:
        print("\n--- Ctrl+C detected. Exiting program. ---", flush=True)
    except Exception as e:
        print(f"\n--- An unexpected error occurred in the main thread: {e} ---", flush=True)
    finally:
        print("--- Main thread initiating cleanup. ---", flush=True)
        # Ensure the CV thread is stopped on exit, regardless of how we got here
        stop_cv_processing()
        print("--- Client Stopped ---", flush=True)
