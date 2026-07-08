import os
import json
import re

ENV_FILE = ".env"
ENV_EXAMPLE = ".env.example"
OUTPUT_FILE = "data/vault/config.json"

def load_env(filepath):
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Ignore comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Match KEY=VALUE (can handle quotes)
            match = re.match(r'^([^=]+)=(.*)$', line)
            if match:
                key = match.group(1).strip()
                val = match.group(2).strip()
                
                # Remove surrounding quotes if present
                if val and val[0] == val[-1] and val.startswith(('"', "'")):
                    val = val[1:-1]
                    
                env_vars[key] = val
    return env_vars

def main():
    print("Generating config.json from environment variables...")
    
    # Load defaults from .env.example
    config = load_env(ENV_EXAMPLE)
    
    # Override with .env if exists
    user_config = load_env(ENV_FILE)
    config.update(user_config)
    
    # Map .env keys to config.json keys
    json_config = {
        "wifi_ssid": config.get("WIFI_SSID", ""),
        "wifi_pass": config.get("WIFI_PASS", ""),
        "llm_provider": config.get("LLM_PROVIDER", "openrouter"),
        "api_key": config.get("LLM_API_KEY", ""),
        "model": config.get("LLM_MODEL", "google/gemini-2.5-flash"),
        "device_name": config.get("DEVICE_NAME", "wireclaw-agent"),
        "api_base_url": config.get("LLM_API_BASE_URL", ""),
        "nats_host": config.get("NATS_HOST", ""),
        "nats_port": int(config.get("NATS_PORT", "4222") or "4222"),
        "telegram_token": config.get("TELEGRAM_TOKEN", ""),
        "telegram_chat_id": config.get("TELEGRAM_CHAT_ID", ""),
        "telegram_cooldown": int(config.get("TELEGRAM_COOLDOWN", "3") or "3"),
        "discord_token": config.get("DISCORD_TOKEN", ""),
        "discord_user_id": config.get("DISCORD_USER_ID", ""),
        "discord_channel_id": config.get("DISCORD_CHANNEL_ID", ""),
        "timezone": config.get("TIMEZONE", "UTC0")
    }
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Write to config.json
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(json_config, f, indent=2)
        f.write("\n")
        
    print(f"Generated {OUTPUT_FILE} successfully.")

if __name__ == "__main__":
    main()
