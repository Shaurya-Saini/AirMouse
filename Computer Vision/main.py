import time
import threading
from pynput import mouse
import sys # For flushing print output
import platform

# --- Configuration ---
# Detection parameters for the middle click sequence
MIDDLE_CLICK_THRESHOLD = 0.15 # Max seconds between clicks (tune this!) must be > CLICK_SIGNAL_DELAY on ESP32
MIDDLE_CLICK_COUNT_TARGET = 3 # Number of rapid clicks to detect

# --- Global State ---
is_cv_mode_active = False # Start in Air Mouse mode (Python perspective)
gesture_processing_thread = None # Thread object for CV task
cv_stop_event = threading.Event() # Event to signal CV thread to stop

# --- Variables for Click Detection ---
last_middle_click_time = 0
middle_click_count = 0

# --- Core Functions ---

def handle_gesture_recognition():
    """Placeholder for MediaPipe gesture recognition loop."""
    global is_cv_mode_active # Access global state if needed inside CV logic
    print("\n--- GESTURE RECOGNITION THREAD [STARTED] ---", flush=True)
    try:
        # --- === Your MediaPipe Setup Code Goes Here === ---
        print("Initializing MediaPipe/Camera (placeholder)...", flush=True)
        # import cv2
        # import mediapipe as mp
        # mp_hands = mp.solutions.hands
        # hands = mp_hands.Hands(...) # Your settings
        # cap = cv2.VideoCapture(0)
        # if not cap.isOpened(): raise IOError("Cannot open webcam")
        # ----------------------------------------------------

        while not cv_stop_event.is_set(): # Loop until stop event is set
            # --- === Your MediaPipe Processing Loop Goes Here === ---
            print("Processing gestures... (placeholder loop)", flush=True)
            # Example:
            # success, image = cap.read()
            # if not success: continue
            # results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            # if results.multi_hand_landmarks:
            #     print("Hand Detected!", flush=True)
            #     # --- Trigger actions based on gestures ---
            #     # e.g., if gesture == 'scroll_up': pyautogui.scroll(10)
            # else:
            #      print("No hand detected.", flush=True)

            # cv2.imshow(...)
            # if cv2.waitKey(5) & 0xFF == 27: break # Allow exit via ESC

            # ------------------------------------------------------
            time.sleep(0.1) # Adjust sleep based on actual processing time

    except Exception as e:
        print(f"###### ERROR in gesture recognition loop: {e} ######", flush=True)
    finally:
        # --- === Your MediaPipe Cleanup Code Goes Here === ---
        print("Cleaning up MediaPipe/Camera (placeholder)...", flush=True)
        # Example:
        # if 'cap' in locals() and cap.isOpened(): cap.release()
        # if 'cv2' in sys.modules: cv2.destroyAllWindows()
        # --------------------------------------------------
        print("--- GESTURE RECOGNITION THREAD [EXITED] ---", flush=True)


def start_cv_processing():
    """Starts the gesture recognition thread if not already running."""
    global gesture_processing_thread, cv_stop_event
    if gesture_processing_thread is None or not gesture_processing_thread.is_alive():
        cv_stop_event.clear() # Ensure stop event is cleared
        gesture_processing_thread = threading.Thread(target=handle_gesture_recognition, daemon=True)
        gesture_processing_thread.start()
    else:
        print("CV Processing thread already running.", flush=True)

def stop_cv_processing():
    """Signals the gesture recognition thread to stop and waits for it."""
    global gesture_processing_thread, cv_stop_event
    if gesture_processing_thread and gesture_processing_thread.is_alive():
        print("Signalling CV Processing thread to stop...", flush=True)
        cv_stop_event.set() # Signal the thread to stop
        gesture_processing_thread.join(timeout=2.0) # Wait for thread to finish
        if gesture_processing_thread.is_alive():
            print("Warning: CV processing thread did not stop cleanly.", flush=True)
        else:
             print("CV Processing thread stopped.", flush=True)
        gesture_processing_thread = None
    else:
         print("CV Processing thread not running or already stopped.", flush=True)


def on_click(x, y, button, pressed):
    """Callback executed when a mouse button is clicked."""
    global is_cv_mode_active, last_middle_click_time, middle_click_count

    # We only care about the press event for detection
    if button == mouse.Button.middle and pressed:
        current_time = time.time()
        # Check if this click is close enough to the previous one
        if current_time - last_middle_click_time < MIDDLE_CLICK_THRESHOLD:
            middle_click_count += 1
        else:
            # Reset counter if the click is too far apart in time
            middle_click_count = 1

        last_middle_click_time = current_time # Update time of the last middle click

        # Check if we reached the target number of clicks
        if middle_click_count >= MIDDLE_CLICK_COUNT_TARGET:
            print(f"\n*** Detected {MIDDLE_CLICK_COUNT_TARGET} rapid middle clicks! ***", flush=True)

            # Toggle the mode state
            is_cv_mode_active = not is_cv_mode_active

            if is_cv_mode_active:
                print("🟢 Switching to GESTURE MODE (Python Side)", flush=True)
                # Start the CV processing in its thread
                start_cv_processing()
            else:
                print("🔵 Switching to AIR MOUSE MODE (Python Side)", flush=True)
                # Stop the CV processing thread
                stop_cv_processing()

            # IMPORTANT: Reset click count immediately after detection
            middle_click_count = 0
            last_middle_click_time = 0 # Also reset time to avoid false trigger on next single click


def start_mouse_listener():
    """Starts the pynput mouse listener."""
    print("Starting mouse listener...", flush=True)
    # Setup the listener in the main thread or a dedicated thread
    # Running in main thread here, as main loop below just waits
    try:
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
    except Exception as e:
         # Permissions errors often occur here on Linux/macOS
         print(f"\n###### ERROR starting mouse listener: {e} ######", flush=True)
         print("###### Ensure you have necessary permissions (e.g., macOS Accessibility, Linux input group/sudo). ######", flush=True)
         sys.exit(1) # Exit if listener fails

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Hybrid Mouse/Gesture Client Starting (Click Detection Mode) ---", flush=True)
    print(f"Platform: {platform.system()}", flush=True)
    print(f"Listening for {MIDDLE_CLICK_COUNT_TARGET} middle clicks within {MIDDLE_CLICK_THRESHOLD*1000:.0f}ms intervals.", flush=True)
    print("Press the button on the ESP32 to switch modes.", flush=True)
    print("--------------------------------------------------", flush=True)

    # Start the mouse listener. This blocks until the listener stops (e.g., error or manual stop).
    # If you need other main thread tasks, run the listener in its own thread.
    listener_thread = threading.Thread(target=start_mouse_listener, daemon=True)
    listener_thread.start()

    # Keep the main thread alive (alternative to listener.join() in main thread)
    try:
        while listener_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Program terminated by user ---", flush=True)
    finally:
        print("--- Stopping CV thread (if running) ---")
        stop_cv_processing() # Ensure CV thread is stopped on exit
        print("--- Client Stopped ---", flush=True)