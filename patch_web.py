with open('src/web_config.cpp', 'r') as f:
    content = f.read()

# Externs
content = content.replace("extern char cfg_api_key[128];", "extern char cfg_api_key[128];\nextern char cfg_llm_provider[32];")

# handleGetConfig API
get_conf_orig = """    snprintf(buf, sizeof(buf),
        "{"
        "\\"wifi_ssid\\":\\"%s\\","
        "\\"wifi_pass\\":\\"%s\\","
        "\\"api_key\\":\\"%s\\","
        "\\"model\\":\\"%s\\","""
get_conf_new = """    snprintf(buf, sizeof(buf),
        "{"
        "\\"wifi_ssid\\":\\"%s\\","
        "\\"wifi_pass\\":\\"%s\\","
        "\\"llm_provider\\":\\"%s\\","
        "\\"api_key\\":\\"%s\\","
        "\\"model\\":\\"%s\\","""
content = content.replace(get_conf_orig, get_conf_new)

get_conf_args_orig = """        cfg_wifi_ssid, masked_pass, masked_key, cfg_model,"""
get_conf_args_new = """        cfg_wifi_ssid, masked_pass, cfg_llm_provider, masked_key, cfg_model,"""
content = content.replace(get_conf_args_orig, get_conf_args_new)

# handlePostConfig API
post_fields_orig = """    static Field fields[12];
    const char *keys[] = {
        "wifi_ssid", "wifi_pass", "api_key", "model", "device_name",
        "api_base_url", "nats_host", "nats_port", "telegram_token",
        "telegram_chat_id", "telegram_cooldown", "timezone"
    };

    for (int i = 0; i < 12; i++) {"""
post_fields_new = """    static Field fields[13];
    const char *keys[] = {
        "wifi_ssid", "wifi_pass", "llm_provider", "api_key", "model", "device_name",
        "api_base_url", "nats_host", "nats_port", "telegram_token",
        "telegram_chat_id", "telegram_cooldown", "timezone"
    };

    for (int i = 0; i < 13; i++) {"""
content = content.replace(post_fields_orig, post_fields_new)

post_write_orig = """    for (int i = 0; i < 12; i++) {
        f.print("  \\""); f.print(fields[i].key); f.print("\\": ");
        wcWriteJsonEscaped(f, fields[i].val);
        if (i < 11) f.print(",");"""
post_write_new = """    for (int i = 0; i < 13; i++) {
        f.print("  \\""); f.print(fields[i].key); f.print("\\": ");
        wcWriteJsonEscaped(f, fields[i].val);
        if (i < 12) f.print(",");"""
content = content.replace(post_write_orig, post_write_new)

# HTML UI Add Dropdown
html_dropdown = """<label>LLM Provider</label>
<select id="c_llm_provider" style="width:100%;padding:0.6rem;background:var(--bg2);color:var(--text);border:1px solid var(--border);border-radius:8px;font-family:var(--mono);">
  <option value="openrouter">OpenRouter</option>
  <option value="deepseek">DeepSeek</option>
  <option value="gemini">Google Gemini</option>
  <option value="openai_compatible">OpenAI Compatible (Local/Custom)</option>
</select>
<label>API Key</label>"""
content = content.replace("<label>API Key</label>", html_dropdown, 1)

# JS Load
js_load_orig = """var f=['wifi_ssid','wifi_pass','api_key','model','device_name','api_base_url',
'nats_host','nats_port','telegram_token','telegram_chat_id','telegram_cooldown','timezone'];"""
js_load_new = """var f=['wifi_ssid','wifi_pass','llm_provider','api_key','model','device_name','api_base_url',
'nats_host','nats_port','telegram_token','telegram_chat_id','telegram_cooldown','timezone'];"""
content = content.replace(js_load_orig, js_load_new)

with open('src/web_config.cpp', 'w') as f:
    f.write(content)

print("Patched web_config.cpp successfully.")
