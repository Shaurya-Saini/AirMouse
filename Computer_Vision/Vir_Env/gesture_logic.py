import cv2
import numpy as np
try:
    import HandTrackingModule as htm
except ImportError:
    print("❌ Error: HandTrackingModule.py not found.")
    print("Ensure HandTrackingModule.py is in the same directory.")
    exit()
import time
import pyautogui
import threading # Needed for stop_event check

def run_gesture_control(stop_event):
    """
    Runs the hand gesture recognition loop.

    Args:
        stop_event (threading.Event): An event that signals when this function should stop.
    """
    print("--- GESTURE CONTROL: Initializing... ---", flush=True)

    # ========== Config ==========
    wCam, hCam = 640, 480
    frameR = 100  # Frame Reduction for cursor movement zone
    smoothening = 5 # Factor to smoothen mouse movement (adjust as needed)
    # prevYScroll = 0 # No longer needed for scroll gesture itself
    prevYVol = 0 # Previous vertical position for volume control
    pTime = 0
    plocX, plocY = 0, 0 # Previous location (for potential mouse move)
    clocX, clocY = 0, 0 # Current location (for potential mouse move)

    # ========== Init ==========
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Cannot open webcam.")
        return # Exit the function if camera fails

    cap.set(3, wCam)
    cap.set(4, hCam)
    try:
        detector = htm.handDetector(maxHands=1, detectionCon=0.75, trackCon=0.6) # Adjusted confidence
    except Exception as e:
        print(f"❌ Error initializing hand detector: {e}")
        cap.release()
        return

    print("--- GESTURE CONTROL: Camera and Detector Initialized ---", flush=True)
    screenW, screenH = pyautogui.size() # Get screen size for mapping

    try:
        # ========== Loop ==========
        while not stop_event.is_set(): # Loop until the stop_event is set
            success, img = cap.read()
            if not success:
                print("⚠️ Failed to grab frame. Trying again...", flush=True)
                time.sleep(0.1) # Prevent tight loop on error
                continue

            # Find Hand
            img = detector.findHands(img)
            lmList, bbox = detector.findPosition(img, draw=False) # Don't draw default positions

            if lmList:
                # Get tip of index and middle fingers (needed for volume control)
                x1, y1 = lmList[8][1:]   # Index finger tip
                x2, y2 = lmList[12][1:]  # Middle finger tip

                # Check which fingers are up
                fingers = detector.fingersUp()
                # print(f"Fingers: {fingers}") # Debug print

                # Draw movement region
                cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)


                # ========== Volume Control (Index + Middle up + Vertical Movement) ==========
                if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                    # Calculate the average vertical position of the index and middle fingers
                    yVol = (y1 + y2) // 2
                    # Draw a circle for visual feedback on the control point
                    cv2.circle(img, ( (x1+x2)//2, yVol ), 10, (0, 255, 0), cv2.FILLED)

                    if prevYVol != 0:
                        diff = yVol - prevYVol
                        vol_action = None
                        vol_threshold = 15 # Sensitivity for volume change detection (adjust as needed)

                        if abs(diff) > vol_threshold:
                            if diff > 0: # Hand moved DOWN on screen
                                vol_action = "volumedown"
                                print("🔉 Volume Down", flush=True)
                            else: # Hand moved UP on screen
                                vol_action = "volumeup"
                                print("🔊 Volume Up", flush=True)

                            if vol_action:
                                pyautogui.press(vol_action)
                                pyautogui.press(vol_action)
                                pyautogui.press(vol_action)
                                time.sleep(0.15) # Add delay to prevent rapid repeats

                    prevYVol = yVol # Update previous position for next frame's comparison

                # ========== Scroll Up (All fingers up) ==========
                elif fingers == [1, 1, 1, 1, 1]:
                    pyautogui.scroll(80) # Positive value scrolls UP (adjust amount as needed)
                    print("📜 Scrolling Up", flush=True)
                    time.sleep(0.15) # Add delay to prevent rapid repeats
                    prevYVol = 0 # Reset volume tracking when scrolling

                # ========== Scroll Down (All fingers down / Fist) ==========
                elif fingers == [0, 0, 0, 0, 0]:
                    pyautogui.scroll(-80) # Negative value scrolls DOWN (adjust amount as needed)
                    print("📜 Scrolling Down", flush=True)
                    time.sleep(0.15) # Add delay to prevent rapid repeats
                    prevYVol = 0 # Reset volume tracking when scrolling

                # ========== CHANGED: Next Tab (Thumb + Index Finger Up Only) ==========
                elif fingers == [1, 1, 0, 0, 0]: # Condition changed here
                    pyautogui.hotkey('ctrl', 'tab')
                    print("📄 Next Tab", flush=True)
                    time.sleep(0.3) # Add longer delay for tab switching
                    prevYVol = 0 # Reset volume tracking

                # ========== CHANGED: Previous Tab (Thumb + Index + Pinky Finger Up Only) ==========
                elif fingers == [1, 1, 0, 0, 1]: # Condition changed here
                    pyautogui.hotkey('ctrl', 'shift', 'tab')
                    print("📄 Previous Tab", flush=True)
                    time.sleep(0.3) # Add longer delay for tab switching
                    prevYVol = 0 # Reset volume tracking

                # ========== Reset previous vertical position if not in Volume gesture ==========
                else:
                     prevYVol = 0 # Reset if not in Index+Middle finger up state or other specific gestures


                # ========== (No change below this point regarding gestures) ==========

            else: # No hand detected
                prevYVol = 0 # Reset if no hand is found


            # ========== FPS Calculation ==========
            cTime = time.time()
            fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
            pTime = cTime
            cv2.putText(img, f'FPS: {int(fps)}', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # ========== Show Image ==========
            cv2.imshow("Gesture Control Active", img)

            # Check for exit key ('q') or if stop event is set by the other thread
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print(" 'q' pressed in Gesture window, stopping.", flush=True)
                stop_event.set() # Signal the main thread (or itself) to stop
            elif key == 27: # ESC key
                 print(" ESC pressed in Gesture window, stopping.", flush=True)
                 stop_event.set()

            # Give the CPU a tiny break
            # time.sleep(0.01)


    except Exception as e:
        print(f"###### ERROR in gesture control loop: {e} ######", flush=True)
        import traceback
        traceback.print_exc() # Print detailed traceback
    finally:
        # ========== Cleanup ==========
        print("--- GESTURE CONTROL: Cleaning up... ---", flush=True)
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        # Need multiple waitKeys to ensure window closes on all OS sometimes
        for _ in range(4):
            cv2.waitKey(1)
        print("--- GESTURE CONTROL: Cleanup Complete ---", flush=True)

# Optional: Add a block to test this file standalone
if __name__ == "__main__":
    print("Running gesture_logic.py standalone test...")
    # Updated print statement for new tab gestures
    print("Gestures: Open Hand=Scroll Up, Fist=Scroll Down, Index+Middle+Move=Volume, Thumb+Index=Next Tab, Thumb+Index+Pinky=Prev Tab")
    print("Press 'q' or ESC in the OpenCV window to stop.")
    # Create a dummy stop event for standalone testing
    stop_event = threading.Event()
    try:
        # Run the gesture control function directly
        run_gesture_control(stop_event)
    except KeyboardInterrupt:
        print("\nStandalone test interrupted by Ctrl+C.")
        stop_event.set() # Signal the function to stop if running
    print("Standalone test finished.")