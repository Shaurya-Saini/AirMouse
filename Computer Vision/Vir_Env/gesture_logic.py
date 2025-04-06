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
    prevYScroll = 0
    pTime = 0
    plocX, plocY = 0, 0 # Previous location
    clocX, clocY = 0, 0 # Current location

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

            img = cv2.flip(img, 1) # Flip image horizontally for intuitive control

            # Find Hand
            img = detector.findHands(img)
            lmList, bbox = detector.findPosition(img, draw=False) # Don't draw default positions

            if lmList:
                # Get tip of index and middle fingers
                x1, y1 = lmList[8][1:]   # Index finger tip
                x2, y2 = lmList[12][1:]  # Middle finger tip

                # Check which fingers are up
                fingers = detector.fingersUp()
                # print(f"Fingers: {fingers}") # Debug print

                # Draw movement region
                cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

                # ========== Mode 1: Moving Mode (Only Index Finger up) ==========
                # For future mouse control, currently placeholder/unused in this specific request
                # if fingers[1] == 1 and fingers[0] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                #     # Convert Coordinates to screen resolution
                #     x_mapped = np.interp(x1, (frameR, wCam - frameR), (0, screenW))
                #     y_mapped = np.interp(y1, (frameR, hCam - frameR), (0, screenH))
                #
                #     # Smoothen Values
                #     clocX = plocX + (x_mapped - plocX) / smoothening
                #     clocY = plocY + (y_mapped - plocY) / smoothening
                #
                #     # Move Mouse (Uncomment to enable mouse movement)
                #     # pyautogui.moveTo(clocX, clocY)
                #     cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED) # Draw indicator
                #     plocX, plocY = clocX, clocY
                #     print("🖐️ Moving Mode (Index Finger)") # Keep print minimal
                #     prevYScroll = 0 # Reset scroll when moving

                # ========== Mode 2: Scrolling Mode (Index and Middle up) ==========
                if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                    # Check distance between fingers for click (optional, not used here)
                    length, img, lineInfo = detector.findDistance(8, 12, img)
                    # print(f"Scroll Mode - Dist: {length:.1f}", flush=True) # Debug

                    yScroll = (y1 + y2) // 2
                    if prevYScroll != 0:
                        diff = yScroll - prevYScroll
                        scroll_amount = 0
                        scroll_threshold = 10 # Sensitivity for scroll detection

                        if abs(diff) > scroll_threshold:
                            if diff > 0:
                                scroll_amount = -30 # Scroll Down (adjust units)
                                print("📜 Scrolling Down", flush=True)
                            else:
                                scroll_amount = 30  # Scroll Up (adjust units)
                                print("📜 Scrolling Up", flush=True)

                            if scroll_amount != 0:
                                pyautogui.scroll(scroll_amount)
                                # Add a small delay to prevent overly fast scrolling
                                time.sleep(0.03)

                    prevYScroll = yScroll # Update previous position for next frame's comparison

                else: # If not in scroll gesture, reset prevYScroll
                    prevYScroll = 0

                # ========== Mode 3: Volume Control ==========
                # Hand open (all fingers up) -> Volume Up
                if fingers == [1, 1, 1, 1, 1]:
                    pyautogui.press("volumeup")
                    print("🔊 Volume Up", flush=True)
                    time.sleep(0.2) # Add delay to prevent rapid repeats

                # Fist (all fingers down) -> Volume Down
                elif fingers == [0, 0, 0, 0, 0]:
                    pyautogui.press("volumedown")
                    print("🔉 Volume Down", flush=True)
                    time.sleep(0.2) # Add delay

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
            # time.sleep(0.01) # Can uncomment if CPU usage is too high


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
    print("Press Middle Mouse Button 3 times quickly to simulate toggle (won't work here).")
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
