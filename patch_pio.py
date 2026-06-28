with open('platformio.ini', 'a') as f:
    f.write("""

[env:esp32-s3-touch-amoled-1.75]
board = esp32-s3-devkitc-1
build_flags =
    -D BOARD_WAVESHARE_AMOLED
    -D BOARD_HAS_PSRAM
    -D ARDUINO_USB_MODE=1
    -D ARDUINO_USB_CDC_ON_BOOT=1
board_build.arduino.memory_type = qio_opi
board_upload.flash_size = 16MB
board_build.partitions = default_16MB.csv
lib_deps =
    lvgl/lvgl @ ~8.3.11
    moononournation/GFX Library for Arduino @ ~1.4.0
    lewisxhe/XPowersLib @ ~0.2.1
""")

print("Added esp32-s3-touch-amoled-1.75 environment to platformio.ini")
