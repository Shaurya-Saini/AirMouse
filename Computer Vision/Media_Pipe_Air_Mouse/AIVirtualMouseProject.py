import cv2
import numpy as np
import HandTrackingModule as htm
import time
import pyautogui

# ========== Config ==========
wCam, hCam = 640, 480
frameR = 100
prevYScroll = 0
pTime = 0

# ========== Init ==========
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(maxHands=1)

# ========== Loop ==========
while True:
    success, img = cap.read()
    if not success:
        print("❌ Failed to grab frame.")
        break

    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    if lmList:
        x1, y1 = lmList[8][1:]   # Index tip
        x2, y2 = lmList[12][1:]  # Middle tip
        fingers = detector.fingersUp()

        # Draw region
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (0, 255, 0), 2)

        # ========== Scroll Gesture ==========
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            yScroll = (y1 + y2) // 2
            if prevYScroll != 0:
                diff = yScroll - prevYScroll
                if abs(diff) > 15:
                    if diff > 0:
                        pyautogui.scroll(-50)
                        print("📜 Scrolling Down")
                    else:
                        pyautogui.scroll(50)
                        print("📜 Scrolling Up")
            prevYScroll = yScroll
        else:
            prevYScroll = 0

        # ========== Volume Control ==========
        if fingers == [1, 1, 1, 1, 1]:  # Hand open
            pyautogui.press("volumeup")
            print("🔊 Volume Up")

        elif fingers == [0, 0, 0, 0, 0]:  # Fist
            pyautogui.press("volumedown")
            print("🔉 Volume Down")

    # ========== FPS ==========
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # ========== Show ==========
    cv2.imshow("Gesture Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ========== Cleanup ==========
cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)
