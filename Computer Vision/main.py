import asyncio
from bleak import BleakClient
# import pyautogui

ESP32_BLE_ADDRESS = "f0:24:f9:5b:41:8a"  # Replace with your ESP32 MAC address
CHARACTERISTIC_UUID = "00002a56-0000-1000-8000-00805f9b34fb"

gesture_mode = False
gesture_task = None

async def handle_gesture():
    global gesture_mode
    while gesture_mode:
        # Add MediaPipe-based gesture recognition here
        print("Processing gestures...")  
        await asyncio.sleep(0.1)

async def notification_handler(sender, data):
    global gesture_mode, gesture_task
    message = data.decode("utf-8").strip()
    
    if message == "Gesture Mode ON":
        print("Switching to Gesture Mode...")
        gesture_mode = True
        if gesture_task is None or gesture_task.done():
            gesture_task = asyncio.create_task(handle_gesture())

    elif message == "Gesture Mode OFF":
        print("Switching to Air Mouse Mode...")
        gesture_mode = False
        if gesture_task:
            gesture_task.cancel()
            gesture_task = None

async def main():
    while True:
        try:
            async with BleakClient(ESP32_BLE_ADDRESS) as client:
                print("Connected to ESP32 BLE Device")
                await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

                try:
                    while True:
                        await asyncio.sleep(1)  # Keep listening for BLE notifications
                except asyncio.CancelledError:
                    break

        except Exception as e:
            print(f"BLE Connection failed: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)  # Retry after a delay

if __name__ == "__main__":
    asyncio.run(main())
