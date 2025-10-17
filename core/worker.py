import asyncio
import httpx
import hashlib
from pathlib import Path
from core.config import WORKSPACE_ROOT
from services.file_utils import decode_attachments
from services.html_generator import generate_static_site
from services.github_service import create_and_push_repo
from services.notifier import post_with_backoff

queue: asyncio.Queue = asyncio.Queue()

async def start_worker():
    asyncio.create_task(worker_loop())

async def worker_loop():
    async with httpx.AsyncClient() as client:
        while True:
            req = await queue.get()
            try:
                await process_task(req, client)
            except Exception as e:
                print("Error processing:", e)
            finally:
                queue.task_done()

async def process_task(req: dict, client: httpx.AsyncClient):
        
    try:
        task_id, nonce = req["task"], req["nonce"]
        round_num = int(req.get("round", 1))

        # ✅ Deterministic repo naming (no random hash)
        repo_name = f"{task_id}".replace(" ", "-").lower()
        folder = WORKSPACE_ROOT / repo_name
        folder.mkdir(exist_ok=True)

        # Decode attachments if any
        files = await decode_attachments(req.get("attachments", []), folder, client)
        fallback_img = files[0] if files else ""

        # Generate HTML/JS for the task
        generate_static_site(folder, req["task"], req.get("brief", ""), fallback_img, round_no=round_num)

        # ✅ Create repo and push to GitHub
        print(f"[GitHub] Starting push for repo: {repo_name}")
        result = await create_and_push_repo(client, repo_name, folder)

        if not result or not isinstance(result, tuple):
            print("[Error] GitHub push failed or returned no result.")
            commit_sha, pages_url = None, None
        else:
            commit_sha, pages_url = result

        # ✅ Send result to evaluation server
        payload = {
            "email": req["email"],
            "task": task_id,
            "round": round_num,
            "nonce": nonce,
            "repo_url": f"https://github.com/{req.get('GITHUB_OWNER')}/{repo_name}",
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }

        # Post results back with retries
        await post_with_backoff(req["evaluation_url"], payload, client)
        print("[System] Task processed successfully.")

    except Exception as e:
        print(f"[Fatal Error] Exception while processing task: {e}")