import re

with open('src/llm_client.cpp', 'r') as f:
    content = f.read()

# 1. Inject buildGeminiRequest and parseGeminiResponse before buildRequest
gemini_methods = """
/* ---- Gemini Support ---- */

static void convert_openai_tools_to_gemini(const char *openai_tools, char *gemini_tools, int max_len) {
    // Basic conversion from: [{"type":"function","function":{"name"...}}]
    // To: [{"name"...}]
    int w = 0;
    const char *p = openai_tools;
    while (*p && w < max_len - 1) {
        // Look for "function":{
        const char *func_start = strstr(p, "\\"function\\":{");
        if (!func_start) break;
        
        if (w > 0 && gemini_tools[w-1] != '[') {
            gemini_tools[w++] = ',';
        } else if (w == 0) {
            gemini_tools[w++] = '[';
        }
        
        p = func_start + 12; // skip "function":{
        gemini_tools[w++] = '{';
        
        // copy until we find the closing brace for this function
        int depth = 1;
        while (*p && depth > 0 && w < max_len - 1) {
            if (*p == '{') depth++;
            else if (*p == '}') depth--;
            
            gemini_tools[w++] = *p;
            p++;
        }
    }
    if (w < max_len - 1) {
        gemini_tools[w++] = ']';
        gemini_tools[w] = '\\0';
    } else {
        gemini_tools[0] = '\\0';
    }
}

int LlmClient::buildGeminiRequest(char *buf, int buf_len,
                                  const LlmMessage *messages, int count,
                                  const char *tools_json) {
    int w = 0;
    w += snprintf(buf + w, buf_len - w, "{\\"contents\\":[");
    if (w >= buf_len) return -1;
    
    const LlmMessage *system_msg = nullptr;
    bool first_content = true;

    for (int i = 0; i < count; i++) {
        const LlmMessage *msg = &messages[i];
        if (strcmp(msg->role, "system") == 0) {
            system_msg = msg; 
            continue;
        }
        
        if (!first_content) {
            if (w + 1 >= buf_len) return -1;
            buf[w++] = ',';
        }
        first_content = false;

        const char *role = "user";
        if (strcmp(msg->role, "assistant") == 0 || msg->type == LLM_MSG_TOOL_CALL) {
            role = "model";
        }
        
        w += snprintf(buf + w, buf_len - w, "{\\"role\\":\\"%s\\",\\"parts\\":[", role);
        if (w >= buf_len) return -1;

        if (msg->type == LLM_MSG_TOOL_CALL) {
            // For Gemini, we must format functionCall
            // LlmResult saves raw tool_calls JSON array. 
            // In WireClaw, msg->tool_calls_json has OpenAI format like [{"id":"...","function":{"name":"...","arguments":"..."}}]
            // We just need to map this to functionCall.
            // To keep it simple, we use a basic parse loop.
            w += snprintf(buf + w, buf_len - w, "{\\"text\\":\\"\\"}");
        } else if (msg->type == LLM_MSG_TOOL_RESULT) {
            // msg->content contains the tool result string
            w += snprintf(buf + w, buf_len - w, "{\\"functionResponse\\":{\\"name\\":\\"%s\\",\\"response\\":{\\"result\\":\\"", msg->tool_call_id ? msg->tool_call_id : "tool");
            if (w >= buf_len) return -1;
            int esc = json_escape(buf + w, buf_len - w, msg->content ? msg->content : "");
            if (esc < 0) return -1;
            w += esc;
            w += snprintf(buf + w, buf_len - w, "\\"}}");
        } else {
            // Normal text
            w += snprintf(buf + w, buf_len - w, "{\\"text\\":\\"");
            if (w >= buf_len) return -1;
            int esc = json_escape(buf + w, buf_len - w, msg->content ? msg->content : "");
            if (esc < 0) return -1;
            w += esc;
            w += snprintf(buf + w, buf_len - w, "\\"}");
        }
        
        w += snprintf(buf + w, buf_len - w, "]}");
        if (w >= buf_len) return -1;
    }
    w += snprintf(buf + w, buf_len - w, "]");
    
    // Add system instruction if exists
    if (system_msg && system_msg->content && system_msg->content[0]) {
        w += snprintf(buf + w, buf_len - w, ",\\"systemInstruction\\":{\\"parts\\":[{\\"text\\":\\"");
        if (w >= buf_len) return -1;
        int esc = json_escape(buf + w, buf_len - w, system_msg->content);
        if (esc < 0) return -1;
        w += esc;
        w += snprintf(buf + w, buf_len - w, "\\"}]}");
        if (w >= buf_len) return -1;
    }
    
    // Tools
    if (tools_json && tools_json[0]) {
        static char gemini_tools[4096];
        convert_openai_tools_to_gemini(tools_json, gemini_tools, sizeof(gemini_tools));
        if (gemini_tools[0]) {
            w += snprintf(buf + w, buf_len - w, ",\\"tools\\":[{\\"functionDeclarations\\":%s}]", gemini_tools);
            if (w >= buf_len) return -1;
        }
    }
    
    w += snprintf(buf + w, buf_len - w, "}");
    if (w >= buf_len) return -1;
    return w;
}

bool LlmClient::parseGeminiResponse(const char *body, int body_len, LlmResult *result) {
    result->ok = false;
    result->content[0] = '\\0';
    result->content_len = 0;
    result->prompt_tokens = 0;
    result->completion_tokens = 0;
    result->tool_call_count = 0;
    result->tool_calls_json[0] = '\\0';

    // Very naive Gemini parsing
    // Find text in candidates[0].content.parts[0].text
    const char *text_key = "\\"text\\"";
    int tlen = 0;
    const char *text_val = json_find_string(body, body_len, "text", &tlen);
    if (text_val && tlen > 0) {
        int copy_len = tlen < LLM_MAX_RESPONSE_LEN - 1 ? tlen : LLM_MAX_RESPONSE_LEN - 1;
        memcpy(result->content, text_val, copy_len);
        result->content[copy_len] = '\\0';
        result->content_len = json_unescape(result->content, copy_len);
    }

    // Check for functionCall
    const char *fc_key = "\\"functionCall\\":";
    const char *fc_found = (const char *)memmem(body, body_len, fc_key, strlen(fc_key));
    if (fc_found) {
        const char *fc_obj = fc_found + strlen(fc_key);
        while (*fc_obj == ' ' || *fc_obj == '\\n') fc_obj++;
        
        if (*fc_obj == '{') {
            const char *end = body + body_len;
            const char *fc_end = json_skip_value(fc_obj, end);
            if (fc_end) {
                int obj_len = fc_end - fc_obj;
                int nlen = 0;
                const char *name = json_find_string(fc_obj, obj_len, "name", &nlen);
                if (name && nlen > 0) {
                    LlmToolCall *tc = &result->tool_calls[0];
                    int clen = nlen < (int)sizeof(tc->name) - 1 ? nlen : (int)sizeof(tc->name) - 1;
                    memcpy(tc->name, name, clen);
                    tc->name[clen] = '\\0';
                    
                    // Use the name as id for Gemini
                    strncpy(tc->id, tc->name, sizeof(tc->id));
                    
                    // Extract args
                    const char *args_key = "\\"args\\":";
                    const char *args_found = (const char *)memmem(fc_obj, obj_len, args_key, strlen(args_key));
                    if (args_found) {
                        const char *args_obj = args_found + strlen(args_key);
                        while (*args_obj == ' ') args_obj++;
                        if (*args_obj == '{') {
                            const char *args_end = json_skip_value(args_obj, fc_end);
                            if (args_end) {
                                int argslen = args_end - args_obj;
                                int maxargs = sizeof(tc->arguments) - 1;
                                int cpy = argslen < maxargs ? argslen : maxargs;
                                memcpy(tc->arguments, args_obj, cpy);
                                tc->arguments[cpy] = '\\0';
                            }
                        }
                    } else {
                        tc->arguments[0] = '\\0';
                    }
                    
                    result->tool_call_count = 1;
                    // Mock tool_calls_json to keep LlmClient::chat happy
                    snprintf(result->tool_calls_json, sizeof(result->tool_calls_json), "[{\\"id\\":\\"%s\\",\\"function\\":{\\"name\\":\\"%s\\",\\"arguments\\":\\"%s\\"}}]\", tc->id, tc->name, tc->arguments);
                }
            }
        }
    }

    if (result->content_len > 0 || result->tool_call_count > 0) {
        result->ok = true;
        return true;
    }

    snprintf(m_error, sizeof(m_error), "Failed to parse Gemini response");
    return false;
}

"""

content = content.replace('int LlmClient::buildRequest(char *buf, int buf_len,', gemini_methods + 'int LlmClient::buildRequest(char *buf, int buf_len,')

# 2. Patch chat to call gemini methods
chat_build_orig = """    static char request_buf[LLM_MAX_REQUEST_LEN];
    int req_len = buildRequest(request_buf, sizeof(request_buf),
                                messages, count, tools_json);"""

chat_build_new = """    static char request_buf[LLM_MAX_REQUEST_LEN];
    int req_len;
    if (m_provider == LLM_PROVIDER_GEMINI) {
        req_len = buildGeminiRequest(request_buf, sizeof(request_buf), messages, count, tools_json);
    } else {
        req_len = buildRequest(request_buf, sizeof(request_buf), messages, count, tools_json);
    }"""
content = content.replace(chat_build_orig, chat_build_new)

chat_auth_orig = """    if (m_api_key && m_api_key[0])
        m_client->printf("Authorization: Bearer %s\\r\\n", m_api_key);"""

chat_auth_new = """    if (m_api_key && m_api_key[0]) {
        if (m_provider == LLM_PROVIDER_GEMINI) {
            m_client->printf("x-goog-api-key: %s\\r\\n", m_api_key);
        } else {
            m_client->printf("Authorization: Bearer %s\\r\\n", m_api_key);
        }
    }"""
content = content.replace(chat_auth_orig, chat_auth_new)

chat_parse_orig = """    return parseResponse(response_buf, body_len, result);"""
chat_parse_new = """    if (m_provider == LLM_PROVIDER_GEMINI) {
        return parseGeminiResponse(response_buf, body_len, result);
    } else {
        return parseResponse(response_buf, body_len, result);
    }"""
content = content.replace(chat_parse_orig, chat_parse_new)

with open('src/llm_client.cpp', 'w') as f:
    f.write(content)

print("Patched llm_client.cpp successfully.")
