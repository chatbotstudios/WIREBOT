import re

with open('src/main.cpp', 'r') as f:
    content = f.read()

# Add include
board_include = """
#ifdef BOARD_WAVESHARE_AMOLED
#include "board_waveshare.h"
#endif
"""
content = content.replace("#include <LittleFS.h>", "#include <LittleFS.h>\n" + board_include)

# Add init to setup
board_init = """
#ifdef BOARD_WAVESHARE_AMOLED
    boardInit();
#endif
"""
content = content.replace("    /* Initialize device registry and rule engine */", board_init + "\n    /* Initialize device registry and rule engine */")

# Add loop to loop
board_loop = """
#ifdef BOARD_WAVESHARE_AMOLED
    boardLoop();
#endif
"""
content = content.replace("    /* Keep sensor EMA values warm (every 10s) */", board_loop + "\n    /* Keep sensor EMA values warm (every 10s) */")

with open('src/main.cpp', 'w') as f:
    f.write(content)

print("Hooked up board_waveshare in main.cpp")
