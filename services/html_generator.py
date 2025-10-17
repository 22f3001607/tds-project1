from pathlib import Path
import os
import re
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_static_site(folder: Path, task: str, brief: str, fallback_img: str, round_no: int = 1):
    """
    Generates or updates a single self-contained index.html file with inline <script>.
    Round 1 → fresh HTML.
    Round 2+ → updates existing content based on the brief.
    """

    html_path = folder / "index.html"
    readme_path = folder / "README.md"

    try:
        # 1️⃣ Load existing HTML
        existing_html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""

        # 2️⃣ Build the prompt
        print(f"[AI] Generating HTML for: {task} (Round {round_no})")

        system_prompt = (
            "You are an expert front-end developer. "
            "Generate a complete, self-contained HTML5 file that runs offline. "
            "All JavaScript must be in ONE <script> tag inside <body>. "
            "All CSS must be in ONE <style> tag inside <head>. "
            "No external dependencies, no CDNs, no imports. "
            "Output ONLY the complete HTML file - no markdown, no code fences, no explanations."
        )

        if round_no == 1:
            user_prompt = f"""
Create a complete HTML file for this project:

Title: {task}
Requirements: {brief}

CRITICAL RULES:
- Output ONLY raw HTML (no ```html or ``` markers)
- Include <!DOCTYPE html> declaration
- All CSS in <style> tag in <head>
- All JavaScript in <script> tag at end of <body>
- Make it functional and visually appealing
- No external resources (CDNs, imports, etc.)
"""
        else:
            user_prompt = f"""
Update the existing HTML file based on new requirements:

Title: {task}
New Requirements: {brief}

EXISTING HTML:
{existing_html}

CRITICAL RULES:
- Output ONLY the COMPLETE updated HTML file (no ```html or ``` markers)
- Keep ALL existing functionality unless the brief explicitly asks to remove it
- Add/modify features as requested in the brief
- Maintain the same structure (CSS in <head>, JS in <body>)
- Ensure backward compatibility where possible
- No external resources (CDNs, imports, etc.)
"""

        # 3️⃣ Call OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=4000,
            temperature=0.7,
        )
        
        ai_output = response.choices[0].message.content.strip()

        if not ai_output:
            raise ValueError("AI returned empty HTML output")

        # 4️⃣ Clean output - remove code fences and extra whitespace
        ai_output = re.sub(r'^```(?:html|javascript|js)?\s*\n?', '', ai_output, flags=re.IGNORECASE)
        ai_output = re.sub(r'\n?```\s*$', '', ai_output)
        ai_output = ai_output.strip()

        # 5️⃣ Validate HTML structure
        if not re.search(r'<!DOCTYPE html>|<html', ai_output, re.IGNORECASE):
            raise ValueError("AI output is not valid HTML")

        # 6️⃣ Write HTML file
        html_path.write_text(ai_output, encoding="utf-8")

        # 7️⃣ Generate proper README
        readme_content = generate_readme(task, brief, round_no, ai_output)
        readme_path.write_text(readme_content, encoding="utf-8")

        print("[✅] HTML and README generated successfully.")
        print(f"    HTML size: {len(ai_output)} chars")
        print(f"    README size: {len(readme_content)} chars")

    except Exception as e:
        print(f"[❌] Error during generation: {e}")
        # Fallback HTML
        fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{task}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; }}
        img {{ max-width: 100%; height: auto; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{task}</h1>
        <p>{brief}</p>
        <img src="{fallback_img}" alt="Placeholder" />
    </div>
    <script>
        console.log('Fallback mode - AI generation failed');
    </script>
</body>
</html>"""
        html_path.write_text(fallback_html, encoding="utf-8")
        
        fallback_readme = generate_readme(task, brief, round_no, fallback_html, is_fallback=True)
        readme_path.write_text(fallback_readme, encoding="utf-8")


def generate_readme(task: str, brief: str, round_no: int, html_content: str, is_fallback: bool = False) -> str:
    """
    Generates a comprehensive README.md file.
    """
    
    # Extract some info from HTML
    has_js = '<script>' in html_content
    has_css = '<style>' in html_content
    js_lines = len(re.findall(r'\n', re.search(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL).group(1))) if has_js else 0
    
    readme = f"""# {task}

## Overview
{brief}

**Round:** {round_no}  
**Status:** {"⚠️ Fallback Mode (AI generation failed)" if is_fallback else "✅ Successfully Generated"}

## Features
"""
    
    if round_no == 1:
        readme += f"""- Initial implementation of {task}
- Self-contained HTML file with inline CSS and JavaScript
- No external dependencies
"""
    else:
        readme += f"""- Enhanced version with updates from Round {round_no}
- Maintains backward compatibility with previous functionality
- New features as per requirements: {brief[:100]}...
"""

    readme += f"""
## Technical Details
- **HTML5** with semantic markup
- **Inline CSS** for styling (~{html_content.count('style') * 50} lines estimated)
- **Vanilla JavaScript** for functionality (~{js_lines} lines)
- **No external dependencies** - runs completely offline

## Setup & Usage

### Local Development
1. Clone this repository
2. Open `index.html` in any modern web browser
3. No build process or server required

### GitHub Pages Deployment
This project is automatically deployed via GitHub Pages and accessible at the repository's GitHub Pages URL.

## Code Structure

```
.
├── index.html          # Complete application (HTML + CSS + JS)
├── README.md          # This file
└── LICENSE            # MIT License
```

### HTML Structure
- **DOCTYPE & Meta Tags**: Proper HTML5 structure with UTF-8 encoding
- **Head Section**: Contains all CSS in a single `<style>` tag
- **Body Section**: Contains all HTML markup and JavaScript in a single `<script>` tag

### JavaScript Implementation
The application uses vanilla JavaScript for all interactivity:
"""

    # Try to extract function names from JS
    if has_js:
        js_content = re.search(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL).group(1)
        functions = re.findall(r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', js_content)
        if functions:
            readme += "\n**Key Functions:**\n"
            for func in functions[:5]:  # Limit to first 5
                readme += f"- `{func}()`: Core functionality handler\n"
        
        # Check for event listeners
        if 'addEventListener' in js_content:
            readme += "\n**Event Handling:**\n- Interactive elements with event listeners\n"
        if 'fetch' in js_content or 'XMLHttpRequest' in js_content:
            readme += "- API integration for external data\n"

    readme += f"""
## Browser Compatibility
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Opera (latest)

## Development Notes

### Round {round_no} Changes
{brief}

### Future Improvements
- Further feature enhancements based on user feedback
- Performance optimizations
- Additional browser compatibility testing

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Generated
- **Round:** {round_no}
- **Generated:** Automatically via AI
- **File Size:** {len(html_content)} bytes
"""

    return readme