# Factorio Parallel Game Control System

## Project Overview

This project creates a system for programmatically controlling multiple Factorio servers in parallel. External agents can autonomously control player characters to perform tasks like:
- Resource gathering and mining operations
- Factory construction and logistics setup  
- Automated crafting and production management
- Multi-server coordination and task distribution

## Agent Directives

Guidelines for AI agents (Claude, Amp, etc.) working on this project:

### Research & Validation
- Use your tools. Search the web, think hard, think long
- Validate code early and often - everything should be validated before reaching main
- Use comprehensive testing and verification at each development stage
- **NEVER claim something is "done" until you've actually tested it works**
- Test all scripts, commands, and functionality before marking tasks complete

### Collaborative Review Process
- When writing/updating specs, spawn a "sub-agent" to act as a "socratic counterpart"
- The counterpart should review and scrutinize decisions, questioning pros/cons
- Interrogate assumptions and thought processes to improve spec quality and precision
- Challenge design decisions in the spirit of improving clarity and robustness

### Parallel Development
- Parallelize tasks via sub-agents and git worktrees when possible
- Maximum of 10 sub-agents at once to maintain coordination
- "Write" tasks can only be parallelized when they are independent
- Ensure proper synchronization points for dependent work

### Design Phase Constraints
- During design phase, only changes to specs are allowed
- No implementation code until design is complete and validated
- Focus on architecture, interfaces, and detailed planning

### AGENT.md Maintenance
- **AGENT.md is sacred** - keep it clean, current, and concise
- Remove outdated/conflicting information immediately when discovered
- Only essential context that agents need across all tasks belongs here
- Detailed technical specs belong in separate spec files, not AGENT.md

## Architecture Principles

Following [Building an Agentic System](https://gerred.github.io/building-an-agentic-system/) principles:
- **Simplicity First**: Minimal infrastructure, direct connections
- **Explicit Safety**: Clear permission systems for destructive actions
- **Composable Tools**: Plugin architecture for extensibility
- **Predictable Behavior**: Consistent outputs for same inputs

## Core Architecture

```
┌─────────────────┐       RCON        ┌─────────────────┐
│ External Agents │ ◄────────────────► │ Factorio Server │
│                 │   Direct Protocol  │                 │
│ - RL Policies   │   (5-20ms latency) │ - Lua Scripts   │
│ - Pathfinding   │   2-3 connections  │ - Game State    │
│ - Task Planning │   per agent        │ - Player Control│
└─────────────────┘                    └─────────────────┘
```

## Factorio Integration (Fact-Checked)

### What Works
- **Movement**: `player.character.walking_state = {walking=true, direction=0}`
- **Mining**: `player.mine_entity(entity, force)`
- **Teleportation**: `player.character.teleport({x, y})` (useful for training)
- **Inventory**: `get_main_inventory().insert/remove()`
- **Crafting**: `player.begin_crafting({recipe=..., count=...})`

### What Doesn't Work (Critical Corrections)
- ❌ `build_from_cursor()` - **REMOVED from API** (not MP-safe)
- ❌ File reading in mods - Mods can **ONLY WRITE** to script-output
- ❌ Direct file I/O communication - Must use **RCON protocol**

### Communication Architecture
1. **External Agent → Factorio**: Direct RCON commands (5-20ms latency)
2. **Factorio → Agent**: RCON responses with JSON data
3. **Connection Pool**: 2-3 RCON connections per agent for throughput

### Building Workaround
Since `build_from_cursor` doesn't exist:
```lua
-- Use surface.create_entity + manual inventory management
local entity = surface.create_entity({name="inserter", position={x,y}, force=player.force})
if entity then
    player.get_main_inventory().remove({name="inserter", count=1})
end
```

## Direct RCON Benefits

- **Simplicity**: No proxy layer complexity or single point of failure
- **Connection Scaling**: 2-3 agents per server with connection pooling
- **Fault Isolation**: Agent failures don't cascade to other agents
- **Easier Testing**: Direct command interface for comprehensive test coverage



## Key Files

- `specs/03-rcon-commands.md` - RCON command specification with implementation options
- `specs/05-implementation-roadmap.md` - Simplified development phases  
- `specs/01-architecture-overview.md` - High-level system design
- `specs/02-factorio-integration.md` - API integration details

## Development Commands

```bash
# Start Factorio headless server
factorio --start-server save.zip --port 25000 --rcon-port 25001 --rcon-password admin

# Test RCON communication  
python test_rcon.py --host localhost --port 25001 --password admin
```
