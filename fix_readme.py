import re

with open('README.md', 'r') as f:
    content = f.read()

# The tool applied the block twice at the top. Let's fix this.
# It replaced from `**[Flash it to your ESP32 from the browser]` to `## Quick Start (For Developers)`
# I'll just restore the original top, and then find the actual `## Quick Start` at the bottom and replace it.

# Restore the top
original_top = """# WireClaw

An AI agent that lives on a $5 microcontroller and controls real hardware.

**Supported chips:** ESP32-C6, ESP32-S3, ESP32-C3 (4 MB flash required)

**[Flash it to your ESP32 from the browser](https://wireclaw.io/flash.html)** - no tools to install, configure from your phone. The web flasher auto-detects your chip.

Tell it what you want in plain language - over Telegram, serial, or NATS - and it wires up GPIO pins, reads sensors, switches relays, and sets up automation rules that keep running without the AI. It remembers your preferences across reboots, knows what time it is, can talk to other WireClaw devices on the network, and bridges to any serial device - Arduinos, GPS modules, CO2 sensors, RFID readers - over UART."""

# We will just replace everything from the start to "Tell it what you want in plain language..."
top_match = re.search(r'# WireClaw.*?Tell it what you want in plain language', content, flags=re.DOTALL)
if top_match:
    content = content[:top_match.start()] + original_top + content[top_match.end()-41:]

new_quick_start = """## Quick Start (For Developers)

Requires PlatformIO (VSCode extension or CLI).

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/wireclaw.git
   cd wireclaw
   ```

2. Configure using `.env`:
   ```bash
   cp .env.example .env
   # Edit .env with your WiFi credentials and LLM API Key.
   # You can choose between gemini, deepseek, openrouter, or openai_compatible.
   ```

3. Build and upload the filesystem (this automatically generates `data/config.json` from `.env`):
   ```bash
   pio run -t uploadfs
   ```

4. Build and upload the firmware:
   ```bash
   pio run -t upload
   ```

5. Monitor serial output (115200 baud):
   ```bash
   pio device monitor
   ```

If you don't use `.env`, you can flash the device and it will host a Setup Portal over WiFi to collect configuration via browser.
"""

old_quick_start_regex = r'## Quick Start\n\nRequires PlatformIO.*?pio run -t upload\n   ```\n'
content = re.sub(old_quick_start_regex, new_quick_start, content, flags=re.DOTALL)

with open('README.md', 'w') as f:
    f.write(content)
