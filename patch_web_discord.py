import re

with open('src/web_config.cpp', 'r') as f:
    content = f.read()

# Add externs
externs = """extern char cfg_discord_token[128];
extern char cfg_discord_user_id[32];
extern char cfg_discord_channel_id[32];"""
content = content.replace("extern char cfg_telegram_chat_id[16];", "extern char cfg_telegram_chat_id[16];\n" + externs)

# Add to GET /api/config
get_conf_orig = """        "\\"telegram_chat_id\\":\\"%s\\","
        "\\"telegram_cooldown\\":%d,"
        "\\"timezone\\":\\"%s\\"}","""
get_conf_new = """        "\\"telegram_chat_id\\":\\"%s\\","
        "\\"telegram_cooldown\\":%d,"
        "\\"discord_token\\":\\"%s\\","
        "\\"discord_user_id\\":\\"%s\\","
        "\\"discord_channel_id\\":\\"%s\\","
        "\\"timezone\\":\\"%s\\"}","""
content = content.replace(get_conf_orig, get_conf_new)

# Mask discord token
mask_token = """
    char masked_discord_token[64] = "";
    if (cfg_discord_token[0] != '\\0') {
        int len = strlen(cfg_discord_token);
        snprintf(masked_discord_token, sizeof(masked_discord_token), "%.4s...%s", 
                 cfg_discord_token, len > 8 ? cfg_discord_token + len - 4 : "");
    }
"""
content = content.replace("char cd_buf[8];", mask_token + "\n    char cd_buf[8];")

get_conf_args_orig = """        cfg_telegram_chat_id, cfg_telegram_cooldown, cfg_timezone);"""
get_conf_args_new = """        cfg_telegram_chat_id, cfg_telegram_cooldown,
        masked_discord_token, cfg_discord_user_id, cfg_discord_channel_id,
        cfg_timezone);"""
content = content.replace(get_conf_args_orig, get_conf_args_new)

# Add to POST /api/config
post_fields_orig = """    static Field fields[13];
    const char *keys[] = {
        "wifi_ssid", "wifi_pass", "llm_provider", "api_key", "model", "device_name",
        "api_base_url", "nats_host", "nats_port", "telegram_token",
        "telegram_chat_id", "telegram_cooldown", "timezone"
    };

    for (int i = 0; i < 13; i++) {"""
post_fields_new = """    static Field fields[16];
    const char *keys[] = {
        "wifi_ssid", "wifi_pass", "llm_provider", "api_key", "model", "device_name",
        "api_base_url", "nats_host", "nats_port", "telegram_token",
        "telegram_chat_id", "telegram_cooldown", 
        "discord_token", "discord_user_id", "discord_channel_id",
        "timezone"
    };

    for (int i = 0; i < 16; i++) {"""
content = content.replace(post_fields_orig, post_fields_new)

post_write_orig = """    for (int i = 0; i < 13; i++) {
        f.print("  \\""); f.print(fields[i].key); f.print("\\": ");
        wcWriteJsonEscaped(f, fields[i].val);
        if (i < 12) f.print(",");"""
post_write_new = """    for (int i = 0; i < 16; i++) {
        f.print("  \\""); f.print(fields[i].key); f.print("\\": ");
        wcWriteJsonEscaped(f, fields[i].val);
        if (i < 15) f.print(",");"""
content = content.replace(post_write_orig, post_write_new)

# Add to HTML UI
html_discord = """</div>
    <div style="margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid var(--border);">
      <h3 style="margin-top:0;">Discord</h3>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
        <div>
          <label>Bot Token</label>
          <input type="text" id="c_discord_token" placeholder="Leave blank to disable">
        </div>
        <div>
          <label>Channel ID</label>
          <input type="text" id="c_discord_channel_id">
        </div>
      </div>
      <div style="margin-top:1rem;">
        <label>User ID (Optional, ignore bot's own msgs)</label>
        <input type="text" id="c_discord_user_id">
      </div>
    </div>"""

content = content.replace("</div>\n    <div style=\"margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid var(--border);\">\n      <h3 style=\"margin-top:0;\">System</h3>", html_discord + "\n    <div style=\"margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid var(--border);\">\n      <h3 style=\"margin-top:0;\">System</h3>")

# JS load
js_load_orig = """var f=['wifi_ssid','wifi_pass','llm_provider','api_key','model','device_name','api_base_url',
'nats_host','nats_port','telegram_token','telegram_chat_id','telegram_cooldown','timezone'];"""
js_load_new = """var f=['wifi_ssid','wifi_pass','llm_provider','api_key','model','device_name','api_base_url',
'nats_host','nats_port','telegram_token','telegram_chat_id','telegram_cooldown',
'discord_token','discord_user_id','discord_channel_id','timezone'];"""
content = content.replace(js_load_orig, js_load_new)

# Status
externs_status = """extern bool g_discord_enabled;"""
content = content.replace("extern bool g_telegram_enabled;", "extern bool g_telegram_enabled;\n" + externs_status)

status_orig = """        "\\"telegram_status\\":\\"%s\\""
        "}",
        WIRECLAW_VERSION, millis() / 1000,
        ESP.getFreeHeap(),
        WiFi.SSID().c_str(), WiFi.localIP().toString().c_str(), WiFi.RSSI(),
        cfg_model,
        g_nats_enabled ? "Connected" : "Disabled",
        g_telegram_enabled ? "Enabled" : "Disabled"
    );"""
status_new = """        "\\"telegram_status\\":\\"%s\\","
        "\\"discord_status\\":\\"%s\\""
        "}",
        WIRECLAW_VERSION, millis() / 1000,
        ESP.getFreeHeap(),
        WiFi.SSID().c_str(), WiFi.localIP().toString().c_str(), WiFi.RSSI(),
        cfg_model,
        g_nats_enabled ? "Connected" : "Disabled",
        g_telegram_enabled ? "Enabled" : "Disabled",
        g_discord_enabled ? "Enabled" : "Disabled"
    );"""
content = content.replace(status_orig, status_new)

html_status_orig = """            '<p><strong>Telegram:</strong> ' + d.telegram_status + '</p>';"""
html_status_new = """            '<p><strong>Telegram:</strong> ' + d.telegram_status + '</p>' +
            '<p><strong>Discord:</strong> ' + d.discord_status + '</p>';"""
content = content.replace(html_status_orig, html_status_new)


with open('src/web_config.cpp', 'w') as f:
    f.write(content)

print("Added Discord to web_config.cpp")
