# OpenAI Image Generation, Editing & Vision

## Table of Contents
1. [Overview](#overview)
2. [Model Comparison](#model-comparison)
3. [API Choices](#api-choices)
4. [Generate Images](#generate-images)
5. [Multi-Turn Image Generation](#multi-turn-image-generation)
6. [Generate vs Edit (Action Parameter)](#generate-vs-edit)
7. [Edit Images](#edit-images)
8. [Inpainting with Masks](#inpainting-with-masks)
9. [Input Fidelity](#input-fidelity)
10. [Customize Image Output](#customize-image-output)
11. [Streaming Images](#streaming-images)
12. [Analyze Images (Vision)](#analyze-images-vision)
13. [Cost Calculation](#cost-calculation)
14. [Limitations](#limitations)
15. [Content Moderation](#content-moderation)

---

## Overview

The OpenAI API provides image generation and editing through two APIs:

- **Image API** — Standalone endpoints for generations, edits, and variations
- **Responses API** — Image generation as a built-in tool within conversations

Both APIs support GPT Image models (`gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini`).

---

## Model Comparison

| Model | Endpoints | Use Case |
|-------|-----------|----------|
| **GPT Image 1.5** | Image API + Responses API | State-of-the-art quality, best overall |
| **GPT Image 1** | Image API + Responses API | Superior instruction following, text rendering |
| **GPT Image 1 Mini** | Image API + Responses API | Cost-effective, lower quality priority |
| DALL·E 3 *(deprecated)* | Image API: Generations only | Higher quality than DALL·E 2 |
| DALL·E 2 *(deprecated)* | Image API: Generations, Edits, Variations | Inpainting, concurrent requests |

> **Recommendation**: Use `gpt-image-1.5` for best quality. Use `gpt-image-1-mini` for cost efficiency.

> DALL·E 2 and DALL·E 3 are deprecated and will stop being supported on 05/12/2026.

---

## API Choices

| Need | Recommended API |
|------|----------------|
| Single image from one prompt | Image API |
| Conversational, editable image experiences | Responses API |
| Multi-turn editing | Responses API |
| File ID–based image inputs | Responses API |

---

## Generate Images

### Via Responses API

```python
from openai import OpenAI
import base64

client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
)

# Extract and save the image
image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    image_base64 = image_data[0]
    with open("otter.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
```

### Generate Multiple Images

Set the `n` parameter to generate multiple images in a single request (defaults to 1).

### Revised Prompt

When using the Responses API, the mainline model automatically revises your prompt for improved performance. Access it via the `revised_prompt` field:

```json
{
  "id": "ig_123",
  "type": "image_generation_call",
  "status": "completed",
  "revised_prompt": "A gray tabby cat hugging an otter. The otter is wearing an orange scarf...",
  "result": "..."
}
```

---

## Multi-Turn Image Generation

Build multi-turn conversations involving image generation using:

1. **`previous_response_id`** — Reference a previous response to continue the conversation
2. **Image ID** — Provide image generation call outputs within context

### Using previous_response_id

```python
from openai import OpenAI
import base64

client = OpenAI()

# First turn
response = client.responses.create(
    model="gpt-5",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
)

image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    with open("cat_and_otter.png", "wb") as f:
        f.write(base64.b64decode(image_data[0]))

# Follow-up turn
response_fwup = client.responses.create(
    model="gpt-5",
    previous_response_id=response.id,
    input="Now make it look realistic",
    tools=[{"type": "image_generation"}],
)

image_data_fwup = [
    output.result
    for output in response_fwup.output
    if output.type == "image_generation_call"
]

if image_data_fwup:
    with open("cat_and_otter_realistic.png", "wb") as f:
        f.write(base64.b64decode(image_data_fwup[0]))
```

---

## Generate vs Edit

The optional `action` parameter (supported on `gpt-image-1.5` and `chatgpt-image-latest`) controls behavior:

| Action | Behavior |
|--------|----------|
| `"auto"` | Model decides whether to generate or edit (recommended) |
| `"generate"` | Always create a new image |
| `"edit"` | Force editing (requires an image in context) |

### Force Generation

```python
response = client.responses.create(
    model="gpt-5",
    input="Generate an image of gray tabby cat hugging an otter",
    tools=[{"type": "image_generation", "action": "generate"}],
)
```

> If you force `"edit"` without providing an image in context, the call returns an error.

When `action` is `"auto"`, the result includes an `action` field showing what the model chose:

```json
{
  "id": "ig_123...",
  "type": "image_generation_call",
  "status": "completed",
  "action": "generate",
  "result": "/9j/4...",
  "revised_prompt": "..."
}
```

---

## Edit Images

### Using Reference Images

Provide one or more images as references to generate a new image. Input images can be supplied as:

1. **Fully qualified URL**
2. **Base64-encoded data URL**
3. **File ID** (created with the Files API)

```python
from openai import OpenAI
import base64

client = OpenAI()

prompt = """Generate a photorealistic image of a gift basket on a white background 
labeled 'Relax & Unwind' with a ribbon and handwriting-like font, 
containing all the items in the reference pictures."""

response = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image1}",
                },
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image2}",
                },
                {
                    "type": "input_image",
                    "file_id": file_id1,
                },
                {
                    "type": "input_image",
                    "file_id": file_id2,
                },
            ],
        }
    ],
    tools=[{"type": "image_generation"}],
)

image_generation_calls = [
    output
    for output in response.output
    if output.type == "image_generation_call"
]

image_data = [output.result for output in image_generation_calls]

if image_data:
    with open("gift-basket.png", "wb") as f:
        f.write(base64.b64decode(image_data[0]))
```

---

## Inpainting with Masks

Edit parts of an image by providing a mask indicating which areas should be replaced.

### Mask Requirements

- Image and mask must be the **same format and size** (< 50 MB)
- Mask must contain an **alpha channel**
- GPT Image masking is **prompt-based** — the model uses the mask as guidance but may not follow its exact shape
- If multiple input images are provided, the mask is applied to the **first image**

### Example

```python
from openai import OpenAI
import base64

client = OpenAI()

file_id = create_file("sunlit_lounge.png")
mask_id = create_file("mask.png")

response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "generate an image of the same sunlit indoor lounge area with a pool but the pool should contain a flamingo",
                },
                {
                    "type": "input_image",
                    "file_id": file_id,
                },
            ],
        },
    ],
    tools=[
        {
            "type": "image_generation",
            "quality": "high",
            "input_image_mask": {
                "file_id": mask_id,
            },
        },
    ],
)

image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    with open("lounge.png", "wb") as f:
        f.write(base64.b64decode(image_data[0]))
```

---

## Input Fidelity

Control how well input image details are preserved in the output.

| Fidelity | Description |
|----------|-------------|
| `"low"` | Default — standard detail preservation |
| `"high"` | Better preserves faces, logos, fine details |

### Model-Specific Behavior

- **`gpt-image-1` / `gpt-image-1-mini`**: First image gets richest texture/detail preservation
- **`gpt-image-1.5`**: First 5 input images get higher fidelity

> High input fidelity uses more image input tokens per request.

### Example

```python
from openai import OpenAI
import base64

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Add the logo to the woman's top, as if stamped into the fabric."},
                {
                    "type": "input_image",
                    "image_url": "https://cdn.openai.com/API/docs/images/woman_futuristic.jpg",
                },
                {
                    "type": "input_image",
                    "image_url": "https://cdn.openai.com/API/docs/images/brain_logo.png",
                },
            ],
        }
    ],
    tools=[{"type": "image_generation", "input_fidelity": "high", "action": "edit"}],
)

image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    with open("woman_with_logo.png", "wb") as f:
        f.write(base64.b64decode(image_data[0]))
```

---

## Customize Image Output

### Available Options

| Option | Values | Default |
|--------|--------|---------|
| `size` | `1024x1024`, `1536x1024`, `1024x1536`, `auto` | `auto` (1024x1024) |
| `quality` | `low`, `medium`, `high`, `auto` | `auto` |
| `output_format` | `png`, `jpeg`, `webp` | `png` |
| `output_compression` | 0–100 (jpeg/webp only) | — |
| `background` | `opaque`, `transparent` | `opaque` |

> `jpeg` is faster than `png` — prioritize it when latency matters.

> Transparency only works with `png` and `webp` formats, and works best at `medium` or `high` quality.

### Transparent Background Example

```python
import openai
import base64

response = openai.responses.create(
    model="gpt-5",
    input="Draw a 2D pixel art style sprite sheet of a tabby gray cat",
    tools=[
        {
            "type": "image_generation",
            "background": "transparent",
            "quality": "high",
        }
    ],
)

image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    with open("sprite.png", "wb") as f:
        f.write(base64.b64decode(image_data[0]))
```

---

## Streaming Images

Stream partial images as they are generated for interactive experiences.

### `partial_images` Parameter

| Value | Behavior |
|-------|----------|
| `0` | Only receive the final image |
| `1`–`3` | Receive up to N partial images (may receive fewer if generation is fast) |

### Example

```python
from openai import OpenAI
import base64

client = OpenAI()

stream = client.responses.create(
    model="gpt-4.1",
    input="Draw a gorgeous image of a river made of white owl feathers through a winter landscape",
    stream=True,
    tools=[{"type": "image_generation", "partial_images": 2}],
)

for event in stream:
    if event.type == "response.image_generation_call.partial_image":
        idx = event.partial_image_index
        image_base64 = event.partial_image_b64
        image_bytes = base64.b64decode(image_base64)
        with open(f"river{idx}.png", "wb") as f:
            f.write(image_bytes)
```

---

## Analyze Images (Vision)

Models can understand images — objects, shapes, colors, textures, and embedded text.

### Input Methods

1. **URL**: Fully qualified image URL
2. **Base64**: Data URL with base64-encoded image
3. **File ID**: Created with the Files API

### Basic Vision Example

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "what's in this image?"},
            {
                "type": "input_image",
                "image_url": "https://example.com/image.jpg",
            },
        ],
    }],
)

print(response.output_text)
```

### Image Input Requirements

| Requirement | Details |
|-------------|---------|
| Supported formats | PNG, JPEG, WEBP, non-animated GIF |
| Size limits | Up to 512 MB total per request, up to 1500 images per request |
| Other | No watermarks/logos, no NSFW, clear enough for human understanding |

### Detail Levels

Control image processing fidelity with the `detail` parameter:

| Level | Best For | Description |
|-------|----------|-------------|
| `"low"` | Fast, low-cost tasks | 512×512 low-res version |
| `"high"` | Standard high-fidelity understanding | Default for detailed analysis |
| `"original"` | Large, dense, spatial images, computer use | Available on `gpt-5.4`+ only |
| `"auto"` | Let the model decide | Default |

```json
{
    "type": "input_image",
    "image_url": "https://example.com/image.jpg",
    "detail": "original"
}
```

### Model Sizing Behavior

| Model Family | Supported Detail | Behavior |
|-------------|-----------------|----------|
| `gpt-5.4`+ | low, high, original, auto | `high`: max 2,500 patches or 2048px. `original`: max 10,000 patches or 6000px |
| `gpt-5.4-mini`, `gpt-5-mini`, `o4-mini`, etc. | low, high, auto | `high`: max 1,536 patches or 2048px |
| `gpt-4o`, `gpt-4.1`, `o1`, `o3` | low, high, auto | Tile-based resizing (512px tiles) |

---

## Cost Calculation

### Image Generation Output Tokens

| Quality | 1024×1024 | 1024×1536 | 1536×1024 |
|---------|-----------|-----------|-----------|
| Low | 272 tokens | 408 tokens | 400 tokens |
| Medium | 1,056 tokens | 1,584 tokens | 1,568 tokens |
| High | 4,160 tokens | 6,240 tokens | 6,208 tokens |

**Total cost** = input text tokens + input image tokens (if editing) + image output tokens.

### Vision Input Tokenization

**Patch-based** (newer models): Images are covered with 32×32px patches. Each model has a patch budget and a token multiplier:

| Model | Multiplier |
|-------|-----------|
| `gpt-5.4-mini` | 1.62 |
| `gpt-5.4-nano` | 2.46 |
| `gpt-5-mini` | 1.62 |
| `gpt-5-nano` | 2.46 |
| `o4-mini` | 1.72 |

**Tile-based** (GPT-4o/4.1/o-series): Images are resized to fit 2048×2048, shortest side scaled to 768px, then split into 512px tiles.

| Model | Base Tokens | Tile Tokens |
|-------|------------|-------------|
| `gpt-5` | 70 | 140 |
| `gpt-4o`, `gpt-4.1` | 85 | 170 |
| `gpt-4o-mini` | 2,833 | 5,667 |
| `o1`, `o3` | 75 | 150 |

---

## Limitations

- **Latency**: Complex prompts may take up to 2 minutes
- **Text rendering**: Improved over DALL·E but can still struggle with precise placement
- **Consistency**: May struggle with recurring characters across generations
- **Composition control**: Difficulty with precise element placement in layout-sensitive compositions
- **Medical images**: Not suitable for interpreting CT scans or medical advice
- **Rotation**: May misinterpret rotated or upside-down text/images
- **Spatial reasoning**: Struggles with precise localization (e.g. chess positions)
- **Counting**: May give approximate counts for objects

---

## Content Moderation

All prompts and generated images are filtered per OpenAI's content policy.

### Moderation Parameter

| Value | Behavior |
|-------|----------|
| `"auto"` (default) | Standard filtering for age-inappropriate content |
| `"low"` | Less restrictive filtering |

```python
tools=[{"type": "image_generation", "moderation": "low"}]
```
