# OpenAI Responses API — Text Generation & Structured Outputs

## Table of Contents
1. [Overview](#overview)
2. [Model Family](#model-family)
3. [Quick Start](#quick-start)
4. [Text Generation](#text-generation)
5. [Prompt Engineering](#prompt-engineering)
6. [Message Roles](#message-roles)
7. [Reusable Prompts](#reusable-prompts)
8. [Structured Outputs](#structured-outputs)
9. [JSON Mode](#json-mode)
10. [Streaming](#streaming)
11. [Best Practices](#best-practices)

---

## Overview

The OpenAI Responses API is the recommended API for all new projects. It generates text, structured data, and supports multi-turn conversations, function calling, and tool use. Models can generate almost any kind of text response — code, mathematical equations, structured JSON data, or human-like prose.

### Key Capabilities
- **Text Generation**: Generate text from prompts using state-of-the-art models
- **Message Roles**: `developer`, `user`, and `assistant` roles with priority hierarchy
- **Reusable Prompts**: Template-based prompts with variable substitution
- **Structured Outputs**: JSON Schema–enforced responses via Pydantic or raw schema
- **Streaming**: Real-time token-by-token output
- **Reasoning**: Controllable reasoning effort for reasoning models

---

## Model Family

| Model | Type | Best For |
|-------|------|----------|
| `gpt-5.4` | Latest flagship | Highest capability, multimodal, original detail vision |
| `gpt-5` | Flagship | General-purpose high-quality generation |
| `gpt-4.1` | Stable | Production workloads, balanced cost/quality |
| `gpt-4.1-mini` | Efficient | Cost-effective, high-volume applications |
| `gpt-4o` | Multimodal | Vision + text, broad compatibility |
| `gpt-4o-mini` | Efficient multimodal | Low-cost multimodal tasks |
| `o3` | Reasoning | Complex reasoning, math, code |
| `o4-mini` | Efficient reasoning | Cost-effective reasoning |

### Pinning Models

Pin production applications to specific model snapshots (e.g. `gpt-5-2025-08-07`) to ensure consistent behavior. Build evals to monitor prompt performance across versions.

---

## Quick Start

```python
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from env

response = client.responses.create(
    model="gpt-5",
    input="Write a one-sentence bedtime story about a unicorn.",
)

print(response.output_text)
```

### Understanding the Output

The `output` property contains an array of generated content:

```json
[
  {
    "id": "msg_67b73f697ba4819183a15cc17d011509",
    "type": "message",
    "role": "assistant",
    "content": [
      {
        "type": "output_text",
        "text": "Under the soft glow of the moon, Luna the unicorn danced through fields of twinkling stardust.",
        "annotations": []
      }
    ]
  }
]
```

> **Important**: The `output` array can contain tool calls, reasoning tokens, and other items. It is **not safe** to assume `output[0].content[0].text` contains the model's text. Use the convenience property `response.output_text` to aggregate all text outputs.

---

## Text Generation

### Basic Generation

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.4",
    input="Write a one-sentence bedtime story about a unicorn.",
)

print(response.output_text)
```

### With Instructions

The `instructions` parameter provides high-level directives that take priority over `input`:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    reasoning={"effort": "low"},
    instructions="Talk like a pirate.",
    input="Are semicolons optional in JavaScript?",
)

print(response.output_text)
```

> **Note**: The `instructions` parameter only applies to the current request. When using `previous_response_id` for multi-turn, previous instructions are not carried forward.

### With Reasoning Control

For reasoning models (`o3`, `gpt-5`), control thinking depth:

```python
response = client.responses.create(
    model="gpt-5",
    reasoning={"effort": "low"},  # "low", "medium", "high"
    input="Explain quantum entanglement simply.",
)
```

---

## Prompt Engineering

### Key Principles

1. **Pin model snapshots** in production (e.g. `gpt-5-2025-08-07`)
2. **Build evals** to measure prompt performance across versions
3. **Reasoning models** (`o3`, `gpt-5`) perform better with the Responses API
4. **Use `instructions`** for system-level behavior; `input` for user content

### Tips

- Be specific and detailed in your instructions
- Provide examples of correct responses when possible
- Use the `developer` role for business logic and rules
- Use the `user` role for end-user inputs
- Reasoning models respond better to different prompts than chat models

---

## Message Roles

Messages have three roles with a priority hierarchy:

| Role | Priority | Description |
|------|----------|-------------|
| `developer` | Highest | Application-level instructions and business logic (like a function definition) |
| `user` | Medium | End-user inputs and configuration (like function arguments) |
| `assistant` | — | Messages generated by the model |

### Using Roles in Input

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    reasoning={"effort": "low"},
    input=[
        {
            "role": "developer",
            "content": "Talk like a pirate.",
        },
        {
            "role": "user",
            "content": "Are semicolons optional in JavaScript?",
        },
    ],
)

print(response.output_text)
```

### Mental Model

- **`developer` messages** = system rules and business logic (function definition)
- **`user` messages** = inputs the rules are applied to (function arguments)

---

## Reusable Prompts

Create reusable prompt templates in the OpenAI dashboard with placeholders, then reference them in API calls.

### String Variables

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    prompt={
        "id": "pmpt_abc123",
        "version": "2",
        "variables": {
            "customer_name": "Jane Doe",
            "product": "40oz juice box",
        },
    },
)

print(response.output_text)
```

### Prompt Object Properties

| Property | Description |
|----------|-------------|
| `id` | Unique identifier from the dashboard |
| `version` | Specific version (defaults to "current") |
| `variables` | Map of placeholder values — strings or input types (`input_image`, `input_file`) |

---

## Structured Outputs

Structured Outputs ensures the model generates responses that adhere to a supplied JSON Schema. Benefits:

- **Reliable type-safety**: No need to validate or retry malformed responses
- **Explicit refusals**: Safety refusals are programmatically detectable
- **Simpler prompting**: No need for strongly worded formatting instructions

### With Pydantic (Recommended)

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

response = client.responses.parse(
    model="gpt-4o-2024-08-06",
    input=[
        {"role": "system", "content": "Extract the event information."},
        {
            "role": "user",
            "content": "Alice and Bob are going to a science fair on Friday.",
        },
    ],
    text_format=CalendarEvent,
)

event = response.output_parsed
```

### Chain of Thought

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

response = client.responses.parse(
    model="gpt-4o-2024-08-06",
    input=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    text_format=MathReasoning,
)

math_reasoning = response.output_parsed
```

### With Raw JSON Schema

```json
{
    "name": "get_weather",
    "description": "Fetches the weather in the given location",
    "strict": true,
    "schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get the weather for"
            },
            "unit": {
                "type": "string",
                "description": "The unit to return the temperature in",
                "enum": ["F", "C"]
            }
        },
        "additionalProperties": false,
        "required": ["location", "unit"]
    }
}
```

### Handling Refusals

When the model refuses for safety reasons, the response includes a `refusal` field instead of parsed output:

```python
result = response.output_parsed

if hasattr(result, "refusal") and result.refusal:
    print("Refused:", result.refusal)
else:
    print(result)
```

Refusal response structure:

```json
{
  "output": [{
    "type": "message",
    "role": "assistant",
    "content": [{
      "type": "refusal",
      "refusal": "I'm sorry, I cannot assist with that request."
    }]
  }]
}
```

### When to Use Structured Outputs

| Scenario | Use |
|----------|-----|
| Connecting model to tools/functions/data | Function calling with structured params |
| Structuring model output for the user/UI | `text_format` with `responses.parse()` |

### Supported Schema Features

**Supported types**: `string`, `number`, `boolean`, `integer`, `object`, `array`, `enum`, `anyOf`

**String constraints**: `pattern` (regex), `format` (`date-time`, `date`, `email`, `uuid`, etc.)

**Number constraints**: `multipleOf`, `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`

**Array constraints**: `minItems`, `maxItems`

### Schema Rules (Critical)

1. **Root must be an `object`** — not `anyOf` or other types
2. **All fields must be `required`** — emulate optional with `"type": ["string", "null"]`
3. **`additionalProperties: false`** must be set on every object
4. **Max 5000 properties**, max 10 levels of nesting
5. **Max 1000 enum values** across all enum properties
6. **Max 120,000 characters** total string length for property names, enum values, etc.
7. **Recursive schemas** are supported (via `$ref`)
8. **Definitions** are supported (via `$defs`)
9. **Key ordering** in output matches schema key ordering

### Unsupported Composition Keywords

`allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`, `then`, `else`

---

## JSON Mode

JSON mode is a simpler alternative to Structured Outputs. It ensures valid JSON but does **not** enforce a schema.

```python
response = client.responses.create(
    model="gpt-5",
    input=[
        {"role": "developer", "content": "Return a JSON object with user info."},
        {"role": "user", "content": "My name is Alice, I'm 30."},
    ],
    text={"format": {"type": "json_object"}},
)
```

### JSON Mode vs Structured Outputs

| Feature | Structured Outputs | JSON Mode |
|---------|-------------------|-----------|
| Valid JSON | Yes | Yes |
| Adheres to schema | Yes | No |
| Enabling | `text_format=MyModel` or `json_schema` | `{"type": "json_object"}` |

> **Important**: When using JSON mode, you **must** instruct the model to produce JSON via a message. Without it, the model may generate an unending stream of whitespace.

> **Recommendation**: Always prefer Structured Outputs over JSON mode when possible.

---

## Streaming

### Streaming Text

```python
from typing import List
from openai import OpenAI
from pydantic import BaseModel

class EntitiesModel(BaseModel):
    attributes: List[str]
    colors: List[str]
    animals: List[str]

client = OpenAI()

with client.responses.stream(
    model="gpt-4.1",
    input=[
        {"role": "system", "content": "Extract entities from the input text"},
        {
            "role": "user",
            "content": "The quick brown fox jumps over the lazy dog with piercing blue eyes",
        },
    ],
    text_format=EntitiesModel,
) as stream:
    for event in stream:
        if event.type == "response.refusal.delta":
            print(event.delta, end="")
        elif event.type == "response.output_text.delta":
            print(event.delta, end="")
        elif event.type == "response.error":
            print(event.error, end="")
        elif event.type == "response.completed":
            print("Completed")

    final_response = stream.get_final_response()
    print(final_response)
```

### Stream Event Types

| Event | Description |
|-------|-------------|
| `response.output_text.delta` | Partial text token |
| `response.refusal.delta` | Partial refusal text |
| `response.error` | Error during generation |
| `response.completed` | Generation finished |

---

## Best Practices

1. **Pin model snapshots** in production for reproducibility
2. **Use `developer` role** for system instructions, `user` role for end-user input
3. **Prefer `instructions` parameter** for high-level behavior directives
4. **Use Structured Outputs** instead of JSON mode whenever possible
5. **Use Pydantic models** (Python) or Zod schemas (JS) to prevent schema divergence
6. **Handle refusals** programmatically — check for `refusal` in output
7. **Add CI rules** to flag when JSON schemas or data objects diverge
8. **Use `output_text`** convenience property instead of manually indexing `output`
9. **Include examples** in developer messages for consistent formatting
10. **Set `reasoning.effort`** to `"low"` for simple tasks to save tokens and latency
