#ifdef BOARD_WAVESHARE_AMOLED

#include "board_waveshare.h"
#if !defined(CONFIG_IDF_TARGET_ESP32)
#include "driver/temperature_sensor.h"
extern temperature_sensor_handle_t g_temp_sensor;
#endif
#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <Arduino_GFX_Library.h>
#include "XPowersLib.h"

// Pin Definitions
#define I2C_SDA_PIN 15
#define I2C_SCL_PIN 14

#define TFT_CS 12
#define TFT_RST 39
#define TFT_SCL 38
#define TFT_D0 4
#define TFT_D1 5
#define TFT_D2 6
#define TFT_D3 7

#define PIN_TP_RESET 40

#define LCD_W_PHYS 466
#define LCD_H_PHYS 466

// Canvas size
#define CANVAS_W 184
#define CANVAS_H 224

XPowersAXP2101 pmu;

// QSPI Display
Arduino_DataBus *bus = nullptr;
Arduino_CO5300 *gfx = nullptr;
Arduino_Canvas *canvas = nullptr;

void boardInit() {
    Serial.println("Initializing Waveshare AMOLED 1.75 Board...");

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

    // Initialize PMU
    bool pmu_ret = pmu.init(Wire, I2C_SDA_PIN, I2C_SCL_PIN, AXP2101_SLAVE_ADDRESS);
    if(pmu_ret) {
        Serial.println("PMU AXP2101 found!");
        // Enable ALL 3.3V LDOs/DCs to guarantee display and touch get power.
        // port_axp2101.cpp in Waveshare repo lists BLDO1 as "OLED VDD 3300"
        pmu.setALDO1Voltage(3300); pmu.enableALDO1();
        pmu.setALDO2Voltage(3300); pmu.enableALDO2();
        pmu.setALDO3Voltage(3300); pmu.enableALDO3();
        pmu.setALDO4Voltage(3300); pmu.enableALDO4();
        
        pmu.setBLDO1Voltage(3300); pmu.enableBLDO1();
        pmu.setBLDO2Voltage(3300); pmu.enableBLDO2();
        
        pmu.setDC1Voltage(3300); pmu.enableDC1();
        pmu.setDC3Voltage(3300); pmu.enableDC3();

        pmu.disableIRQ(XPOWERS_AXP2101_ALL_IRQ);
        pmu.clearIrqStatus();
    } else {
        Serial.println("PMU AXP2101 not found!");
    }

    // Un-stall Touch Controller
    pinMode(PIN_TP_RESET, OUTPUT);
    digitalWrite(PIN_TP_RESET, HIGH);

    bus = new Arduino_ESP32QSPI(TFT_CS, TFT_SCL, TFT_D0, TFT_D1, TFT_D2, TFT_D3);
    
    // 6 is the column offset for CO5300 round panels
    gfx = new Arduino_CO5300(bus, TFT_RST, 0, LCD_W_PHYS, LCD_H_PHYS, 6, 0, 0, 0);
    
    canvas = new Arduino_Canvas(CANVAS_W, CANVAS_H, gfx);

    // Initialize Display
    if (!canvas->begin()) {
        Serial.println("Failed to init canvas!");
    }
    
    gfx->fillScreen(0x0000); // BLACK
    gfx->setBrightness(200);
}

// Gemini Buddy Boot Screen
static uint16_t dimColor(uint16_t color, float alpha, uint16_t bg) {
    if (alpha >= 1.0f) return color;
    if (alpha <= 0.0f) return bg;
    uint8_t r = (color >> 11) & 0x1F;
    uint8_t g = (color >> 5) & 0x3F;
    uint8_t b = color & 0x1F;
    uint8_t br = (bg >> 11) & 0x1F;
    uint8_t bg_g = (bg >> 5) & 0x3F;
    uint8_t bb = bg & 0x1F;
    r = br + (uint8_t)((float)(r - br) * alpha);
    g = bg_g + (uint8_t)((float)(g - bg_g) * alpha);
    b = bb + (uint8_t)((float)(b - bb) * alpha);
    return (uint16_t)((r << 11) | (g << 5) | b);
}

static void drawCenteredText(const char *s, int cx, int cy, int sz, uint16_t fg, uint16_t bg) {
    int w = (int)strlen(s) * 6 * sz;
    int h = 8 * sz;
    canvas->setTextColor(fg, bg);
    canvas->setTextSize(sz);
    canvas->setCursor(cx - w / 2, cy - h / 2);
    canvas->print(s);
}

void boardUpdateUI(const char* deviceName, bool wifiOn, const char* ipAddress) {
    if (!canvas) return;
    
    // Draw Gemini Boot Logo
    float alpha = 1.0f;
    uint16_t bg = 0x0000;
    canvas->fillScreen(bg);
    uint16_t gemBlue = canvas->color565(66, 133, 244);
    uint16_t cLogo = dimColor(gemBlue, alpha, bg);
    uint16_t cText = dimColor(gemBlue, alpha, bg);
    uint16_t cSub = dimColor(0x7BEF, alpha, bg);

    int cx = CANVAS_W / 2;
    int cy = CANVAS_H / 2 - 50;
    int size = 25;
    canvas->fillTriangle(cx, cy - size, cx - 6, cy, cx + 6, cy, cLogo);
    canvas->fillTriangle(cx, cy + size, cx - 6, cy, cx + 6, cy, cLogo);
    canvas->fillTriangle(cx - size, cy, cx, cy - 6, cx, cy + 6, cLogo);
    canvas->fillTriangle(cx + size, cy, cx, cy - 6, cx, cy + 6, cLogo);

    drawCenteredText("WireBot", CANVAS_W / 2, CANVAS_H / 2 - 5, 3, cText, bg);
    // drawCenteredText(deviceName, CANVAS_W / 2, CANVAS_H / 2 + 40, 1, cSub, bg);

    // Display WiFi and IP Address as requested
    if (wifiOn && ipAddress != nullptr && strlen(ipAddress) > 0) {
        canvas->setTextColor(canvas->color565(0, 255, 0), bg); // Green
        drawCenteredText("WiFi: ON", CANVAS_W / 2, CANVAS_H / 2 + 55, 1, canvas->color565(0, 255, 0), bg);
        drawCenteredText(ipAddress, CANVAS_W / 2, CANVAS_H / 2 + 65, 1, canvas->color565(255, 255, 255), bg);
    } else {
        canvas->setTextColor(canvas->color565(255, 0, 0), bg); // Red
        drawCenteredText("WiFi: OFF", CANVAS_W / 2, CANVAS_H / 2 + 55, 1, canvas->color565(255, 0, 0), bg);
        drawCenteredText("No IP", CANVAS_W / 2, CANVAS_H / 2 + 65, 1, canvas->color565(100, 100, 100), bg);
    }

#if !defined(CONFIG_IDF_TARGET_ESP32)
    float temp = 0.0;
    if (g_temp_sensor) {
        temperature_sensor_get_celsius(g_temp_sensor, &temp);
    }
    uint16_t temp_color;
    if (temp < 30.0) temp_color = canvas->color565(0, 255, 0);
    else if (temp <= 33.0) temp_color = canvas->color565(255, 165, 0);
    else temp_color = canvas->color565(255, 0, 0);
    char tempBuf[32];
    snprintf(tempBuf, sizeof(tempBuf), "Temp: %.1fC", temp);
    drawCenteredText(tempBuf, CANVAS_W / 2, CANVAS_H / 2 + 80, 1, temp_color, bg);
#endif


    // Letterbox scale to physical display (fixes internal RAM allocation limits)
    static uint16_t* s_frameBuf = nullptr;
    if (!s_frameBuf) {
        s_frameBuf = (uint16_t*)heap_caps_malloc(LCD_W_PHYS * LCD_H_PHYS * sizeof(uint16_t), MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
        if (!s_frameBuf) { Serial.println("PSRAM alloc failed"); return; }
        memset(s_frameBuf, 0, LCD_W_PHYS * LCD_H_PHYS * sizeof(uint16_t));
    }
    
    uint16_t* src = (uint16_t*)canvas->getFramebuffer();
    constexpr int DEST_W = 276;
    constexpr int DEST_H = 336;
    constexpr int OFF_X  = (LCD_W_PHYS - DEST_W) / 2;
    constexpr int OFF_Y  = (LCD_H_PHYS - DEST_H) / 2;
    constexpr uint32_t SCALE_X = ((uint32_t)CANVAS_W << 16) / DEST_W;
    constexpr uint32_t SCALE_Y = ((uint32_t)CANVAS_H << 16) / DEST_H;

    for (int dy = 0; dy < DEST_H; dy++) {
        uint32_t sy_fp = (uint32_t)dy * SCALE_Y;
        int y0 = sy_fp >> 16;
        int y1 = (y0 + 1 < CANVAS_H) ? y0 + 1 : y0;
        uint32_t fy = (sy_fp >> 11) & 0x1F;
        uint32_t inv_fy = 32 - fy;

        uint16_t* row0 = src + y0 * CANVAS_W;
        uint16_t* row1 = src + y1 * CANVAS_W;
        uint16_t* dstRow = s_frameBuf + (dy + OFF_Y) * LCD_W_PHYS + OFF_X;

        for (int dx = 0; dx < DEST_W; dx++) {
            uint32_t sx_fp = (uint32_t)dx * SCALE_X;
            int x0 = sx_fp >> 16;
            int x1 = (x0 + 1 < CANVAS_W) ? x0 + 1 : x0;
            uint32_t fx = (sx_fp >> 11) & 0x1F;
            uint32_t inv_fx = 32 - fx;

            uint16_t p00 = row0[x0];
            uint16_t p01 = row0[x1];
            uint16_t p10 = row1[x0];
            uint16_t p11 = row1[x1];

            uint32_t t_rb = (p00 & 0xF81F) * inv_fx + (p01 & 0xF81F) * fx;
            uint32_t t_g  = (p00 & 0x07E0) * inv_fx + (p01 & 0x07E0) * fx;
            uint32_t b_rb = (p10 & 0xF81F) * inv_fx + (p11 & 0xF81F) * fx;
            uint32_t b_g  = (p10 & 0x07E0) * inv_fx + (p11 & 0x07E0) * fx;

            uint32_t rb = (t_rb * inv_fy + b_rb * fy) >> 10;
            uint32_t g  = (t_g  * inv_fy + b_g  * fy) >> 10;
            dstRow[dx] = (uint16_t)((rb & 0xF81F) | (g & 0x07E0));
        }
    }
    
    // Fill margins
    uint16_t bgColor = src[0];
    for (int y = 0; y < OFF_Y; y++) {
        uint16_t* dstRow = s_frameBuf + y * LCD_W_PHYS;
        for (int x = 0; x < LCD_W_PHYS; x++) dstRow[x] = bgColor;
    }
    for (int y = OFF_Y + DEST_H; y < LCD_H_PHYS; y++) {
        uint16_t* dstRow = s_frameBuf + y * LCD_W_PHYS;
        for (int x = 0; x < LCD_W_PHYS; x++) dstRow[x] = bgColor;
    }
    for (int y = OFF_Y; y < OFF_Y + DEST_H; y++) {
        uint16_t* dstRow = s_frameBuf + y * LCD_W_PHYS;
        for (int x = 0; x < OFF_X; x++) dstRow[x] = bgColor;
        for (int x = OFF_X + DEST_W; x < LCD_W_PHYS; x++) dstRow[x] = bgColor;
    }
    
    // Push the PSRAM buffer
    gfx->draw16bitRGBBitmap(0, 0, s_frameBuf, LCD_W_PHYS, LCD_H_PHYS);
}

#endif // BOARD_WAVESHARE_AMOLED
