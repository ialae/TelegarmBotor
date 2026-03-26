# Veo 3.1 Video Generation API - Complete Documentation

## Overview

Veo 3.1 is Google's state-of-the-art video generation model accessible through the Gemini API. It generates high-fidelity videos with natively generated audio.

### Key Capabilities

- **Video Quality**: 720p, 1080p, or 4k resolution
- **Duration**: 4, 6, or 8 seconds per generation
- **Audio**: Native audio generation including dialogue, sound effects, and ambient noise
- **Aspect Ratios**: Landscape (16:9) or Portrait (9:16)
- **Frame Rate**: 24fps

### Core Features

1. **Text-to-Video**: Generate videos from text prompts
2. **Image-to-Video**: Animate a starting image
3. **Video Extension**: Extend previously generated Veo videos by 7 seconds (up to 20 times)
4. **Frame Interpolation**: Specify first and/or last frames for precise control
5. **Reference Images**: Use up to 3 reference images to guide content (Veo 3.1 only)

---

## Installation & Setup

### Required Imports

```python
import time
from google import genai
from google.genai import types
```

### Initialize Client

```python
client = genai.Client()
```

---

## Model Information

### Available Models

| Model | Code | Status | Use Case |
|-------|------|--------|----------|
| Veo 3.1 | `veo-3.1-generate-preview` | Preview | High-quality generation with all features |
| Veo 3.1 Fast | `veo-3.1-fast-generate-preview` | Preview | Optimized for speed, ideal for production |
| Veo 3 | `veo-3-generate` | Stable | Previous generation model |
| Veo 2 | `veo-2-generate` | Stable | Legacy model (no audio) |

### Input/Output Specifications

- **Input**: Text (up to 1,024 tokens), Images, Videos
- **Output**: Video with audio (MP4 format)
- **Videos per Request**: 1

---

## API Reference

### Main Method: `generate_videos()`

```python
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=str,                    # Required
    image=Image,                   # Optional
    video=Video,                   # Optional (for extension)
    config=GenerateVideosConfig()  # Optional
)
```

### Parameters

#### Instance Parameters (Direct Arguments)

| Parameter | Type | Description | Availability |
|-----------|------|-------------|--------------|
| `prompt` | `string` | Text description for the video. Supports audio cues (dialogue, SFX, ambient) | All models |
| `image` | `Image` | Initial image to animate (first frame) | All models |
| `video` | `Video` | Video from previous generation for extension | Veo 3.1 only |

#### Config Parameters (`GenerateVideosConfig`)

| Parameter | Type | Default | Description | Options |
|-----------|------|---------|-------------|---------|
| `aspect_ratio` | `string` | `"16:9"` | Video aspect ratio | `"16:9"`, `"9:16"` |
| `resolution` | `string` | `"720p"` | Output resolution | `"720p"`, `"1080p"`, `"4k"` |
| `duration_seconds` | `string` | `"8"` | Video length | `"4"`, `"6"`, `"8"` |
| `number_of_videos` | `int` | `1` | Number of videos to generate | `1` |
| `person_generation` | `string` | Varies | Controls people generation | See Regional Limitations |
| `seed` | `int` | None | Improves determinism (not guaranteed) | Any integer |
| `last_frame` | `Image` | None | Final image for interpolation | Image object |
| `reference_images` | `list` | None | Up to 3 reference images | List of `VideoGenerationReferenceImage` |

#### Important Parameter Constraints

1. **Duration Requirements**:
   - 1080p and 4k: Must use `duration_seconds="8"`
   - Extension, reference images: Must use `duration_seconds="8"`

2. **Resolution Restrictions**:
   - Video extension: Limited to `"720p"` only
   
3. **Person Generation Regional Limits**:
   - **Veo 3.1**: 
     - Text-to-video & Extension: `"allow_all"` only
     - Image-to-video, Interpolation, Reference images: `"allow_adult"` only
   - **EU/UK/CH/MENA regions**: `"allow_adult"` only

---

## Usage Examples

### 1. Basic Text-to-Video Generation

Generate a video with dialogue and sound effects:

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """A close up of two people staring at a cryptic drawing on a wall, torchlight flickering.
A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'"""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("dialogue_example.mp4")
print("Generated video saved to dialogue_example.mp4")
```


### 2. Control Aspect Ratio

Generate portrait (9:16) videos for mobile/social media:

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """A montage of pizza making: a chef tossing and flattening the floury dough, 
ladling rich red tomato sauce in a spiral, sprinkling mozzarella cheese and pepperoni, 
and a final shot of the bubbling golden-brown pizza, upbeat electronic music with a 
rhythmical beat is playing, high energy professional video."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",  # Portrait mode
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("pizza_making.mp4")
print("Generated video saved to pizza_making.mp4")
```

**Available Aspect Ratios**:
- `"16:9"` - Landscape (default)
- `"9:16"` - Portrait

---

### 3. Control Resolution

Generate high-resolution 4k videos:

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """A stunning drone view of the Grand Canyon during a flamboyant sunset 
that highlights the canyon's colors. The drone slowly flies towards the sun then 
accelerates, dives and flies inside the canyon."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=types.GenerateVideosConfig(
        resolution="4k",
        # Note: 4k requires duration_seconds="8" (implied default)
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("4k_grand_canyon.mp4")
print("Generated video saved to 4k_grand_canyon.mp4")
```

**Resolution Options**:
- `"720p"` - Default, fastest, works with all features
- `"1080p"` - High quality, requires 8s duration
- `"4k"` - Ultra HD, requires 8s duration, higher latency and cost

**Important Notes**:
- Higher resolution = higher latency and cost
- Video extension is limited to 720p only
- 1080p and 4k require `duration_seconds="8"`

---

### 4. Image-to-Video Generation

Animate a static image by using it as the first frame:

```python
import time
from google import genai

client = genai.Client()

prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"

# Step 1: Generate an image with Gemini 2.5 Flash Image (Nano Banana)
image = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
    config={"response_modalities": ['IMAGE']}
)

# Step 2: Generate video with Veo 3.1 using the image as first frame
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    image=image.parts[0].as_image(),  # Use generated image as first frame
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3_with_image_input.mp4")
print("Generated video saved to veo3_with_image_input.mp4")
```

**Use Cases**:
- Animate artwork or drawings
- Bring static product photos to life
- Add motion to scene compositions

---

### 5. Using Reference Images (Veo 3.1 Only)

Guide video content using up to 3 reference images to preserve appearance:

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """The video opens with a medium, eye-level shot of a beautiful woman with 
dark hair and warm brown eyes. She wears a magnificent, high-fashion flamingo dress 
with layers of pink and fuchsia feathers, complemented by whimsical pink, heart-shaped 
sunglasses. She walks with serene confidence through the crystal-clear, shallow turquoise 
water of a sun-drenched lagoon. The camera slowly pulls back to a medium-wide shot, 
revealing the breathtaking scene as the dress's long train glides and floats gracefully 
on the water's surface behind her. The cinematic, dreamlike atmosphere is enhanced by 
the vibrant colors of the dress against the serene, minimalist landscape, capturing a 
moment of pure elegance and high-fashion fantasy."""

# Create reference image objects
dress_reference = types.VideoGenerationReferenceImage(
    image=dress_image,  # Generated separately with Nano Banana
    reference_type="asset"
)

sunglasses_reference = types.VideoGenerationReferenceImage(
    image=glasses_image,  # Generated separately with Nano Banana
    reference_type="asset"
)

woman_reference = types.VideoGenerationReferenceImage(
    image=woman_image,  # Generated separately with Nano Banana
    reference_type="asset"
)

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=types.GenerateVideosConfig(
        reference_images=[dress_reference, sunglasses_reference, woman_reference],
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_with_reference_images.mp4")
print("Generated video saved to veo3.1_with_reference_images.mp4")
```

**Reference Image Guidelines**:
- Maximum 3 images
- Use for preserving appearance of people, characters, or products
- `reference_type="asset"` for objects/products
- Veo 3.1 only feature

---

### 6. Frame Interpolation (First & Last Frame)

Specify both starting and ending frames for precise control:

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """A cinematic, haunting video. A ghostly woman with long white hair and a 
flowing dress swings gently on a rope swing beneath a massive, gnarled tree in a foggy, 
moonlit clearing. The fog thickens and swirls around her, and she slowly fades away, 
vanishing completely. The empty swing is left swaying rhythmically on its own in the 
eerie silence."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    image=first_image,  # The starting frame (primary input)
    config=types.GenerateVideosConfig(
        last_frame=last_image  # The ending frame (config parameter)
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_with_interpolation.mp4")
print("Generated video saved to veo3.1_with_interpolation.mp4")
```

**Interpolation Details**:
- First frame: Pass via `image` parameter
- Last frame: Pass via `config.last_frame` parameter
- Veo generates smooth transition between frames
- Veo 3.1 only feature

---

### 7. Video Extension

Extend previously generated Veo videos by 7 seconds:

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

# Extension prompt (describes what happens next)
prompt = """Track the butterfly into the garden as it lands on an orange origami flower. 
A fluffy white puppy runs up and gently pats the flower."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    video=previous_operation.response.generated_videos[0].video,  # Video from previous generation
    prompt=prompt,
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        resolution="720p"  # Extension only supports 720p
    ),
)

# Poll the operation status until the video is ready
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the extended video
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("veo3.1_extension.mp4")
print("Generated video saved to veo3.1_extension.mp4")
```

**Extension Requirements**:
- **Veo 3.1 only** feature
- Input must be a Veo-generated video
- Video must be from `operation.response.generated_videos[0].video`
- Maximum input length: 141 seconds
- Extension adds 7 seconds
- Can extend up to 20 times (total: 148 seconds)
- **Resolution**: 720p only
- **Aspect ratio**: 9:16 or 16:9
- Videos stored for 2 days (timer resets when referenced)
- Output is single combined video (input + extension)

**Important**: Voice cannot be effectively extended if not present in the last 1 second of input video.

---

## Handling Asynchronous Operations

Video generation is computationally intensive and runs asynchronously. The API returns an operation object immediately, which you must poll until completion.

### Operation Polling Pattern

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

# Start the video generation job
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="A cinematic shot of a majestic lion in the savannah.",
)

# Method 1: Poll using the original operation object
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)  # Check every 10 seconds
    operation = client.operations.get(operation)

# Method 2: Recreate operation object using operation name
operation = types.GenerateVideosOperation(name=operation.name)
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)

# Access the result
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("output.mp4")
```

### Operation Object Structure

```python
operation.name              # String: Unique operation identifier
operation.done              # Boolean: True when generation is complete
operation.response          # GenerateVideosResponse: Available when done=True
operation.response.generated_videos[0].video  # Video object
```

### Recommended Polling Interval

- **Minimum**: 10 seconds between checks
- **Expected Latency**: 11 seconds to 6 minutes (during peak hours)

---

## Prompt Writing Guide

Effective prompts are detailed, specific, and structured. Veo excels when given clear guidance.

### Prompt Structure Elements

| Element | Required | Description | Examples |
|---------|----------|-------------|----------|
| **Subject** | ✅ Yes | Main focus of the video | "cityscape", "calico kitten", "vintage car" |
| **Action** | ✅ Yes | What the subject is doing | "walking", "running", "rotating slowly" |
| **Style** | ✅ Recommended | Creative/visual direction | "cinematic", "film noir", "3D cartoon", "photorealistic" |
| **Camera** | ⚪ Optional | Camera positioning & motion | "aerial view", "dolly shot", "POV shot", "tracking drone" |
| **Composition** | ⚪ Optional | Shot framing | "wide shot", "close-up", "two-shot", "extreme close-up" |
| **Lens Effects** | ⚪ Optional | Focus and lens type | "shallow focus", "wide-angle lens", "macro lens" |
| **Ambiance** | ⚪ Optional | Lighting & color mood | "blue tones", "warm sunset", "neon glow", "natural light" |

### Audio Prompting (Veo 3.1 & 3)

Veo natively generates audio including dialogue, sound effects, and ambient noise.

#### Dialogue

Use quotes for specific speech:

```
A man murmurs, 'This must be it. That's the secret code.'
The woman whispers excitedly, 'What did you find?'
```

#### Sound Effects (SFX)

Explicitly describe sounds:

```
tires screeching loudly, engine roaring
footsteps on the damp earth, twigs snapping
```

#### Ambient Noise

Describe the environmental soundscape:

```
A faint, eerie hum resonates in the background
upbeat electronic music with a rhythmical beat is playing
A lone bird chirps in the distance
```

### Example Prompts

#### Simple vs. Detailed Prompts

**Simple** (Basic):
```
A cute creature with snow leopard-like fur is walking in winter forest, 3D cartoon style render.
```

**Detailed** (Better):
```
Create a short 3D animated scene in a joyful cartoon style. A cute creature with snow 
leopard-like fur, large expressive eyes, and a friendly, rounded form happily prances 
through a whimsical winter forest. The scene should feature rounded, snow-covered trees, 
gentle falling snowflakes, and warm sunlight filtering through the branches. The creature's 
bouncy movements and wide smile should convey pure delight. Aim for an upbeat, heartwarming 
tone with bright, cheerful colors and playful animation.
```

#### By Element Type

**Subject & Context**:
```
An architectural rendering of a white concrete apartment building with flowing organic 
shapes, seamlessly blending with lush greenery and futuristic elements.
```

**Action**:
```
A wide shot of a woman walking along the beach, looking content and relaxed towards 
the horizon at sunset.
```

**Style**:
```
Film noir style, man and woman walk on the street, mystery, cinematic, black and white.
```

**Camera Motion & Composition**:
```
A POV shot from a vintage car driving in the rain, Canada at night, cinematic.
Extreme close-up of an eye with city reflected in it.
```

**Ambiance**:
```
A close-up of a girl holding adorable golden retriever puppy in the park, sunlight.
Cinematic close-up shot of a sad woman riding a bus in the rain, cool blue tones, sad mood.
```

**Combining Elements**:
```
Close up shot (composition) of melting icicles (subject) on a frozen rock wall (context) 
with cool blue tones (ambiance), zoomed in (camera motion) maintaining close-up detail 
of water drips (action).
```

### Negative Prompts

Specify elements you **don't** want in the video.

❌ **Don't use**: Instructive language like "no" or "don't"
```
Bad: "No walls, don't show people"
```

✅ **Do use**: Descriptive terms for unwanted elements
```
Good: "wall, frame, urban background, man-made structures"
```

### Best Practices

1. **Be Descriptive**: Use adjectives and adverbs liberally
2. **Specify Detail**: For facial focus, use words like "portrait"
3. **Layer Details**: Combine multiple elements for richer results
4. **Audio Integration**: Include audio cues naturally in the prompt
5. **Test Iterations**: Start simple, add details based on results

---
## Model Features Comparison

| Feature | Veo 3.1 & 3.1 Fast | Veo 3 & 3 Fast | Veo 2 |
|---------|-------------------|----------------|-------|
| **Audio Generation** | ✅ Native audio | ✅ Native audio | ❌ Silent only |
| **Input Modalities** | Text, Image, Video | Text, Image | Text, Image |
| **Resolution** | 720p, 1080p, 4k<br>(720p for extension) | 720p, 1080p | 720p |
| **Frame Rate** | 24fps | 24fps | 24fps |
| **Duration** | 4s, 6s, 8s<br>(8s for 1080p/4k/ref images) | 4s, 6s, 8s<br>(8s for 1080p/4k) | 5s, 6s, 8s |
| **Aspect Ratios** | 16:9, 9:16 | 16:9, 9:16 | 16:9, 9:16 |
| **Reference Images** | ✅ Up to 3 images | ❌ Not available | ❌ Not available |
| **Video Extension** | ✅ By 7 seconds | ❌ Not available | ❌ Not available |
| **Frame Interpolation** | ✅ First & last frames | ❌ Last frame only | ❌ Last frame only |
| **Videos per Request** | 1 | 1 | 1 or 2 |
| **Status** | Preview | Stable | Stable |

---

## Limitations & Important Notes

### Performance

- **Latency**: 11 seconds (minimum) to 6 minutes (maximum during peak hours)
- **Higher resolution**: Increases latency and cost
  - 4k videos: Highest latency and pricing
  - 1080p: Medium latency and pricing
  - 720p: Lowest latency and pricing (recommended for most use cases)

### Regional Restrictions

**Person Generation Controls** (EU, UK, CH, MENA):

| Model | Allowed Values |
|-------|---------------|
| Veo 3.1 | `"allow_adult"` only for image-based inputs |
| Veo 3 | `"allow_adult"` only |
| Veo 2 | `"dont_allow"` (default), `"allow_adult"` |

### Video Storage & Retention

- **Storage Duration**: 2 days from generation
- **Extension Timer Reset**: Referencing a video for extension resets its 2-day timer
- **Download Deadline**: Must download within 2 days to save locally
- **Extended Videos**: Treated as new generations with their own 2-day timer

### Safety & Content Filters

1. **Safety Filters**: All videos pass through safety filters for offensive content
2. **Memorization Checking**: Helps mitigate privacy and copyright risks
3. **Watermarking**: All videos watermarked with SynthID
   - Verification available via SynthID verification platform
4. **Prompt Blocking**: Prompts violating terms and guidelines are blocked
5. **Audio Blocking**: Videos may be blocked due to audio safety filters
   - No charge if video is blocked

### Audio Generation Notes

- **Extension Limitation**: Voice cannot be effectively extended if not present in the last 1 second of input video
- **Error Handling**: Audio processing issues may block video generation (no charge)

---

## Common Patterns & Code Snippets

### Basic Generation Workflow

```python
import time
from google import genai
from google.genai import types

# Initialize
client = genai.Client()

# Generate
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Your detailed prompt here",
    config=types.GenerateVideosConfig(
        aspect_ratio="16:9",
        resolution="720p",
        duration_seconds="8"
    )
)

# Poll until complete
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)

# Download
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("output.mp4")
```

### Generate Multiple Durations

```python
durations = ["4", "6", "8"]
operations = []

prompt = "A serene mountain landscape at sunset"

for duration in durations:
    op = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        config=types.GenerateVideosConfig(
            duration_seconds=duration
        )
    )
    operations.append((op, duration))

# Poll all operations
for op, duration in operations:
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
    
    video = op.response.generated_videos[0]
    client.files.download(file=video.video)
    video.video.save(f"output_{duration}s.mp4")
```

### Chain Generation and Extension

```python
# Step 1: Generate initial video
operation1 = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="A butterfly flaps its wings on a flower",
    config=types.GenerateVideosConfig(resolution="720p")
)

while not operation1.done:
    time.sleep(10)
    operation1 = client.operations.get(operation1)

# Step 2: Extend the video
operation2 = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    video=operation1.response.generated_videos[0].video,
    prompt="The butterfly takes flight and soars into the sky",
    config=types.GenerateVideosConfig(resolution="720p")
)

while not operation2.done:
    time.sleep(10)
    operation2 = client.operations.get(operation2)

# Download extended video (combined)
video = operation2.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("extended_video.mp4")
```

### Error Handling

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

try:
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt="Your prompt",
        config=types.GenerateVideosConfig(
            aspect_ratio="16:9",
            resolution="720p"
        )
    )
    
    # Poll with timeout
    max_wait_time = 400  # 6 minutes + buffer
    start_time = time.time()
    
    while not operation.done:
        if time.time() - start_time > max_wait_time:
            print("Operation timeout - may still be processing")
            break
        time.sleep(10)
        operation = client.operations.get(operation)
    
    if operation.done:
        video = operation.response.generated_videos[0]
        client.files.download(file=video.video)
        video.video.save("output.mp4")
        print("Video generated successfully")
    
except Exception as e:
    print(f"Error during video generation: {e}")
```

---

## Quick Reference

### Model Selection Guide

| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| Production apps requiring speed | `veo-3.1-fast-generate-preview` | Optimized for low latency |
| Highest quality output | `veo-3.1-generate-preview` | All features, best quality |
| Video with audio (stable) | `veo-3-generate` | Stable release with audio |
| Legacy projects | `veo-2-generate` | Backward compatibility |

### Feature Availability Matrix

| Feature | Required Model | Required Config |
|---------|---------------|----------------|
| Text-to-video | All models | Prompt only |
| Image-to-video | All models | `image` parameter |
| Audio generation | Veo 3.1, 3, 3.1 Fast, 3 Fast | Automatic |
| 1080p/4k | Veo 3.1, 3, 3.1 Fast, 3 Fast | `resolution`, `duration_seconds="8"` |
| Portrait mode | All models | `aspect_ratio="9:16"` |
| Reference images | Veo 3.1, 3.1 Fast only | `reference_images` list |
| Video extension | Veo 3.1, 3.1 Fast only | `video` parameter, `resolution="720p"` |
| Frame interpolation | Veo 3.1, 3.1 Fast only | `image` + `config.last_frame` |

### Parameter Quick Reference

```python
# Minimal configuration
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Your prompt"
)

# Full configuration
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Detailed prompt with dialogue, SFX, and ambient sounds",
    image=starting_image,  # Optional: first frame
    video=previous_video,  # Optional: for extension
    config=types.GenerateVideosConfig(
        aspect_ratio="16:9",           # "16:9" or "9:16"
        resolution="720p",             # "720p", "1080p", "4k"
        duration_seconds="8",          # "4", "6", "8"
        number_of_videos=1,
        person_generation="allow_all", # Region-dependent
        seed=12345,                    # Optional: for reproducibility
        last_frame=ending_image,       # Optional: for interpolation
        reference_images=[             # Optional: Veo 3.1 only
            types.VideoGenerationReferenceImage(
                image=ref_img,
                reference_type="asset"
            )
        ]
    )
)
```

---

## Troubleshooting

### Common Issues

**Issue**: Operation takes longer than expected
- **Solution**: Latency varies (11s-6min). Higher resolutions take longer. Check during off-peak hours.

**Issue**: Video generation blocked
- **Solution**: Review prompt for policy violations. Audio safety filters may trigger. No charge for blocked videos.

**Issue**: Extension fails
- **Solution**: Ensure input video is:
  - From a Veo generation (not uploaded)
  - Under 141 seconds
  - 720p resolution
  - Generated/referenced within last 2 days

**Issue**: Cannot download video
- **Solution**: Videos are stored for 2 days only. Must download within this window.

**Issue**: Reference images not working
- **Solution**: Feature is Veo 3.1 only. Maximum 3 images. Requires `duration_seconds="8"`.

**Issue**: 1080p or 4k generation fails
- **Solution**: These resolutions require `duration_seconds="8"`. Not available for extension.

---

## Additional Resources

### Model Information

- **Latest Update**: January 2026
- **Input Token Limit**: 1,024 tokens
- **Output Videos per Request**: 1
- **Supported Languages**: Text prompts in multiple languages

### Best Practices Summary

1. ✅ Use detailed, descriptive prompts with all elements (subject, action, style, etc.)
2. ✅ Include audio cues naturally in prompts (dialogue in quotes, explicit SFX descriptions)
3. ✅ Start with 720p for testing, upgrade to 1080p/4k for final output
4. ✅ Poll operations every 10 seconds
5. ✅ Download videos within 2 days of generation
6. ✅ Use reference images for consistent character/product appearance (Veo 3.1)
7. ✅ Test prompts iteratively, adding detail based on results
8. ❌ Don't use video extension with resolutions above 720p
9. ❌ Don't expect perfect determinism even with seed parameter
10. ❌ Don't use instructive negative language ("no", "don't") in prompts

---

## Version History

| Version | Release Date | Key Features |
|---------|-------------|--------------|
| Veo 3.1 | January 2026 | Reference images, video extension, frame interpolation, 1080p/4k |
| Veo 3 | 2025 | Native audio generation, improved quality |
| Veo 2 | 2024 | Initial release, silent videos only |

---

## Glossary

- **Operation**: Async job object returned immediately upon video generation request
- **Polling**: Repeatedly checking operation status until completion
- **Reference Images**: Up to 3 images guiding video content (Veo 3.1 only)
- **Extension**: Adding 7 seconds to a previously generated Veo video
- **Interpolation**: Generating video between specified first and last frames
- **SynthID**: Google's watermarking technology for AI-generated content
- **Aspect Ratio**: Video width-to-height ratio (16:9 landscape or 9:16 portrait)
- **Resolution**: Video pixel dimensions (720p, 1080p, 4k)
- **Frame Rate**: 24 frames per second (fps) for all Veo videos

---

*End of Documentation*