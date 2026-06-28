import os

header = """
#ifndef BOARD_WAVESHARE_H
#define BOARD_WAVESHARE_H

#ifdef BOARD_WAVESHARE_AMOLED

void boardInit();
void boardLoop();

#endif // BOARD_WAVESHARE_AMOLED

#endif // BOARD_WAVESHARE_H
"""

cpp = """
#ifdef BOARD_WAVESHARE_AMOLED

#include "board_waveshare.h"
#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <Arduino_GFX_Library.h>
#include <lvgl.h>
#include "XPowersLib.h"

// Pin Definitions
#define I2C_SDA_PIN 6
#define I2C_SCL_PIN 7

#define TFT_CS 9
#define TFT_RST 14
#define TFT_SCL 10
#define TFT_SDA 11
#define TFT_RESX 14

XPowersAXP2101 pmu;

// QSPI Display
Arduino_DataBus *bus = new Arduino_ESP32QSPI(
    TFT_CS /* CS */, TFT_SCL /* SCK */, TFT_SDA /* D0 */,
    12 /* D1 */, 13 /* D2 */, 15 /* D3 */);
Arduino_GFX *gfx = new Arduino_CO5300(
    bus, TFT_RST /* RST */, 0 /* rotation */, true /* IPS */,
    466 /* width */, 466 /* height */,
    0 /* col offset 1 */, 0 /* row offset 1 */,
    0 /* col offset 2 */, 0 /* row offset 2 */);

/* LVGL variables */
static const uint32_t screenWidth  = 466;
static const uint32_t screenHeight = 466;
static lv_disp_draw_buf_t draw_buf;
static lv_color_t *disp_draw_buf;
static lv_disp_drv_t disp_drv;

/* Display flushing */
void my_disp_flush(lv_disp_drv_t *disp_drv, const lv_area_t *area, lv_color_t *color_p) {
    uint32_t w = (area->x2 - area->x1 + 1);
    uint32_t h = (area->y2 - area->y1 + 1);

    gfx->draw16bitRGBBitmap(area->x1, area->y1, (uint16_t *)&color_p->full, w, h);
    lv_disp_flush_ready(disp_drv);
}

void boardInit() {
    Serial.println("Initializing Waveshare AMOLED 1.75 Board...");

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

    // Initialize PMU
    bool pmu_ret = pmu.init(Wire, I2C_SDA_PIN, I2C_SCL_PIN, AXP2101_SLAVE_ADDRESS);
    if(pmu_ret) {
        Serial.println("PMU AXP2101 found!");
        pmu.setALDO1Voltage(3300);
        pmu.enableALDO1();
        pmu.setALDO2Voltage(3300);
        pmu.enableALDO2();
        pmu.setALDO3Voltage(3300);
        pmu.enableALDO3();
        pmu.setALDO4Voltage(3300);
        pmu.enableALDO4();
        pmu.setBLDO1Voltage(3300);
        pmu.enableBLDO1();
        pmu.setBLDO2Voltage(3300);
        pmu.enableBLDO2();
        pmu.setCPUSleepVoltage(1000);
        
        // Turn on backlight (if controlled by PMU, though CO5300 has built-in brightness control)
    } else {
        Serial.println("PMU AXP2101 not found!");
    }

    // Initialize Display
    gfx->begin();
    gfx->fillScreen(BLACK);

    // Initialize LVGL
    lv_init();

    // Allocate draw buffer in PSRAM
    disp_draw_buf = (lv_color_t *)heap_caps_malloc(sizeof(lv_color_t) * screenWidth * screenHeight / 4, MALLOC_CAP_SPIRAM);
    if (!disp_draw_buf) {
        Serial.println("LVGL disp_draw_buf allocate failed!");
    } else {
        lv_disp_draw_buf_init(&draw_buf, disp_draw_buf, NULL, screenWidth * screenHeight / 4);

        /* Initialize the display */
        lv_disp_drv_init(&disp_drv);
        disp_drv.hor_res = screenWidth;
        disp_drv.ver_res = screenHeight;
        disp_drv.flush_cb = my_disp_flush;
        disp_drv.draw_buf = &draw_buf;
        lv_disp_drv_register(&disp_drv);

        /* Basic UI */
        lv_obj_t *label = lv_label_create(lv_scr_act());
        lv_label_set_text(label, "WireClaw AI Agent");
        lv_obj_align(label, LV_ALIGN_CENTER, 0, 0);
        lv_obj_set_style_text_color(label, lv_color_white(), 0);
        lv_obj_set_style_bg_color(lv_scr_act(), lv_color_black(), 0);
    }
}

void boardLoop() {
    lv_timer_handler();
}

#endif // BOARD_WAVESHARE_AMOLED
"""

os.makedirs('include', exist_ok=True)
os.makedirs('src', exist_ok=True)

with open('include/board_waveshare.h', 'w') as f:
    f.write(header)
    
with open('src/board_waveshare.cpp', 'w') as f:
    f.write(cpp)
    
print("Created board_waveshare files")
