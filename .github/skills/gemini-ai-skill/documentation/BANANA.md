# Nano Banana Image Generation API - Complete Documentation

## Overview

Nano Banana is Gemini's native image generation capability that allows you to create, edit, and iterate on images conversationally using text prompts, images, or combinations of both. All generated images include a SynthID watermark for authenticity verification.

### Available Models

| Model Name | Model Code | Type | Use Case |
|------------|-----------|------|----------|
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | Preview | High-efficiency, optimized for speed and high-volume developer use cases |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | Preview | Professional asset production with advanced reasoning ("Thinking") |
| **Nano Banana** | `gemini-2.5-flash-image` | Stable | Speed and efficiency for high-volume, low-latency tasks |

### Key Capabilities

- **Text-to-Image**: Generate images from descriptive prompts
- **Image-to-Image**: Edit and transform existing images
- **Multi-turn Editing**: Iterate conversationally on generated images
- **High Resolution**: Up to 4K output (model-dependent)
- **Text Rendering**: Generate legible, stylized text in images
- **Google Search Grounding**: Generate images based on real-time information
- **Google Image Search**: Use web images as visual context (3.1 Flash only)
- **Multiple Reference Images**: Use up to 14 images as input (model-dependent)
- **Character Consistency**: Maintain consistent appearance across generations
- **Thinking Mode**: Advanced reasoning for complex prompts (Gemini 3 models)

---

## Installation & Setup

### Required Imports

```python
from google import genai
from google.genai import types
from PIL import Image
```

### Initialize Client

```python
client = genai.Client()
```

---

## Model Specifications

### Nano Banana 2 (Gemini 3.1 Flash Image Preview)

**Model Code**: `gemini-3.1-flash-image-preview`

| Feature | Specification |
|---------|--------------|
| **Status** | Preview |
| **Resolution** | 512, 1K, 2K, 4K |
| **Default Resolution** | 1K (1024px) |
| **Aspect Ratios** | 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9 |
| **Reference Images** | Up to 14 total (10 objects + 4 characters) |
| **Character Consistency** | Up to 4 characters |
| **Thinking Levels** | Minimal, High |
| **Google Search** | Web Search + Image Search |
| **Best For** | High-volume developer use, speed optimization |

### Nano Banana Pro (Gemini 3 Pro Image Preview)

**Model Code**: `gemini-3-pro-image-preview`

| Feature | Specification |
|---------|--------------|
| **Status** | Preview |
| **Resolution** | 1K, 2K, 4K |
| **Default Resolution** | 1K (1024px) |
| **Aspect Ratios** | 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9 |
| **Reference Images** | Up to 14 total (6 objects + 5 characters) |
| **Character Consistency** | Up to 5 characters |
| **Thinking Mode** | Always enabled (advanced reasoning) |
| **Google Search** | Web Search only |
| **Best For** | Professional asset production, complex instructions |

### Nano Banana (Gemini 2.5 Flash Image)

**Model Code**: `gemini-2.5-flash-image`

| Feature | Specification |
|---------|--------------|
| **Status** | Stable |
| **Resolution** | 1024px fixed |
| **Aspect Ratios** | 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9 |
| **Reference Images** | Up to 3 images |
| **Thinking Mode** | Not available |
| **Google Search** | Not available |
| **Best For** | High-volume, low-latency tasks |

---

## API Reference

### Main Method: `generate_content()`

```python
response = client.models.generate_content(
    model=str,                        # Required: Model ID
    contents=list,                    # Required: Prompts and/or images
    config=GenerateContentConfig()    # Optional: Configuration
)
```

### Configuration Parameters

#### `GenerateContentConfig`

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `response_modalities` | `list[str]` | Output types: `['TEXT', 'IMAGE']` or `['IMAGE']` | `['TEXT', 'IMAGE']` |
| `image_config` | `ImageConfig` | Image generation settings | None |
| `tools` | `list[Tool]` | Enable Google Search grounding | None |
| `thinking_config` | `ThinkingConfig` | Control thinking levels (3.1 Flash only) | None |

#### `ImageConfig`

| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| `aspect_ratio` | `string` | See Aspect Ratio table | Output image aspect ratio |
| `image_size` | `string` | `"512"`, `"1K"`, `"2K"`, `"4K"` | Output resolution (3.1 Flash/3 Pro only) |

**Important**: Use uppercase 'K' (e.g., `"1K"`, `"2K"`, `"4K"`). The `"512"` value does not use a 'K' suffix.

#### `ThinkingConfig` (Gemini 3.1 Flash Image only)

| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| `thinking_level` | `string` | `"minimal"`, `"high"` | Amount of reasoning applied |
| `include_thoughts` | `boolean` | `true`, `false` | Return thinking process in response |

**Note**: Thinking tokens are billed regardless of `include_thoughts` setting.

#### Google Search Tool

```python
# Web Search only
tools=[{"google_search": {}}]

# Web Search + Image Search (3.1 Flash only)
tools=[
    types.Tool(google_search=types.GoogleSearch(
        search_types=types.SearchTypes(
            web_search=types.WebSearch(),
            image_search=types.ImageSearch()
        )
    ))
]
```

---

## Usage Examples

### 1. Basic Text-to-Image Generation

Generate an image from a text prompt:

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
)

# Process response
for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
```

---

### 2. Image Editing (Image-to-Image)

Modify an existing image with text instructions:

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = """Create a picture of my cat eating a nano-banana in a 
fancy restaurant under the Gemini constellation"""

image = Image.open("/path/to/cat_image.png")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, image],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("edited_image.png")
```

**Use Cases**:
- Add or remove elements
- Change style or color grading
- Modify backgrounds
- Transform artistic styles

---

### 3. Multi-Turn Image Editing (Conversational)

Iterate on images through chat interactions:

```python
from google import genai
from google.genai import types

client = genai.Client()

# Create a chat session
chat = client.chats.create(
    model="gemini-3.1-flash-image-preview",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        tools=[{"google_search": {}}]
    )
)

# First turn: Generate initial image
message1 = """Create a vibrant infographic that explains photosynthesis 
as if it were a recipe for a plant's favorite food. Show the "ingredients" 
(sunlight, water, CO2) and the "finished dish" (sugar/energy). The style 
should be like a page from a colorful kids' cookbook, suitable for a 4th grader."""

response1 = chat.send_message(message1)

for part in response1.parts:
    if part.text is not None:
        print(part.text)
    elif image := part.as_image():
        image.save("photosynthesis.png")

# Second turn: Modify the image
message2 = "Update this infographic to be in Spanish. Do not change any other elements of the image."

response2 = chat.send_message(
    message2,
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        ),
    )
)

for part in response2.parts:
    if part.text is not None:
        print(part.text)
    elif image := part.as_image():
        image.save("photosynthesis_spanish.png")
```

**Benefits**:
- Maintain context across edits
- Incremental refinements
- Natural conversation flow

---

### 4. Control Aspect Ratio and Resolution

Generate images with specific dimensions:

```python
from google import genai
from google.genai import types

client = genai.Client()

prompt = """Da Vinci style anatomical sketch of a dissected Monarch butterfly. 
Detailed drawings of the head, wings, and legs on textured parchment with notes in English."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",    # Square format
            image_size="4K"        # Ultra high resolution
        ),
    )
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif image := part.as_image():
        image.save("butterfly_4k.png")
```

**Available Aspect Ratios**:
- Square: `1:1`
- Portrait: `2:3`, `3:4`, `4:5`, `9:16`
- Landscape: `3:2`, `4:3`, `5:4`, `16:9`, `21:9`
- Ultra-wide: `4:1`, `8:1`, `1:4`, `1:8` (3.1 Flash only)

**Available Resolutions**:
- `"512"` - 512px (3.1 Flash only)
- `"1K"` - 1024px (default)
- `"2K"` - 2048px
- `"4K"` - 4096px

---

### 5. Using Multiple Reference Images

Use up to 14 images as references for character consistency and object fidelity:

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = "An office group photo of these people, they are making funny faces."

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        prompt,
        Image.open('person1.png'),
        Image.open('person2.png'),
        Image.open('person3.png'),
        Image.open('person4.png'),
        Image.open('person5.png'),
    ],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="5:4",
            image_size="2K"
        ),
    )
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif image := part.as_image():
        image.save("office_photo.png")
```

**Reference Image Limits**:

| Model | Objects (High-Fidelity) | Characters (Consistency) | Total |
|-------|------------------------|-------------------------|-------|
| 3.1 Flash Image | Up to 10 | Up to 4 | 14 |
| 3 Pro Image | Up to 6 | Up to 5 | 14 |
| 2.5 Flash Image | Up to 3 | Up to 3 | 3 |

---

### 6. Grounding with Google Search (Web Search)

Generate images based on real-time information:

```python
from google import genai
from google.genai import types

client = genai.Client()

prompt = """Visualize the current weather forecast for the next 5 days 
in San Francisco as a clean, modern weather chart. Add a visual on what 
I should wear each day"""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
        ),
        tools=[{"google_search": {}}]  # Enable web search
    )
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif image := part.as_image():
        image.save("weather_forecast.png")

# Access grounding metadata
if response.candidates and response.candidates[0].grounding_metadata:
    metadata = response.candidates[0].grounding_metadata
    # searchEntryPoint contains HTML/CSS for search suggestions
    # groundingChunks contains top 3 web sources used
```

**Grounding Response Fields**:
- `searchEntryPoint`: HTML/CSS for required search suggestions
- `groundingChunks`: Top 3 web sources used for grounding
- Must display search suggestions in UI when using grounding

---

### 7. Grounding with Google Image Search (3.1 Flash Only)

Use web images as visual context for generation:

```python
from google import genai
from google.genai import types
from IPython.display import HTML, display

client = genai.Client()

prompt = "A detailed painting of a Timareta butterfly resting on a flower"

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        tools=[
            types.Tool(google_search=types.GoogleSearch(
                search_types=types.SearchTypes(
                    web_search=types.WebSearch(),
                    image_search=types.ImageSearch()
                )
            ))
        ]
    )
)

# Display grounding sources
if (response.candidates and 
    response.candidates[0].grounding_metadata and 
    response.candidates[0].grounding_metadata.search_entry_point):
    display(HTML(response.candidates[0].grounding_metadata.search_entry_point.rendered_content))

for part in response.parts:
    if image := part.as_image():
        image.save("butterfly_painting.png")
```

**Image Search Response Fields**:
- `imageSearchQueries`: Queries used for image search
- `groundingChunks`: Contains image sources with redirect URLs
  - `uri`: Web page URL (landing page) - **required for attribution**
  - `image_uri`: Direct image URL
- `groundingSupports`: Maps content to citation sources
- `searchEntryPoint`: "Google Search" chip with HTML/CSS

**Display Requirements**:
1. **Source Attribution**: Must provide link to webpage containing source image
2. **Direct Navigation**: Single-click path from source images to webpage
3. **No Multi-click Delays**: Cannot use intermediate image viewers

---

### 8. Controlling Thinking Levels (3.1 Flash Only)

Balance quality and latency by controlling thinking intensity:

```python
from google import genai
from google.genai import types

client = genai.Client()

prompt = "A futuristic city built inside a giant glass bottle floating in space"

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        thinking_config=types.ThinkingConfig(
            thinking_level="high",      # "minimal" or "high"
            include_thoughts=True       # View the thinking process
        ),
    )
)

# Process thoughts (optional)
for part in response.parts:
    if part.thought:  # Skip thought parts
        if part.text:
            print("Thought:", part.text)
        elif image := part.as_image():
            print("Thought image generated")
        continue
    
    # Final output
    if part.text:
        print(part.text)
    elif image := part.as_image():
        image.save("futuristic_city.png")
```

**Thinking Levels**:
- `"minimal"` (default): Faster generation, less reasoning
- `"high"`: More reasoning, better quality for complex prompts

**Note**: Thinking tokens are **always billed** even if `include_thoughts=False`.

---

### 9. Image-Only Output (No Text)

Generate only images without accompanying text:

```python
from google import genai
from google.genai import types

client = genai.Client()

prompt = "A minimalist logo for a coffee shop called 'Morning Brew'"

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE']  # Only images, no text
    )
)

for part in response.parts:
    if image := part.as_image():
        image.save("logo.png")
```

---

### 10. Sequential Art & Comic Panels

Create multi-panel stories with character consistency:

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

# Input character image
character_image = Image.open("man_with_glasses.png")

prompt = """Make a 3 panel comic in a gritty, noir art style. 
Put the character in a dark alley confrontation scene."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, character_image],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="21:9",
            image_size="2K"
        ),
    )
)

for part in response.parts:
    if part.text:
        print(part.text)
    elif image := part.as_image():
        image.save("comic_panels.png")
```

---

## Thought Signatures

Thought signatures are encrypted representations of the model's internal thought process, used to preserve reasoning context across multi-turn interactions.

### Key Points

- **Automatic Handling**: SDKs automatically manage thought signatures in chat mode
- **Manual Handling**: If building custom history, pass signatures back exactly as received
- **Failure Risk**: Not circulating signatures may cause responses to fail

### Signature Rules

1. All `inline_data` image parts in final response have signatures
2. First text part after thoughts has a signature
3. Thought images do NOT have signatures
4. Subsequent text parts do NOT have signatures

### Example Structure

```json
[
  {
    "inline_data": {"data": "<base64>", "mime_type": "image/png"},
    "thought": true  // No signature
  },
  {
    "text": "Here is...",
    "thought_signature": "<Signature_A>"  // First non-thought has signature
  },
  {
    "inline_data": {"data": "<base64>", "mime_type": "image/png"},
    "thought_signature": "<Signature_B>"  // Image parts have signatures
  },
  {
    "text": "Step 2..."  // Follow-up text: no signature
  }
]
```

---

## Batch Image Generation

For high-volume image generation, use the Batch API for higher rate limits with up to 24-hour turnaround.

```python
# See Batch API documentation for complete examples
# https://ai.google.dev/api/batch
```

**Benefits**:
- Higher rate limits
- Cost-effective for bulk generation
- Asynchronous processing

**Trade-offs**:
- Up to 24-hour delay
- Not suitable for real-time applications

---

## Prompt Writing Guide

Master image generation by writing descriptive, narrative prompts rather than keyword lists. The model's deep language understanding produces better results from detailed paragraphs.

### Core Principle

✅ **Do**: Describe the scene narratively
```
A photorealistic close-up portrait of an elderly Japanese ceramicist, her weathered hands 
carefully shaping a clay bowl on a spinning wheel. Soft, natural light streams through a 
paper shoji screen, illuminating fine details like the texture of the clay and the concentration 
in her eyes. Shot with a 50mm lens at f/1.8, creating a shallow depth of field.
```

❌ **Don't**: List keywords
```
ceramicist, hands, clay, wheel, light, japanese, portrait
```

---

### Prompt Templates by Use Case

#### 1. Photorealistic Scenes

Use photography terminology for realistic images.

**Template**:
```
A photorealistic [shot type] of [subject], [action or expression], set in
[environment]. The scene is illuminated by [lighting description], creating
a [mood] atmosphere. Captured with a [camera/lens details], emphasizing
[key textures and details]. The image should be in a [aspect ratio] format.
```

**Example**:
```python
prompt = """A photorealistic close-up portrait of an elderly Japanese ceramicist, 
her weathered hands carefully shaping a clay bowl on a spinning wheel. Soft, natural 
light streams through a paper shoji screen, illuminating fine details like the texture 
of the clay and the concentration in her eyes. Shot with a 50mm lens at f/1.8, creating 
a shallow depth of field. 3:2 aspect ratio."""
```

**Photography Terms**:
- **Shot types**: Close-up, wide shot, medium shot, extreme close-up
- **Angles**: Eye-level, low angle, high angle, bird's eye view, worm's eye
- **Lenses**: 50mm, 35mm, macro lens, wide-angle lens, telephoto
- **Lighting**: Natural light, golden hour, soft light, hard light, studio lighting
- **Depth of field**: Shallow (f/1.8), deep (f/16), bokeh effect

---

#### 2. Stylized Illustrations & Stickers

Perfect for icons, stickers, and design assets.

**Template**:
```
A [style] sticker of a [subject], featuring [key characteristics] and a
[color palette]. The design should have [line style] and [shading style].
The background must be transparent.
```

**Example**:
```python
prompt = """A kawaii-style sticker of a happy red panda holding a bamboo shoot, 
featuring large sparkling eyes and rosy cheeks, with a warm pastel color palette 
of oranges and creams. The design should have smooth, rounded line work and soft, 
gradient shading. The background must be transparent."""
```

**Style Keywords**:
- Kawaii, chibi, flat design, minimalist, geometric
- Vector art, line art, pixel art, watercolor
- Vintage, retro, modern, futuristic

---

#### 3. Accurate Text in Images

Generate legible text for infographics, logos, and marketing materials.

**Template**:
```
Create a [image type] for [brand/concept] with the text "[text to render]"
in a [font style]. The design should be [style description], with a
[color scheme].
```

**Example**:
```python
prompt = """Create a modern, minimalist logo for a coffee shop called 'The Daily Grind' 
with the text clearly displayed in a bold, sans-serif font. The design should feature 
a simple coffee bean icon integrated with the letter 'D', using an earthy color scheme 
of deep browns and warm beiges on a cream background."""
```

**Best Practices for Text**:
- Place text in quotes: `"The Daily Grind"`
- Describe font descriptively: "bold sans-serif", "elegant serif", "handwritten script"
- Specify text placement: "centered", "top-left corner", "along the bottom"
- Use Nano Banana Pro for professional text-heavy assets

---

#### 4. Product Mockups & Commercial Photography

Create professional product shots for e-commerce and advertising.

**Template**:
```
A high-resolution, studio-lit product photograph of a [product description]
on a [background surface/description]. The lighting is a [lighting setup]
to [lighting purpose]. The camera angle is a [angle type] to showcase
[specific feature]. Ultra-realistic, with sharp focus on [key detail]. [Aspect ratio].
```

**Example**:
```python
prompt = """A high-resolution, studio-lit product photograph of a minimalist ceramic 
coffee mug with a matte black finish on a light oak wooden surface. The lighting is 
a three-point softbox setup to eliminate harsh shadows and highlight the mug's smooth 
texture. The camera angle is a 45-degree angle to showcase the elegant handle and 
clean lines. Ultra-realistic, with sharp focus on the rim detail. 4:3 aspect ratio."""
```

**Lighting Setups**:
- Three-point lighting, softbox, ring light, natural window light
- Backlighting, rim lighting, side lighting
- High-key (bright), low-key (dramatic shadows)

---

#### 5. Minimalist & Negative Space Design

Ideal for backgrounds where text will be overlaid.

**Template**:
```
A minimalist composition featuring a single [subject] positioned in the
[bottom-right/top-left/etc.] of the frame. The background is a vast, empty
[color] canvas, creating significant negative space. Soft, subtle lighting.
[Aspect ratio].
```

**Example**:
```python
prompt = """A minimalist composition featuring a single, delicate red maple leaf 
positioned in the bottom-right of the frame. The background is a vast, empty soft 
cream canvas, creating significant negative space for text overlay. Soft, subtle 
lighting from above casts a gentle shadow. 16:9 aspect ratio."""
```

**Use Cases**:
- Website headers and banners
- Presentation backgrounds
- Social media templates
- Marketing materials with text overlay

---

#### 6. Sequential Art (Comic Panels/Storyboards)

Create visual narratives with character consistency.

**Template**:
```
Make a [number] panel comic in a [style]. Put the character in a [type of scene].
[Additional story/mood details].
```

**Example**:
```python
# With character reference image
character_image = Image.open("man_with_glasses.png")

prompt = """Make a 3 panel comic in a gritty, noir art style. Put the character 
in a dark alley confrontation scene. Show: Panel 1 - character walking cautiously, 
Panel 2 - sudden encounter with shadow figure, Panel 3 - tense standoff. Use high 
contrast black and white with dramatic shadows."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, character_image],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="21:9", image_size="2K")
    )
)
```

**Best with**: Gemini 3 Pro and 3.1 Flash for accurate text and storytelling

---

#### 7. Grounding with Google Search

Generate images based on real-time, factual information.

**Example**:
```python
prompt = """Make a simple but stylish graphic of last night's Arsenal game 
in the Champion's League, showing the final score, key statistics, and team logos."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE'],
        tools=[{"google_search": {}}]
    )
)
```

**Use Cases**:
- Live sports scores and stats
- Weather forecasts and maps
- Stock market charts
- News events visualization
- Current facts and data

---

### Prompt Templates for Image Editing

#### 1. Adding and Removing Elements

**Template**:
```
Using the provided image of [subject], please [add/remove/modify] [element]
to/from the scene. Ensure the change is [description of how the change should
integrate].
```

**Example**:
```python
cat_image = Image.open("ginger_cat.png")

prompt = """Using the provided image of my cat, please add a small, knitted wizard hat 
tilted playfully on its head. The hat should match the lighting and be the same warm, 
cozy aesthetic as the rest of the image. Make it look natural and whimsical."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, cat_image]
)
```

---

#### 2. Inpainting (Semantic Masking)

Edit specific parts while preserving everything else.

**Template**:
```
Using the provided image, change only the [specific element] to [new
element/description]. Keep everything else in the image exactly the same,
preserving the original style, lighting, and composition.
```

**Example**:
```python
room_image = Image.open("living_room.png")

prompt = """Using the provided image of a living room, change only the blue sofa 
to be a vintage, brown leather chesterfield sofa with button tufting. Keep everything 
else in the image exactly the same, preserving the original style, lighting, and composition."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, room_image]
)
```

---

#### 3. Style Transfer

Transform content into different artistic styles.

**Template**:
```
Transform the provided photograph of [subject] into the artistic style of
[artist/art style]. Preserve the original composition but render it with
[description of stylistic elements].
```

**Example**:
```python
city_image = Image.open("city_street.png")

prompt = """Transform the provided photograph of a modern city street at night into 
the artistic style of Vincent van Gogh's Starry Night. Preserve the original composition 
of buildings and street layout but render it with swirling, expressive brushstrokes, 
vibrant blues and yellows, and that characteristic post-impressionist energy."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, city_image]
)
```

**Popular Styles**:
- Van Gogh, Monet, Picasso, Warhol
- Watercolor, oil painting, charcoal sketch
- Anime, pixel art, comic book, film noir

---

#### 4. Advanced Composition (Combining Multiple Images)

Merge elements from multiple images into one scene.

**Template**:
```
Create a new image by combining the elements from the provided images. Take
the [element from image 1] and place it with/on the [element from image 2].
The final image should be a [description of the final scene].
```

**Example**:
```python
dress_image = Image.open("blue_dress.png")
model_image = Image.open("woman_model.png")

prompt = """Create a professional e-commerce fashion photo by combining these images. 
Take the blue floral summer dress from the first image and place it on the woman from 
the second image. The final image should be a clean, studio-lit fashion photograph 
with the woman wearing the dress, standing in a natural pose against a white background."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, dress_image, model_image],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="2:3", image_size="2K")
    )
)
```

---

#### 5. High-Fidelity Detail Preservation

Preserve critical details like faces or logos during edits.

**Template**:
```
Using the provided images, place [element from image 2] onto [element from
image 1]. Ensure that the features of [element from image 1] remain
completely unchanged. The added element should [description of how the
element should integrate].
```

**Example**:
```python
headshot_image = Image.open("professional_headshot.png")
logo_image = Image.open("company_logo.png")

prompt = """Take the first image of the woman with brown hair, blue eyes, and a neutral 
expression, and add the logo from the second image to her shirt as if it's embroidered 
on a polo shirt. Ensure that her facial features, hair, and expression remain completely 
unchanged. The logo should appear naturally placed on the upper left chest area."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, headshot_image, logo_image]
)
```

---

#### 6. Bring Something to Life

Transform sketches into polished images.

**Template**:
```
Turn this rough [medium] sketch of a [subject] into a [style description]
photo. Keep the [specific features] from the sketch but add [new details/materials].
```

**Example**:
```python
sketch_image = Image.open("car_sketch.png")

prompt = """Turn this rough pencil sketch of a sports car into a photorealistic, 
high-resolution photo. Keep the sleek, aerodynamic design from the sketch but add 
realistic metallic paint (deep blue), chrome details, carbon fiber accents, and 
professional studio lighting. Show the car in a modern showroom."""

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, sketch_image],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size="4K")
    )
)
```

---

#### 7. Character Consistency (360° View)

Generate multiple angles of the same character.

**Template**:
```
A studio portrait of [person] against [background], [looking forward/in profile/etc.]
```

**Example**:
```python
# Front view
original_image = Image.open("man_glasses_front.png")

# Generate side view
prompt_side = """A studio portrait of this man against a neutral gray background, 
in profile looking right. Match the lighting and photography style exactly."""

response_side = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt_side, original_image]
)

# Generate back view
prompt_back = """A studio portrait of this man against a neutral gray background, 
facing away showing the back of his head and shoulders."""

response_back = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt_back, original_image, generated_side_image]
)
```

**Tip**: Include previously generated angles in subsequent prompts for better consistency.

---

## Best Practices

### 1. Be Hyper-Specific

Include granular details for maximum control.

❌ **Vague**: "fantasy armor"
✅ **Specific**: "ornate elven plate armor, etched with silver leaf patterns, with a high collar and pauldrons shaped like falcon wings"

### 2. Provide Context and Intent

Explain the purpose to guide the model's composition.

❌ **No context**: "Create a logo"
✅ **With context**: "Create a logo for a high-end, minimalist skincare brand targeting eco-conscious millennials"

### 3. Iterate and Refine

Use conversational follow-ups for incremental improvements.

```python
# First generation
response1 = chat.send_message("Create a sunset beach scene")

# Refinement
response2 = chat.send_message("That's great, but can you make the lighting a bit warmer?")

# Further refinement
response3 = chat.send_message("Perfect! Now add a silhouette of a person walking along the shore")
```

### 4. Use Step-by-Step Instructions

Break complex scenes into sequential steps.

```
First, create a background of a serene, misty forest at dawn with soft golden light 
filtering through the trees. Then, in the foreground, add a moss-covered ancient stone 
altar with intricate Celtic carvings. Finally, place a single, glowing sword standing 
upright on top of the altar, emanating a soft blue light.
```

### 5. Use Semantic Negative Prompts

Describe what you DO want, not what you DON'T want.

❌ **Don't use**: "no cars, no buildings, no people"
✅ **Do use**: "an empty, deserted street surrounded by untouched nature, with no signs of traffic or urban development"

### 6. Control the Camera

Use cinematic terminology for precise composition.

**Camera Terms**:
- **Angles**: Wide-angle shot, macro shot, low-angle perspective, bird's eye view
- **Movement**: Tracking shot, dolly shot, pan, tilt
- **Framing**: Rule of thirds, centered composition, off-center
- **Focus**: Shallow depth of field, deep focus, selective focus

### 7. Match Input Image Quality

For best editing results, use high-quality input images.

✅ **Best**: High-resolution, well-lit, clear subject
⚠️ **Acceptable**: Medium quality with clear subject
❌ **Poor**: Blurry, low-resolution, poorly lit

---

## Aspect Ratio & Resolution Reference

### Gemini 3.1 Flash Image Preview

| Aspect Ratio | 512 | 1K | 2K | 4K | Tokens* |
|--------------|-----|----|----|-----|---------|
| 1:1 | 512×512 | 1024×1024 | 2048×2048 | 4096×4096 | 747-2000 |
| 1:4 | 256×1024 | 512×2048 | 1024×4096 | 2048×8192 | 747-2000 |
| 1:8 | 192×1536 | 384×3072 | 768×6144 | 1536×12288 | 747-2000 |
| 2:3 | 424×632 | 848×1264 | 1696×2528 | 3392×5056 | 747-2000 |
| 3:2 | 632×424 | 1264×848 | 2528×1696 | 5056×3392 | 747-2000 |
| 3:4 | 448×600 | 896×1200 | 1792×2400 | 3584×4800 | 747-2000 |
| 4:1 | 1024×256 | 2048×512 | 4096×1024 | 8192×2048 | 747-2000 |
| 4:3 | 600×448 | 1200×896 | 2400×1792 | 4800×3584 | 747-2000 |
| 4:5 | 464×576 | 928×1152 | 1856×2304 | 3712×4608 | 747-2000 |
| 5:4 | 576×464 | 1152×928 | 2304×1856 | 4608×3712 | 747-2000 |
| 8:1 | 1536×192 | 3072×384 | 6144×768 | 12288×1536 | 747-2000 |
| 9:16 | 384×688 | 768×1376 | 1536×2752 | 3072×5504 | 747-2000 |
| 16:9 | 688×384 | 1376×768 | 2752×1536 | 5504×3072 | 747-2000 |
| 21:9 | 792×168 | 1584×672 | 3168×1344 | 6336×2688 | 747-2000 |

*Token count varies by resolution (512=747, 1K=1120, 2K=1120, 4K=2000)

### Gemini 3 Pro Image Preview

| Aspect Ratio | 1K | 2K | 4K | Tokens* |
|--------------|----|----|-----|---------|
| 1:1 | 1024×1024 | 2048×2048 | 4096×4096 | 1120-2000 |
| 2:3 | 848×1264 | 1696×2528 | 3392×5056 | 1120-2000 |
| 3:2 | 1264×848 | 2528×1696 | 5056×3392 | 1120-2000 |
| 3:4 | 896×1200 | 1792×2400 | 3584×4800 | 1120-2000 |
| 4:3 | 1200×896 | 2400×1792 | 4800×3584 | 1120-2000 |
| 4:5 | 928×1152 | 1856×2304 | 3712×4608 | 1120-2000 |
| 5:4 | 1152×928 | 2304×1856 | 4608×3712 | 1120-2000 |
| 9:16 | 768×1376 | 1536×2752 | 3072×5504 | 1120-2000 |
| 16:9 | 1376×768 | 2752×1536 | 5504×3072 | 1120-2000 |
| 21:9 | 1584×672 | 3168×1344 | 6336×2688 | 1120-2000 |

*Token count: 1K/2K=1120, 4K=2000

### Gemini 2.5 Flash Image

| Aspect Ratio | Dimensions | Tokens |
|--------------|------------|---------|
| 1:1 | 1024×1024 | 1120 |
| 2:3 | 848×1264 | 1120 |
| 3:2 | 1264×848 | 1120 |
| 3:4 | 896×1200 | 1120 |
| 4:3 | 1200×896 | 1120 |
| 4:5 | 928×1152 | 1120 |
| 5:4 | 1152×928 | 1120 |
| 9:16 | 768×1376 | 1120 |
| 16:9 | 1376×768 | 1120 |
| 21:9 | 1584×672 | 1120 |

Fixed at 1024px resolution

---

Prompts for generating images
The following strategies will help you create effective prompts to generate exactly the images you're looking for.

1. Photorealistic scenes
For realistic images, use photography terms. Mention camera angles, lens types, lighting, and fine details to guide the model toward a photorealistic result.

Template
Prompt
Python
JavaScript
Go
Java
REST

A photorealistic [shot type] of [subject], [action or expression], set in
[environment]. The scene is illuminated by [lighting description], creating
a [mood] atmosphere. Captured with a [camera/lens details], emphasizing
[key textures and details]. The image should be in a [aspect ratio] format.
A photorealistic close-up portrait of an elderly Japanese ceramicist...
A photorealistic close-up portrait of an elderly Japanese ceramicist...
2. Stylized illustrations & stickers
To create stickers, icons, or assets, be explicit about the style and request a transparent background.

Template
Prompt
Python
JavaScript
Go
Java
REST

A [style] sticker of a [subject], featuring [key characteristics] and a
[color palette]. The design should have [line style] and [shading style].
The background must be transparent.
A kawaii-style sticker of a happy red...
A kawaii-style sticker of a happy red panda...
3. Accurate text in images
Gemini excels at rendering text. Be clear about the text, the font style (descriptively), and the overall design. Use Gemini 3 Pro Image Preview for professional asset production.

Template
Prompt
Python
JavaScript
Go
Java
REST
Create a [image type] for [brand/concept] with the text "[text to render]"
in a [font style]. The design should be [style description], with a
[color scheme].
Create a modern, minimalist logo for a coffee shop called 'The Daily Grind'...
Create a modern, minimalist logo for a coffee shop called 'The Daily Grind'...
4. Product mockups & commercial photography
Perfect for creating clean, professional product shots for ecommerce, advertising, or branding.

Template
Prompt
Python
JavaScript
Go
Java
REST

A high-resolution, studio-lit product photograph of a [product description]
on a [background surface/description]. The lighting is a [lighting setup,
e.g., three-point softbox setup] to [lighting purpose]. The camera angle is
a [angle type] to showcase [specific feature]. Ultra-realistic, with sharp
focus on [key detail]. [Aspect ratio].
A high-resolution, studio-lit product photograph of a minimalist ceramic coffee mug...
A high-resolution, studio-lit product photograph of a minimalist ceramic coffee mug...
5. Minimalist & negative space design
Excellent for creating backgrounds for websites, presentations, or marketing materials where text will be overlaid.

Template
Prompt
Python
JavaScript
Go
Java
REST

A minimalist composition featuring a single [subject] positioned in the
[bottom-right/top-left/etc.] of the frame. The background is a vast, empty
[color] canvas, creating significant negative space. Soft, subtle lighting.
[Aspect ratio].
A minimalist composition featuring a single, delicate red maple leaf...
A minimalist composition featuring a single, delicate red maple leaf...
6. Sequential art (Comic panel / Storyboard)
Builds on character consistency and scene description to create panels for visual storytelling. For accuracy with text and storytelling ability, these prompts work best with Gemini 3 Pro and Gemini 3.1 Flash Image Preview.

Template
Prompt
Python
JavaScript
Go
Java
REST

Make a 3 panel comic in a [style]. Put the character in a [type of scene].
Input

Output

Man in white glasses
Input image
Make a 3 panel comic in a gritty, noir art style...
Make a 3 panel comic in a gritty, noir art style...
7. Grounding with Google Search
Use Google Search to generate images based on recent or real-time information. This is useful for news, weather, and other time-sensitive topics.

Prompt
Python
JavaScript
Go
Java
REST

Make a simple but stylish graphic of last night's Arsenal game in the Champion's League
AI-generated graphic of an Arsenal football score
AI-generated graphic of an Arsenal football score
Prompts for editing images
These examples show how to provide images alongside your text prompts for editing, composition, and style transfer.

1. Adding and removing elements
Provide an image and describe your change. The model will match the original image's style, lighting, and perspective.

Template
Prompt
Python
JavaScript
Go
Java
REST

Using the provided image of [subject], please [add/remove/modify] [element]
to/from the scene. Ensure the change is [description of how the change should
integrate].
Input

Output

A photorealistic picture of a fluffy ginger cat..
A photorealistic picture of a fluffy ginger cat...
Using the provided image of my cat, please add a small, knitted wizard hat...
Using the provided image of my cat, please add a small, knitted wizard hat...
2. Inpainting (Semantic masking)
Conversationally define a "mask" to edit a specific part of an image while leaving the rest untouched.

Template
Prompt
Python
JavaScript
Go
Java
REST

Using the provided image, change only the [specific element] to [new
element/description]. Keep everything else in the image exactly the same,
preserving the original style, lighting, and composition.
Input

Output

A wide shot of a modern, well-lit living room...
A wide shot of a modern, well-lit living room...
Using the provided image of a living room, change only the blue sofa to be a vintage, brown leather chesterfield sofa...
Using the provided image of a living room, change only the blue sofa to be a vintage, brown leather chesterfield sofa...
3. Style transfer
Provide an image and ask the model to recreate its content in a different artistic style.

Template
Prompt
Python
JavaScript
Go
Java
REST

Transform the provided photograph of [subject] into the artistic style of [artist/art style]. Preserve the original composition but render it with [description of stylistic elements].
Input

Output

A photorealistic, high-resolution photograph of a busy city street...
A photorealistic, high-resolution photograph of a busy city street...
Transform the provided photograph of a modern city street at night...
Transform the provided photograph of a modern city street at night...
4. Advanced composition: Combining multiple images
Provide multiple images as context to create a new, composite scene. This is perfect for product mockups or creative collages.

Template
Prompt
Python
JavaScript
Go
Java
REST

Create a new image by combining the elements from the provided images. Take
the [element from image 1] and place it with/on the [element from image 2].
The final image should be a [description of the final scene].
Input 1

Input 2

Output

A professionally shot photo of a blue floral summer dress...
A professionally shot photo of a blue floral summer dress...
Full-body shot of a woman with her hair in a bun...
Full-body shot of a woman with her hair in a bun...
Create a professional e-commerce fashion photo...
Create a professional e-commerce fashion photo...
5. High-fidelity detail preservation
To ensure critical details (like a face or logo) are preserved during an edit, describe them in great detail along with your edit request.

Template
Prompt
Python
JavaScript
Go
Java
REST

Using the provided images, place [element from image 2] onto [element from
image 1]. Ensure that the features of [element from image 1] remain
completely unchanged. The added element should [description of how the
element should integrate].
Input 1

Input 2

Output

A professional headshot of a woman with brown hair and blue eyes...
A professional headshot of a woman with brown hair and blue eyes...
A simple, modern logo with the letters 'G' and 'A'...
A simple, modern logo with the letters 'G' and 'A'...
Take the first image of the woman with brown hair, blue eyes, and a neutral expression...
Take the first image of the woman with brown hair, blue eyes, and a neutral expression...
6. Bring something to life
Upload a rough sketch or drawing and ask the model to refine it into a finished image.

Template
Prompt
Python
JavaScript
Go
Java
REST

Turn this rough [medium] sketch of a [subject] into a [style description]
photo. Keep the [specific features] from the sketch but add [new details/materials].
Input

Output

Sketch of a car
Rough sketch of a car
Output showing the final concept car
Polished photo of a car
7. Character consistency: 360 view
You can generate 360-degree views of a character by iteratively prompting for different angles. For best results, include previously generated images in subsequent prompts to maintain consistency. For complex poses, include a reference image of the desired pose.

Template
Prompt
Python
JavaScript
Go
Java
REST

A studio portrait of [person] against [background], [looking forward/in profile looking right/etc.]
Input

Output 1

Output 2

Original input of a man in white glasses
Original image
Output of a man in white glasses looking right
Man in white glasses looking right
Output of a man in white glasses looking forward
Man in white glasses looking forward
Best Practices
To elevate your results from good to great, incorporate these professional strategies into your workflow.

Be Hyper-Specific: The more detail you provide, the more control you have. Instead of "fantasy armor," describe it: "ornate elven plate armor, etched with silver leaf patterns, with a high collar and pauldrons shaped like falcon wings."
Provide Context and Intent: Explain the purpose of the image. The model's understanding of context will influence the final output. For example, "Create a logo for a high-end, minimalist skincare brand" will yield better results than just "Create a logo."
Iterate and Refine: Don't expect a perfect image on the first try. Use the conversational nature of the model to make small changes. Follow up with prompts like, "That's great, but can you make the lighting a bit warmer?" or "Keep everything the same, but change the character's expression to be more serious."
Use Step-by-Step Instructions: For complex scenes with many elements, break your prompt into steps. "First, create a background of a serene, misty forest at dawn. Then, in the foreground, add a moss-covered ancient stone altar. Finally, place a single, glowing sword on top of the altar."
Use "Semantic Negative Prompts": Instead of saying "no cars," describe the desired scene positively: "an empty, deserted street with no signs of traffic."
Control the Camera: Use photographic and cinematic language to control the composition. Terms like wide-angle shot, macro shot, low-angle perspective.
Limitations
For best performance, use the following languages: EN, ar-EG, de-DE, es-MX, fr-FR, hi-IN, id-ID, it-IT, ja-JP, ko-KR, pt-BR, ru-RU, ua-UA, vi-VN, zh-CN.
Image generation does not support audio or video inputs.
The model won't always follow the exact number of image outputs that the user explicitly asks for.
gemini-2.5-flash-image works best with up to 3 images as input, while gemini-3-pro-image-preview supports 5 images with high fidelity, and up to 14 images in total. gemini-3.1-flash-image-preview supports character resemblance of up to 4 characters and the fidelity of up to 10 objects in a single workflow.
When generating text for an image, Gemini works best if you first generate the text and then ask for an image with the text.
All generated images include a SynthID watermark.
Optional configurations
You can optionally configure the response modalities and aspect ratio of the model's output in the config field of generate_content calls.

Output types
The model defaults to returning text and image responses (i.e. response_modalities=['Text', 'Image']). You can configure the response to return only images without text using response_modalities=['Image'].

Python
JavaScript
Go
Java
REST

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
    config=types.GenerateContentConfig(
        response_modalities=['Image']
    )
)
Aspect ratios and image size
The model defaults to matching the output image size to that of your input image, or otherwise generates 1:1 squares. You can control the aspect ratio of the output image using the aspect_ratio field under image_config in the response request, shown here:

Python
JavaScript
Go
Java
REST

# For gemini-2.5-flash-image
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
        )
    )
)

# For gemini-3.1-flash-image-preview and gemini-3-pro-image-preview
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K",
        )
    )
)
The different ratios available and the size of the image generated are listed in the following tables:

3.1 Flash Image Preview
3 Pro Image Preview
Gemini 2.5 Flash Image
Aspect ratio	512 resolution	0.5K tokens	1K resolution	1K tokens	2K resolution	2K tokens	4K resolution	4K tokens
1:1	512x512	747	1024x1024	1120	2048x2048	1120	4096x4096	2000
1:4	256x1024	747	512x2048	1120	1024x4096	1120	2048x8192	2000
1:8	192x1536	747	384x3072	1120	768x6144	1120	1536x12288	2000
2:3	424x632	747	848x1264	1120	1696x2528	1120	3392x5056	2000
3:2	632x424	747	1264x848	1120	2528x1696	1120	5056x3392	2000
3:4	448x600	747	896x1200	1120	1792x2400	1120	3584x4800	2000
4:1	1024x256	747	2048x512	1120	4096x1024	1120	8192x2048	2000
4:3	600x448	747	1200x896	1120	2400x1792	1120	4800x3584	2000
4:5	464x576	747	928x1152	1120	1856x2304	1120	3712x4608	2000
5:4	576x464	747	1152x928	1120	2304x1856	1120	4608x3712	2000
8:1	1536x192	747	3072x384	1120	6144x768	1120	12288x1536	2000
9:16	384x688	747	768x1376	1120	1536x2752	1120	3072x5504	2000
16:9	688x384	747	1376x768	1120	2752x1536	1120	5504x3072	2000
21:9	792x168	747	1584x672	1120	3168x1344	1120	6336x2688	2000
Model selection
Choose the model best suited for your specific use case.

Gemini 3.1 Flash Image Preview (Nano Banana 2 Preview) should be your go-to image generation model, as the best all around performance and intelligence to cost and latency balance. Check the model pricing and capabilities page for more details.

Gemini 3 Pro Image Preview (Nano Banana Pro Preview) is designed for professional asset production and complex instructions. This model features real-world grounding using Google Search, a default "Thinking" process that refines composition prior to generation, and can generate images of up to 4K resolutions. Check the model pricing and capabilities page for more details.

Gemini 2.5 Flash Image (Nano Banana) is designed for speed and efficiency. This model is optimized for high-volume, low-latency tasks and generates images at 1024px resolution. Check the model pricing and capabilities page for more details.

---

## Limitations

### Language Support

For best performance, use one of the following languages:
- **Primary**: EN (English)
- **Supported**: ar-EG, de-DE, es-MX, fr-FR, hi-IN, id-ID, it-IT, ja-JP, ko-KR, pt-BR, ru-RU, ua-UA, vi-VN, zh-CN

### Input Limitations

- ❌ **Audio inputs**: Not supported
- ❌ **Video inputs**: Not supported
- ✅ **Image inputs**: Supported (varies by model)

### Reference Image Limits

| Model | Max Images | Objects | Characters |
|-------|-----------|---------|------------|
| 3.1 Flash | 14 | Up to 10 | Up to 4 |
| 3 Pro | 14 | Up to 6 | Up to 5 |
| 2.5 Flash | 3 | Up to 3 | Up to 3 |

### Output Behavior

- Model may not generate the **exact** number of images explicitly requested
- Text generation works best when **text is generated first**, then included in image prompt
- All generated images include **SynthID watermark** (cannot be disabled)

### Model-Specific Limitations

**Gemini 2.5 Flash Image**:
- Fixed 1024px resolution
- No thinking mode
- No Google Search grounding
- Maximum 3 reference images

**Gemini 3.1 Flash Image & 3 Pro Image**:
- Thinking tokens are billed even when thoughts are hidden

---

## Model Selection Guide

Choose the right model for your specific use case and requirements.

### Decision Tree

```
Need professional text rendering or complex instructions?
├─ YES → Nano Banana Pro (gemini-3-pro-image-preview)
└─ NO → Continue...

Need ultra-fast generation for high-volume tasks?
├─ YES → Nano Banana (gemini-2.5-flash-image)
└─ NO → Continue...

Need Image Search grounding or 512px resolution?
├─ YES → Nano Banana 2 (gemini-3.1-flash-image-preview)
└─ NO → Nano Banana 2 (default choice)
```

### Model Comparison

| Factor | Nano Banana 2<br>(3.1 Flash) | Nano Banana Pro<br>(3 Pro) | Nano Banana<br>(2.5 Flash) |
|--------|------------------------|----------------------|---------------------|
| **Speed** | ⚡⚡⚡ Fast | ⚡⚡ Moderate | ⚡⚡⚡⚡ Fastest |
| **Quality** | ⭐⭐⭐⭐ High | ⭐⭐⭐⭐⭐ Highest | ⭐⭐⭐ Good |
| **Text Accuracy** | ⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐ Good |
| **Cost** | $$ Mid | $$$ High | $ Low |
| **Thinking Mode** | Adjustable (minimal/high) | Always enabled | Not available |
| **Max Resolution** | 4K | 4K | 1024px |
| **Min Resolution** | 512 | 1K | 1024px |
| **Reference Images** | 14 (10 obj + 4 char) | 14 (6 obj + 5 char) | 3 |
| **Google Search** | Web + Image | Web only | Not available |
| **Ultra-wide Ratios** | ✅ (1:8, 8:1, etc.) | ❌ | ❌ |
| **Best For** | Developer workflows | Professional assets | High-volume tasks |

### Use Case Recommendations

| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| E-commerce product images | Nano Banana 2 | Fast, high quality, good text |
| Marketing materials with text | Nano Banana Pro | Best text rendering |
| Social media content (bulk) | Nano Banana | Fastest, cost-effective |
| Infographics & diagrams | Nano Banana Pro | Complex instructions, text |
| Logo design | Nano Banana Pro | Precision text, thinking mode |
| Icon/sticker generation | Nano Banana 2 | Fast, transparent backgrounds |
| Photorealistic scenes | Nano Banana Pro | Highest quality |
| Real-time news/weather graphics | Nano Banana 2 | Web + Image Search |
| Character consistency (comics) | Nano Banana 2 | 4 characters supported |
| Professional photography | Nano Banana Pro | 4K quality, advanced reasoning |
| Rapid A/B testing | Nano Banana | Speed & cost |
| Complex multi-edit workflows | Nano Banana Pro | Advanced thinking |

---

## Common Patterns & Code Snippets

### Basic Workflow

```python
from google import genai
from google.genai import types

client = genai.Client()

# Simple generation
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="A serene mountain lake at sunset",
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        )
    )
)

# Save image
for part in response.parts:
    if image := part.as_image():
        image.save("mountain_lake.png")
```

### Generate Multiple Variations

```python
# Generate 3 variations of the same prompt
prompt = "A minimalist logo for a tech startup"
variations = []

for i in range(3):
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )
    
    for part in response.parts:
        if image := part.as_image():
            image.save(f"variation_{i+1}.png")
            variations.append(image)
```

### Iterative Refinement Pattern

```python
# Create chat for iterative editing
chat = client.chats.create(
    model="gemini-3.1-flash-image-preview",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)

# Step 1: Initial generation
response1 = chat.send_message("Create a modern website hero image")
image1 = response1.parts[0].as_image()
image1.save("step1.png")

# Step 2: Adjust colors
response2 = chat.send_message("Make the colors more vibrant")
image2 = response2.parts[0].as_image()
image2.save("step2.png")

# Step 3: Add text
response3 = chat.send_message("Add the text 'Welcome' in large bold letters")
image3 = response3.parts[0].as_image()
image3.save("final.png")
```

### Error Handling

```python
from google import genai
from google.genai import types

client = genai.Client()

def safe_generate_image(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE']
                )
            )
            
            for part in response.parts:
                if image := part.as_image():
                    return image
            
            print(f"No image generated on attempt {attempt + 1}")
            
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise
    
    return None

# Usage
image = safe_generate_image("A futuristic cityscape")
if image:
    image.save("output.png")
```

---

## Quick Reference

### Essential Code Templates

#### Minimal Generation
```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="your prompt here"
)
```

#### With All Options
```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt, image1, image2],  # Text + multiple images
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],  # or ['IMAGE'] only
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        ),
        tools=[
            types.Tool(google_search=types.GoogleSearch(
                search_types=types.SearchTypes(
                    web_search=types.WebSearch(),
                    image_search=types.ImageSearch()
                )
            ))
        ],
        thinking_config=types.ThinkingConfig(
            thinking_level="high",
            include_thoughts=True
        )
    )
)
```

#### Chat Mode
```python
chat = client.chats.create(
    model="gemini-3.1-flash-image-preview",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)

response = chat.send_message("your prompt")
```

### Parameter Quick Reference

| Parameter | Values | Default |
|-----------|--------|---------|
| `model` | `gemini-3.1-flash-image-preview`<br>`gemini-3-pro-image-preview`<br>`gemini-2.5-flash-image` | N/A (required) |
| `response_modalities` | `['TEXT', 'IMAGE']`<br>`['IMAGE']` | `['TEXT', 'IMAGE']` |
| `aspect_ratio` | See Aspect Ratio table | Matches input or 1:1 |
| `image_size` | `"512"`, `"1K"`, `"2K"`, `"4K"` | `"1K"` |
| `thinking_level` | `"minimal"`, `"high"` | `"minimal"` |
| `include_thoughts` | `true`, `false` | `false` |

---

## Troubleshooting

### Common Issues & Solutions

**Issue**: Generated text is illegible or incorrect
- **Solution**: Use Nano Banana Pro for text-heavy images
- **Solution**: Generate text separately first, then request image with that text
- **Solution**: Be very specific about text placement and font style

**Issue**: Generated images don't match the prompt
- **Solution**: Use more descriptive, narrative prompts instead of keywords
- **Solution**: Break complex prompts into step-by-step instructions
- **Solution**: Use reference images for specific subjects/styles

**Issue**: Character appearance changes between generations
- **Solution**: Use character reference images in each generation
- **Solution**: Include previous good outputs as references
- **Solution**: Be very detailed about character features in prompt

**Issue**: Image quality is lower than expected
- **Solution**: Increase `image_size` to `"2K"` or `"4K"`
- **Solution**: Use Nano Banana Pro for highest quality
- **Solution**: Use `thinking_level="high"` for complex scenes

**Issue**: Slow generation times
- **Solution**: Use Nano Banana (2.5 Flash) for speed
- **Solution**: Reduce `image_size` to `"1K"` or `"512"`
- **Solution**: Use `thinking_level="minimal"` (3.1 Flash only)

**Issue**: Google Search grounding not working
- **Solution**: Ensure `tools=[{"google_search": {}}]` is in config
- **Solution**: Make prompt clearly reference current/real-time info
- **Solution**: Image Search requires 3.1 Flash model specifically

**Issue**: Cannot generate transparent backgrounds
- **Solution**: Explicitly state "transparent background" in prompt
- **Solution**: Works best for stickers, icons, and simple objects
- **Solution**: May not work for complex photorealistic scenes

**Issue**: Aspect ratio not applied
- **Solution**: Verify aspect_ratio is in `image_config`, not top-level config
- **Solution**: Check spelling matches table exactly (e.g., `"16:9"` not `"16x9"`)
- **Solution**: 2.5 Flash has limited aspect ratio options

---

## Best Practices Summary

1. ✅ Use **narrative descriptions**, not keyword lists
2. ✅ Be **hyper-specific** about details you care about
3. ✅ Provide **context and intent** for the image
4. ✅ **Iterate conversationally** using chat mode
5. ✅ Use **reference images** for character/object consistency
6. ✅ Match **model to use case** (Pro for quality, 2.5 for speed)
7. ✅ **Break down complex scenes** into sequential steps
8. ✅ Use **photography terms** for photorealistic results
9. ✅ **Test text separately** before including in images
10. ✅ Leverage **Google Search** for factual, real-time content

### Anti-Patterns to Avoid

1. ❌ Keyword-only prompts: "sunset, beach, palm trees"
2. ❌ Negative instructions: "no people, no cars, no buildings"
3. ❌ Expecting exact image counts different from model defaults
4. ❌ Using lowercase 'k' for resolution: `"2k"` instead of `"2K"`
5. ❌ Forgetting to specify transparent background for stickers
6. ❌ Using wrong model for text-heavy tasks
7. ❌ Not utilizing chat mode for iterative edits
8. ❌ Ignoring aspect ratio constraints for different models

---

## Additional Resources

### Related Services

- **Imagen 4**: Standalone image generation model for advanced use cases
- **Imagen 4 Ultra**: Highest quality (generates one image at a time)
- **Batch API**: High-volume generation with up to 24-hour turnaround

---

## Glossary

- **Nano Banana**: Brand name for Gemini's native image generation capabilities
- **Thinking Mode**: Advanced reasoning process that generates interim images before final output
- **Thought Signature**: Encrypted representation of thinking process for multi-turn context
- **Grounding**: Using Google Search (web or image) to base generation on real-time information
- **Reference Images**: Input images used to guide content, style, or character consistency
- **Inpainting**: Editing specific parts of an image while preserving the rest
- **Style Transfer**: Transforming an image into a different artistic style
- **SynthID**: Google's watermarking technology for AI-generated images
- **Semantic Masking**: Conversationally defining areas to edit without explicit masks
- **Character Consistency**: Maintaining the same character appearance across multiple generations

---

*End of Documentation*