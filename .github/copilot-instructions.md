IMPORTANT : You MUST read this entire file before writing any code or review feedback.

# Copilot Instructions

These are the broad, universal rules and instructions that apply across the entire project regardless of language, framework, business domain, or architecture. For every task, I want you to first consult these instructions from top to bottom before writing any code or review feedback. They represent the coding philosophy, best practices, and non-negotiable rules that govern all work in this codebase. If you find yourself ignoring or violating any of these instructions, stop and ask for clarification before proceeding.
I repeat, you must read this entire file before writing any code or review feedback. It is not optional. It is the foundation for everything you do in this project.
After reading the entire file, I want you also to check if there are any specific skills that apply to the task at hand (e.g., React component design, Python API design, testing best practices) and consult those as well. The skills contain framework-specific or technology-specific guidance that builds on top of these universal instructions.

---

## Coding Philosophy

- Write code for humans first, machines second. Clarity always wins over cleverness.
- Favor simplicity. If a solution feels complex, step back and find a simpler one.
- Every piece of code should have a single, clear reason to exist. If you cannot explain why something is there, remove it.
- Make the wrong thing look wrong. Code should visually communicate intent.
- Leave code better than you found it. Small, continuous improvements compound.
- Do not over-engineer. Build for today's real requirements, not imagined future ones. (YAGNI — You Aren't Gonna Need It.)
- Prefer explicit over implicit. Hidden behavior causes hidden bugs.
- Composition over inheritance. Build systems from small, interchangeable parts.
- Treat warnings as errors. Never ignore or suppress them without documented justification.
- Follow the Principle of Least Surprise. Code should behave the way a reasonable person would expect.
- Separate concerns ruthlessly. Each layer, module, or component should have one reason to change.
- Design for deletion. Write code so that any part can be removed or replaced without cascading damage.
- Make dependencies visible. If module A depends on module B, that relationship should be obvious from the code, not hidden in runtime behavior.
- Minimize surface area. Expose only what is necessary. The smaller the public interface, the easier it is to maintain and the harder it is to misuse.
- Be boring on purpose. Use well-known patterns and conventions. Save creativity for the product, not the plumbing.
- Optimize for change. Requirements will change. Assume every decision you make today will be revisited.
- Think in contracts. Define clear inputs, outputs, and invariants for every boundary — function, module, service, or API.
- Automate everything you do more than twice. If a manual step exists in your workflow, it will eventually be forgotten or done wrong.
- Embrace constraints. Limitations (time, scope, resources) force better design decisions. Work within them, not around them.

---

## Non-Negotiables — Never Allow These

- Never commit secrets, credentials, API keys, or tokens into source control. Ever.
- Never silently swallow errors or exceptions. Always handle them meaningfully or let them propagate.
- Never use magic numbers or magic strings. Define named constants with clear intent.
- Never leave dead code, commented-out code, or TODO placeholders in production code.
- Never mutate shared state without controlled, explicit synchronization.
- Never ignore accessibility. Every interactive element must be usable by keyboard and assistive technology.
- Never trust user input. Validate, sanitize, and constrain all external data at every boundary.
- Never disable or skip tests to make a build pass.
- Never introduce a dependency without evaluating its maintenance status, license, security, and size.
- Never write a function or method longer than 40 lines. If it is longer, split it.
- Never nest logic deeper than 3 levels. Flatten with early returns, guard clauses, or extraction.
- Never duplicate logic. If the same code appears twice, extract it.
- Never hard-code environment-specific values (URLs, ports, paths). Use configuration.
- Never leave a pull request without a description explaining what and why.

---

## Coding Preferences and Style

### Naming

- Use descriptive, intention-revealing names. A name should tell you what something is or does without needing a comment.
- Follow the naming conventions of the language and framework you are using (e.g., `snake_case` in Python, `camelCase` in JavaScript). Never invent your own casing style.
- Booleans must read as yes/no questions, prefixed with `is`, `has`, `can`, `should`, or equivalent.
- Functions and methods must start with a verb describing the action they perform.
- Avoid abbreviations unless they are universally understood (`id`, `url`, `http`). Spell it out.
- Collections use plural nouns. Single items use singular nouns.
- Avoid generic names like `data`, `info`, `temp`, `result`, `value`, `item` unless scope is extremely narrow (< 5 lines).
- Event handlers follow a consistent prefix pattern (e.g., `on_` or `handle_` prefix) — pick one convention per project and stick to it.
- Constants use `UPPER_SNAKE_CASE` (this is universal across nearly all languages).
- Name things at the right level of abstraction. A helper inside a function can be short; a public API symbol must be fully descriptive.
- Avoid negated boolean names. Use `is_enabled` instead of `is_not_disabled`. Negations compound confusingly in conditions.

### File Naming Conventions

- Follow the established convention of the language or framework for source code files. When no convention exists, use `kebab-case` as the default.
- Component files (UI): follow the framework convention (e.g., PascalCase for React/Vue/Svelte components).
- Test files: same name as the file they test, with a `.test` or `.spec` suffix.
- Style files: match the name of the component or module they style.
- Configuration files: use the conventional name required by the tool. Do not rename configs for aesthetics.
- Documentation files: `PascalCase` or `UPPER_CASE` for root-level docs (e.g., `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`).
- Environment files: `.env`, `.env.local`, `.env.production` — always gitignored except templates (`.env.example`).
- Migration/seed files: timestamp-prefixed with a short description.
- File names must never contain spaces. Use dashes or underscores as the separator.
- One file = one responsibility. The file name should clearly reflect its single purpose.

### Structure and Formatting

- One concept per file. Do not mix unrelated logic in a single file.
- Keep files under 1000 lines. If a file is longer, it is doing too much — split it.
- Group related files by feature or domain, not by technical type.
- Order members consistently within a file: constants → types → helpers → main logic → exports.
- Always use consistent indentation and formatting as enforced by the project formatter. Never format manually.
- Blank lines separate logical sections within a file. Use them deliberately, not randomly.
- Imports go at the top of the file, grouped logically: standard library, third-party, then internal. Separate groups with a blank line.
- Never mix tabs and spaces. Configure your editor and formatter, then never think about it again.
- Keep line length reasonable (80–120 characters depending on the language convention). Long lines force horizontal scrolling and hide complexity.

### Functions and Methods

- Every function does exactly one thing.
- Limit parameters to 3 or fewer. If you need more, group them into an object, struct, or data class.
- Prefer pure functions where possible — same input always produces same output, no side effects.
- Return early to avoid deep nesting. Guard clauses go at the top.
- Never use flags (boolean parameters) to toggle behavior. Use two separate functions instead.
- Functions should operate at a single level of abstraction. Do not mix high-level orchestration with low-level details in the same function.
- Side effects (I/O, network, database, file system) should be pushed to the edges. Keep the core logic pure and testable.
- If a function needs a comment to explain what it does, its name is wrong or it is doing too much.

### Comments and Documentation

- Code should be self-documenting. A comment that restates what the code does is noise — remove it.
- Comments explain *why*, never *what*. The code tells you what; the comment tells you the reason behind a non-obvious decision.
- Every public function, method, or module must have a documentation comment explaining its purpose, parameters, and return value.
- Mark genuinely temporary workarounds with `HACK:` and a linked issue or ticket number. These must never stay permanently.
- Document architectural decisions and trade-offs in dedicated decision records, not scattered across code comments.
- Keep documentation close to the code it describes. A README in a module folder is better than a wiki page no one updates.
- If an API, function, or module has non-obvious preconditions or constraints, document them at the call site, not just the definition.

### Error Handling

- Fail fast and fail loud. Detect invalid state as early as possible and surface it immediately.
- Provide context in error messages: what happened, what was expected, and what the caller can do about it.
- Use typed/structured errors where the language supports it. Avoid relying on string matching for error handling.
- Log errors with enough context to reproduce the issue without exposing sensitive data.

### Testing

- Every new feature or bug fix ships with tests. No exceptions.
- Tests are first-class code. Apply the same quality standards as production code.
- Test behavior, not implementation. Tests should not break when internals are refactored.
- Each test must be independent — no shared mutable state between tests, no order dependency.
- Name tests as sentences that describe the expected behavior (e.g., "should return empty list when no users exist").
- Aim for fast, deterministic tests. Mock external dependencies at the boundary.
- Arrange–Act–Assert (or Given–When–Then) structure in every test. No exceptions.
- Test the edges: empty inputs, null/nil values, boundary conditions, error paths, and permission failures — not just the happy path.
- If a bug is found, write a failing test that reproduces it *before* writing the fix.
- Do not test private internals. If you feel the need to, the code probably needs to be restructured so the logic is testable through a public interface.
- Keep test setup minimal. If your test requires 30 lines of setup, the code under test has too many dependencies.

---

## Priorities — In This Order

1. **Correctness** — The code must do what it is supposed to do. Nothing else matters if it is wrong.
2. **Security** — Never trade security for convenience or speed.
3. **Readability** — Code is read 10x more than it is written. Optimize for the reader.
4. **Maintainability** — Code must be easy to change. Tight coupling and hidden dependencies are defects.
5. **Performance** — Optimize only after measuring. Premature optimization is wasted effort. But never choose an algorithm that is obviously worse when a better one is equally simple.
6. **Reusability** — Extract when duplication is proven (rule of three), not when it is assumed.

---

## UI/UX Best Practices

### Accessibility (A11y)

- All interactive elements must be reachable and operable via keyboard alone.
- Every image must have meaningful alt text (or empty alt for decorative images).
- Use semantic elements for their intended purpose: buttons for actions, links for navigation, headings for hierarchy.
- Maintain a logical heading hierarchy (h1 → h2 → h3). Never skip levels.
- Color must never be the sole means of conveying information. Use text, icons, or patterns alongside.
- Maintain a minimum contrast ratio of 4.5:1 for normal text and 3:1 for large text.
- All form inputs must have visible, associated labels. Placeholder text is not a label.
- Focus states must be visible and distinct. Never remove outline styles without providing an alternative.
- Interactive elements must have a minimum tap/click target of 44×44 pixels.
- Test with screen readers. If it does not work announced, it does not work.
- Provide skip navigation links for content-heavy pages.
- Use ARIA attributes only when native semantic HTML is insufficient. Prefer native elements first.
- Ensure all time-based media (video, audio) has captions or transcripts.
- Animated content must respect the user's `prefers-reduced-motion` setting.
- Never auto-play audio or video. The user controls when media starts.

### Visual Design

- Maintain consistent spacing using a defined scale (e.g., 4px, 8px, 12px, 16px, 24px, 32px, 48px). Never use arbitrary pixel values.
- Limit the type scale to a small, defined set of sizes. Do not invent new font sizes ad hoc.
- Use no more than two typefaces. One for headings, one for body — at most.
- Align elements to a grid. Visual alignment creates order and trust.
- Use whitespace generously. Crowded interfaces feel broken.
- Icons must be paired with text labels when the meaning is not universally unambiguous.
- Never use emojis instead of icons or text in a professional UI. They are not universally supported and can look unprofessional.
- In tables, left-align text and right-align numbers and dates. Center-aligning everything is a common mistake that reduces readability.
- Tables must be scrollable on small viewports. Never squeeze all columns into a fixed width that causes overflow or truncation.
- Use a consistent color palette defined as design tokens or variables. Never hard-code color values inline.
- Establish a clear visual hierarchy: primary action stands out, secondary is subdued, tertiary is minimal. The user's eye should know where to go.
- Limit the number of distinct visual weights on any single screen. Too many bold, colored, or large elements competing for attention creates chaos.
- Group related elements visually using proximity, borders, or background color — not just by placing them near each other.
- Maintain consistent border radii, shadow depths, and elevation levels across the entire application.
- Ensure the design system includes states for every component: default, hover, active, focused, disabled, loading, error, and empty.
- Dark mode is not just inverting colors. It requires a dedicated palette with adjusted contrast, reduced brightness, and desaturated colors.
- Use motion with purpose: to show relationships, provide feedback, or guide attention. Never animate purely for decoration.

### Interaction Design

- Every user action must have immediate, visible feedback (loading states, disabled states, success/error messages).
- Destructive actions require explicit confirmation and must be visually distinct (e.g., red).
- Never rely on hover for essential information or actions — hover does not exist on touch devices.
- Forms must validate inline as the user progresses, not only on submission.
- Error messages must be specific, human-readable, and placed next to the relevant field.
- Use progressive disclosure: show only what is relevant to the user's current task.
- Empty states must guide the user toward the next action, not show a blank screen.
- Always show a loading indicator if an operation takes more than 300ms.
- Never use a spinner for operations that can provide progress feedback (e.g., "Uploading 3 of 10 files...").
- Never use alert() or confirm() for user interactions in a web application. Use custom modals or inline messages instead.
- Modals should not dismiss when clicking outside or pressing Escape unless they are explicitly marked as non-critical. Critical modals (e.g., confirming deletion) must require an explicit action to dismiss.
- All modals must be the same size and layout and must be centered on the screen. Never use full-screen modals or side panels for simple interactions.
- Provide undo for destructive or significant actions whenever possible. Undo is always better than "Are you sure?".
- Disable buttons after the user clicks them to prevent double-submission. Re-enable only after the operation completes or fails.
- Preserve user input. If a form submission fails, never clear the fields. If the user navigates away and back, restore their state when possible.
- Paginate or virtualize long lists. Never dump hundreds of items into a single scrollable area.
- Keyboard shortcuts should be discoverable (displayed in tooltips or a help modal) and must never conflict with browser or OS defaults.
- Notifications and toasts must be dismissable, must not stack excessively, and must auto-dismiss after a reasonable duration (5–8 seconds).
- Never block the entire UI for a background operation. Keep the interface interactive whenever possible.

### Responsive Design

- Design mobile-first, enhance for larger viewports.
- No horizontal scrolling on any viewport width.
- Touch targets must be spaced far enough apart to prevent accidental taps.
- Content and layout must remain usable from 320px viewport width and up.
- Images and media must be responsive and never overflow their containers.
- In mobile version, feel free to hide non-essential content or use accordions/tabs to manage space, but never hide core functionality.

### Content and Copy

- Use plain, direct language. Avoid jargon, marketing speak, or technical terms in user-facing text.
- Buttons describe what they do: "Save Changes", "Delete Account", "Send Message" — not "Submit", "OK", or "Click Here".
- Sentences not paragraphs. Keep UI copy as short as possible without losing meaning.
- Be consistent with terminology. One concept = one word, everywhere.
- Error messages address what went wrong and what the user should do next.
- Use sentence case for UI labels and headings, not Title Case (unless it is a proper noun or brand name).
- Success messages should confirm the result, not just say "Success". (e.g., "Your changes have been saved" not "Success!").
- Avoid double negatives. "Enable notifications" not "Don't disable notifications".
- Dates, numbers, and currencies must be formatted according to the user's locale.
- Microcopy matters. Labels, placeholders, hints, and helper text deserve the same care as any other UX element.

### Navigation and Information Architecture

- Navigation must be consistent across all pages. The user should always know where they are and how to get back.
- Use breadcrumbs for deeply nested content.
- The most important actions and content must be reachable in the fewest clicks/taps possible.
- Never change the user's context unexpectedly. Opening a new tab, redirecting, or navigating away requires clear intent signal.
- Search must be available on any app with more than a handful of content items. Search results must be relevant, fast, and clearly displayed.
- Maintain URL state for meaningful views. If a user copies the URL, they should return to the same view.

### Performance Perception

- Optimistic UI updates improve perceived speed. Show the expected result immediately and reconcile with the server in the background.
- Skeleton screens are preferred over spinners for initial page loads.
- Lazy-load below-the-fold content, images, and heavy components.
- Perceived performance matters as much as actual performance. Prioritize rendering what the user sees first.

---

## Version Control Practices

- Commit often, in small, logical units. Each commit should represent one coherent change.
- Write commit messages in imperative mood: "Add user validation", not "Added user validation".
- First line of a commit message is a concise summary (50 characters or fewer). Add detail in the body if needed.
- Never commit generated files, build artifacts, or dependencies. Use `.gitignore` properly.
- Branch names follow the pattern: `type/short-description` (e.g., `feature/user-auth`, `fix/cart-total`, `chore/update-deps`).
- Keep pull requests small and focused. A PR that changes 50+ files is almost always too big to review effectively.
- Rebase or squash before merging to keep history clean and linear when the team convention allows it.

---

## Dependency Management

- Pin dependency versions. Never use floating ranges in production.
- Audit dependencies regularly for security vulnerabilities.
- Prefer well-maintained, widely-adopted packages with active communities.
- If a dependency provides a single utility you need, consider implementing it yourself instead.
- Keep the dependency tree as shallow and small as possible.
- Lock files must be committed to version control. They ensure reproducible builds.

---

## API Design Principles

- APIs are contracts. Once published, they are hard to change. Design them carefully upfront.
- Use consistent naming, patterns, and conventions across all endpoints or interfaces.
- Return meaningful status codes and error responses. Never return 200 for an error.
- Paginate list responses by default. Never return unbounded collections.
- Version APIs from the start. Even if you only have v1, the versioning mechanism must exist.
- Inputs must be validated and sanitized at the API boundary. Never trust the caller.
- Document every public API — endpoints, parameters, response shapes, error cases, and authentication requirements.
- Make APIs idempotent where possible. Retrying the same request should produce the same result.

---

## Data Handling

- Never store plain-text passwords. Use proper hashing algorithms.
- Apply the principle of least privilege to data access. Only query and expose what is needed.
- Validate data at every boundary: user input, API responses, database reads, file parsing.
- Use transactions for operations that must be atomic. Partial writes are bugs.
- Separate read and write models when complexity justifies it. Do not prematurely optimize, but know the pattern.
- Always handle empty, null, and missing data gracefully. Never assume a field will be present.

---

## Security Practices

- Apply the principle of least privilege everywhere: users, services, database roles, file permissions.
- Sanitize all output to prevent injection attacks (SQL, HTML, OS commands).
- Use parameterized queries for all database operations. Never concatenate user input into queries.
- Set appropriate security headers for web responses (Content-Security-Policy, X-Frame-Options, etc.).
- Tokens and sessions must expire. Define and enforce reasonable lifetimes.
- Rate-limit sensitive endpoints (login, signup, password reset, API calls).
- Never expose stack traces, debug info, or internal paths in production error responses.
- Use HTTPS everywhere. No exceptions.

---

## Logging and Observability

- Log at appropriate levels: `debug` for development details, `info` for significant events, `warn` for recoverable issues, `error` for failures.
- Never log sensitive data (passwords, tokens, personal information).
- Include correlation IDs, timestamps, and context in log entries.
- Structured logging (key-value or JSON) over free-form text strings.
- Logs must be actionable. If a log entry does not help someone diagnose a problem, it is noise.
- Monitor and alert on error rates, latency, and key business metrics. Logs alone are not observability.

---

## Configuration

- All environment-specific values come from environment variables or configuration files — never from source code.
- Provide sensible defaults. The application should work out of the box for local development with zero configuration.
- Validate configuration at startup. Fail immediately if required values are missing.
- Document every configuration option in a `.env.example` or equivalent.

---


## Resilience and Fault Tolerance

- Assume every external call (network, database, file system, third-party API) can fail. Handle it.
- Use retries with exponential backoff for transient failures. Never retry indefinitely.
- Set timeouts on all external calls. A missing timeout is a production outage waiting to happen.
- Design for graceful degradation. If a non-critical feature fails, the rest of the application must continue working.
- Circuit breakers protect downstream services from cascading failures. Use them for high-traffic external dependencies.

---

## Output Quality Check

Before you consider your code or review feedback complete, run through this checklist:
- Does the code do what it is supposed to do? (Correctness)
- Is it secure? (No secrets, proper validation, least privilege)
- Can a human read and understand it? (Readability)
- Can it be easily changed in the future? (Maintainability)
- Is it reasonably efficient? (Performance)
- Is it reusable where it should be? (Reusability)
- Does it follow the established conventions and patterns of the project?
- Are there any edge cases or error paths that are not handled?
- Is it properly tested? (Unit tests, integration tests, edge cases)
- Did I use all relevant skills for the technologies and patterns involved?

If the answer to any of these questions is "no", it is not done. Keep iterating until you can confidently check every box.
