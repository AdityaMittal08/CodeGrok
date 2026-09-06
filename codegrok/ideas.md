# Codegrok Design Direction

## Three possible approaches

### Theme Name: Signal Yard
Very brief intro: A bright editorial developer-tool aesthetic built from ink navy, cobalt, chartreuse, coral, and warm paper tones. It treats semantic search like a physical research instrument: labeled, tactile, and a little unruly.
Probability: 0.03

### Theme Name: Archive Heat
Very brief intro: A dark, saturated console with phosphor colors, scanline textures, and hot annotation marks. It makes code search feel like digging through a living archive rather than using a generic SaaS dashboard.
Probability: 0.07

### Theme Name: Monochrome Lab
Very brief intro: A quiet black-and-white workbench with one red signal color, precise typographic hierarchy, and a focus on reading code. It is restrained, forensic, and intentionally low-noise.
Probability: 0.02

## Chosen approach: Signal Yard

### Design Movement
Post-digital editorial maximalism with risograph print logic, technical drawing language, and a research-lab instrument mindset.

### Core Principles
1. **Semantic layers, not flat cards:** code, metadata, confidence, and action are separated into tactile visual layers.
2. **Color is functional signage:** cobalt marks navigation, chartreuse marks readiness, coral marks attention, and lilac marks semantic type.
3. **Dense shell, legible code:** the surrounding interface is expressive; the actual code stays dark, spacious, and easy to scan.
4. **Asymmetry with a stable spine:** a persistent rail and strong left edge give the tool a dependable structure while the content shifts and stacks.

### Color Philosophy
Deep ink navy creates the sense of a serious instrument. Warm cream gives the page a printed-paper warmth rather than a generic dark-mode feel. Cobalt is the primary action color; acid chartreuse signals success and indexed readiness; coral adds urgency to ingestion and errors; lilac distinguishes semantic categories. Every saturated hue should communicate status or hierarchy, never decoration alone.

### Layout Paradigm
A persistent left navigation rail anchors the workspace. The main content is split into an oversized semantic search bay and a narrower repository-status bay, followed by a full-width result feed. Result cards use an offset metadata strip and a code surface rather than a centered dashboard grid.

### Signature Elements
1. A tiny orbital mark made from brackets, a lens, and an arrow, used in the rail and hero.
2. Offset corner labels and technical registration marks around major panels.
3. Gradient similarity bars that behave like instrument readouts, paired with a monospace score.

### Interaction Philosophy
Interactions should feel like operating a well-made tool: short, crisp, and acknowledged. Buttons compress on press, panels lift slightly on hover, filters switch like physical toggles, and search results arrive in a small cascade. Errors are explicit, nearby, and actionable.

### Animation
Use 160–240ms transitions with a pronounced ease-out. Results enter with a 24px upward motion and opacity fade, staggered by 45ms. The indexing progress accent should pulse in a thin scanline rather than spin endlessly. Respect `prefers-reduced-motion` by removing entrance translations and pulses.

### Typography System
Headings use **Space Grotesk** with weight 700–800 for a geometric editorial voice. Body copy uses **DM Sans** for clear reading. Code and metadata use **IBM Plex Mono**. Labels are uppercase monospace with letter spacing. The visual hierarchy is intentionally split: expressive display type in the shell, quiet monospace in the data.

### Brand Essence
A semantic code search workbench for developers who think in intent, not keywords; different because it makes the invisible structure of a codebase legible.
Personality: **curious, exacting, kinetic**.

### Brand Voice
Headlines are direct and slightly provocative. CTAs are verbs with a sense of motion. Microcopy names the state of the system without hiding behind vague AI language.

Example headline: **Find the behavior, not the token.**

Example CTA: **Index a repository →**

### Wordmark & Logo
The mark is a compact orbital lens built from an opening code bracket, a circular search lens, and a diagonal arrow that exits the bracket. The wordmark should be set in Space Grotesk ExtraBold with a custom cut in the `g`, but the symbol must remain legible on its own.

### Signature Brand Color
**Signal Chartreuse `#D8FF3E`** — a high-energy readiness color that feels like a highlighted annotation on dark engineering paper.

## Style Decisions
- Use a deep ink navy base with warm cream surfaces instead of a generic white SaaS background.
- Keep gradients limited to status readouts and data visualization; no ambient purple blob gradients.
- Use generated Codegrok mark and grid texture assets in prominent areas.
- Do not fabricate customer reviews, ratings, or testimonials.
