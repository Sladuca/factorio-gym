# Factorio Agent Architecture Overview

## High-Level Approach

Based on research, there are several ways to automate Factorio:

### Option 1: Factorio Mod + External Agent (Recommended)
- **Factorio Mod (Lua)**: Controls the player character directly via Factorio's Lua API
- **External Agent**: Handles high-level decision making and task planning
- **Communication**: File I/O, RCON, or custom protocol

### Option 2: Computer Vision + Input Simulation
- Read game state via screen capture
- Send keyboard/mouse inputs to game
- More fragile but works without modding

### Option 3: Memory Reading + Input Injection
- Read game memory directly
- Inject inputs at OS level
- Very fragile, version-dependent

## Recommended Architecture: Mod + Agent

```
┌─────────────────┐    Commands     ┌─────────────────┐
│                 │ ──────────────> │                 │
│ External Agent  │                 │ Factorio Mod    │
│ (Node.js/Python)│ <────────────── │ (control.lua)   │
│                 │    Game State   │                 │
└─────────────────┘                 └─────────────────┘
                                             │
                                             v
                                    ┌─────────────────┐
                                    │ Factorio Game   │
                                    │ (Player Control)│
                                    └─────────────────┘
```

## Key Components

### 1. Factorio Mod (control.lua)
- Read game state (inventories, resources, entities)
- Control player movement (`walking_state`)
- Execute actions (mine, craft, build, place)
- Handle communication with external agent

### 2. External Agent
- High-level task planning ("go refill turrets")
- Pathfinding and logistics
- Resource management
- Decision making AI

### 3. Communication Layer
- Command queue (agent → mod)
- State reporting (mod → agent)
- File-based or network-based

## Benefits of This Approach
- Native game integration
- Full access to game state
- Precise control
- Extensible and maintainable
- Works in multiplayer
