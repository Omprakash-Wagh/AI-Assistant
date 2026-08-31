import sys
import os
import subprocess
import textwrap
import json

# Point Python to our bundled 'lib' folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from flowlauncher import FlowLauncher, FlowLauncherAPI
import keyring

class AiPlugin(FlowLauncher):

    @property
    def concise_mode(self) -> bool:
        req = getattr(self, "rpc_request", {})
        if isinstance(req, dict):
            rpc_settings = req.get("settings", {})
            if isinstance(rpc_settings, dict):
                return str(rpc_settings.get("concise_mode", "true")).lower() == "true"
        return True

    @property
    def action_keyword(self) -> str:
        req = getattr(self, "rpc_request", {})
        if isinstance(req, dict):
            ak = req.get("actionKeyword") or req.get("ActionKeyword")
            if ak:
                return str(ak)
        # Fallback in case Flow Launcher doesn't provide it
        return "ai"

    def query(self, param: str = '') -> list:
        query = param.strip()
        
        # Detect if user is entering a Groq API key
        if query.startswith("gsk_"):
            try:
                keyring.set_password("flow-groq", "api_key", query)
                return [
                    {
                        "Title": "API Key Saved Successfully!",
                        "SubTitle": f"Your Groq API Key has been securely stored. You can now use the '{self.action_keyword}' command.",
                        "IcoPath": "icon.png"
                    }
                ]
            except Exception as e:
                return [
                    {
                        "Title": "Failed to save API Key",
                        "SubTitle": str(e),
                        "IcoPath": "icon.png"
                    }
                ]

        # 2. Retrieve the API key from keyring
        api_key = keyring.get_password("flow-groq", "api_key")

        # 3. Guardrail: Tell the user if they forgot to enter their key
        if not api_key:
            return [
                {
                    "Title": "API Key is missing",
                    "SubTitle": "Please paste your Groq API Key (gsk_...) right here to save it securely.",
                    "IcoPath": "icon.png"
                }
            ]

        if not query:
            return [
                {
                    "Title": "Type a prompt for your Ai Assistant",
                    "SubTitle": f"Example: '{self.action_keyword} explain quantum computing in one sentence'",
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
                    "SubTitle": f"Example: '{self.action_keyword} explain quantum computing in one sentence'",
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
        
        FlowLauncherAPI.change_query(f"{self.action_keyword} > {query}", requery=True)
        return []

    def execute_groq_query(self, api_key: str, query: str) -> list:
        try:
            import urllib.request
            import urllib.error
            import json
            
            # Check if user enabled Concise Mode in settings
            messages = []
            if self.concise_mode:
                messages.append({
                    "role": "system",
                    "content": "You are a direct, concise AI assistant inside a desktop launcher. Provide clear, short answers without conversational filler or introductions. Use bullet points if listing multiple items."
                })
            messages.append({"role": "user", "content": query})
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            data = json.dumps({
                "model": "groq/compound-mini",
                "messages": messages
            }).encode("utf-8")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "FlowLauncher-AiAssistant/1.0"
            }
            
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            
            try:
                with urllib.request.urlopen(req) as response:
                    response_body = response.read().decode("utf-8")
                    result_json = json.loads(response_body)
                    full_response = (result_json["choices"][0]["message"]["content"] or "").strip()
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                raise Exception(f"HTTP {e.code}: {error_body}")
            
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
            import traceback
            try:
                with open(os.path.join(os.path.dirname(__file__), "error.log"), "w", encoding="utf-8") as f:
                    f.write(traceback.format_exc())
            except:
                pass
            return [
                {
                    "Title": "Error",
                    "SubTitle": str(e),
                    "IcoPath": "icon.png"
                }
            ]


    def copy_to_clipboard(self, text):
        subprocess.run(['clip'], input=text, text=True)

if __name__ == "__main__":
    AiPlugin()