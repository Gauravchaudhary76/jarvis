#!/usr/bin/env python3
"""
Hugging Face SDXL Image Generator
- Watches Frontend/Files/ImageGeneration.data for "<prompt>,True"
- Generates 4 images, saves to Data/, opens them
- Resets file to "False,False" after generation
"""

import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import load_dotenv, get_key
import os
from time import sleep
from typing import Dict, Any, Tuple, Optional

# === CONFIG ===
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
TRIGGER_FILE = os.path.join("Frontend", "Files", "ImageGeneration.data")
DATA_DIR = "Data"
POLL_INTERVAL = 1.0  # seconds

# === HELPERS ===
def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(TRIGGER_FILE), exist_ok=True)

def get_api_key() -> str:
    load_dotenv(override=False)
    key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HuggingFaceAPIKey")
    if key:
        return key.strip()
    try:
        if os.path.exists(".env"):
            key = get_key(".env", "HUGGINGFACE_API_KEY") or get_key(".env", "HuggingFaceAPIKey")
            if key:
                return key.strip()
    except Exception:
        pass
    raise RuntimeError("Hugging Face API key not found. Add it to environment or .env")

def mime_to_ext(mime: str) -> str:
    mime = (mime or "").lower()
    if "png" in mime:
        return ".png"
    if "jpeg" in mime or "jpg" in mime:
        return ".jpg"
    return ".png"

def open_images(prompt: str):
    prompt_key = prompt.replace(" ", "_")
    for i in range(1, 5):
        img_path = os.path.join(DATA_DIR, f"{prompt_key}_{i}.png")
        if not os.path.exists(img_path):
            img_path = os.path.join(DATA_DIR, f"{prompt_key}_{i}.jpg")
        try:
            img = Image.open(img_path)
            img.show()
            sleep(0.5)
        except Exception as e:
            print(f"[WARN] Cannot open {img_path}: {e}")

def post_to_hf(payload: Dict[str, Any], headers: Dict[str, str]) -> Tuple[bytes, str]:
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
    return resp.content, resp.headers.get("content-type", "")

async def query(payload: Dict[str, Any], headers: Dict[str, str]):
    return await asyncio.to_thread(post_to_hf, payload, headers)

async def generate_images(prompt: str):
    
    api_key = get_api_key()
    headers = {"Authorization": f"Bearer {api_key}"}
    prompt_key = prompt.replace(" ", "_")

    tasks = []
    for _ in range(4):
        seed = randint(0, 1_000_000)
        payload = {
            "inputs": f"{prompt}, ultra high detail, 4K, sharp focus, seed={seed}",
            "options": {"wait_for_model": True}
        }
        tasks.append(asyncio.create_task(query(payload, headers)))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    success = False

    for i, res in enumerate(results, start=1):
        if isinstance(res, Exception):
            print(f"[ERROR] Request {i} failed: {res}")
            continue

        content, mime = res
        if "application/json" in (mime or ""):
            try:
                import json
                print(f"[ERROR] HF returned error: {json.loads(content)}")
            except Exception:
                print(f"[ERROR] Non-image response: {content[:200]}")
            continue

        ext = mime_to_ext(mime)
        file_path = os.path.join(DATA_DIR, f"{prompt_key}_{i}{ext}")
        with open(file_path, "wb") as f:
            f.write(content)
        print(f"[OK] Saved {file_path}")
        success = True

    if not success:
        raise RuntimeError("All image generations failed.")

def read_trigger() -> Optional[Tuple[str, bool]]:
    try:
        with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
            data = f.read().strip()
        if "," not in data:
            return None
        prompt, status = data.split(",", 1)
        return prompt.strip(), status.strip().lower() == "true"
    except FileNotFoundError:
        with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
            f.write("False,False")
        return None

def write_trigger(text: str):
    with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
        f.write(text)

def run_watcher():
    ensure_dirs()
    print("[INFO] Watching trigger file for prompts...")

    while True:
        trig = read_trigger()
        if trig and trig[1]:  # status is True
            prompt = trig[0]
            print(f"[INFO] Generating images for: {prompt}")
            try:
                asyncio.run(generate_images(prompt))
                open_images(prompt)
                print("[INFO] Done.")
            except Exception as e:
                print(f"[ERROR] {e}")
            write_trigger("False,False")
        else:
            sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_watcher()
