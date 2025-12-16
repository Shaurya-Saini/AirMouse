# Air Mouse: Dual-Mode Wireless Human-Computer Interface

<div style="text-align:center;">
  <img
    src="Working%20Prototype/Glove%20image.jpg"
    alt="Prototype"
    title="AirMouse Prototype"
    width="500"
  />
</div>



## Overview  
The **Air Mouse** is a wireless, dual-mode input device that enables **cursor control, left/right clicks, scrolling, zooming, volume control, and tab/application switching** through motion tracking and hand gesture recognition. It combines embedded sensor data and real-time computer vision for seamless human-computer interaction.

The system operates in two modes:

- **Normal Mode:**  
  Utilizes an **ESP32 microcontroller** connected to an **MPU6050 IMU** and **flex sensors**. The ESP32 processes orientation (pitch, roll, yaw) and finger bend data to control the mouse pointer and simulate mouse clicks. All data is transmitted to the host computer via **Bluetooth Low Energy (BLE)** for low-latency wireless control.

- **Gesture Mode:**  
  Triggered by a physical button, this mode launches a **Python-based computer vision pipeline** using **OpenCV** and **MediaPipe**. A webcam captures hand landmarks, and gestures are mapped to specific actions like zoom in/out, scroll up/down, and switch tabs or applications. On releasing the button, the system returns to Normal Mode.

The Air Mouse is ideal for a wide range of applications including **gaming**, **presentations**, **media control**, **AR/VR interactions**, and **accessible computing environments** where touchless input is essential.

---

## Key Features

- **Dual-Mode Operation:**
  - *Normal Mode:* Hand movements control the mouse pointer via the MPU6050; finger bends via flex sensors simulate left/right clicks.
  - *Gesture Mode:* On button press, switches to OpenCV + MediaPipe-based gesture recognition for scroll, zoom, and tab actions.

- **Wireless Communication:**
  - Uses **Bluetooth Low Energy (BLE)** via the ESP32 to connect to the host computer.

- **Sensors Used:**
  - **MPU6050** (gyroscope + accelerometer)
  - **Flex sensors** for finger movement detection

- **Computer Vision Integration:**
  - **MediaPipe** for real-time hand tracking
  - **OpenCV** for gesture analysis and command execution

- **Applications:**
  - Touch-free navigation
  - Presentation control
  - Accessibility tool for users with limited mobility

---

## Files and Folders

- `Computer_Vision/Vir_Env`: `HandTrackingModule.py` and `gesture_logic.py` for gesture detection using OpenCV and MediaPipe and `pyconnect.py` to recieve signals for the esp32 to switch between modes
- `Electronics/`: Arduino code for reading and processing sensors and sending data via BLE in `esp32.ino` and `Schematic Air-Mouse.pdf` with the schematic diagram of the circuit.
- `Working Prototype/`: Includes photos and working videos for the working prototype
- `README.md`: Project documentation (this file).

---

## About  
This project combines embedded systems and computer vision to provide a novel human-computer interface. The dual-mode Air Mouse is ideal for futuristic interaction models, accessibility use cases, and creative tech demos.

---

## Resources
- [MediaPipe Documentation](https://google.github.io/mediapipe/)
- [OpenCV Python](https://docs.opencv.org/)
- [Arduino ESP32 Core](https://github.com/espressif/arduino-esp32)
