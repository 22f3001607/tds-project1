# tds-project1

# 🧠 AI Static Site Generator

An intelligent, automated static site generator that uses OpenAI’s API to build and iteratively improve self-contained web apps.  
It creates a single `index.html` file with all functionality embedded (HTML + JS + CSS) — no external dependencies required.

---

## 🚀 Overview

This project allows you to describe any web task or feature in plain English, and the system will automatically generate or update a fully working HTML file.

- **Round 1:** Creates a fresh, offline-ready `index.html` based on your brief.  
- **Round 2+:** Intelligently updates existing functionality and merges new code without overwriting or breaking old features.  
- Each generation is logged and saved, ensuring versioned progress via `README.md` in each task folder.

It’s ideal for quickly prototyping small tools, demos, and visual interfaces — all in a single portable file.

---

## 🧩 Key Features

✅ **Self-contained HTML output** – one file, no assets or external scripts.  
✅ **Smart multi-round evolution** – the model updates existing projects while preserving previous functionality.  
✅ **Automatic JS merging** – detects and merges new functions, avoiding duplicates.  
✅ **HTML structure management** – merges or replaces body sections intelligently.  
✅ **Traceable rounds** – every generation is logged in a `README.md` inside the output folder.  
✅ **Offline-ready fallback mode** – generates a functional default template if AI generation fails.

---

## ⚙️ How It Works

1. The script calls OpenAI’s `gpt-4o-mini` model with your task and brief.
2. The model generates a complete HTML5 document with inline JavaScript.
3. For later rounds, it:
   - Loads the existing `index.html`
   - Extracts previous JavaScript
   - Merges new logic and UI components
   - Writes a final, unified `index.html`
4. A `README.md` is automatically generated to document the process.

---

## 🧰 Folder Structure

project-root/
├── core/
│ └── config.py # Contains global config (e.g., GitHub owner, API keys)
├── outputs/
│ └── <task-name>/ # Each generated project folder
│ ├── index.html # Generated HTML file (self-contained)
│ └── README.md # Log of task brief, round info, and AI output summary
├── generate_static_site.py # Main script (core logic)
└── requirements.txt # Dependencies


---

## 🖥️ Usage

1. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your_api_key_here"

2. **Run the generator:**
   ```python
   from pathlib import Path
   from generate_static_site import generate_static_site

   generate_static_site(
        folder=Path("outputs/my_project"),
        task="Interactive Calculator",
        brief="A web-based calculator that supports basic operations and keyboard input.",
        fallback_img="fallback.png",
        round_no=1
   )

3. **Iterate with Round 2+:**
   ```python
   generate_static_site(
      folder=Path("outputs/my_project"),
      task="Interactive Calculator",
      brief="Add a dark mode toggle and memory feature.",
      fallback_img="fallback.png",
      round_no=2
    )

## 🧾 Output Example

After running the generator, your folder will contain:
outputs/my_project/
├── index.html   # Fully working web app
└── README.md    # Contains task brief, AI output, and summary

The resulting HTML file runs fully offline — simply open it in any browser.

## 💡 Notes & Best Practices

- Keep your briefs descriptive — short instructions like “Add button” may not give meaningful output.
- Always check the generated HTML before deploying it publicly.
- If a round fails, the fallback template ensures a valid HTML structure is written.

## 🧱 Tech Stack

- Language: Python 3.10+
- AI Model: OpenAI GPT-4o-mini

- Libraries:
    - openai
    - pathlib, re, os

## 📜 License

MIT License © 2025 — You’re free to use, modify, and distribute this code.
