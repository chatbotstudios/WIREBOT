
#ifndef BOARD_WAVESHARE_H
#define BOARD_WAVESHARE_H

#ifdef BOARD_WAVESHARE_AMOLED

void boardInit();
void boardUpdateUI(const char* deviceName, bool wifiOn, const char* ipAddress);

#endif // BOARD_WAVESHARE_AMOLED

#endif // BOARD_WAVESHARE_H
