# J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### Mark-IV Tactical AI Assistant with OmniRoute Multi-Provider Integration

An ultra-sophisticated, modular desktop AI assistant inspired by Tony Stark's J.A.R.V.I.S. Engineered with Python, local-first offline resilience, **OmniRoute** multi-LLM orchestration gateway, high-fidelity British neural speech synthesis, Asimov safety directives, proactive hardware telemetry, and an animated Arc-Reactor Tactical HUD.

---

## 🏛️ System Architecture

```
                                ┌─────────────────────────────────────────┐
                                │              PERCEPTION                 │
                                │  • Auditory Intake (SpeechRecognition)  │
                                │  • Multimodal Display Capture (mss/PIL) │
                                │  • Optical Webcam Inspection (OpenCV)   │
                                └────────────────────┬────────────────────┘
                                                     │
                                                     ▼
                                ┌─────────────────────────────────────────┐
                                │           SENTINEL & SAFETY             │
                                │  • Asimov Prime Directive (Zero Harm)   │
                                │  • Financial Gatekeeper (CONFIRM-TOKEN) │
                                │  • Credential Guardian (Auto-Redaction) │
                                │  • Single-Question Protocol Enforcer    │
                                └────────────────────┬────────────────────┘
                                                     │
                                                     ▼
                                ┌─────────────────────────────────────────┐
                                │            COGNITIVE MATRIX             │
                                │  • Tier 1: OmniRoute Local Gateway      │
                                │    (http://localhost:20128/v1)          │
                                │  • Tier 2: Direct Cloud LLMs            │
                                │    (Google Gemini / OpenAI GPT-4o)      │
                                │  • Tier 3: 100% Offline Local Engine    │
                                │    (Instant fallback on disconnect)     │
                                └──────────────┬──────────────────┬───────┘
                                               │                  │
                        ┌──────────────────────┘                  └──────────────────────┐
                        ▼                                                                ▼
 ┌───────────────────────────────────────────┐                    ┌───────────────────────────────────────────┐
 │                 ACTION                    │                    │                EXPRESSION                 │
 │  • Hardware Watchdog (Battery & Thermal)  │                    │  • British Neural TTS (RyanNeural)        │
 │  • Detached App Launch & Vitals Control   │                    │  • SAPI5 Zero-Downtime Voice Failover     │
 │  • Offline Schedule & Agenda (SQLite)     │                    │  • Acoustic Barge-In (Stop Speaking / Esc)│
 │  • Zero-Key Atmospheric Weather Telemetry │                    │  • Arc-Reactor Tactical Desktop HUD       │
 │  • Protocol Sunrise Executive Briefings   │                    │  • Mobile Command Web Portal (:5050)      │
 └───────────────────────────────────────────┘                    └───────────────────────────────────────────┘
```

---

## 🌐 OmniRoute AI Integration

J.A.R.V.I.S. is integrated with [**OmniRoute**](https://github.com/diegosouzapw/OmniRoute), the intelligent multi-provider LLM gateway and load balancer.

### Features of the OmniRoute Bridge:
1. **Unified Endpoint:** Routes cognitive reasoning through `http://localhost:20128/v1` via OpenAI-compatible API schemas.
2. **Zero-Cost Free Providers Cascade:** Natively pre-configured to cascade through free zero-credit models without requiring paid API tokens:
   - `ddgw/mistral-small-2603` (Fast, highly articulate British butler cadence)
   - `ddgw/gpt-5.4-mini` (High-efficiency reasoning)
   - `ddgw/gpt-5.6-luna` (Advanced synthesis)
   - `auto/best-chat` / `auto` (Self-healing free pool router)
3. **Graceful Failover:** If OmniRoute is not running or takes longer than 5.5s to respond, J.A.R.V.I.S. automatically fails over to direct cloud providers or immediately executes via the offline deterministic matrix.

### Configuration (`.env`):
```ini
# OmniRoute Gateway Settings
OMNIROUTE_PORT=20128
OMNIROUTE_BASE_URL=http://localhost:20128/v1
OMNIROUTE_API_KEY=your_omniroute_token_if_configured
OMNIROUTE_MODEL=ddgw/mistral-small-2603

# Voice Conversation & Biometric Settings
VOICE_PAUSE_THRESHOLD=2.2
VOICE_PHRASE_TIME_LIMIT=35.0
VOICE_CONVERSATION_IDLE_TIMEOUT=12.0
VOICE_VERIFICATION_ENABLED=true
VOICE_PROFILE_TOLERANCE=0.65
```

---

## 🎙️ Hands-Free Voice Conversation & Dual-Frequency Biometrics

J.A.R.V.I.S. features continuous hands-free voice dialogue with adaptive pause detection and acoustic authentication:

1. **Adaptive End-of-Speech Detection:** Configured with a `2.2s` silence timeout, allowing users to comfortably formulate thoughts, breathe, or pause mid-sentence without being interrupted.
2. **Dual-Frequency Biometric Speaker Verification:** Authenticates the authorized user across both low frequencies (65 Hz - 180 Hz chest resonance) and high frequencies (180 Hz - 450+ Hz pitch elevation & inflections), ignoring background chatter or imposter voices.
3. **100% Offline Speech-to-Text (`core/offline_stt.py`):** Operates with local Vosk Kaldi neural models cached on-device, enabling air-gapped speech recognition without internet access.
4. **Proactive Butler Autonomy (`core/proactive_agent.py`):**
   - **Spoken Agenda Reminders:** Proactively warns you 10 minutes prior to appointments (*"Pardon the interruption, sir. You have your meeting in 10 minutes"*), and at start time.
   - **Protocol Sunrise:** Automated morning wake-up executive briefing delivering daily agenda, weather, and hardware vitals at your designated time (`SUNRISE_TIME=08:00`).
   - **Hardware Health Sentinel:** Monitors for prolonged critical RAM/CPU load and discreetly suggests optimizations.
5. **Continuous Conversational Flow (`--voice`):** Keeps an interactive dialog window open (12s idle timeout) after each response, removing the need to repeat wake words on every follow-up turn.
6. **Autonomous Multi-Step Task Execution:** Leverages OmniRoute free models (`ddgw/mistral-small-2603`, `auto/best-chat`) to plan and execute complex compound directives with tools:
   - Live web search and web scraping (DuckDuckGo zero-cost APIs)
   - Real-time system vitals inspection (CPU, RAM, Disk)
   - Screen inspection & webcam vision
   - Safe workspace file creation, reading, and manipulation
   - Desktop and application launching / process control

---

## 🛡️ Core Sentinels & Safety Protocols

- **Asimov's Prime Directive (`core/asimov_guard.py`):** Strictly rejects any commands intended to inflict physical harm, sabotage infrastructure, or produce malware.
- **Financial Gatekeeper (`core/security_sentinels.py`):** Any action involving funds, purchases, credit cards, or bank transfers is halted with a mandatory two-step challenge: *"Sir, please confirm with `CONFIRM-<TOKEN>`."*
- **Credential Guardian (`core/security_sentinels.py`):** Automatically redacts API tokens, private keys, passwords, and `.env` contents from logs and speech outputs.
- **Single Question Protocol (`core/single_question.py`):** Ensures J.A.R.V.I.S. never bombards the user with multiple follow-ups, limiting clarification to at most one concise question per turn.
- **Acoustic Barge-In (`core/voice.py`):** Interrupt vocalization instantly at any point by saying *"Jarvis, stop"*, hitting `Escape`, or clicking **SILENCE** on the HUD.

---

## 📁 Repository Structure

```
c:\jarvis ai\
├── .agents/
│   ├── rules/
│   │   └── jarvis_architecture_and_safety.md  # Always-on architecture guidelines
│   └── skills/
│       └── jarvis-testing-and-debugging/       # Automated diagnostics runbook
├── assets/
│   └── ironman.ico                             # Desktop Stark Industries icon
├── core/
│   ├── asimov_guard.py                         # Asimov Prime Directive enforcer
│   ├── brain.py                                # OmniRoute & Gemini cognition matrix
│   ├── chimes.py                               # Sci-fi acoustic frequency feedback
│   ├── listener.py                             # Auditory intake & "Hey Jarvis" wake monitor
│   ├── schedule_manager.py                     # 100% offline agenda & reminder engine
│   ├── security_sentinels.py                   # Financial, credential & device sentinels
│   ├── single_question.py                      # Interactivity gatekeeper
│   ├── voice.py                                # Dual-mode British neural & SAPI5 TTS
│   └── watchdog.py                             # Proactive hardware & battery monitor
├── memory/
│   └── memory_store.py                         # Persistent SQLite episodic memory
├── tools/
│   ├── briefing_tools.py                       # Protocol Sunrise executive briefing
│   ├── camera_tools.py                         # Optical webcam inspection
│   ├── omniroute_controller.py                 # OmniRoute gateway supervisor & telemetry
│   ├── schedule_tools.py                       # Agenda NLP tool hooks
│   ├── shortcut_creator.py                     # Desktop shortcut installer
│   ├── system_controller.py                    # Detached non-blocking Windows process launcher
│   ├── system_tools.py                         # Volume, vitals, media transport, web search
│   ├── terminal_tools.py                       # Safe PowerShell and filesystem operations
│   ├── tool_registry.py                        # Autonomous function calling registry
│   ├── vision_tools.py                         # Multimodal display screen inspection
│   └── weather_tools.py                        # Zero-key atmospheric telemetry (Open-Meteo)
├── ui/
│   ├── hud.py                                  # Stark Mark-III Tactical HUD with Arc Reactor
│   └── web_portal.py                           # Mobile command web portal (Port 5050)
├── tests/
│   ├── test_agenda_and_watchdog.py             # Agenda & hardware monitoring tests
│   ├── test_asimov_and_sentinels.py            # Safety, financial gate & credentials tests
│   ├── test_offline_matrix.py                  # Full offline deterministic matrix tests
│   ├── test_vision_and_briefing.py             # Vision, camera, weather & briefing tests
│   └── ...                                     # 38 passing comprehensive unit tests
├── .env.example                                # Clean configuration template
├── .gitignore                                  # Credential and database security rules
├── config.py                                   # Global constants & path resolvers
├── main.py                                     # Master launcher (HUD or CLI)
├── requirements.txt                            # Python dependencies
└── run_jarvis.bat                              # 1-Click Windows HUD launcher
```

---

## ⚡ Directives & Voice Commands

| Domain | Spoken Trigger | Function |
| :--- | :--- | :--- |
| **Briefing** | *"Morning briefing"*, *"Protocol Sunrise"* | Complete summary of time, local weather, battery/CPU vitals & today's agenda |
| **Agenda** | *"Remind me to call Pepper at 4 PM"*, *"What's on my agenda today?"* | 100% offline schedule management in local SQLite |
| **Webcam** | *"Look through the camera"*, *"What am I holding?"* | Physical camera snapshot & visual object analysis |
| **Screen** | *"Look at my screen"*, *"What's on my display?"* | Multimodal analysis of active Windows workspace |
| **Vitals** | *"System vitals"*, *"Status report"*, *"Diagnostics"* | Live CPU load, RAM allocation, disk capacity & battery health |
| **Atmospheric**| *"What's the weather in London?"*, *"Is it raining?"* | Real-time weather telemetry without requiring third-party API keys |
| **Security** | *"Hey Jarvis, unlock my device"*, *"Lock my device"* | Authenticated workstation locking and secure access |
| **Power** | *"Lets Sleep Jarvis"*, *"Shut down"* | Verified power sentinel shutdown / sleep sequence |
| **Media/Volume**| *"Volume up"*, *"Mute"*, *"Play music"*, *"Pause"* | Hardware audio level & media transport control |
| **Apps** | *"Open Chrome"*, *"Open Notepad"*, *"Open Calculator"* | Detached Windows process launcher |
| **OmniRoute** | *"OmniRoute status"*, *"Check OmniRoute"* | Live telemetry & model metrics from OmniRoute local gateway (:20128) |

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+ (Tested up to Python 3.14)
- Windows 10/11
- Microphone & Audio Output

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/your-username/jarvis-ai.git
cd "jarvis-ai"

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env
```

### 3. Running J.A.R.V.I.S.
```powershell
# Launch Mark-III Tactical Arc-Reactor HUD
python main.py

# Launch Headless CLI Mode
python main.py --cli
```

### 4. Running Diagnostics & Tests
```powershell
# Execute complete unit test suite (38 tests)
pytest tests/ -v
```

---

## 📄 License
MIT License. Inspired by Marvel's Iron Man / J.A.R.V.I.S.
