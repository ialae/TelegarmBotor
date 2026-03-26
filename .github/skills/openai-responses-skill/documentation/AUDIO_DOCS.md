# OpenAI Audio — Speech-to-Text & Text-to-Speech

## Table of Contents
1. [Overview](#overview)
2. [Speech-to-Text Models](#speech-to-text-models)
3. [Transcriptions](#transcriptions)
4. [Speaker Diarization](#speaker-diarization)
5. [Translations](#translations)
6. [Timestamps](#timestamps)
7. [Streaming Transcriptions](#streaming-transcriptions)
8. [Realtime API Transcription](#realtime-api-transcription)
9. [Prompting for Transcription Quality](#prompting-for-transcription-quality)
10. [Longer Inputs](#longer-inputs)
11. [Text-to-Speech](#text-to-speech)
12. [Voice Options](#voice-options)
13. [Custom Voices](#custom-voices)
14. [Streaming Audio Output](#streaming-audio-output)
15. [Output Formats](#output-formats)
16. [Supported Languages](#supported-languages)

---

## Overview

The OpenAI Audio API provides:

- **Speech-to-Text** — Transcribe and translate audio via `transcriptions` and `translations` endpoints
- **Text-to-Speech** — Generate lifelike spoken audio from text via the `speech` endpoint

### Input Requirements

| Requirement | Details |
|-------------|---------|
| Max file size | 25 MB |
| Supported formats | `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `wav`, `webm` |

---

## Speech-to-Text Models

| Model | Output Formats | Features |
|-------|---------------|----------|
| `gpt-4o-transcribe` | `json`, `text` | Prompts, logprobs, streaming |
| `gpt-4o-mini-transcribe` | `json`, `text` | Prompts, logprobs, streaming |
| `gpt-4o-transcribe-diarize` | `json`, `text`, `diarized_json` | Speaker labels, chunking strategy |
| `whisper-1` | `json`, `text`, `srt`, `verbose_json`, `vtt` | Timestamps, translations |

---

## Transcriptions

### Basic Transcription

```python
from openai import OpenAI

client = OpenAI()
audio_file = open("/path/to/file/audio.mp3", "rb")

transcription = client.audio.transcriptions.create(
    model="gpt-4o-transcribe",
    file=audio_file,
)

print(transcription.text)
```

### Response Format

Default response is JSON with raw text:

```json
{
  "text": "Imagine the wildest idea that you've ever had..."
}
```

### With Custom Options

```python
from openai import OpenAI

client = OpenAI()
audio_file = open("/path/to/file/speech.mp3", "rb")

transcription = client.audio.transcriptions.create(
    model="gpt-4o-transcribe",
    file=audio_file,
    response_format="text",
)

print(transcription.text)
```

---

## Speaker Diarization

`gpt-4o-transcribe-diarize` produces speaker-aware transcripts with speaker labels, start/end timestamps.

### Requirements

- Use `diarized_json` response format for speaker metadata
- Set `chunking_strategy` (required for audio > 30 seconds; `"auto"` recommended)
- Does **not** support prompts, logprobs, or `timestamp_granularities[]`

### Known Speaker References

Optionally supply up to 4 short audio references (2–10 seconds each) to identify known speakers:

- `known_speaker_names[]` — Names of known speakers
- `known_speaker_references[]` — Audio clips as data URLs

### Example

```python
import base64
from openai import OpenAI

client = OpenAI()


def to_data_url(path: str) -> str:
    with open(path, "rb") as fh:
        return "data:audio/wav;base64," + base64.b64encode(fh.read()).decode("utf-8")


with open("meeting.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe-diarize",
        file=audio_file,
        response_format="diarized_json",
        chunking_strategy="auto",
        extra_body={
            "known_speaker_names": ["agent"],
            "known_speaker_references": [to_data_url("agent.wav")],
        },
    )

for segment in transcript.segments:
    print(segment.speaker, segment.text, segment.start, segment.end)
```

### Streaming Diarization

When `stream=True`, diarized responses emit:

- `transcript.text.segment` — When a segment completes (with speaker label)
- `transcript.text.delta` — Includes `segment_id` but partial speaker assignments are not streamed

---

## Translations

Translate audio from any supported language into English. Only supports `whisper-1`.

```python
from openai import OpenAI

client = OpenAI()
audio_file = open("/path/to/file/german.mp3", "rb")

translation = client.audio.translations.create(
    model="whisper-1",
    file=audio_file,
)

print(translation.text)
# Output: "Hello, my name is Wolfgang and I come from Germany..."
```

> Only English output is supported for translations.

---

## Timestamps

Get word-level or segment-level timestamps with `whisper-1` only:

```python
from openai import OpenAI

client = OpenAI()
audio_file = open("/path/to/file/speech.mp3", "rb")

transcription = client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-1",
    response_format="verbose_json",
    timestamp_granularities=["word"],
)

print(transcription.words)
```

> `timestamp_granularities[]` is only supported for `whisper-1`.

---

## Streaming Transcriptions

### Streaming a Completed Recording

For completed audio files or push-to-talk recordings, use `stream=True`:

```python
from openai import OpenAI

client = OpenAI()
audio_file = open("/path/to/file/speech.mp3", "rb")

stream = client.audio.transcriptions.create(
    model="gpt-4o-mini-transcribe",
    file=audio_file,
    response_format="text",
    stream=True,
)

for event in stream:
    print(event)
```

### Stream Events

| Event | Description |
|-------|-------------|
| `transcript.text.delta` | Partial transcription text |
| `transcript.text.done` | Complete transcription with full text |
| `transcript.text.segment` | Speaker-labeled segment (diarized mode) |

> Use `include[]` parameter to add `logprobs` for confidence scoring.

> Streamed transcription is **not** supported in `whisper-1`.

---

## Realtime API Transcription

Stream transcription of ongoing audio via WebSocket:

### Connection URL

```
wss://api.openai.com/v1/realtime?intent=transcription
```

### Session Configuration

```json
{
  "type": "transcription_session.update",
  "input_audio_format": "pcm16",
  "input_audio_transcription": {
    "model": "gpt-4o-transcribe",
    "prompt": "",
    "language": ""
  },
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 500
  },
  "input_audio_noise_reduction": {
    "type": "near_field"
  },
  "include": ["item.input_audio_transcription.logprobs"]
}
```

### Sending Audio

```json
{
  "type": "input_audio_buffer.append",
  "audio": "Base64EncodedAudioData"
}
```

### Authentication

Authenticate via API key directly, or use an ephemeral token from:

```
POST /v1/realtime/transcription_sessions
```

This returns a `client_secret` for secure WebSocket authentication.

### Noise Reduction Options

| Type | Best For |
|------|----------|
| `"near_field"` | Close microphone setups |
| `"far_field"` | Room-scale audio |

---

## Prompting for Transcription Quality

For `gpt-4o-transcribe` and `gpt-4o-mini-transcribe`, use prompts to improve quality:

```python
from openai import OpenAI

client = OpenAI()
audio_file = open("/path/to/file/speech.mp3", "rb")

transcription = client.audio.transcriptions.create(
    model="gpt-4o-transcribe",
    file=audio_file,
    response_format="text",
    prompt="The following conversation is a lecture about OpenAI, GPT-4.5 and the future of AI.",
)

print(transcription.text)
```

### Prompting Tips

| Scenario | Prompt Approach |
|----------|----------------|
| Uncommon words/acronyms | Include them in the prompt: `"...technology like DALL·E, GPT-3, and ChatGPT..."` |
| Split file continuity | Use the transcript of the preceding segment as the prompt |
| Missing punctuation | Include punctuated text: `"Hello, welcome to my lecture."` |
| Preserve filler words | Include them: `"Umm, let me think like, hmm..."` |
| Writing style preference | Write the prompt in your preferred style (e.g. simplified vs traditional Chinese) |

> For `whisper-1`, only the final 224 tokens of the prompt are considered.

> Prompting is **not** available for `gpt-4o-transcribe-diarize`.

---

## Longer Inputs

For files > 25 MB, split into chunks. Avoid breaking mid-sentence:

```python
from pydub import AudioSegment

song = AudioSegment.from_mp3("good_morning.mp3")

ten_minutes = 10 * 60 * 1000
first_10_minutes = song[:ten_minutes]
first_10_minutes.export("good_morning_10.mp3", format="mp3")
```

---

## Text-to-Speech

### Quick Start

```python
from pathlib import Path
from openai import OpenAI

client = OpenAI()
speech_file_path = Path(__file__).parent / "speech.mp3"

with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="coral",
    input="Today is a wonderful day to build something people love!",
    instructions="Speak in a cheerful and positive tone.",
) as response:
    response.stream_to_file(speech_file_path)
```

### TTS Models

| Model | Characteristics |
|-------|----------------|
| `gpt-4o-mini-tts` | Latest, most reliable; supports speech prompting (accent, emotion, speed, tone, whispering) |
| `tts-1` | Lower latency, lower quality |
| `tts-1-hd` | Higher quality, higher latency |

### Promptable Speech

With `gpt-4o-mini-tts`, use the `instructions` parameter to control:

- Accent
- Emotional range
- Intonation
- Impressions
- Speed of speech
- Tone
- Whispering

---

## Voice Options

### Built-in Voices (13 voices)

| Voice | Available On |
|-------|-------------|
| `alloy` | All models |
| `ash` | All models |
| `ballad` | `gpt-4o-mini-tts` |
| `coral` | All models |
| `echo` | All models |
| `fable` | All models |
| `nova` | All models |
| `onyx` | All models |
| `sage` | All models |
| `shimmer` | All models |
| `verse` | `gpt-4o-mini-tts` |
| `marin` | `gpt-4o-mini-tts` |
| `cedar` | `gpt-4o-mini-tts` |

> **Recommendation**: Use `marin` or `cedar` for best quality.

> `tts-1` and `tts-1-hd` support: `alloy`, `ash`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`.

---

## Custom Voices

Create unique voices from a short audio sample. Requires two recordings:

1. **Consent recording** — Voice actor reads a consent phrase
2. **Sample recording** — Audio the model will replicate (must match consent voice)

### Requirements

| Constraint | Detail |
|-----------|--------|
| Max voices per org | 20 |
| Audio length | ≤ 30 seconds |
| Supported formats | `mpeg`, `wav`, `ogg`, `aac`, `flac`, `webm`, `mp4` |

### Recording Tips

- Record in a quiet space with minimal echo
- Use a professional XLR microphone
- Stay 7–8 inches from the mic with a pop filter
- Be consistent in energy, style, and accent
- Try multiple samples to find the best fit

### Creating a Consent Recording

Upload via API with the exact consent phrase (any deviation fails):

```bash
curl https://api.openai.com/v1/audio/voice_consents \
  -X POST \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F "name=test_consent" \
  -F "language=en" \
  -F "recording=@consent_recording.wav;type=audio/x-wav"
```

**English consent phrase**: "I am the owner of this voice and I consent to OpenAI using this voice to create a synthetic voice model."

Supported consent languages: `de`, `en`, `es`, `fr`, `hi`, `id`, `it`, `ja`, `ko`, `nl`, `pl`, `pt`, `ru`, `uk`, `vi`, `zh`

### Creating a Voice

```bash
curl https://api.openai.com/v1/audio/voices \
  -X POST \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F "name=test_voice" \
  -F "audio_sample=@audio_sample.wav;type=audio/x-wav" \
  -F "consent=cons_123abc"
```

### Using a Custom Voice

```bash
curl https://api.openai.com/v1/audio/speech \
  -X POST \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini-tts",
    "voice": {"id": "voice_123abc"},
    "input": "Hello, this is my custom voice.",
    "format": "wav"
  }' \
  --output sample.wav
```

### Using in Realtime API

```javascript
const sessionConfig = JSON.stringify({
  session: {
    type: "realtime",
    model: "gpt-realtime",
    audio: {
      output: {
        voice: { id: "voice_123abc" },
      },
    },
  },
});
```

---

## Streaming Audio Output

Stream audio in real time before the full file is generated:

```python
import asyncio
from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer

openai = AsyncOpenAI()


async def main() -> None:
    async with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input="Today is a wonderful day to build something people love!",
        instructions="Speak in a cheerful and positive tone.",
        response_format="pcm",
    ) as response:
        await LocalAudioPlayer().play(response)


if __name__ == "__main__":
    asyncio.run(main())
```

> For fastest response times, use `wav` or `pcm` as the response format.

---

## Output Formats

| Format | Use Case |
|--------|----------|
| `mp3` | Default, general use |
| `opus` | Internet streaming, low latency |
| `aac` | Digital compression, YouTube/Android/iOS |
| `flac` | Lossless compression, archiving |
| `wav` | Uncompressed, low-latency applications |
| `pcm` | Raw 24kHz 16-bit signed low-endian, no header |

---

## Supported Languages

Both STT and TTS support the following languages:

Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, and Welsh.

> Voices are optimized for English. Other languages work but quality may vary.

> For GPT-4o transcription models, some ISO 639-1 and 639-3 language codes are supported. For unsupported codes, try prompting with the language name (e.g., "Output in English").
