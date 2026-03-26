```skill
---
name: openai-responses-skill
description: This skill covers all capabilities available through the OpenAI Responses API and related endpoints, including text generation, image generation/editing, vision, structured outputs, speech-to-text, and text-to-speech. Use it for any task involving OpenAI API generation tasks, and refer to the specific documentation files for detailed instructions on each capability.
---

# Instructions

This skill covers all generation capabilities available through the OpenAI Python SDK (`openai`). Read the appropriate documentation file based on the task.

---

## Prerequisite — API Key Check (Do This First)

Before executing any task from this skill, you **must** verify the OpenAI API key is available:

1. Look for a `.env` file (or `.env.example` if `.env` does not exist) in the project root.
2. Check that the following variable is defined and has a non-empty value:

   ```
   OPENAI_API_KEY=<your-openai-api-key>
   ```

3. **If the key is missing or empty, STOP immediately.** Do not proceed with any code generation. Instead, ask the user:

   > "I need an OpenAI API key to continue. Please add `OPENAI_API_KEY` to your `.env` file (you can get one from https://platform.openai.com/api-keys). Once it's set, let me know and I'll continue."

4. Once the key is confirmed present, **always** load it from the environment — never hardcode it:

   ```python
   import os
   from openai import OpenAI

   client = OpenAI()  # reads OPENAI_API_KEY from env automatically
   ```

   If the project uses `python-dotenv`, load the `.env` file first:

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

> **Never** pass a raw API key string in code. The key must come from an environment variable loaded at runtime. This applies to all code examples in the documentation files — override any hardcoded key placeholders with `os.environ["OPENAI_API_KEY"]` or rely on the SDK's automatic env loading.

---

## Documentation Files

### 1. RESPONSES_DOCS.md — Core Responses API & Structured Outputs

**Read this for**: text generation, prompt engineering, message roles (`developer` / `user` / `assistant`), `instructions` parameter, reusable prompts with variables, structured outputs with Pydantic / JSON Schema, `responses.parse()`, JSON mode, streaming text, refusals, chain-of-thought, recursive schemas, supported schema constraints, and best practices.

**Models covered**: `gpt-5.4`, `gpt-5`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4o`, `gpt-4o-mini`

**Location**: [documentation/RESPONSES_DOCS.md](documentation/RESPONSES_DOCS.md)

---

### 2. IMAGE_DOCS.md — Image Generation, Editing & Vision

**Read this for**: image generation via Responses API and Image API, multi-turn image editing, `action` parameter (`generate` / `edit` / `auto`), inpainting with masks, input fidelity control, transparency, streaming partial images, revised prompts, image analysis (vision), detail levels (`low` / `high` / `original`), cost calculation (patch-based and tile-based tokenization), output customization (size, quality, format, compression), and content moderation.

**Models covered**: `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini`, `gpt-5.4`, `gpt-5`, `gpt-4.1`, `gpt-4o`

**Location**: [documentation/IMAGE_DOCS.md](documentation/IMAGE_DOCS.md)

---

### 3. AUDIO_DOCS.md — Speech-to-Text & Text-to-Speech

**Read this for**: audio transcription, translation, speaker diarization, streaming transcriptions, Realtime API transcription, timestamps, prompting for transcription quality, text-to-speech generation, built-in and custom voices, voice instructions/prompting, streaming audio output, output formats (MP3/Opus/WAV/PCM/AAC/FLAC), and custom voice creation with consent.

**Models covered**: `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe-diarize`, `whisper-1`, `gpt-4o-mini-tts`, `tts-1`, `tts-1-hd`

**Location**: [documentation/AUDIO_DOCS.md](documentation/AUDIO_DOCS.md)

---

## Quick Decision Guide

| Task | Read |
|------|------|
| Generate text from a prompt | RESPONSES_DOCS.md |
| Chat / multi-turn conversation | RESPONSES_DOCS.md |
| Use message roles (`developer`, `user`) | RESPONSES_DOCS.md |
| Reusable prompt templates | RESPONSES_DOCS.md |
| Structured JSON output (Pydantic) | RESPONSES_DOCS.md |
| JSON mode | RESPONSES_DOCS.md |
| Streaming text responses | RESPONSES_DOCS.md |
| Generate images from text | IMAGE_DOCS.md |
| Edit images / inpainting with masks | IMAGE_DOCS.md |
| Multi-turn image editing | IMAGE_DOCS.md |
| Analyze / understand images (vision) | IMAGE_DOCS.md |
| Transparent backgrounds | IMAGE_DOCS.md |
| Stream partial images | IMAGE_DOCS.md |
| Transcribe audio to text | AUDIO_DOCS.md |
| Translate audio to English | AUDIO_DOCS.md |
| Speaker diarization | AUDIO_DOCS.md |
| Stream transcriptions | AUDIO_DOCS.md |
| Text-to-speech generation | AUDIO_DOCS.md |
| Custom voice creation | AUDIO_DOCS.md |
| Realtime audio streaming | AUDIO_DOCS.md |

```
