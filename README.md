# JARVIS-GUI

JARVIS-GUI is a personal AI assistant featuring a custom desktop interface and an integrated voice engine. It connects directly to the Gemini API to provide fast, intelligent, and interactive responses.

---

## Features
* **Smart Chatting**: Get instant answers, brainstorming help, or coding assistance from a powerful AI.
* **Voice Engine**: Listen to responses out loud instead of just reading them.
* **Custom GUI**: Chat through a clean, modern, and simple desktop window.
* **Secure Setup**: Keeps your personal API keys safe and hidden.

---

## How to Install and Run

### 1. Download the Code
Clone this repository to your computer:
git clone https://github.com/anarbaynurislam/JARVIS-GUI.git
Go into the project folder:
cd JARVIS-GUI

### 2. Install Libraries
Install all required libraries using the terminal:
pip install -r requirements.txt

### 3. Add Your API Key
1. Copy the `.env.example` file and rename it to `.env`.
2. Open the `.env` file and insert your personal Gemini API key:
GEMINI_API_KEY=your_actual_api_key_here

### 4. Start JARVIS
Launch the assistant by running the main interface:
python main_gui.py
