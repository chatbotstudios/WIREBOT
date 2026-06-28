import re

with open('src/main.cpp', 'r') as f:
    content = f.read()

# 1. Add globals
discord_globals = """
#include <WiFiClientSecure.h>

bool g_discord_enabled = false;
static WiFiClientSecure discordClient;
static unsigned long discordLastPoll = 0;
static const char *DISCORD_API_HOST = "discord.com";
static const int DISCORD_API_PORT = 443;
static char discordLastMessageId[32] = "";

"""
# We will just append it after the g_telegram_enabled = false;
content = content.replace("bool g_telegram_enabled = false;", "bool g_telegram_enabled = false;\n" + discord_globals)

# 2. Add discordSendMessage and discordTick
discord_funcs = """
/*============================================================================
 * Discord Bot Client
 *============================================================================*/

static int discordApiCall(const char *method, const char *endpoint, const char *body, int body_len, char *buf, int buf_len) {
    discordClient.stop();
    if (!discordClient.connect(DISCORD_API_HOST, DISCORD_API_PORT)) {
        if (g_debug) Serial.printf("[Discord] Connect failed\\n");
        return -1;
    }

    static char httpReq[512];
    int hdr_len = snprintf(httpReq, sizeof(httpReq),
        "%s /api/v10%s HTTP/1.1\\r\\n"
        "Host: %s\\r\\n"
        "Authorization: Bot %s\\r\\n"
        "Content-Type: application/json\\r\\n"
        "Content-Length: %d\\r\\n"
        "Connection: close\\r\\n\\r\\n",
        method, endpoint, DISCORD_API_HOST, cfg_discord_token, body_len);

    discordClient.write((uint8_t *)httpReq, hdr_len);
    if (body_len > 0) {
        discordClient.write((uint8_t *)body, body_len);
    }

    unsigned long wait_start = millis();
    while (!discordClient.available()) {
        if (!discordClient.connected()) return -1;
        if (millis() - wait_start > 10000) return -1;
        delay(50);
    }

    int content_length = -1;
    while (discordClient.connected()) {
        String line = discordClient.readStringUntil('\\n');
        line.trim();
        if (line.length() == 0) break;
        if (line.startsWith("Content-Length:") || line.startsWith("content-length:")) {
            content_length = line.substring(15).toInt();
        }
    }

    int total = 0;
    if (content_length > 0) {
        int to_read = content_length < buf_len - 1 ? content_length : buf_len - 1;
        total = discordClient.readBytes(buf, to_read);
    } else {
        while (total < buf_len - 1) {
            int avail = discordClient.available();
            if (avail > 0) {
                int rd = discordClient.readBytes(buf + total, min(avail, buf_len - 1 - total));
                total += rd;
            } else if (!discordClient.connected()) {
                break;
            } else {
                delay(10);
            }
        }
    }
    discordClient.stop();
    buf[total] = '\\0';
    return total;
}

bool discordSendMessage(const char *text) {
    if (!g_discord_enabled) return false;
    static char req[LLM_MAX_RESPONSE_LEN + 256];
    static char escaped[LLM_MAX_RESPONSE_LEN + 128];
    int w = 0;
    for (int i = 0; text[i] && w < (int)sizeof(escaped) - 2; i++) {
        char c = text[i];
        if (c == '"' || c == '\\\\') { escaped[w++] = '\\\\'; escaped[w++] = c; }
        else if (c == '\\n') { escaped[w++] = '\\\\'; escaped[w++] = 'n'; }
        else if ((uint8_t)c >= 0x20) { escaped[w++] = c; }
    }
    escaped[w] = '\\0';

    int req_len = snprintf(req, sizeof(req), "{\\"content\\":\\"%s\\"}", escaped);
    static char endpoint[128];
    snprintf(endpoint, sizeof(endpoint), "/channels/%s/messages", cfg_discord_channel_id);
    static char resp[256];
    return discordApiCall("POST", endpoint, req, req_len, resp, sizeof(resp)) > 0;
}

static void discordTick() {
    unsigned long now = millis();
    if (now - discordLastPoll < 5000) return; // Poll every 5s to avoid rate limits
    discordLastPoll = now;

    static char endpoint[128];
    snprintf(endpoint, sizeof(endpoint), "/channels/%s/messages?limit=1", cfg_discord_channel_id);
    static char resp[2048];
    int rlen = discordApiCall("GET", endpoint, "", 0, resp, sizeof(resp));
    if (rlen <= 0) return;
    
    // Parse response. Should be an array of messages: [{"id": "...", "content": "...", "author": {"id": "..."}}]
    const char *id_key = strstr(resp, "\\"id\\"");
    if (!id_key) return;
    const char *p = id_key + 4;
    while (*p == ':' || *p == ' ' || *p == '"') p++;
    char msg_id[32];
    int mw = 0;
    while (*p && *p != '"' && mw < sizeof(msg_id) - 1) msg_id[mw++] = *p++;
    msg_id[mw] = '\\0';

    // If it's the same as the last seen message, ignore
    if (discordLastMessageId[0] != '\\0' && strcmp(msg_id, discordLastMessageId) == 0) return;

    // Check author
    const char *auth_str = strstr(resp, "\\"author\\"");
    if (auth_str) {
        const char *auth_id_str = strstr(auth_str, "\\"id\\"");
        if (auth_id_str) {
            p = auth_id_str + 4;
            while (*p == ':' || *p == ' ' || *p == '"') p++;
            char auth_id[32];
            int aw = 0;
            while (*p && *p != '"' && aw < sizeof(auth_id) - 1) auth_id[aw++] = *p++;
            auth_id[aw] = '\\0';
            
            // Ignore messages from the bot itself (if DISCORD_USER_ID is set)
            if (cfg_discord_user_id[0] != '\\0' && strcmp(auth_id, cfg_discord_user_id) == 0) {
                strncpy(discordLastMessageId, msg_id, sizeof(discordLastMessageId));
                return;
            }
        }
    }

    // Is this the first poll? If so, just record the latest ID and do not respond to old messages
    if (discordLastMessageId[0] == '\\0') {
        strncpy(discordLastMessageId, msg_id, sizeof(discordLastMessageId));
        return; 
    }
    
    strncpy(discordLastMessageId, msg_id, sizeof(discordLastMessageId));

    // Extract content
    const char *content_key = strstr(resp, "\\"content\\"");
    if (!content_key) return;
    p = content_key + 9;
    while (*p == ':' || *p == ' ') p++;
    if (*p != '"') return;
    p++;
    
    static char msgBuf[512];
    mw = 0;
    while (*p && *p != '"' && mw < (int)sizeof(msgBuf) - 1) {
        if (*p == '\\\\' && *(p + 1)) {
            p++;
            if (*p == 'n') msgBuf[mw++] = '\\n';
            else msgBuf[mw++] = *p;
        } else {
            msgBuf[mw++] = *p;
        }
        p++;
    }
    msgBuf[mw] = '\\0';
    if (mw == 0) return;

    Serial.printf("\\n[Discord] Message: %s\\n", msgBuf);

    if (msgBuf[0] == '/') {
        if (handleCommand(msgBuf + 1, cmdResponseBuf, sizeof(cmdResponseBuf))) {
            discordSendMessage(cmdResponseBuf);
        } else {
            snprintf(cmdResponseBuf, sizeof(cmdResponseBuf), "Unknown command: %s", msgBuf);
            discordSendMessage(cmdResponseBuf);
        }
        Serial.printf("> ");
        return;
    }

    const char *response = chatWithLLM(msgBuf);
    if (response) {
        discordSendMessage(response);
    } else {
        discordSendMessage("[error: LLM call failed]");
    }
    Serial.printf("> ");
}

static void discordYield() {
    discordClient.stop();
}

"""

# Insert before handleSerialCommand
content = content.replace("/*============================================================================\n * Serial Commands", discord_funcs + "/*============================================================================\n * Serial Commands")

# 3. Add to tgYield / unknown command processing
content = content.replace("tgYield(); /* Free Telegram TLS so LLM can allocate */", "tgYield(); discordYield(); /* Free TLS so LLM can allocate */")

# 4. Add setup init
discord_setup = """
    /* Discord (optional) */
    if (cfg_discord_token[0] != '\\0' && cfg_discord_channel_id[0] != '\\0') {
        g_discord_enabled = true;
        discordClient.setInsecure();
        discordClient.setTimeout(30);
        discordLastPoll = millis() - 5000; // Trigger immediately
        Serial.printf("Discord: enabled (channel_id %s)\\n", cfg_discord_channel_id);
    } else {
        Serial.printf("Discord: disabled (no token/channel in config)\\n");
    }
"""
content = content.replace("/* Web config portal (HTTP on port 80 + mDNS) */", discord_setup + "\n    /* Web config portal (HTTP on port 80 + mDNS) */")

# 5. Add to loop
discord_loop = """
    if (g_discord_enabled) {
        discordTick();
    }
"""
content = content.replace("    if (g_telegram_enabled) {\n        telegramTick();\n    }", "    if (g_telegram_enabled) {\n        telegramTick();\n    }\n" + discord_loop)

# 6. Serial info
discord_serial = """        Serial.printf("Discord:   %s\\n", g_discord_enabled ? "enabled" : "disabled");"""
content = content.replace("Serial.printf(\"Telegram:  %s\\n\", g_telegram_enabled ? \"enabled\" : \"disabled\");", "Serial.printf(\"Telegram:  %s\\n\", g_telegram_enabled ? \"enabled\" : \"disabled\");\n" + discord_serial)


with open('src/main.cpp', 'w') as f:
    f.write(content)

print("Added Discord to main.cpp")
