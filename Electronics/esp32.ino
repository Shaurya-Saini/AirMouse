#include <Wire.h>
#include <MPU6050.h>
#include <BleMouse.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

#define BUTTON_PIN 5 // Toggle button for modes

// offline baought golden
#define FLEX_LEFT_PIN 34  // Left click flex sensor

//online baought black
#define FLEX_RIGHT_PIN 35 // Right click flex sensor

MPU6050 mpu;
BleMouse bleMouse("ESP32 Mouse", "ESP32", 100); // working fine stand alone

bool gestureMode = false;
BLECharacteristic *pCharacteristic;
unsigned long lastButtonPress = 0;

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
    BLEDevice::init("ESP32 Gesture Mode");

    // BLE Server Setup
    BLEServer *pServer = BLEDevice::createServer();
    BLEService *pService = pServer->createService("0000181a-0000-1000-8000-00805f9b34fb");
    pCharacteristic = pService->createCharacteristic(
        "00002a56-0000-1000-8000-00805f9b34fb",
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pCharacteristic->addDescriptor(new BLE2902());
    pService->start();
}

void loop() {
    if (millis() - lastButtonPress > 300) {
        if (digitalRead(BUTTON_PIN) == HIGH) {
            lastButtonPress = millis();
            gestureMode = !gestureMode;

            if (gestureMode) {
                Serial.println("Switching to Gesture Mode...");
                pCharacteristic->setValue("Gesture Mode ON");
                pCharacteristic->notify();
            } else {
                Serial.println("Switching to Air Mouse Mode...");
                pCharacteristic->setValue("Gesture Mode OFF");
                pCharacteristic->notify();
            }
        }
    }

    if (!gestureMode) {
        airmouse_mode();
    }
}
