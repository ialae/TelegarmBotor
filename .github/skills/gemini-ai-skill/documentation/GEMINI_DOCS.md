# Gemini 3 API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Model Family](#model-family)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Usage Examples](#usage-examples)
6. [Thought Signatures](#thought-signatures)
7. [Advanced Features](#advanced-features)
8. [Migration Guide](#migration-guide)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Quick Reference](#quick-reference-tables)
12. [Glossary](#glossary)

---

## Overview

**Gemini 3** is Google's most intelligent model family to date, built on a foundation of state-of-the-art reasoning. It is designed to bring any idea to life by mastering agentic workflows, autonomous coding, and complex multimodal tasks.

### Key Capabilities
- **Advanced Reasoning**: Dynamic thinking with controllable depth
- **Multimodal Understanding**: Text, images, video, audio, and PDFs
- **Code Execution**: Built-in Python runtime with visual manipulation
- **Function Calling**: Multimodal tool integration with thought preservation
- **Structured Outputs**: JSON schema enforcement with tool combination
- **Image Generation**: High-quality 4K image creation with reasoning
- **Grounding**: Real-time Google Search integration

### What's New in Gemini 3
- **Thinking Levels**: Control reasoning depth (`minimal`, `low`, `medium`, `high`)
- **Media Resolution**: Granular control over vision processing fidelity
- **Thought Signatures**: Encrypted reasoning context for multi-turn workflows
- **4K Image Generation**: Ultra-high resolution with text rendering
- **Code Execution with Vision**: Programmatic image analysis and manipulation
- **Multimodal Function Responses**: Return images/media from tools

---

## Model Family

### Model Comparison

| Model | Best For | Context Window | Knowledge Cutoff | Thinking Default |
|-------|----------|----------------|------------------|------------------|
| **Gemini 3.1 Pro** | Complex reasoning, broad knowledge | 1M / 64k | Jan 2025 | High (Dynamic) |
| **Gemini 3 Flash** | Pro-level intelligence at Flash speed | 1M / 64k | Jan 2025 | High (Dynamic) |
| **Gemini 3.1 Flash-Lite** | Cost-efficiency, high-volume tasks | 1M / 64k | Jan 2025 | Minimal |
| **Gemini 3 Pro Image** | Highest quality image generation | 65k / 32k | Jan 2025 | N/A (Image) |
| **Gemini 3.1 Flash Image** | High-volume image generation | 128k / 32k | Jan 2025 | N/A (Image) |

### Pricing (Per 1M Tokens)

| Model ID | Input Pricing | Output Pricing | Notes |
|----------|---------------|----------------|-------|
| `gemini-3.1-pro-preview` | $2 (<200k), $4 (>200k) | $12 (<200k), $18 (>200k) | Best reasoning |
| `gemini-3-flash-preview` | $0.50 | $3 | Pro-level speed |
| `gemini-3.1-flash-lite-preview` | $0.25 (text/image/video), $0.50 (audio) | $1.50 | Most economical |
| `gemini-3-pro-image-preview` | $2 (text input) | $0.134 (per image)* | Highest quality |
| `gemini-3.1-flash-image-preview` | $0.25 (text input) | $0.067 (per image)* | High volume |

*Image output pricing varies by resolution (512px, 1K, 2K, 4K).

### Model Selection Guide

**Use Gemini 3.1 Pro when:**
- Complex multi-step reasoning required
- Broad world knowledge needed
- Advanced code analysis/generation
- High-stakes decision making

**Use Gemini 3 Flash when:**
- Need Pro-level intelligence at lower cost
- Real-time/interactive applications
- Balanced performance and price

**Use Gemini 3.1 Flash-Lite when:**
- Simple instruction following
- High-throughput chat applications
- Cost is primary concern

**Use Image Models when:**
- Gemini 3 Pro Image: Maximum quality, detailed prompts
- Gemini 3.1 Flash Image: High-volume generation, lower latency

---

## Quick Start

### Installation

```bash
pip install google-genai
```

### Basic Usage

```python
from google import genai

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Find the race condition in this multi-threaded C++ snippet: [code here]",
)

print(response.text)
```

### Available Models

All Gemini 3 models are currently in **preview** status.

---

## API Reference

### Core Parameters

#### GenerateContentConfig

Primary configuration object for all Gemini 3 models.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `thinking_config` | ThinkingConfig | Controls reasoning depth (see below) | `high` (Pro/Flash) |
| `media_resolution` | str | Vision processing fidelity | Model-dependent |
| `temperature` | float | Output randomness (keep at 1.0) | `1.0` |
| `tools` | List[Tool] | Enable built-in tools (search, code, etc.) | `[]` |
| `response_mime_type` | str | Output format (e.g., "application/json") | `"text/plain"` |
| `response_json_schema` | dict | JSON schema for structured outputs | `None` |
| `image_config` | ImageConfig | Image generation settings | `None` |

---

### Thinking Level

**Parameter**: `thinking_config.thinking_level`

Controls the maximum depth of the model's internal reasoning process before producing a response. Gemini 3 uses **dynamic thinking** by default.

#### Thinking Level Options

| Level | Gemini 3.1 Pro | Gemini 3.1 Flash-Lite | Gemini 3 Flash | Description |
|-------|----------------|----------------------|----------------|-------------|
| `minimal` | ❌ Not supported | ✅ Default | ✅ Supported | No thinking for most queries. May think minimally for complex coding. Minimizes latency. **Note**: Does not guarantee thinking is off. |
| `low` | ✅ Supported | ✅ Supported | ✅ Supported | Minimal latency and cost. Best for simple instruction following, chat, high-throughput apps. |
| `medium` | ✅ Supported | ✅ Supported | ✅ Supported | Balanced thinking for most tasks. |
| `high` | ✅ **Default** (Dynamic) | ✅ Supported (Dynamic) | ✅ **Default** (Dynamic) | Maximum reasoning depth. Slower first token, but more carefully reasoned output. |

#### When to Use Each Level

- **`minimal`**: Simple chat, FAQ responses, formatting tasks
- **`low`**: Translation, summarization, basic Q&A
- **`medium`**: Code review, document analysis, moderate complexity
- **high`**: Complex math, bug finding, multi-step reasoning, research

#### Code Example: Thinking Level

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="How does AI work?",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="low")
    ),
)

print(response.text)
```

**Important**: You cannot use both `thinking_level` and the legacy `thinking_budget` parameter in the same request. Doing so will return a **400 error**.
---

### Media Resolution

**Parameter**: `media_resolution` (per-part or global)

Controls multimodal vision processing fidelity. Higher resolutions improve text reading and detail identification but increase token usage and latency.

#### Media Resolution Levels

| Level | Images (Tokens) | Video (Tokens/Frame) | Description |
|-------|----------------|---------------------|-------------|
| `media_resolution_low` | 280 | 70 | Fastest processing, lowest cost |
| `media_resolution_medium` | 560 | 70 (same as low) | Balanced for most tasks |
| `media_resolution_high` | 1120 | 280 | Maximum quality for text/details |
| `media_resolution_ultra_high` | Higher* | N/A | Per-part only, highest fidelity |

*Ultra-high resolution is only available per-part (not globally).

#### Recommended Settings by Media Type

| Media Type | Recommended Setting | Max Tokens | Usage Guidance |
|------------|-------------------|-----------|----------------|
| **Images** | `media_resolution_high` | 1120 | Recommended for most image analysis to ensure maximum quality. |
| **PDFs** | `media_resolution_medium` | 560 | Optimal for document understanding. Quality saturates at medium; increasing to high rarely improves OCR. |
| **Video (General)** | `media_resolution_low` or `medium` | 70 | Low and medium treated identically for video. Sufficient for action recognition and scene description. |
| **Video (Text-Heavy)** | `media_resolution_high` | 280 | Required only for reading dense text (OCR) or small details in video frames. |

#### Token Consumption Notes

- **Images** scale linearly: low (280) → medium (560) → high (1120)
- **Video** is compressed: low/medium (70 tokens/frame), high (280 tokens/frame)
- Use lower resolutions when context window is limited
- Higher resolutions significantly increase latency

#### Code Example: Media Resolution

```python
from google import genai
from google.genai import types
import base64

# The media_resolution parameter is currently only available in the v1alpha API version.
client = genai.Client(
    api_key="YOUR_API_KEY",
    http_options={'api_version': 'v1alpha'}
)

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        types.Content(
            parts=[
                types.Part(text="What is in this image?"),
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=base64.b64decode("..."),
                    ),
                    media_resolution={"level": "media_resolution_high"}
                )
            ]
        )
    ]
)

print(response.text)
```

---

### Temperature

**Parameter**: `temperature` (default: `1.0`)

For all Gemini 3 models, **keep temperature at 1.0** (default).

**Why?**
- Gemini 3's reasoning capabilities are optimized for `temperature=1.0`
- Changing temperature (especially below 1.0) may cause:
  - **Looping**: Model repeats itself endlessly
  - **Degraded performance**: Particularly in math/reasoning tasks
  - Unexpected behavior in complex workflows

**When to adjust** (rarely):
- Creative writing: May increase to 1.2-1.5 for more variety
- Deterministic outputs: Use structured outputs instead of lowering temperature

```python
# ✅ RECOMMENDED: Use default temperature
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Explain quantum computing",
)

# ❌ AVOID: Lowering temperature on Gemini 3
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Explain quantum computing",
    config=types.GenerateContentConfig(temperature=0.3)  # May cause issues
)
```

---

## Thought Signatures

### What Are Thought Signatures?

**Thought Signatures** are encrypted representations of the model's internal reasoning process. They preserve reasoning context across multi-turn API calls, allowing the model to maintain coherent thought chains.

### Why They Matter

Thought signatures enable:
- **Multi-turn reasoning**: Model remembers its thought process between API calls
- **Function calling**: Model understands tool outputs in context
- **Image editing**: Model remembers previous image composition for edits
- **Complex workflows**: Maintain reasoning across agentic/multi-step tasks

### Validation Rules

| Scenario | Validation | Consequence if Missing |
|----------|-----------|------------------------|
| **Function Calling** | **Strict** | 400 error |
| **Image Generation/Editing** | **Strict** | 400 error |
| **Text/Chat** | Soft | Degraded reasoning quality |
| **Streaming** | Soft | May arrive in final chunk |

**Important**: Thought signatures are required **even when `thinking_level` is set to `minimal`** for Gemini 3 Flash.

---

### Automatic Handling (Recommended)

If you use the official SDKs (Python, Node, Java) with standard chat history, **thought signatures are handled automatically**. You do not need to manually manage these fields.

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# SDK automatically preserves thought signatures in history
chat = client.chats.create(model="gemini-3-flash-preview")

response_1 = chat.send_message("What are the best coding practices?")
print(response_1.text)

# Thought signature from response_1 is automatically included
response_2 = chat.send_message("Can you elaborate on the first one?")
print(response_2.text)
```

---

### Manual Handling

When manually constructing conversation history, you **must return thought signatures** exactly as received.

#### Function Calling (Strict Validation)

When Gemini generates a `functionCall`, it relies on the `thoughtSignature` to process the tool's output correctly.

**Rules**:
1. **Single Function Call**: The `functionCall` part contains a signature. Return it.
2. **Parallel Function Calls**: Only the *first* `functionCall` has a signature. Return parts in order.
3. **Multi-Step (Sequential)**: Each step's `functionCall` has a signature. Return *all* accumulated signatures.

##### Single Function Call Example

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# Step 1: Define tool
get_weather = types.FunctionDeclaration(
    name="get_weather",
    description="Get current weather",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string"}
        },
        "required": ["city"]
    }
)

# Step 2: Initial request
response_1 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="What's the weather in Paris?",
    config=types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[get_weather])]
    )
)

function_call = response_1.function_calls[0]
print(f"Model wants: {function_call.name}({function_call.args})")

# Step 3: Execute tool (your code)
weather_data = {"temperature": "15C", "condition": "Sunny"}

# Step 4: Send result back WITH thought signature
history = [
    types.Content(role="user", parts=[types.Part(text="What's the weather in Paris?")]),
    response_1.candidates[0].content,  # Contains thoughtSignature automatically
    types.Content(
        role="user",
        parts=[types.Part.from_function_response(
            name=function_call.name,
            response=weather_data
        )]
    )
]

response_2 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=history,
    config=types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[get_weather])]
    )
)

print(response_2.text)
```

##### Parallel Function Calls Example

```python
# User asks: "Check the weather in Paris and London."
# Model returns TWO function calls in one response.

response_1 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Check the weather in Paris and London.",
    config=types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[get_weather])]
    )
)

# Response structure:
# {
#   "role": "model",
#   "parts": [
#     {
#       "functionCall": {"name": "get_weather", "args": {"city": "Paris"}},
#       "thoughtSignature": "<Signature_A>"  # Only first call has signature
#     },
#     {
#       "functionCall": {"name": "get_weather", "args": {"city": "London"}}
#       # No signature on second call
#     }
#   ]
# }

# Execute both tools
paris_weather = {"temperature": "15C"}
london_weather = {"temperature": "12C"}

# Return results (SDK handles signature automatically)
history = [
    types.Content(role="user", parts=[types.Part(text="Check the weather in Paris and London.")]),
    response_1.candidates[0].content,  # Preserves signature from first functionCall
    types.Content(
        role="user",
        parts=[
            types.Part.from_function_response(name="get_weather", response=paris_weather),
            types.Part.from_function_response(name="get_weather", response=london_weather)
        ]
    )
]

response_2 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=history,
    config=types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[get_weather])]
    )
)

print(response_2.text)
```

##### Multi-Step Sequential Function Calls

```python
# Scenario: User asks question requiring TWO steps (Check Flight → Book Taxi)

# Step 1: Model calls Flight Tool
# Returns <Sig_A>

# Step 2: Send Flight Result back WITH <Sig_A>

# Step 3: Model calls Taxi Tool
# Returns <Sig_B>

# Step 4: Send Taxi Result back WITH <Sig_A> AND <Sig_B>
# You must accumulate ALL signatures in the history

history = [
    types.Content(role="user", parts=[types.Part(text="Check flight AA100...")]),
    
    # Model Turn 1: Flight function call with <Sig_A>
    types.Content(
        role="model",
        parts=[types.Part(
            function_call=types.FunctionCall(name="check_flight", args={...}),
            thought_signature="<Sig_A>"  # REQUIRED
        )]
    ),
    
    # User Turn 1: Flight response
    types.Content(
        role="user",
        parts=[types.Part.from_function_response(name="check_flight", response={...})]
    ),
    
    # Model Turn 2: Taxi function call with <Sig_B>
    types.Content(
        role="model",
        parts=[types.Part(
            function_call=types.FunctionCall(name="book_taxi", args={...}),
            thought_signature="<Sig_B>"  # REQUIRED
        )]
    ),
    
    # User Turn 2: Taxi response
    types.Content(
        role="user",
        parts=[types.Part.from_function_response(name="book_taxi", response={...})]
    )
]
```

---

#### Text/Chat (Soft Validation)

For standard chat, signatures are not strictly enforced but recommended for best performance.

```python
# Non-Streaming
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Analyze this investment strategy..."
)

# The final content part MAY contain a thoughtSignature
# If present, include it in the next turn for better follow-up reasoning
if hasattr(response.candidates[0].content.parts[-1], 'thought_signature'):
    # SDK handles this automatically in chat sessions
    pass
```

**Streaming**: Signatures may arrive in a final chunk with empty text. Check for signatures even if `text` field is empty.

```python
for chunk in client.models.generate_content_stream(
    model="gemini-3-flash-preview",
    contents="What are the risks?"
):
    if chunk.text:
        print(chunk.text, end="")
    # Signature may be in final chunk with no text
```

---

#### Image Generation/Editing (Strict Validation)

For `gemini-3-pro-image-preview` and `gemini-3.1-flash-image-preview`, thought signatures are **critical for conversational editing**.

**Rules**:
- Signatures appear on the **first part** (text or image) after thoughts
- Signatures appear on **every subsequent image part**
- **All signatures must be returned** to avoid 400 errors

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# Turn 1: Generate image
response_1 = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="Generate a cyberpunk city at night",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9")
    )
)

# Response structure:
# {
#   "role": "model",
#   "parts": [
#     {
#       "text": "I will generate a cyberpunk city...",
#       "thoughtSignature": "<Signature_D>"  # First part has signature
#     },
#     {
#       "inlineData": {...},  # Image data
#       "thoughtSignature": "<Signature_E>"  # Image part has signature
#     }
#   ]
# }

# Save the image
image = response_1.parts[1].as_image()
image.save('cyberpunk_night.png')

# Turn 2: Edit the image (requires ALL signatures from Turn 1)
history = [
    types.Content(role="user", parts=[types.Part(text="Generate a cyberpunk city at night")]),
    response_1.candidates[0].content,  # SDK preserves both signatures
    types.Content(role="user", parts=[types.Part(text="Make it daytime.")])
]

response_2 = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=history,
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9")
    )
)

# The model uses the signatures to understand the original composition
edited_image = response_2.parts[1].as_image()
edited_image.save('cyberpunk_day.png')
```

---

### Migrating from Other Models

If transferring a conversation from another model (e.g., Gemini 2.5) or injecting a custom function call not generated by Gemini 3, you won't have a valid signature.

**Workaround**: Use this dummy signature to bypass strict validation:

```python
"thoughtSignature": "context_engineering_is_the_way_to_go"
```

**When to use**:
- Importing chat history from Gemini 2.5
- Manually constructing function calls for testing
- Cross-model conversation migration

```python
# Example: Injecting a manual function call
history = [
    types.Content(role="user", parts=[types.Part(text="Get weather")]),
    types.Content(
        role="model",
        parts=[types.Part(
            function_call=types.FunctionCall(name="get_weather", args={"city": "NYC"}),
            thought_signature="context_engineering_is_the_way_to_go"  # Bypass validation
        )]
    ),
    types.Content(
        role="user",
        parts=[types.Part.from_function_response(
            name="get_weather",
            response={"temp": "20C"}
        )]
    )
]
```

---

## Usage Examples

### Example 1: Basic Text Generation

```python
from google import genai

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Explain the halting problem in computer science.",
)

print(response.text)
```

---

### Example 2: Controlling Thinking Level

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# High thinking for complex reasoning
response_complex = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Find all edge cases in this sorting algorithm: [code]",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high")
    ),
)

print("Complex analysis:", response_complex.text)

# Low thinking for simple chat
response_simple = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Hello! How are you?",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="low")
    ),
)

print("Simple chat:", response_simple.text)
```

---

### Example 3: High-Resolution Image Analysis

```python
from google import genai
from google.genai import types
from PIL import Image
import base64

client = genai.Client(
    api_key="YOUR_API_KEY",
    http_options={'api_version': 'v1alpha'}
)

# Load image
with open("document.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        types.Content(
            parts=[
                types.Part(text="Extract all text from this document, preserving formatting."),
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=base64.b64decode(image_data),
                    ),
                    media_resolution={"level": "media_resolution_high"}
                )
            ]
        )
    ]
)

print(response.text)
```

---

### Example 4: Structured Outputs with Google Search

```python
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

class MatchResult(BaseModel):
    winner: str = Field(description="The name of the winner.")
    final_match_score: str = Field(description="The final match score.")
    scorers: List[str] = Field(description="The names of all scorers.")
    venue: str = Field(description="The venue where the match was played.")

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Search for all details for the latest Champions League final.",
    config={
        "tools": [
            {"google_search": {}},
            {"url_context": {}}
        ],
        "response_mime_type": "application/json",
        "response_json_schema": MatchResult.model_json_schema(),
    },  
)

result = MatchResult.model_validate_json(response.text)
print(f"Winner: {result.winner}")
print(f"Score: {result.final_match_score}")
print(f"Scorers: {', '.join(result.scorers)}")
print(f"Venue: {result.venue}")
```

---

### Example 5: Image Generation with Google Search Grounding

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="Generate an infographic showing the current weather in Tokyo with temperature, conditions, and forecast.",
    config=types.GenerateContentConfig(
        tools=[{"google_search": {}}],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="4K"
        )
    )
)

# Extract and save the image
image_parts = [part for part in response.parts if part.inline_data]

if image_parts:
    image = image_parts[0].as_image()
    image.save('weather_tokyo.png')
    image.show()
    print("Image saved as weather_tokyo.png")
else:
    print("No image generated")
```

---

### Example 6: Multi-Turn Image Editing

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# Turn 1: Generate initial image
response_1 = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="Generate a cozy coffee shop interior with warm lighting",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        )
    )
)

# Save initial image
image_1 = response_1.parts[1].as_image()
image_1.save('coffee_shop_original.png')
print("Original image saved")

# Turn 2: Edit the image (SDK handles thought signatures automatically)
chat = client.chats.create(
    model="gemini-3-pro-image-preview",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        )
    )
)

# Start with the original request
chat.send_message("Generate a cozy coffee shop interior with warm lighting")

# Request edit
response_2 = chat.send_message("Add more plants and make it brighter")

# Save edited image
for part in response_2.parts:
    if part.inline_data:
        edited_image = part.as_image()
        edited_image.save('coffee_shop_edited.png')
        print("Edited image saved")
```

---

### Example 7: Code Execution with Visual Analysis

```python
from google import genai
from google.genai import types
import requests
from PIL import Image
import io

client = genai.Client(api_key="YOUR_API_KEY")

# Load image from URL
image_url = "https://example.com/complex_diagram.jpg"
image_bytes = requests.get(image_url).content
image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        image_part,
        "Zoom into the text labels and list all the component names. Use code to enhance clarity if needed."
    ],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(include_thoughts=True)
    ),
)

# Display all parts (text, code, results, manipulated images)
for part in response.candidates[0].content.parts:
    if part.text:
        print("TEXT:", part.text)
    if part.executable_code:
        print("CODE EXECUTED:")
        print(part.executable_code.code)
    if part.code_execution_result:
        print("CODE OUTPUT:")
        print(part.code_execution_result.output)
    if part.as_image():
        # Model may return annotated/cropped images
        enhanced_image = Image.open(io.BytesIO(part.as_image().image_bytes))
        enhanced_image.save('enhanced_diagram.png')
        print("Enhanced image saved")
```

---

### Example 8: Multimodal Function Calling

```python
from google import genai
from google.genai import types
import requests

client = genai.Client(api_key="YOUR_API_KEY")

# Define a function that returns multimedia
get_product_image = types.FunctionDeclaration(
    name="get_product_image",
    description="Retrieves the product image for a specific order item.",
    parameters={
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The unique identifier for the product."
            }
        },
        "required": ["product_id"],
    },
)

tool = types.Tool(function_declarations=[get_product_image])

# Step 1: User asks for product
prompt = "Show me the laptop I ordered last week (product ID: LAP-001)."
response_1 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[prompt],
    config=types.GenerateContentConfig(tools=[tool]),
)

# Step 2: Check if function was called
if response_1.function_calls:
    function_call = response_1.function_calls[0]
    product_id = function_call.args["product_id"]
    
    print(f"Model requested: {function_call.name}({product_id})")
    
    # Execute your function (fetch image from database/API)
    image_url = f"https://example.com/products/{product_id}.jpg"
    image_bytes = requests.get(image_url).content
    
    # Step 3: Return multimodal function response
    function_response_data = {
        "product_id": product_id,
        "name": "UltraBook Pro",
        "status": "Delivered"
    }
    
    function_response_image = types.FunctionResponsePart(
        inline_data=types.FunctionResponseBlob(
            mime_type="image/jpeg",
            display_name=f"{product_id}.jpg",
            data=image_bytes,
        )
    )
    
    # Step 4: Send back text + image response
    history = [
        types.Content(role="user", parts=[types.Part(text=prompt)]),
        response_1.candidates[0].content,
        types.Content(
            role="user",
            parts=[
                types.Part.from_function_response(
                    name=function_call.name,
                    response=function_response_data,
                    parts=[function_response_image]
                )
            ],
        )
    ]
    
    response_2 = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=history,
        config=types.GenerateContentConfig(
            tools=[tool],
            thinking_config=types.ThinkingConfig(include_thoughts=True)
        ),
    )
    
    print(f"Final response: {response_2.text}")
```

---

### Example 9: Video Analysis with Custom Resolution

```python
from google import genai
from google.genai import types
import base64

client = genai.Client(
    api_key="YOUR_API_KEY",
    http_options={'api_version': 'v1alpha'}
)

# Load video file
with open("product_demo.mp4", "rb") as f:
    video_data = base64.b64encode(f.read()).decode()

# High resolution for text-heavy video (e.g., tutorial with code)
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        types.Content(
            parts=[
                types.Part(text="Transcribe all code shown in this programming tutorial video."),
                types.Part(
                    inline_data=types.Blob(
                        mime_type="video/mp4",
                        data=base64.b64decode(video_data),
                    ),
                    media_resolution={"level": "media_resolution_high"}  # 280 tokens/frame for text OCR
                )
            ]
        )
    ]
)

print(response.text)
```

---

### Example 10: Streaming with Thought Signatures

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

print("Model response (streaming):")

for chunk in client.models.generate_content_stream(
    model="gemini-3-flash-preview",
    contents="Analyze the economic implications of universal basic income.",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="high",
            include_thoughts=True
        )
    )
):
    if chunk.text:
        print(chunk.text, end="", flush=True)
    
    # Check for thought signature in final chunk (may have empty text)
    if hasattr(chunk, 'candidates') and len(chunk.candidates) > 0:
        for part in chunk.candidates[0].content.parts:
            if hasattr(part, 'thought_signature') and part.thought_signature:
                # Save signature for multi-turn conversation
                pass

print("\n\nStream complete.")
```
---

## Advanced Features

### Structured Outputs with Tools

Gemini 3 allows combining **Structured Outputs** (JSON schema enforcement) with **built-in tools** like Google Search, URL Context, and Code Execution.

**Supported tools**:
- `google_search`: Real-time web search
- `url_context`: Fetch and analyze web pages
- `code_execution`: Python runtime
- Function calling (custom tools)

**Example: Grounded Structured Output**

```python
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

class StockAnalysis(BaseModel):
    symbol: str
    current_price: float
    day_change_percent: float
    analyst_ratings: List[str]
    summary: str

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Search for Tesla stock analysis and provide structured data.",
    config={
        "tools": [{"google_search": {}}],
        "response_mime_type": "application/json",
        "response_json_schema": StockAnalysis.model_json_schema(),
    },
)

result = StockAnalysis.model_validate_json(response.text)
print(f"{result.symbol}: ${result.current_price} ({result.day_change_percent:+.2f}%)")
```

---

### Code Execution with Images

Gemini 3 Flash can **programmatically manipulate images** using Python code to:
- **Zoom and crop**: Examine small details
- **Annotate**: Draw bounding boxes, arrows, labels
- **Visual math**: Extract data and plot charts
- **Transform**: Rotate, enhance, filter images

**How it works**:
1. Model analyzes image
2. Model writes Python code (PIL, OpenCV, Matplotlib)
3. Code executes in sandbox
4. Model returns manipulated image + analysis

**Example: Receipt Analysis with Plotting**

```python
from google import genai
from google.genai import types
from PIL import Image
import io

client = genai.Client(api_key="YOUR_API_KEY")

# Load receipt image
with open("receipt.jpg", "rb") as f:
    receipt_image = types.Part.from_bytes(data=f.read(), mime_type="image/jpeg")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        receipt_image,
        "Extract all line items and create a pie chart showing spending breakdown by category."
    ],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        thinking_config=types.ThinkingConfig(include_thoughts=True)
    ),
)

# Process response parts
for part in response.candidates[0].content.parts:
    if part.text:
        print("ANALYSIS:", part.text)
    if part.executable_code:
        print("\nCODE EXECUTED:")
        print(part.executable_code.code)
    if part.code_execution_result:
        print("\nOUTPUT:")
        print(part.code_execution_result.output)
    if part.as_image():
        # The pie chart generated by code
        chart = Image.open(io.BytesIO(part.as_image().image_bytes))
        chart.save('spending_breakdown.png')
        print("\nChart saved!")
```

---

### Image Generation Capabilities

**Both models** (Gemini 3 Pro Image and 3.1 Flash Image) support:
- **4K resolution**: Up to 4096×4096 pixels
- **Text rendering**: Legible text in images/infographics
- **Grounded generation**: Use Google Search for factual accuracy
- **Multi-turn editing**: Conversational image refinement
- **Multiple aspect ratios**: 1:1, 16:9, 9:16, 4:3, 3:4, and more

**Key differences**:

| Feature | Gemini 3 Pro Image | Gemini 3.1 Flash Image |
|---------|-------------------|------------------------|
| Quality | Highest | High |
| Speed | Slower | Faster |
| Aspect Ratios | 10 options | 14 options |
| Image Search Grounding | ❌ No | ✅ Yes |
| Price (4K) | $0.134/image | $0.067/image |

**Image generation limitations**:
- Cannot generate images of public figures
- Limited to 10 images per turn
- Thought signatures required for editing workflow

---

### Computer Use (Preview)

Gemini 3 Pro and Gemini 3 Flash support **Computer Use** tool for interacting with graphical interfaces.

**Capabilities**:
- Click, type, scroll, navigate GUIs
- Read screen content
- Multi-step workflows

**Note**: Unlike Gemini 2.5, you don't need a separate model to access Computer Use.

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# Computer Use tool configuration
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Open Chrome, search for 'Python tutorials', and click the first result.",
    config=types.GenerateContentConfig(
        tools=[types.Tool(computer_use=types.ToolComputerUse)]
    ),
)

print(response.text)
```

---

### OpenAI Compatibility

Gemini 3 supports the **OpenAI API format** with automatic parameter mapping:

| OpenAI Parameter | Gemini Equivalent |
|-----------------|-------------------|
| `reasoning_effort` | `thinking_level` |
| `low` | `low` |
| `medium` | `medium` |
| `high` | `high` |

**Example using OpenAI format**:

```python
from openai import OpenAI

# Point to Gemini API endpoint
client = OpenAI(
    api_key="YOUR_GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-3-flash-preview",
    messages=[
        {"role": "user", "content": "Explain quantum entanglement"}
    ],
    reasoning_effort="high"  # Automatically maps to thinking_level="high"
)

print(response.choices[0].message.content)
```

---

## Migration Guide

### Migrating from Gemini 2.5

Gemini 3 offers significant improvements over Gemini 2.5. Consider these changes:

#### 1. Thinking and Prompting

**Before (Gemini 2.5)**:
```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="""
    Let's think step by step:
    1. First, analyze the data
    2. Then, identify patterns
    3. Finally, provide recommendations
    
    [Complex prompt engineering to force reasoning]
    """
)
```

**After (Gemini 3)**:
```python
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Analyze this data and provide recommendations.",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high")
    )
)
```

**Key change**: Remove complex prompt engineering. Let `thinking_level` handle reasoning.

---

#### 2. Temperature Settings

**Before (Gemini 2.5)**:
```python
# For deterministic outputs
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="Summarize this document",
    config=types.GenerateContentConfig(temperature=0.2)  # Common practice
)
```

**After (Gemini 3)**:
```python
# Use default temperature=1.0
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Summarize this document"
    # No temperature parameter - use default 1.0
)

# For deterministic structured output, use JSON schema instead
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Summarize this document",
    config={
        "response_mime_type": "application/json",
        "response_json_schema": {...}
    }
)
```

**Key change**: Keep `temperature=1.0`. Use structured outputs for determinism.

---

#### 3. PDF and Document Understanding

**Before (Gemini 2.5)**: Default resolution handled automatically.

**After (Gemini 3)**: Explicitly set `media_resolution_medium` for PDFs.

```python
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        types.Content(
            parts=[
                types.Part(text="Extract all key points from this document."),
                types.Part(
                    inline_data=types.Blob(mime_type="application/pdf", data=pdf_bytes),
                    media_resolution={"level": "media_resolution_medium"}  # Optimal for PDFs
                )
            ]
        )
    ]
)
```

---

#### 4. Image Segmentation

**Not supported** in Gemini 3 Pro or Gemini 3 Flash. If you need pixel-level masks:

**Option 1**: Continue using Gemini 2.5 Flash with thinking turned off.

**Option 2**: Use Gemini Robotics-ER 1.5.

```python
# Gemini 2.5 Flash for segmentation
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, "Segment all objects in this image"],
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="minimal")
    )
)
```

---

#### 5. Computer Use Tool

**Before (Gemini 2.5)**: Required separate model (`gemini-2.5-computer-use`).

**After (Gemini 3)**: Built into main models.

```python
# Gemini 3 - Computer Use built-in
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Navigate to example.com and click 'Sign Up'",
    config=types.GenerateContentConfig(
        tools=[types.Tool(computer_use=types.ToolComputerUse)]
    )
)
```

---

#### 6. Tool Support Changes

**Not yet supported in Gemini 3**:
- ❌ Maps grounding
- ❌ Combining built-in tools with function calling (coming soon)

**Workaround for function calling + built-in tools**:
Use separate API calls or wait for support.

---

#### 7. Token Consumption

**Impact of default settings**:
- **PDFs**: May use MORE tokens (higher default resolution)
- **Videos**: May use FEWER tokens (optimized compression)

**If exceeding context window**:
```python
# Reduce media resolution to fit in context
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        types.Content(
            parts=[
                types.Part(text="Analyze this video"),
                types.Part(
                    inline_data=types.Blob(mime_type="video/mp4", data=video_bytes),
                    media_resolution={"level": "media_resolution_low"}  # 70 tokens/frame instead of 280
                )
            ]
        )
    ]
)
```

---

### Migration Checklist

✅ **Remove complex prompt engineering** (chain-of-thought, step-by-step guidance)  
✅ **Use `thinking_level` parameter** instead of prompt tricks  
✅ **Remove explicit `temperature` settings** (keep default 1.0)  
✅ **Set `media_resolution_medium` for PDFs** if processing documents  
✅ **Check token consumption** for PDFs/videos, adjust resolution if needed  
✅ **Update image segmentation workflows** to use Gemini 2.5 or Robotics-ER 1.5  
✅ **Migrate Computer Use** from separate model to built-in tool  
✅ **Remove maps grounding** (not yet supported)  
✅ **Test thought signature handling** if manually constructing history  

---

## Best Practices

### Prompting

1. **Be concise**: Gemini 3 prefers direct, clear instructions over verbose prompts.
2. **Place instructions at the end**: When providing large context (books, code, videos), put your question/instruction at the end.
3. **Anchor to context**: Start questions with "Based on the information above..." for long contexts.
4. **Control verbosity**: If you want a chatty persona, explicitly request it ("Explain this as a friendly assistant").
5. **Avoid over-engineering**: Don't force reasoning with prompts like "think step by step" — use `thinking_level` instead.

```python
# ❌ AVOID: Over-engineered prompt
contents = """
Let's approach this systematically:
Step 1: Analyze the code
Step 2: Identify bugs
Step 3: Suggest fixes
Now, here's the code: [code]
"""

# ✅ BETTER: Simple prompt with thinking_level
contents = "Find and fix bugs in this code: [code]"
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="high")
)
```

---

### Performance Optimization

1. **Choose the right thinking level**:
   - Simple tasks: `low` or `minimal`
   - Moderate complexity: `medium`
   - Complex reasoning: `high`

2. **Optimize media resolution**:
   - Images: `high` for text/details, `medium` for general analysis
   - PDFs: `medium` (quality saturates, `high` rarely helps)
   - Video: `low`/`medium` for action, `high` only for text OCR

3. **Batch independent requests**: Use asyncio for parallel calls.

4. **Use streaming** for long-running requests to reduce perceived latency.

5. **Cache large contexts**: Reuse uploaded files for multiple queries.

---

### Thought Signature Management

1. **Use official SDKs**: Automatic signature handling with `client.chats.create()`.
2. **Preserve conversation history**: Always include full history with signatures.
3. **Never modify signatures**: Return them exactly as received.
4. **Test multi-turn workflows**: Verify signatures are preserved across turns.
5. **Use dummy signature for migration**: `"context_engineering_is_the_way_to_go"` when importing from other models.

---

### Error Handling

```python
from google.genai import errors

try:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="Analyze this data"
    )
except errors.ClientError as e:
    print(f"Client error: {e}")
    # Handle 400 errors (bad request, missing signatures, etc.)
except errors.ServerError as e:
    print(f"Server error: {e}")
    # Handle 500 errors (retry with backoff)
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

### Cost Optimization

1. **Use Flash models** for most tasks (3x cheaper than Pro).
2. **Use Flash-Lite** for high-volume simple tasks (10x cheaper than Pro).
3. **Lower media resolution** when detail isn't critical.
4. **Enable streaming** to avoid buffering large responses.
5. **Monitor token usage**: Log input/output tokens for cost tracking.

```python
response = client.models.generate_content(
    model="gemini-3-flash-preview",  # $0.50/1M vs $2/1M for Pro
    contents="Summarize this article",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="low")  # Faster, cheaper
    )
)

# Log token usage
print(f"Input tokens: {response.usage_metadata.prompt_token_count}")
print(f"Output tokens: {response.usage_metadata.candidates_token_count}")
```

---

## Troubleshooting

### 400 Error: Missing Thought Signature

**Symptoms**: Error when calling API after function call or image generation.

**Cause**: Missing `thoughtSignature` in conversation history.

**Solution**: Use official SDK with chat sessions, or manually preserve signatures.

```python
# ✅ FIX: Use chat session (automatic signature handling)
chat = client.chats.create(model="gemini-3-flash-preview")
response = chat.send_message("What's the weather?")  # Signatures handled automatically
```

---

### Looping or Degraded Performance

**Symptoms**: Model repeats itself or gives poor answers.

**Cause**: Temperature set below 1.0.

**Solution**: Remove `temperature` parameter or set to 1.0.

```python
# ❌ PROBLEM
config = types.GenerateContentConfig(temperature=0.3)

# ✅ FIX
# Option 1: Remove temperature (uses default 1.0)
config = types.GenerateContentConfig()

# Option 2: Explicitly set to 1.0
config = types.GenerateContentConfig(temperature=1.0)
```

---

### 400 Error: Cannot Use thinking_level and thinking_budget Together

**Symptoms**: Error message about conflicting parameters.

**Cause**: Using legacy `thinking_budget` with new `thinking_level`.

**Solution**: Use only `thinking_level`.

```python
# ❌ PROBLEM
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        thinking_level="high",
        thinking_budget=1000  # Legacy parameter
    )
)

# ✅ FIX
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="high")
)
```

---

### Context Window Exceeded

**Symptoms**: Error about exceeding token limit.

**Cause**: Large media files with high resolution settings.

**Solution**: Reduce media resolution or split into chunks.

```python
# ✅ FIX: Lower resolution
response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        types.Content(
            parts=[
                types.Part(text="Analyze this video"),
                types.Part(
                    inline_data=types.Blob(mime_type="video/mp4", data=video_bytes),
                    media_resolution={"level": "media_resolution_low"}  # 70 tokens/frame
                )
            ]
        )
    ]
)
```

---

### Image Generation: No Image Returned

**Symptoms**: Response contains only text, no image.

**Cause**: Model determined it couldn't generate the requested image (policy violation, impossible request).

**Solution**: Check response text for explanation, modify prompt.

```python
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="Generate an image of [request]",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9")
    )
)

# Check if image was generated
image_parts = [part for part in response.parts if part.inline_data]
if not image_parts:
    print(f"No image generated. Reason: {response.text}")
else:
    image = image_parts[0].as_image()
    image.save('output.png')
```

---

### Function Call Not Triggered

**Symptoms**: Model returns text instead of calling declared function.

**Cause**: Function description unclear or prompt doesn't match use case.

**Solution**: Improve function description and prompt specificity.

```python
# ❌ PROBLEM: Vague description
get_weather = types.FunctionDeclaration(
    name="get_weather",
    description="Weather",  # Too vague
    parameters={...}
)

# ✅ FIX: Clear, detailed description
get_weather = types.FunctionDeclaration(
    name="get_weather",
    description="Get current weather conditions and forecast for a specific city. Returns temperature, conditions, humidity, and 3-day forecast.",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city name (e.g., 'Paris', 'New York')"
            },
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit"
            }
        },
        "required": ["city"]
    }
)
```

---

### Streaming: Missing Final Thoughts

**Symptoms**: Thought signature not received in streaming mode.

**Cause**: Not checking final chunks with empty text.

**Solution**: Check all chunks for signatures, even if `text` is empty.

```python
for chunk in client.models.generate_content_stream(
    model="gemini-3-flash-preview",
    contents="Explain recursion"
):
    # Print text
    if chunk.text:
        print(chunk.text, end="")
    
    # Check for signatures in ALL chunks (including empty text)
    if hasattr(chunk, 'candidates') and len(chunk.candidates) > 0:
        for part in chunk.candidates[0].content.parts:
            if hasattr(part, 'thought_signature') and part.thought_signature:
                # Save for next turn
                saved_signature = part.thought_signature
```

---

## Quick Reference Tables

### Model Selection Matrix

| Use Case | Recommended Model | Thinking Level |
|----------|------------------|----------------|
| Code debugging, bug finding | Gemini 3.1 Pro | `high` |
| Complex math, research | Gemini 3.1 Pro | `high` |
| Code review, architecture | Gemini 3 Flash | `medium` |
| Document analysis (PDF) | Gemini 3 Flash | `medium` |
| Translation | Gemini 3 Flash | `low` |
| Summarization | Gemini 3 Flash | `low` |
| Chat, FAQ, simple Q&A | Gemini 3.1 Flash-Lite | `minimal` |
| Formatting, data extraction | Gemini 3.1 Flash-Lite | `minimal` |
| High-quality image generation | Gemini 3 Pro Image | N/A |
| High-volume image generation | Gemini 3.1 Flash Image | N/A |

---

### Thinking Levels by Model

| Thinking Level | 3.1 Pro | 3 Flash | 3.1 Flash-Lite | Latency Impact | Cost Impact |
|----------------|---------|---------|----------------|----------------|-------------|
| `minimal` | ❌ | ✅ | ✅ (Default) | Lowest | Lowest |
| `low` | ✅ | ✅ | ✅ | Low | Low |
| `medium` | ✅ | ✅ | ✅ | Moderate | Moderate |
| `high` | ✅ (Default) | ✅ (Default) | ✅ | High | High |

---

### Media Resolution Guide

| Media Type | Task | Recommended Level | Tokens (Image) | Tokens (Video/Frame) |
|------------|------|------------------|----------------|---------------------|
| Image | General analysis | `media_resolution_high` | 1120 | N/A |
| Image | Quick glance | `media_resolution_medium` | 560 | N/A |
| PDF | Document extraction | `media_resolution_medium` | 560 | N/A |
| PDF | Dense text OCR | `media_resolution_high` | 1120 | N/A |
| Video | Action recognition | `media_resolution_low` | N/A | 70 |
| Video | Scene description | `media_resolution_medium` | N/A | 70 |
| Video | Text OCR in frames | `media_resolution_high` | N/A | 280 |

---

### API Endpoints

| Endpoint | Gemini Model | OpenAI Compatible |
|----------|--------------|-------------------|
| `generativelanguage.googleapis.com/v1beta` | ✅ Primary | ❌ |
| `generativelanguage.googleapis.com/v1alpha` | ✅ Alpha features | ❌ |
| `generativelanguage.googleapis.com/v1beta/openai` | ✅ Via adapter | ✅ |

---

### Error Codes

| Code | Meaning | Common Cause | Solution |
|------|---------|--------------|----------|
| 400 | Bad Request | Missing thought signature | Use SDK chat session or preserve signatures manually |
| 400 | Bad Request | `thinking_level` + `thinking_budget` conflict | Remove `thinking_budget`, use only `thinking_level` |
| 400 | Invalid Argument | Unsupported parameter combination | Check API documentation for compatibility |
| 429 | Too Many Requests | Rate limit exceeded | Implement exponential backoff retry |
| 500 | Internal Server Error | Temporary service issue | Retry with backoff |
| 503 | Service Unavailable | Model overloaded | Retry or use different model |

---

## Glossary

**Thinking Level**: Parameter controlling the depth of internal reasoning before generating a response. Higher levels produce more carefully reasoned outputs but increase latency.

**Thought Signature**: Encrypted representation of the model's internal reasoning context, required to maintain coherent multi-turn workflows.

**Media Resolution**: Controls the number of tokens allocated to processing visual inputs (images, videos, PDFs). Higher resolutions improve detail recognition but increase cost and latency.

**Dynamic Thinking**: Gemini 3's adaptive reasoning mechanism that adjusts thinking depth based on query complexity within the specified `thinking_level`.

**Grounding**: Using external data sources (Google Search, URLs) to verify facts and enhance generation accuracy.

**Structured Outputs**: Enforcing a specific JSON schema on model responses using `response_json_schema`.

**Code Execution**: Built-in Python runtime that allows the model to write and execute code to solve problems or manipulate data.

**Multimodal Function Calling**: Function responses that contain images, videos, or other media in addition to text.

**Context Window**: Maximum number of input tokens the model can process in a single request (1M for Pro/Flash, 128k for Flash Image, 65k for Pro Image).

**Token**: Basic unit of text/data processing. Roughly 4 characters of English text = 1 token.

**Computer Use**: Tool that allows the model to interact with graphical user interfaces (click, type, navigate).

**Streaming**: Incremental response delivery where text is sent in chunks as it's generated, reducing perceived latency.

**Temperature**: Controls randomness in output generation. Gemini 3 is optimized for `temperature=1.0`.

---

*End of Documentation*