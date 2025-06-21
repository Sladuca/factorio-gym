# Factorio Integration Deep Dive

## Factorio Mod Capabilities

### Player Control API
Based on Lua API research:

```lua
-- Movement
player.walking_state = {walking = true, direction = defines.direction.north}

-- Mining
player.mine_entity(entity, force)

-- Building/Placing
player.build_from_cursor({position = {x, y}})

-- Inventory Management
player.get_main_inventory().insert({name = "iron-plate", count = 50})

-- Crafting
player.begin_crafting({recipe = "iron-gear-wheel", count = 10})
```

### Game State Access
```lua
-- Player info
local inventory = player.get_main_inventory()
local position = player.position
local health = player.character.health

-- World scanning
local entities = surface.find_entities_in_area(area)
local resources = surface.find_entities_filtered({type = "resource"})

-- Factory status
local inserters = surface.find_entities_filtered({name = "inserter"})
```

## Communication Methods

### Method 1: File I/O (Simple)
- Agent writes commands to `commands.json`
- Mod reads file every tick, executes commands
- Mod writes game state to `state.json`
- **Pros**: Simple, cross-platform
- **Cons**: File I/O overhead, polling

### Method 2: RCON (Network)
- Use Factorio's RCON protocol
- Send Lua commands directly
- **Pros**: Real-time, built-in
- **Cons**: Limited to simple commands

### Method 3: Custom Network Protocol
- Mod opens socket connection
- Direct TCP/UDP communication
- **Pros**: Efficient, real-time
- **Cons**: More complex, mod security

## Recommended: File I/O + Event System

Start with file-based communication for simplicity:

```
commands/
  ├── move.json        # Movement commands
  ├── mine.json        # Mining targets
  ├── build.json       # Construction queue
  └── craft.json       # Crafting orders

state/
  ├── player.json      # Player status
  ├── inventory.json   # Current inventory
  ├── world.json       # Nearby entities
  └── resources.json   # Resource locations
```

## Mod Structure

```
factorio-agent-mod/
├── info.json          # Mod metadata
├── control.lua        # Main mod logic
├── commands/
│   ├── movement.lua   # Handle movement commands
│   ├── mining.lua     # Handle mining commands
│   ├── building.lua   # Handle construction
│   └── crafting.lua   # Handle crafting
└── state/
    ├── scanner.lua    # World state scanning
    └── reporter.lua   # State export
```

## Performance Considerations
- Limit file I/O to once per second
- Cache game state between updates
- Use efficient entity scanning (find_entities_filtered)
- Batch commands when possible
