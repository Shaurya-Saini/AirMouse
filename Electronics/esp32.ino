#include <Wire.h>
#include <MPU6050.h>
#include <BleMouse.h>


#define BUTTON_PIN 5 // Toggle button for modes

// offline baought golden
#define FLEX_LEFT_PIN 34  // Left click flex sensor

//online baought black
#define FLEX_RIGHT_PIN 35 // Right click flex sensor

#define CLICK_SIGNAL_DELAY 40 // Milliseconds between signal clicks
#define BUTTON_DEBOUNCE_MS 500 // Milliseconds to wait after button press

MPU6050 mpu;
BleMouse bleMouse("ESP32 Mouse", "ESP32", 100); // working fine stand alone

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



void airmouse_mode() {
    if (!gestureMode && bleMouse.isConnected()) {
        
        // tested code
        int16_t ax, ay, az, gx, gy, gz;
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        int moveX = gx / 650;  
        int moveY = gy / 650;
        int moveZ = gz / 650;
    
        bleMouse.move(-moveZ, moveX);
        // working till here

        int flexLeftValue = analogRead(FLEX_LEFT_PIN);
        int flexRightValue = analogRead(FLEX_RIGHT_PIN);
        // flex sensors working

        //have to adjust values based on the sensor approx done
        // offline baought golden
        if (flexLeftValue > 1100) {
            bleMouse.press(MOUSE_LEFT);
        } else {
            bleMouse.release(MOUSE_LEFT);
        }

        //online baought black
        if (flexRightValue > 4000) {
            bleMouse.press(MOUSE_RIGHT);
        } else {
            bleMouse.release(MOUSE_RIGHT);
        }
    }
    delay(10);
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
            Serial.println("Button Pressed: Switching to GESTURE Mode.");
            // Ensure mouse buttons are released when entering gesture mode
            if(bleMouse.isConnected()){
                 bleMouse.release(MOUSE_LEFT);
                 bleMouse.release(MOUSE_RIGHT);
                 // Optionally add MIDDLE, BACK, FORWARD releases if used elsewhere
            }
             // Send the signal *after* releasing buttons if needed
            sendModeSwitchSignal();
        } else {
            Serial.println("Button Pressed: Switching to AIR MOUSE Mode.");
            // Send the signal
            sendModeSwitchSignal();
            // Air mouse functionality will resume automatically in loop()
        }
    }
    lastButtonState = currentButtonState; // Update last state for edge detection
}




void setup() {
    Wire.begin();
    Serial.begin(115200);
    while (!mpu.testConnection()) {
        Serial.println("MPU6050 connection failed. Retrying...");
        delay(1000);
    }
    Serial.println("MPU6050 connected");

    bleMouse.begin();
    pinMode(FLEX_LEFT_PIN, INPUT);
    pinMode(FLEX_RIGHT_PIN, INPUT);
    pinMode(BUTTON_PIN, INPUT_PULLDOWN);
}

void loop() {
    // Check the button state on every loop iteration
    checkButton();

    // Only run air mouse functions if NOT in gesture mode
    if (!gestureMode) {
        airmouse_mode();
    }
}
