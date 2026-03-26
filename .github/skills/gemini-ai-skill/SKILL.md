---
name: gemini-ai-skill
description: This skill covers all AI generation capabilities available through the `google-genai` Python SDK, including text, image, and video generation. Use it for any task involving Google AI generation tasks, and refer to the specific documentation files for detailed instructions on each type of generation.
---

# Instructions

This skill covers all AI generation capabilities available through the `google-genai` Python SDK. Read the appropriate documentation file based on the task.

---

## Prerequisite — API Key Check (Do This First)

Before executing any task from this skill, you **must** verify the Gemini API key is available:

1. Look for a `.env` file (or `.env.example` if `.env` does not exist) in the project root.
2. Check that the following variable is defined and has a non-empty value:

   ```
   GOOGLE_API_KEY=<your-gemini-api-key>
   ```

3. **If the key is missing or empty, STOP immediately.** Do not proceed with any code generation. Instead, ask the user:

   > "I need a Gemini API key to continue. Please add `GOOGLE_API_KEY` to your `.env` file (you can get one from https://aistudio.google.com/apikey). Once it's set, let me know and I'll continue."

4. Once the key is confirmed present, **always** load it from the environment — never hardcode it:

   ```python
   import os
   from google import genai

   client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
   ```

   If the project uses `python-dotenv`, load the `.env` file first:

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

> **Never** pass a raw API key string in code. The key must come from an environment variable loaded at runtime. This applies to all code examples in GEMINI_DOCS.md, BANANA.md, and VEO_DOCS.md — override any hardcoded `"YOUR_API_KEY"` placeholders with `os.environ["GOOGLE_API_KEY"]`.

---

## Documentation Files

### 1. GEMINI_DOCS.md — Core Gemini 3 API

**Read this for**: text generation, chat, streaming, structured JSON outputs, function calling (single/parallel/sequential), multimodal function responses, thinking levels, thought signatures, media resolution, code execution, computer use, Google Search grounding, OpenAI compatibility, error handling, cost optimization, and migration from Gemini 2.5.

**Models covered**: `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, `gemini-3.1-flash-lite-preview`

**Location**: [.github/skills/gemini-skill/GEMINI_DOCS.md](.github/skills/gemini-skill/GEMINI_DOCS.md)

---

### 2. BANANA.md — Nano Banana Image Generation API

**Read this for**: text-to-image generation, image-to-image editing, multi-turn conversational image editing, aspect ratio and resolution control (512/1K/2K/4K), multiple reference images for character consistency, Google Search grounding for images, Google Image Search grounding (Flash only), thinking level control for image models, image-only output mode, sequential art and comic panels, thought signatures for image workflows, batch image generation, and prompt writing techniques for image generation.

**Models covered**: `gemini-3.1-flash-image-preview` (Nano Banana 2), `gemini-3-pro-image-preview` (Nano Banana Pro), `gemini-2.5-flash-image` (Nano Banana)

**Location**: [.github/skills/gemini-skill/BANANA.md](.github/skills/gemini-skill/BANANA.md)

---

### 3. VEO_DOCS.md — Veo Video Generation API

**Read this for**: text-to-video generation, image-to-video animation, video extension (up to 148s), frame interpolation (first/last frame), reference images for video, resolution control (720p/1080p/4K), aspect ratio (16:9/9:16), native audio generation (dialogue, SFX, ambient), asynchronous operation polling, and prompt writing techniques for video generation.

**Models covered**: `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3-generate`, `veo-2-generate`

**Location**: [.github/skills/gemini-skill/VEO_DOCS.md](.github/skills/gemini-skill/VEO_DOCS.md)

---

## Quick Decision Guide

| Task | Read |
|------|------|
| Generate or analyze text | GEMINI_DOCS.md |
| Chat, multi-turn conversation | GEMINI_DOCS.md |
| Structured JSON output | GEMINI_DOCS.md |
| Function calling / tool use | GEMINI_DOCS.md |
| Analyze images, PDFs, or video | GEMINI_DOCS.md |
| Code execution in sandbox | GEMINI_DOCS.md |
| Google Search grounding (text) | GEMINI_DOCS.md |
| Generate or edit images | BANANA.md |
| Character consistency in images | BANANA.md |
| Image Search grounding | BANANA.md |
| Generate video from text | VEO_DOCS.md |
| Animate an image into video | VEO_DOCS.md |
| Extend or interpolate video | VEO_DOCS.md |
| Video with dialogue/audio | VEO_DOCS.md |
