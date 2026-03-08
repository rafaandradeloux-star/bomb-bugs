# Bomb Bugs

Bomb Bugs is a game project that starts simple and grows into a fast, ability-based **single-player** bug fighting game for the web.

## Project Vision

Build an intense single-player combat game where the player controls bugs with unique abilities, clear visual identity, and responsive controls.

## Current Goal (Phase 1)

Create a playable prototype where:

- A cube (placeholder player) moves left and right.
- Input feels responsive with keyboard first (mobile touch can be added later).
- The game runs in a browser.

This phase validates controls, performance baseline, and development pipeline before investing in full character systems.

## Recommended Technology (Web First, Python)

For a web-first launch with Python and fast iteration:

- Engine/Framework: pygame-ce
- Language: Python 3.11+
- Web packaging: pygbag (WebAssembly build for browser)
- Input: Keyboard first, optional gamepad/touch later
- Source control: Git + GitHub
- Art pipeline: Placeholder sprites first, final art later
- Audio: pygame mixer

Why pygame-ce + pygbag:

- Pure Python development workflow
- Fast for 2D prototyping and combat loops
- Can ship to browser using WebAssembly
- Simple local iteration before web builds

Alternative:

- Godot Web export is viable, but pygame-ce + pygbag keeps the stack fully Python.

## Core Game Requirements (Target State)

### Gameplay

- Real-time player-vs-enemy combat
- Multiple playable bug classes
- Unique abilities per bug
- Health, damage, cooldown, and status-effect systems
- Win/lose conditions per match

### Controls

- Left/right movement (MVP)
- Attack button(s)
- Ability trigger buttons
- UI that works on desktop browser (mobile web support can be phase 2+)

### Technical

- Stable 60 FPS target on modern desktop browsers
- Scalable architecture for adding new bugs and abilities
- Save basic player progression/settings locally
- Crash-safe build and telemetry-ready structure

### Content

- Distinct bug roster (stats + abilities)
- Arena(s) with hazards or tactical variation
- VFX/SFX feedback for hits and abilities

## Roadmap (2 Programmers, Single-Player Web App)

### Phase 1: Movement Prototype (1 week)

- pygame-ce project setup
- pygbag web build setup
- Simple scene + cube placeholder
- Left/right movement with keyboard input
- Basic camera and boundaries
- Browser build and local deploy

Deliverable: controllable cube prototype in browser.

### Phase 2: Combat Vertical Slice (3-4 weeks)

- Replace cube with one bug character
- Basic attack + one special ability
- Enemy AI dummy
- Health/damage/death loop
- Temporary UI (HP bars, cooldowns)

Deliverable: one complete combat loop.

### Phase 3: Multi-Bug Framework (4-6 weeks)

- Data-driven bug definitions (stats, abilities, cooldowns)
- 4-6 playable bugs
- Ability system refactor for reusability
- Arena hazards and match rules
- Improved animations, hit feedback, and effects

Deliverable: replayable pre-alpha with multiple bugs.

### Phase 4: Production Pre-Release (6-10 weeks)

- Progression/meta layer (unlocks, profile)
- UI polish and onboarding/tutorial
- Performance optimization for older devices
- QA pass, bug fixing, balancing
- Web deployment (staging + production)

Deliverable: beta-ready single-player web build.

## Estimated Total Timeline

With 2 programmers: **12 to 18 weeks** for a solid beta, depending on art/audio scope and feature creep.

## Team Split (Suggested)

Programmer 1 (Gameplay Systems):

- Movement and combat logic
- Ability framework
- AI and match flow

Programmer 2 (Platform + UX + Tooling):

- Input/UI integration
- Web build/deploy pipeline and performance
- Save/progression systems
- Debug/dev tooling

Both collaborate on architecture, code reviews, and balancing.

## Milestones and Exit Criteria

### Milestone A - MVP Controls

- Cube moves left/right smoothly in browser
- Build runs without critical errors

### Milestone B - Combat Loop

- One bug can attack and use one ability
- Match can start and end cleanly

### Milestone C - Playable Pre-Alpha

- 4+ bugs with unique abilities
- Stable frame rate and no blockers

### Milestone D - Beta

- Polish pass complete
- External testers can play full sessions in browser

## Risks to Manage Early

- Scope expansion before systems are stable
- Underestimating UI/UX effort across different browsers/resolutions
- Performance regressions from VFX-heavy abilities
- Balancing complexity as roster grows

## Next Step (Immediate)

Implement Phase 1 this week: create the pygame-ce project, configure pygbag, add cube movement, and ship a first playable browser build.

## Run Locally (Current Prototype)

1. Activate the virtual environment:
   `source .venv/bin/activate`
2. Run the game:
   `python main.py`

Controls:

- Move left: `Left Arrow` or `A`
- Move right: `Right Arrow` or `D`
- Jump: `Space`, `W`, or `Up Arrow`
- Dash: `Left Shift` or `Right Shift`
- Slash attack: `Left Mouse Click`
- Throw bomb (5 damage, 5s cooldown): `F`
- Heal + green floor splash: `E`
- Quit: close the game window

## Code Structure (Modularized)

The gameplay code was split into focused modules so it is easier to read and extend:

- `main.py`: thin entrypoint that starts the game.
- `bomb_bugs/game.py`: orchestration loop (wires modules together).
- `bomb_bugs/gameplay.py`: gameplay systems (input, combat, movement, bombs, respawn, floating text events).
- `bomb_bugs/rendering.py`: frame rendering pipeline.
- `bomb_bugs/config.py`: constants and tuning values (movement, combat, timing).
- `bomb_bugs/models.py`: shared data models (`Actor`, particles, state objects).
- `bomb_bugs/world.py`: platform creation and landing/collision helpers.
- `bomb_bugs/combat.py`: slash hitbox construction.
- `bomb_bugs/effects.py`: slash visuals, dust death effect, reverse-dust respawn effect, dash trail.
- `bomb_bugs/ui.py`: health bars, debug HUD text, pixel-font floating number rendering.

If you want to tune game feel quickly, start with `bomb_bugs/config.py`.
