import sys
import os
import subprocess
import textwrap
import json

# Point Python to our bundled 'lib' folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from flowlauncher import FlowLauncher, FlowLauncherAPI
from groq import Groq

class AiPlugin(FlowLauncher):

    # 1. This property dynamically fetches settings saved by Flow Launcher and syncs them to disk
    @property
    def settings(self) -> dict:
        merged = {}
        
        # Load from official Flow Launcher Settings.json if available
        fl_settings_dir = os.path.join(os.getenv("APPDATA", ""), "FlowLauncher", "Settings", "Plugins", "Ai Assistant")
        fl_settings_path = os.path.join(fl_settings_dir, "Settings.json")
        try:
            if os.path.exists(fl_settings_path):
                with open(fl_settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        merged.update(data)
        except Exception:
            pass

        # Load from local backup config.json inside plugin folder
        local_config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            if os.path.exists(local_config_path):
                with open(local_config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if k == "api_key":
                                if not str(merged.get("api_key", "") or "").strip() and str(v or "").strip():
                                    merged["api_key"] = v
                            elif k not in merged:
                                merged[k] = v
        except Exception:
            pass

        # Merge from Flow Launcher's in-memory RPC request
        req = getattr(self, "rpc_request", {})
        if isinstance(req, dict):
            rpc_settings = req.get("settings", {})
            if isinstance(rpc_settings, dict):
                for k, v in rpc_settings.items():
                    if k == "api_key":
                        if str(v or "").strip():
                            merged["api_key"] = v
                    else:
                        merged[k] = v

        # Persist and fsync settings to disk so they survive device restarts and abrupt shutdowns
        api_key_val = str(merged.get("api_key", "") or "").strip()
        if api_key_val:
            # Sync to local config.json in plugin folder
            try:
                save_needed = True
                if os.path.exists(local_config_path):
                    with open(local_config_path, "r", encoding="utf-8") as f:
                        if json.load(f) == merged:
                            save_needed = False
                if save_needed:
                    with open(local_config_path, "w", encoding="utf-8") as f:
                        json.dump(merged, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())
            except Exception:
                pass

            # Sync to official Flow Launcher Settings.json
            try:
                if os.path.exists(fl_settings_dir):
                    save_needed = True
                    if os.path.exists(fl_settings_path):
                        with open(fl_settings_path, "r", encoding="utf-8") as f:
                            if json.load(f) == merged:
                                save_needed = False
                    if save_needed:
                        with open(fl_settings_path, "w", encoding="utf-8") as f:
                            json.dump(merged, f, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
            except Exception:
                pass

        return merged

    def query(self, param: str = '') -> list:
        query = param.strip()
        # 2. Retrieve the API key from the settings UI
        api_key = str(self.settings.get("api_key", "") or "").strip()

        # 3. Guardrail: Tell the user if they forgot to enter their key
        if not api_key:
            return [
                {
                    "Title": "API Key is missing",
                    "SubTitle": "Open Flow Launcher Settings > Plugins > Ai Assistant to enter your Groq API Key",
                    "IcoPath": "icon.png"
                }
            ]

        if not query:
            return [
                {
                    "Title": "Type a prompt for your Ai Assistant",
                    "SubTitle": "Example: 'ai explain quantum computing in one sentence'",
                    "IcoPath": "icon.png"
                }
            ]

        # Check if query starts with '> ' or '>' indicating execution mode
        is_exec_mode = False
        actual_query = query
        if query.startswith(">"):
            actual_query = query.lstrip(">").strip()
            flag_path = os.path.join(os.path.dirname(__file__), ".exec_flag")
            if os.path.exists(flag_path):
                try:
                    with open(flag_path, "r", encoding="utf-8") as f:
                        flag_val = f.read().strip()
                    os.remove(flag_path)
                    if flag_val == actual_query:
                        is_exec_mode = True
                except Exception:
                    pass

        if not actual_query:
            return [
                {
                    "Title": "Type a prompt for your Ai Assistant",
                    "SubTitle": "Example: 'ai explain quantum computing in one sentence'",
                    "IcoPath": "icon.png"
                }
            ]

        if not is_exec_mode:
            return [
                {
                    "Title": f"Ask Ai Assistant: '{actual_query}'",
                    "SubTitle": "Press Enter to send query to Groq AI",
                    "IcoPath": "icon.png",
                    "JsonRPCAction": {
                        "method": "ask_ai",
                        "parameters": [actual_query],
                        "dontHideAfterAction": True
                    }
                }
            ]

        return self.execute_groq_query(api_key, actual_query)

    def ask_ai(self, param: str = '') -> list:
        query = param.strip()
        if not query:
            return []
        flag_path = os.path.join(os.path.dirname(__file__), ".exec_flag")
        try:
            with open(flag_path, "w", encoding="utf-8") as f:
                f.write(query)
        except Exception:
            pass
        
        FlowLauncherAPI.change_query(f"ai > {query}", requery=True)
        return []

    def execute_groq_query(self, api_key: str, query: str) -> list:
        try:
            client = Groq(api_key=api_key)
            
            # Check if user enabled Concise Mode in settings
            concise_mode = str(self.settings.get("concise_mode", "true")).lower() == "true"
            messages = []
            if concise_mode:
                messages.append({
                    "role": "system",
                    "content": "You are a direct, concise AI assistant inside a desktop launcher. Provide clear, short answers without conversational filler or introductions. Use bullet points if listing multiple items."
                })
            messages.append({"role": "user", "content": query})
            
            completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
            )
            
            full_response = (completion.choices[0].message.content or "").strip()
            
            # Break down multi-line or long responses into 80-char chunks so Flow Launcher shows the entire text!
            chunks = []
            for line in full_response.splitlines():
                line_str = line.strip()
                if not line_str:
                    continue
                if len(line_str) <= 80:
                    chunks.append(line_str)
                else:
                    chunks.extend(textwrap.wrap(line_str, width=80))
            
            if not chunks:
                chunks = [full_response]
                
            # If the answer is short (just 1 chunk), return a single item
            if len(chunks) == 1:
                return [
                    {
                        "Title": chunks[0],
                        "SubTitle": "Press Enter to copy full response to clipboard",
                        "IcoPath": "icon.png",
                        "JsonRPCAction": {
                            "method": "copy_to_clipboard",
                            "parameters": [full_response],
                            "dontHideAfterAction": False
                        }
                    }
                ]
            
            # For multi-line/long answers, return a header item + individual line items
            results = [
                {
                    "Title": "✨ Full Response (Press Enter to Copy All)",
                    "SubTitle": f"Length: {len(full_response)} chars across {len(chunks)} lines • Press Enter to copy complete text",
                    "IcoPath": "icon.png",
                    "JsonRPCAction": {
                        "method": "copy_to_clipboard",
                        "parameters": [full_response],
                        "dontHideAfterAction": False
                    }
                }
            ]
            
            for i, chunk in enumerate(chunks, 1):
                results.append({
                    "Title": f"💬 {chunk}",
                    "SubTitle": f"Line {i}/{len(chunks)} • Press Enter to copy complete response to clipboard",
                    "IcoPath": "icon.png",
                    "JsonRPCAction": {
                        "method": "copy_to_clipboard",
                        "parameters": [full_response],
                        "dontHideAfterAction": False
                    }
                })
                
            return results
        except Exception as e:
            return [
                {
                    "Title": "Error querying Groq API",
                    "SubTitle": str(e),
                    "IcoPath": "icon.png"
                }
            ]


    def copy_to_clipboard(self, text):
        subprocess.run(['clip'], input=text, text=True)

if __name__ == "__main__":
    AiPlugin()