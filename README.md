# 🤖 AI Assistant for Flow Launcher

An ultra-fast, intelligent AI assistant inside [Flow Launcher](https://github.com/Flow-Launcher/Flow.Launcher), powered by **Groq API** and the cutting-edge **Llama 3.3 70B Versatile** model. Ask questions, generate code snippets, and get answers in milliseconds without ever leaving your keyboard or opening a browser!

---

## ✨ Features

- ⚡ **Blazing Fast Responses**: Leverages Groq's LPU™ Inference Engine for near-instantaneous AI answers directly on your desktop.
- 🎯 **Native Desktop Integration**: Trigger queries anytime using the simple `ai` keyword in Flow Launcher.
- 🧠 **Concise Mode (Recommended)**: Specially engineered prompt formatting that keeps responses direct, punchy, and structured (using bullet points) so they fit cleanly inside Flow Launcher without visual clutter.
- 📋 **Smart Multi-Line Chunking**: Automatically breaks down long or multi-line answers into readable 80-character rows. 
- 🚀 **One-Click Clipboard Copy**: Press **Enter** on any result line (or on the main header) to instantly copy the complete text response to your clipboard.
- 🔒 **Secure & Persistent Storage**: Your Groq API key is saved securely in Flow Launcher's local plugin settings with atomic disk syncing—ensuring your settings survive system restarts and shutdowns.

---

## 📦 Installation

### Option 1: Via Flow Launcher Plugin Store (Recommended)
Open Flow Launcher and type:
```bash
pm install Ai Assistant
```

### Option 2: Manual Git Installation
1. Clone this repository into your Flow Launcher user plugins directory:
   ```powershell
   git clone https://github.com/Omprakash-Wagh/flow-groq.git "%APPDATA%\FlowLauncher\Plugins\Ai Assistant"
   ```
2. Restart Flow Launcher or type `reload_plugins` in the launcher.

---

## ⚙️ Configuration & Setup

1. **Get a Free Groq API Key**:
   - Visit the [Groq Cloud Console](https://console.groq.com/keys).
   - Create an account (free tier available) and generate a new API key (`gsk_...`).

2. **Configure the Plugin**:
   - Open Flow Launcher settings (`Alt + Space` ➔ type `settings` ➔ press Enter).
   - Navigate to **Plugins** ➔ **Ai Assistant**.
   - Paste your API key into the **Groq API Key** password box.
   - Verify that **Concise Mode (Recommended)** is enabled for optimal desktop formatting.

---

## 🚀 Usage

Trigger the assistant by typing `ai` followed by your prompt:

| Command Example | Description |
| :--- | :--- |
| `ai what is the capital of France?` | Returns a direct answer in milliseconds. Press **Enter** to copy! |
| `ai write a git command to undo last commit` | Returns clean, copy-ready terminal commands without conversation filler. |
| `ai summarize quantum computing in 3 bullets` | Generates a structured multi-line list. Press **Enter** on any line to copy the whole response. |

### Tip: Copying Long Responses
When a response spans multiple lines, Flow Launcher displays:
- ✨ **Full Response Header**: Shows total length and number of lines. Pressing Enter copies everything.
- 💬 **Individual Chunks**: Line-by-line breakdown for scannability. Pressing Enter on any chunk also copies the complete answer to your clipboard!

---

## 🛠️ Technology Stack

- **Language**: Python 3
- **AI SDK**: Official `groq` Python library
- **Model**: `llama-3.3-70b-versatile`
- **Integration**: `flowlauncher` API library

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [repository issues](https://github.com/Omprakash-Wagh/flow-groq/issues) page.
