# Factorio Integration Deep Dive

## Factorio Mod Capabilities (Fact-Checked)

### Player Control API
Based on actual Lua API capabilities:

```lua
-- Movement (CONFIRMED WORKING)
player.character.walking_state = {walking = true, direction = defines.direction.north}

-- Mining (CONFIRMED WORKING)
player.mine_entity(entity, force)

-- Building/Placing (CORRECTED - build_from_cursor was REMOVED)
-- Must use surface.create_entity instead:
local entity = surface.create_entity({
    name = "iron-chest",
    position = {x, y},
    force = player.force
})
-- Note: This bypasses inventory - must manually remove items

-- Inventory Management (CONFIRMED WORKING)
player.get_main_inventory().insert({name = "iron-plate", count = 50})
player.get_main_inventory().remove({name = "iron-plate", count = 25})

-- Crafting (CONFIRMED WORKING)
player.begin_crafting({recipe = "iron-gear-wheel", count = 10})

-- Teleportation (CONFIRMED WORKING - useful for fast training)
player.character.teleport({x, y})
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

## Communication Methods (CORRECTED)

### Method 1: RCON + Script Output (ACTUAL WORKING METHOD)
- External agent sends Lua commands via RCON protocol
- Factorio mod executes commands directly
- Mod writes game state to `script-output/` folder (only write access)
- External agent reads state files
- **Pros**: Real-time command execution, leverages built-in protocol
- **Cons**: RCON setup required, ~10-50ms latency per command

**Critical Correction**: Factorio mods CANNOT read files - only write to script-output folder!

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

## Recommended: RCON + Script Output System

Use RCON for commands, script-output for state:

```python
# External Agent → Factorio (via RCON)
rcon.send_command('/c player.character.walking_state = {walking=true, direction=0}')

# Factorio → External Agent (via script-output files)
# Mod writes: script-output/gym_state_1234.json
```

```
script-output/           # Factorio writes here (only write access)
  ├── player_state.json  # Player status updates
  ├── world_state.json   # Nearby entities 
  └── events.json        # Game events log
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

## Performance Considerations (Updated)
- RCON commands have ~10-50ms latency - batch when possible
- Limit state exports to once per second (expensive operations)
- Use efficient entity scanning with small areas (find_entities_filtered)
- Realistic target: 10-100 environment steps/second depending on complexity
