# Waveshare ESP32-S3 TOUCH-AMOLED 1.75 Examples

The Waveshare board includes advanced peripherals that are automatically exposed to the WireClaw rule engine.

## IMU (Motion Detection)

**Goal:** Turn on the display backlight when the device is moved.

```
"When the imu_accel_x changes by more than 0.5, turn on the display."
```

## Battery Management

**Goal:** Send a Discord alert when battery drops below 15%.

```
"Send a Discord message 'Battery low: {value}%' when battery_percent drops below 15."
```
