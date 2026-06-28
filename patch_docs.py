import os

# Update README.md
with open('README.md', 'r') as f:
    readme = f.read()

discord_readme = """
It can also text you via Telegram or Discord:

```
You:  "Send me a Discord message when chip temperature goes above 40."
```

And natively supports the **Waveshare ESP32-S3 TOUCH-AMOLED 1.75** board with full LVGL UI, touch, IMU, and PMU support out of the box!
"""

readme = readme.replace("It can also text you:\n", discord_readme + "\n")
with open('README.md', 'w') as f:
    f.write(readme)

# Update CONFIGURATION.md
with open('docs/CONFIGURATION.md', 'r') as f:
    config = f.read()

discord_config = """| Telegram Token / Chat ID | No | - |
| Discord Token / Channel ID | No | - |
| Discord User ID | No | - |"""
config = config.replace("| Telegram Token / Chat ID | No | - |", discord_config)

with open('docs/CONFIGURATION.md', 'w') as f:
    f.write(config)

# Create EXAMPLES_WAVESHARE.md
examples = """# Waveshare ESP32-S3 TOUCH-AMOLED 1.75 Examples

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
"""
with open('docs/EXAMPLES_WAVESHARE.md', 'w') as f:
    f.write(examples)

print("Updated documentation")
