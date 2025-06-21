# Factorio Parallel Game Control System

## Overview

This system enables programmatic control of multiple Factorio servers in parallel through external agents. Each agent can autonomously control a player character to perform tasks like resource gathering, construction, and factory management.

## Core Architecture: RCON Batching

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

### 1. Infrastructure Manager
- Spawns multiple headless Factorio servers in parallel
- Manages port allocation and server health monitoring
- Handles mod deployment across all servers
- Coordinates agent assignments to servers

### 2. External Agents
- Node.js/Python processes that connect to individual servers
- Execute game commands via RCON batching protocol
- Handle multi-packet response parsing and state management
- Implement game logic (movement, mining, building, crafting)

### 3. Factorio Mod (Optional Enhancement)
- Provides helper functions for common operations
- Optimizes state export and command processing
- Reduces RCON command complexity

### 4. RCON Communication Protocol
- Batches 3-5 operations per RCON call (4096 byte limit)
- Returns immediate JSON state via `rcon.print()`
- Handles response fragmentation and reassembly

## Detailed Component Interfaces

### Server Management (Parallel Factorio Instances)

**Infrastructure Manager**
```
┌─────────────────────────────────────────────────────────────┐
│ Infrastructure Manager (Node.js)                            │
├─────────────────────────────────────────────────────────────┤
│ - Spawn N headless Factorio servers                        │
│ - Port allocation (25000+N, 25100+N for RCON)             │
│ - Server health monitoring                                  │
│ - Automatic restart on crash                               │
│ - Resource usage tracking                                   │
└─────────────────────────────────────────────────────────────┘
```

**Server Spawn Command Template**
```bash
factorio --start-server saves/training-{id}.zip \
  --port {base_port + id} \
  --rcon-port {rcon_base_port + id} \
  --rcon-password {password} \
  --server-settings server-settings.json \
  --mod-directory mods/
```

### Client Management (Parallel Agents)

**Agent Pool Manager**
```
┌─────────────────────────────────────────────────────────────┐
│ Agent Pool Manager                                          │
├─────────────────────────────────────────────────────────────┤
│ - Spawn agent processes per server                         │
│ - RCON connection management                               │
│ - Task queue distribution                                  │
│ - Performance monitoring                                   │
│ - Failure recovery                                         │
└─────────────────────────────────────────────────────────────┘
```

**Agent Connection Protocol**
```javascript
// Each agent connects to one server
const agent = new FactorioAgent({
  serverId: 1,
  rconHost: 'localhost',
  rconPort: 25101,
  rconPassword: 'admin',
  stateFile: 'script-output/agent-1-state.json'
});
```

### Mod Installation & Distribution

**Mod Package Structure**
```
mods/
├── factorio-agent_1.0.0.zip
│   ├── info.json
│   ├── control.lua
│   ├── agent-interface.lua
│   └── state-export.lua
└── mod-list.json
```

**Automated Mod Installation**
```javascript
// Infrastructure manager handles mod deployment
class ModManager {
  deployMod(modPath, serverIds) {
    for (const id of serverIds) {
      copyMod(modPath, `servers/${id}/mods/`);
      updateModList(`servers/${id}/mods/mod-list.json`);
    }
  }
}
```

### Command Protocol (Agent → Mod)

**RCON Command Interface**
```lua
-- Commands sent via RCON as Lua scripts
/c global.agent_command_queue = global.agent_command_queue or {}
/c table.insert(global.agent_command_queue, {
  type = "move",
  target = {x = 100, y = 50},
  timestamp = game.tick
})
```

**Command Types**
```lua
-- Movement commands
{type = "move", target = {x, y}}
{type = "stop"}

-- Interaction commands  
{type = "mine", entity_id = 12345}
{type = "place", item = "inserter", position = {x, y}}
{type = "craft", recipe = "iron-gear-wheel", count = 10}

-- Inventory commands
{type = "pick_up", item = "iron-ore", count = 50}
{type = "drop", item = "stone", count = 100}
```

### State Export Protocol (Mod → Agent)

**File-Based State Export**
```lua
-- Mod writes to script-output/agent-{id}-state.json every N ticks
local state = {
  tick = game.tick,
  player = {
    position = player.position,
    health = player.character.health,
    inventory = export_inventory(player.get_main_inventory())
  },
  nearby_entities = scan_nearby_entities(player.position, 32),
  resources = scan_resources(player.position, 64)
}

game.write_file("agent-" .. agent_id .. "-state.json", 
                game.table_to_json(state), false)
```

**State Schema**
```javascript
// JSON schema for state file
{
  "tick": 12345,
  "player": {
    "position": {"x": 0, "y": 0},
    "health": 250,
    "inventory": {"iron-ore": 50, "coal": 30}
  },
  "nearby_entities": [
    {"type": "tree", "position": {"x": 5, "y": 3}},
    {"type": "rock", "position": {"x": -2, "y": 8}}
  ],
  "resources": [
    {"type": "iron-ore", "amount": 1000, "position": {"x": 50, "y": 20}}
  ]
}
```

### Communication Timing & Coordination

**Polling Strategy**
```javascript
class FactorioAgent {
  async run() {
    while (this.running) {
      // Send queued commands via RCON
      await this.sendCommands();
      
      // Poll for state updates
      const state = await this.readStateFile();
      
      // Make decisions based on state
      const commands = this.planActions(state);
      this.queueCommands(commands);
      
      await sleep(50); // 20 FPS polling
    }
  }
}
```

## Final Architecture: RCON Batching + Response Parsing

After extensive research and socratic review, here's the viable architecture:

### Core Communication Pattern
1. **Batched Commands**: External agent sends multi-operation Lua scripts via RCON
2. **Immediate Response**: Commands execute + return state via `rcon.print()` JSON
3. **Multi-packet Handling**: Agent buffers and reassembles fragmented responses
4. **Tick Coordination**: Separate polling for multi-tick operations (movement)

### RCON Protocol Constraints (Critical)
- **Packet Size Limit**: 4096 bytes maximum per RCON command
- **Response Fragmentation**: Large JSON responses split into multiple packets  
- **Synchronous Execution**: Commands execute immediately, but effects may take ticks
- **No Multi-tick Waiting**: Cannot wait for movement completion within single call

### Practical Batching Strategy
```lua
-- Compact command batch (under 3800 bytes)
/c do
  local p = game.player
  local results = {}
  
  -- Execute 3-5 operations per batch
  p.character.walking_state = {walking=true, direction=2}
  local entity = p.surface.find_entity('iron-ore', {100, 50})
  if entity then p.mine_entity(entity); results.mined = true end
  
  -- Return minimal state
  rcon.print(game.table_to_json({
    tick = game.tick,
    pos = p.position,
    walking = p.character.walking_state.walking,
    results = results
  }))
end
```

### Multi-Packet Response Handling
```javascript
class RCONClient {
  async sendBatch(luaScript) {
    const response = await this.rcon.send(luaScript);
    
    // Handle fragmented responses
    if (response.includes('"truncated":true')) {
      return await this.reassembleFragmentedResponse();
    }
    
    return JSON.parse(response);
  }
}
```

### Performance Reality Check
- **Batch Size**: 3-5 operations per RCON call (3800 byte limit)
- **Latency**: 10-50ms per batch (not per operation)  
- **Throughput**: 60-300 operations/second (vs original 6.6/sec)
- **Coordination**: Separate state polling for multi-tick operations

This architecture is **actually implementable** within Factorio's constraints.
