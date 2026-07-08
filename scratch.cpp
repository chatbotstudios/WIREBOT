#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int json_escape(char *dst, int dst_len, const char *src) {
    int w = 0;
    for (int i = 0; src[i]; i++) {
        char c = src[i];
        const char *esc = nullptr;
        switch (c) {
            case '"':  esc = "\\\""; break;
            case '\\': esc = "\\\\"; break;
            case '\n': esc = "\\n";  break;
            case '\r': esc = "\\r";  break;
            case '\t': esc = "\\t";  break;
            default:
                if ((unsigned char)c < 0x20) continue;
                if (w + 1 >= dst_len) return -1;
                dst[w++] = c;
                continue;
        }
        int elen = strlen(esc);
        if (w + elen >= dst_len) return -1;
        memcpy(dst + w, esc, elen);
        w += elen;
    }
    if (w >= dst_len) return -1;
    dst[w] = '\0';
    return w;
}

static void convert_openai_tools_to_gemini(const char *openai_tools, char *gemini_tools, int max_len) {
    int w = 0;
    const char *p = openai_tools;
    while (*p && w < max_len - 1) {
        const char *func_start = strstr(p, "\"function\":{");
        if (!func_start) break;
        
        if (w > 0 && gemini_tools[w-1] != '[') {
            gemini_tools[w++] = ',';
        } else if (w == 0) {
            gemini_tools[w++] = '[';
        }
        
        p = func_start + 12; // skip "function":{
        gemini_tools[w++] = '{';
        
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
        gemini_tools[w] = '\0';
    } else {
        gemini_tools[0] = '\0';
    }
}

int main() {
    FILE *f = fopen("src/tools.cpp", "r");
    char tools_buf[10000];
    int len = fread(tools_buf, 1, sizeof(tools_buf), f);
    fclose(f);
    tools_buf[len] = '\0';
    
    char *start = strstr(tools_buf, "TOOLS_JSON = R\"JSON([");
    start += strlen("TOOLS_JSON = R\"JSON([") - 1;
    char *end = strstr(start, "])JSON\"");
    end[1] = '\0';

    char gemini_tools[4096];
    convert_openai_tools_to_gemini(start, gemini_tools, sizeof(gemini_tools));
    if (gemini_tools[0] == '\0') {
        printf("GEMINI_TOOLS truncated to EMPTY\n");
    } else {
        printf("GEMINI_TOOLS generated!\n");
    }

    // Now let's try to build the gemini request
    char *buf = (char*)malloc(20480);
    int w = 0;
    w += snprintf(buf + w, 20480 - w, "{\"contents\":[");
    w += snprintf(buf + w, 20480 - w, "{\"role\":\"user\",\"parts\":[{\"text\":\"Hello\"}]}");
    w += snprintf(buf + w, 20480 - w, "]}");

    if (gemini_tools[0]) {
        w += snprintf(buf + w, 20480 - w, ",\"tools\":[{\"functionDeclarations\":%s}]", gemini_tools);
    }

    w += snprintf(buf + w, 20480 - w, "}");

    printf("Payload size: %d\n", w);
    printf("Payload preview: %.*s ... %s\n", 50, buf, buf + w - 50);
    
    FILE *out = fopen("scratch/payload.json", "w");
    fwrite(buf, 1, w, out);
    fclose(out);
    return 0;
}
