#include <Wire.h>
#include <MPU6050.h>
#include <BleMouse.h>

#define BUTTON_PIN 5 // Toggle button for modes

// Flex sensor pins
#define FLEX_LEFT_PIN 34  // Left click flex sensor (offline golden)
#define FLEX_RIGHT_PIN 35 // Right click flex sensor (online black)

// --- Tuning Parameters ---
#define GYRO_SENSITIVITY 650  // Lower value = More sensitive mouse movement. Adjust as needed.
#define FLEX_LEFT_THRESHOLD 0   // Adjust based on your "golden" sensor's bent value for click
#define FLEX_RIGHT_THRESHOLD 4000 // Adjust based on your "black" sensor's bent value for click

// --- Timing Parameters ---
#define CLICK_SIGNAL_DELAY 40   // Milliseconds between signal clicks
#define BUTTON_DEBOUNCE_MS 4000  // Reduced debounce for better responsiveness (5000ms is very long)
#define AIRMOUSE_LOOP_DELAY 10  // Delay in airmouse loop (ms)

MPU6050 mpu;
BleMouse bleMouse("ESP32 Mouse", "ESP32", 100);

// --- State Variables ---
bool gestureMode = false; // false = Air Mouse Mode, true = CV Gesture Mode
unsigned long lastButtonPressTime = 0;
bool lastButtonState = LOW; // Assuming INPUT_PULLDOWN, so LOW is resting state

// Function to send the 3 middle clicks signal
void sendModeSwitchSignal() {
    if (!bleMouse.isConnected()) {
        Serial.println("BLE not connected, cannot send signal.");
        return;
    }
    Serial.println("Sending mode switch signal (3 middle clicks)...");
    bleMouse.click(MOUSE_MIDDLE);
    delay(CLICK_SIGNAL_DELAY);
    bleMouse.click(MOUSE_MIDDLE);
    delay(CLICK_SIGNAL_DELAY);
    bleMouse.click(MOUSE_MIDDLE);
    Serial.println("Signal sent.");
}

// Function for Air Mouse Mode operation
void airmouse_mode() {
    // Only proceed if in Air Mouse mode AND connected via BLE
    if (gestureMode || !bleMouse.isConnected()) {
        return; // Exit if not in correct mode or not connected
    }

    // Read MPU6050 data
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Calculate mouse movement based on gyro data
    // Mapping: Gyro X -> Mouse Y, Gyro Z (negated) -> Mouse X
    // Adjust GYRO_SENSITIVITY define above if movement is too fast/slow
    int mouseMoveX = -(gz / GYRO_SENSITIVITY);
    int mouseMoveY = gx / GYRO_SENSITIVITY;

    // Send mouse movement if there is any change
    if (mouseMoveX != 0 || mouseMoveY != 0) {
         // Serial.print("Moving Mouse X:"); Serial.print(mouseMoveX); // Uncomment for debugging
         // Serial.print(" Y:"); Serial.println(mouseMoveY);            // Uncomment for debugging
         bleMouse.move(mouseMoveX, mouseMoveY);
    }


    // Read Flex Sensor data
    int flexLeftValue = analogRead(FLEX_LEFT_PIN);
    int flexRightValue = analogRead(FLEX_RIGHT_PIN);
    Serial.print("Flex Left: "); Serial.print(flexLeftValue);       // Uncomment for debugging
    // Serial.print(" | Flex Right: "); Serial.println(flexRightValue); // Uncomment for debugging

    // Handle Left Click (adjust FLEX_LEFT_THRESHOLD define above)
    // Assuming lower value means bent/click for this sensor
    if (flexLeftValue == FLEX_LEFT_THRESHOLD) {
        Serial.println("Left Pressed"); // Uncomment for debugging
        bleMouse.press(MOUSE_LEFT);
    } else {
        bleMouse.release(MOUSE_LEFT);
    }

    // Handle Right Click (adjust FLEX_RIGHT_THRESHOLD define above)
    // Assuming higher value means bent/click for this sensor
    if (flexRightValue > FLEX_RIGHT_THRESHOLD) {
        // Serial.println("Right Pressed"); // Uncomment for debugging
        bleMouse.press(MOUSE_RIGHT);
    } else {
        bleMouse.release(MOUSE_RIGHT);
    }

    // Small delay to prevent overwhelming BLE and allow sensor updates
    delay(AIRMOUSE_LOOP_DELAY);
}

// Function to check the button state and toggle mode
void checkButton() {
    bool currentButtonState = digitalRead(BUTTON_PIN);
    unsigned long currentTime = millis();

    // Check for rising edge (button pressed) with debounce
    if (currentButtonState == HIGH && lastButtonState == LOW && (currentTime - lastButtonPressTime > BUTTON_DEBOUNCE_MS)) {
        lastButtonPressTime = currentTime;
        gestureMode = !gestureMode; // Toggle the mode

        if (gestureMode) {
            Serial.println(">>> Button Pressed: Switching to GESTURE Mode.");
            // Ensure mouse buttons are released when entering gesture mode
            if (bleMouse.isConnected()) {
                bleMouse.release(MOUSE_LEFT);
                bleMouse.release(MOUSE_RIGHT);
                // Optionally add MIDDLE, BACK, FORWARD releases if used elsewhere
            }
            // Send the signal *after* releasing buttons
            sendModeSwitchSignal();
        } else {
            Serial.println(">>> Button Pressed: Switching to AIR MOUSE Mode.");
            // Send the signal
            sendModeSwitchSignal();
            // Air mouse functionality will resume automatically in loop()
        }
         Serial.print("Current mode set to: ");
         Serial.println(gestureMode ? "GESTURE" : "AIR MOUSE");
    }
    lastButtonState = currentButtonState; // Update last state for edge detection
}

void setup() {
    Serial.begin(115200);
    Serial.println("ESP32 AirMouse Starting...");

    // Initialize I2C
    Wire.begin(); // Use default SDA=21, SCL=22

    // --- Initialize MPU6050 ---
    Serial.println("Initializing MPU6050...");
    mpu.initialize(); // *** THIS IS THE CRUCIAL ADDITION ***

    // Verify MPU6050 connection AFTER initialization
    Serial.println("Testing MPU6050 connection...");
    if (!mpu.testConnection()) {
        Serial.println("MPU6050 connection failed! Halting.");
        while (1); // Stop execution if MPU fails
    }
    Serial.println("MPU6050 connection successful.");

    // Initialize BLE Mouse
    Serial.println("Initializing BLE Mouse...");
    bleMouse.begin();

    // Configure Pin Modes
    pinMode(FLEX_LEFT_PIN, INPUT);
    pinMode(FLEX_RIGHT_PIN, INPUT);
    pinMode(BUTTON_PIN, INPUT_PULLDOWN); // Button pin setup

    Serial.println("Setup complete. Waiting for BLE connection...");
}

void loop() {
    // Check BLE connection status (optional, but good practice)
    if (bleMouse.isConnected()) {
        // Check the mode switch button state on every loop iteration
        checkButton();

        // Only run air mouse functions if NOT in gesture mode
        // The check is also performed inside airmouse_mode() for safety
        if (!gestureMode) {
            airmouse_mode();
        } else {
            // Placeholder for gesture mode logic if any is needed directly in the loop
            // delay(10); // Add a small delay if gesture mode does nothing here
        }
    } else {
        // Optional: Add behavior while disconnected, e.g., blink LED
        // Serial.println("Waiting for BLE connection...");
        delay(500); // Wait longer if not connected
    }
}