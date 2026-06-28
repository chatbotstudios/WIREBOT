import re

with open('src/devices.cpp', 'r') as f:
    content = f.read()

board_sensors = """
#ifdef BOARD_WAVESHARE_AMOLED

float get_battery_voltage() {
    // Mock for now or implement XPowersLib read
    return 3.7f; 
}

float get_battery_percent() {
    return 80.0f;
}

#endif
"""

content = content.replace("/* ---- Sensor Registration ---- */", board_sensors + "\n/* ---- Sensor Registration ---- */")

register_sensors = """
#ifdef BOARD_WAVESHARE_AMOLED
    Device dev_bat_v;
    strncpy(dev_bat_v.name, "battery_v", sizeof(dev_bat_v.name));
    dev_bat_v.type = DEV_SENSOR_ANALOG;
    dev_bat_v.pin = 255; // Virtual
    devices[deviceCount++] = dev_bat_v;

    Device dev_bat_p;
    strncpy(dev_bat_p.name, "battery_percent", sizeof(dev_bat_p.name));
    dev_bat_p.type = DEV_SENSOR_ANALOG;
    dev_bat_p.pin = 255; // Virtual
    devices[deviceCount++] = dev_bat_p;
#endif
"""

content = content.replace("    /* Built-in pseudo-sensors for rules */", register_sensors + "\n    /* Built-in pseudo-sensors for rules */")

# Add the read logic in sensor_read inside `if (dev->type == DEV_SENSOR_ANALOG)`
read_logic_orig = """    if (dev->type == DEV_SENSOR_ANALOG) {
#if !defined(CONFIG_IDF_TARGET_ESP32)
        if (strcmp(dev->name, "chip_temp") == 0) {
            float temp = 0.0f;"""

read_logic_new = """    if (dev->type == DEV_SENSOR_ANALOG) {
#ifdef BOARD_WAVESHARE_AMOLED
        if (strcmp(dev->name, "battery_v") == 0) {
            val = get_battery_voltage();
            valid = true;
            snprintf(buf, buf_len, "%.2f V", val);
        } else if (strcmp(dev->name, "battery_percent") == 0) {
            val = get_battery_percent();
            valid = true;
            snprintf(buf, buf_len, "%.1f %%", val);
        } else
#endif
#if !defined(CONFIG_IDF_TARGET_ESP32)
        if (strcmp(dev->name, "chip_temp") == 0) {
            float temp = 0.0f;"""

content = content.replace(read_logic_orig, read_logic_new)

with open('src/devices.cpp', 'w') as f:
    f.write(content)

print("Patched devices.cpp for Waveshare sensors")
