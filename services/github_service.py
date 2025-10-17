import httpx
from git import Repo
from pathlib import Path
import time
import subprocess
import asyncio
import re
import os
from core.config import GITHUB_TOKEN, GITHUB_OWNER
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def create_and_push_repo(client: httpx.AsyncClient, repo_name: str, folder: Path, brief: str = ""):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Check if repo exists
    repo_check = await client.get(f"https://api.github.com/repos/{GITHUB_OWNER}/{repo_name}", headers=headers)
    repo_exists = repo_check.status_code == 200

    # Step 1 & 2: Create repo if missing
    if not repo_exists:
        print(f"[GitHub] Creating repo: {repo_name}")
        r = await client.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json={
                "name": repo_name,
                "private": False,
                "auto_init": False,
                "description": f"Auto-generated project for task '{brief}'",
                "license_template": "mit"
            },
        )
        if r.status_code not in (201, 422):
            print("Repo creation failed:", r.status_code, await r.text())
        else:
            print("[GitHub] Repo created successfully.")
    else:
        print(f"[GitHub] Repo '{repo_name}' already exists — reusing it for update.")

    # Step 3: Initialize and push
    repo = Repo.init(folder)
    repo.git.add(all=True)
    repo.index.commit("Auto update from round")
    repo.git.branch("-M", "main")

    remote_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_OWNER}/{repo_name}.git"
    if "origin" in [r.name for r in repo.remotes]:
        repo.delete_remote("origin")
    repo.create_remote("origin", remote_url)
    repo.git.push("--set-upstream", "origin", "main", force=True)
    print("[GitHub] Code pushed to main branch.")

    # Step 4: Ensure MIT LICENSE
    license_path = folder / "LICENSE"
    if not license_path.exists():
        license_path.write_text(
            "MIT License\n\nCopyright (c) "
            + time.strftime("%Y")
            + f" {GITHUB_OWNER}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy "
              "of this software and associated documentation files (the 'Software'), to deal in the Software "
              "without restriction, including without limitation the rights to use, copy, modify, merge, publish, "
              "distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the "
              "Software is furnished to do so, subject to the following conditions:\n\n"
              "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED."
        )
        repo.git.add("LICENSE")
        repo.index.commit("Add MIT License")
        repo.git.push("origin", "main")
        print("[GitHub] MIT LICENSE added.")
    
    # Step 5.5: Generate or update README.md
    print("[GitHub] Generating/updating README.md...")
    readme_path = folder / "README.md"
    existing_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

    readme_content = ""

    try:
        system_prompt = (
            "You are an expert open-source documentation writer. "
            "Write a concise but complete README.md for a GitHub repository. "
            "It should include: a summary, setup instructions, usage guide, short code explanation, and license notice. "
            "Use clean Markdown. Keep it professional and easy to read."
        )

        user_prompt = f"""
    Repository name: {repo_name}
    Project description or brief: {brief or '(No description provided)'}
    License: MIT

    Existing README content:
    {existing_readme or '(No existing README)'}

    New instructions/updates (round 2 changes):
    {brief}

    Update the README.md to reflect the new requirements,
    preserving existing content where appropriate.
    """

        # Call GPT safely
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=1200,
        )

        readme_content = (response.output_text or "").strip()

        # Remove accidental code fences
        readme_content = re.sub(r"```(markdown)?", "", readme_content).strip("` \n")

        # Fallback if GPT gives nothing
        if not readme_content:
            raise ValueError("Empty README response")

    except Exception as e:
        print("[GitHub] README generation failed, using fallback:", e)
        if not existing_readme:
            readme_content = f"""# {repo_name}

## Overview
This repository contains the project **{repo_name}**, automatically generated and deployed via the AI web app pipeline.

## Setup
No special installation is required. Simply open `index.html` in a web browser to view the project.

## Usage
You can modify the HTML and JavaScript directly to customize this app.  
The project runs entirely client-side (no backend required).

## Code Explanation
- The app was generated based on a user-defined brief.
- It includes a single `index.html` file with embedded JavaScript for interactivity.
- GitHub Pages hosts the live version.

## License
This project is licensed under the MIT License.
"""
    else:
        # Preserve existing README if fallback triggered
        readme_content = existing_readme

    # ✅ Write the README file safely
    readme_path.write_text(readme_content, encoding="utf-8")
    print("[GitHub] README.md added/updated successfully.")



    # Step 6: Enable GitHub Pages

    print("[GitHub] Enabling GitHub Pages...")
    pages_endpoint = f"https://api.github.com/repos/{GITHUB_OWNER}/{repo_name}/pages"
    enable_payload = {
        "source": {"branch": "main", "path": "/"},
        "build_type": "legacy"  # required for static HTML
    }
    resp = await client.post(pages_endpoint, headers=headers, json=enable_payload)
    if resp.status_code not in (201, 204, 409):
        print("[GitHub] Failed to enable Pages:", resp.status_code, await resp.text())
    
    pages_url = f"https://{GITHUB_OWNER}.github.io/{repo_name}/"

    # Step 7: Wait for Pages to go live
    print("[GitHub] Waiting for GitHub Pages to become reachable...")

    await asyncio.sleep(10)  # give GitHub some time to start deployment

    for attempt in range(12):  # total ~120s
        try:
            resp = await client.get(pages_url, timeout=10)
            if resp.status_code == 200:
                print(f"[GitHub] GitHub Pages is live at {pages_url}.")
                break
            else:
                print(f"[GitHub] Attempt {attempt+1}: {resp.status_code} — not live yet.")
        except Exception as e:
            print(f"[GitHub] Attempt {attempt+1} failed: {e}")
        await asyncio.sleep(10)
    else:
        print("[Warning] GitHub Pages did not respond with 200 OK after retries.")


    # Step 8: Scan for secrets (optional if installed)
    try:
        subprocess.run(["trufflehog", "filesystem", str(folder)], check=False)
        subprocess.run(["gitleaks", "detect", "--source", str(folder)], check=False)
        print("[Security] Secret scan completed.")
    except FileNotFoundError:
        print("[Security] Skipped secret scan (trufflehog/gitleaks not installed).")

    # ✅ Return results after all steps
    sha = repo.head.commit.hexsha
    print(f"[GitHub] Returning commit SHA: {sha}")
    return sha, pages_url
