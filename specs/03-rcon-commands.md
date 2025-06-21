# RCON Command Specification

## Simplified Architecture

Agents connect directly to Factorio via RCON with minimal infrastructure:

```
┌─────────────────┐       RCON        ┌─────────────────┐
│ External Agents │ ◄────────────────► │ Factorio Server │
│                 │   Direct Commands  │   + Optional    │
│ - Python Client │   JSON Responses   │     Mod         │
│ - Connection    │   5-20ms latency   │                 │
│   Pooling (2-3) │                    │                 │
└─────────────────┘                    └─────────────────┘
```

**Key simplifications:**
- No proxy/server layer
- Optional minimal mod for helper functions  
- Agents manage own connections and state caching
- Direct Lua execution via RCON

## Core Movement Semantics (Fact-Checked)

### Movement is State-Based, Not Action-Based

**Critical Discovery**: Factorio character movement is **continuous state**, not discrete actions.

```lua
-- This sets walking state for CONTINUOUS movement until changed
player.character.walking_state = {
    walking = true,
    direction = defines.direction.north  -- 0=north, 2=east, 4=south, 6=west
}

-- Movement continues each tick until walking_state changes
-- To stop: set walking = false
player.character.walking_state = {walking = false}
```

### Direction Semantics
```lua
defines.direction = {
    north = 0,      -- ↑
    northeast = 1,  -- ↗  
    east = 2,       -- →
    southeast = 3,  -- ↘
    south = 4,      -- ↓
    southwest = 5,  -- ↙
    west = 6,       -- ←
    northwest = 7   -- ↖
}
```

## Action Categories

### 1. Continuous State Actions
These set persistent state that continues until changed:

```lua
-- Movement (most important)
player.character.walking_state = {walking = true, direction = 2}

-- Mining (continuous until complete or cancelled)  
player.mine_entity(entity)

-- Crafting
player.begin_crafting({recipe = "iron-plate", count = 10})
```

### 2. Instant Actions
These execute immediately:

```lua
-- Teleportation (for training scenarios)
player.character.teleport({x = 100, y = 50})

-- Inventory operations
player.get_main_inventory().insert({name = "iron-ore", count = 50})
player.get_main_inventory().remove({name = "iron-plate", count = 10})

-- Building (workaround for removed build_from_cursor)
local entity = surface.create_entity({
    name = "inserter", 
    position = {x = 10, y = 20}, 
    force = player.force
})
if entity then
    player.get_main_inventory().remove({name = "inserter", count = 1})
end
```

### 3. Query Operations
These return current state:

```lua
-- Position and state
local pos = player.character.position
local inventory = player.get_main_inventory().get_contents()
local walking = player.character.walking_state

-- Entity detection
local entities = player.character.surface.find_entities_filtered({
    area = {{pos.x-5, pos.y-5}, {pos.x+5, pos.y+5}},
    type = "resource"
})
```

## Command Interface Specification

### Response Format Standard

All commands return JSON responses with this structure:
```lua
{
    status = "success|error",
    message = "Human readable description",
    data = { /* command-specific data */ }
}
```

### 1. Movement Commands

#### `set_walking_state(player_name, walking, direction)`
Sets continuous movement state.

**Parameters:**
- `player_name` (string): Player identifier
- `walking` (boolean): Whether to start/stop walking
- `direction` (integer, optional): Direction (0-7, see defines.direction)

**Returns:**
```lua
{
    status = "success",
    data = {
        position = {x = 100.5, y = 50.2},
        walking_state = {walking = true, direction = 2}
    }
}
```

**Implementation:**
```lua
function set_walking_state(player_name, walking, direction)
    local player = game.get_player(player_name)
    if not player or not player.character then
        return {status = "error", message = "Player has no character"}
    end
    
    local walking_state = {walking = walking}
    if walking and direction then
        walking_state.direction = direction
    end
    
    player.character.walking_state = walking_state
    
    return {
        status = "success",
        data = {
            position = player.character.position,
            walking_state = player.character.walking_state
        }
    }
end
```

#### `teleport(player_name, x, y)`
Instant teleportation (for training scenarios).

**Parameters:**
- `player_name` (string): Player identifier  
- `x` (number): Target X coordinate
- `y` (number): Target Y coordinate

**Returns:**
```lua
{
    status = "success",
    data = {
        old_position = {x = 50.0, y = 25.0},
        new_position = {x = 100.0, y = 50.0}
    }
}
```

### 2. Mining Commands

#### `start_mining(player_name, x, y)`
Begin mining entity at position.

**Parameters:**
- `player_name` (string): Player identifier
- `x` (number): Target X coordinate  
- `y` (number): Target Y coordinate

**Returns:**
```lua
{
    status = "success",
    data = {
        mining_target = "iron-ore",
        mining_hardness = 0.9,
        estimated_time = 1.5
    }
}
```

**Error Cases:**
- `"No entity at position"`
- `"Entity not minable"`  
- `"Out of reach"`
- `"No mining tool"`

### 3. Building Commands

#### `place_entity(player_name, entity_name, x, y, direction)`
Place entity from inventory.

**Parameters:**
- `player_name` (string): Player identifier
- `entity_name` (string): Entity prototype name
- `x` (number): Placement X coordinate
- `y` (number): Placement Y coordinate  
- `direction` (integer, optional): Entity direction (0-7)

**Returns:**
```lua
{
    status = "success", 
    data = {
        entity_id = 12345,
        position = {x = 100, y = 50},
        direction = 0
    }
}
```

### 4. Inventory Commands

#### `get_inventory(player_name, inventory_type)`
Get inventory contents.

**Parameters:**
- `player_name` (string): Player identifier
- `inventory_type` (string): "main" | "quickbar" | "armor" | "guns" | "ammo"

**Returns:**
```lua
{
    status = "success",
    data = {
        contents = {
            ["iron-ore"] = 45,
            ["iron-plate"] = 12,
            ["coal"] = 30
        },
        size = 40,
        free_slots = 37
    }
}
```

#### `transfer_items(player_name, items, source, target)`
Transfer items between inventories.

**Parameters:**
- `player_name` (string): Player identifier
- `items` (table): Array of {name, count} items
- `source` (string): Source inventory type
- `target` (string): Target inventory type or entity ID

### 5. Crafting Commands

#### `begin_crafting(player_name, recipe, count)`
Start crafting items.

**Parameters:**
- `player_name` (string): Player identifier
- `recipe` (string): Recipe name
- `count` (integer): Number to craft

**Returns:**
```lua
{
    status = "success",
    data = {
        recipe = "iron-plate",
        count = 10,
        crafting_time = 3.2,
        queue_position = 1
    }
}
```

### 6. Query Commands

#### `get_player_state(player_name)`
Get complete player state.

**Returns:**
```lua
{
    status = "success",
    data = {
        position = {x = 100.5, y = 50.2},
        walking_state = {walking = false, direction = 0},
        mining_state = {
            mining = true,
            target = "iron-ore", 
            progress = 0.65
        },
        inventory = { /* see get_inventory */ },
        health = 250,
        energy = 1000,
        crafting_queue = [
            {recipe = "iron-plate", count = 8, progress = 0.6}
        ]
    }
}
```

#### `find_entities(player_name, area, filters)`
Find entities in area around player.

**Parameters:**
- `player_name` (string): Player identifier
- `area` (number): Search radius
- `filters` (table, optional): {type = "resource", name = "iron-ore"}

**Returns:**
```lua
{
    status = "success",
    data = {
        entities = [
            {
                name = "iron-ore",
                type = "resource",
                position = {x = 102, y = 48},
                amount = 850
            }
        ]
    }
}
```

## Implementation Requirements

### Error Handling Standard

All command functions must implement this error handling pattern:

```lua
function command_name(parameters)
    local success, result = pcall(function()
        -- Command implementation
        return {status = "success", data = command_result}
    end)
    
    if not success then
        return {status = "error", message = result}
    end
    
    return result
end
```

### Player Validation

All commands operating on players must validate:

```lua
local player = game.get_player(player_name)
if not player then
    return {status = "error", message = "Player not found"}
end

if not player.character then
    return {status = "error", message = "Player has no character"}
end
```

### Position Validation

Commands using coordinates must validate reachability:

```lua
local distance = math.sqrt((x - player.character.position.x)^2 + (y - player.character.position.y)^2)
if distance > player.reach_distance then
    return {status = "error", message = "Position out of reach"}
end
```

## Implementation Options

### Option 1: Minimal Mod + RCON Functions

**Mod provides helper functions:**
```lua
-- In mod control.lua  
function set_walking_state(player_name, walking, direction)
    local player = game.get_player(player_name)
    if not player or not player.character then
        return game.table_to_json({status = "error", message = "No character"})
    end
    
    player.character.walking_state = {walking = walking, direction = direction}
    return game.table_to_json({
        status = "success",
        data = {position = player.character.position}
    })
end
```

**Agent calls via RCON:**
```python
class FactorioAgent:
    def move(self, direction):
        result = self.rcon.command(f"/c set_walking_state('{self.player_name}', true, {direction})")
        return json.loads(result)
```

### Option 2: Pure RCON (No Mod)

**Agent sends raw Lua:**
```python
def move(self, direction):
    lua_code = f"""
    local player = game.get_player('{self.player_name}')
    if not player or not player.character then
        return game.table_to_json({{status = 'error', message = 'No character'}})
    end
    player.character.walking_state = {{walking = true, direction = {direction}}}
    return game.table_to_json({{status = 'success', data = {{position = player.character.position}}}})
    """
    result = self.rcon.command(lua_code)
    return json.loads(result)
```

### State Management Strategy

**Agent-side caching eliminates frequent queries:**
```python
class FactorioAgent:
    def __init__(self):
        self.cached_entities = []
        self.last_position = None
        self.entity_cache_valid_distance = 5
        
    def get_state_efficiently(self):
        # Always get lightweight state (~100 bytes)
        basic_state = self.rcon.command("get_basic_player_state('agent1')")
        
        # Only scan entities if moved far enough
        if self.moved_far_enough(basic_state['position']):
            self.cached_entities = self.rcon.command("find_entities('agent1', 10)")
            
        return self.merge_with_cache(basic_state)
```

### Connection Management

- **Connection Pool**: 2-3 RCON connections per agent
- **Connection Limit**: 5 total concurrent RCON connections per server  
- **Latency**: 5-20ms per command (localhost)
- **Throughput**: 60 commands/second sustainable per agent

## Testing Interface

The specification defines these commands for comprehensive testing:

1. **Movement**: `set_walking_state`, `teleport`
2. **Mining**: `start_mining` 
3. **Building**: `place_entity`
4. **Inventory**: `get_inventory`, `transfer_items`
5. **Crafting**: `begin_crafting`
6. **Query**: `get_player_state`, `find_entities`

Each command has defined:
- Parameter types and validation
- Success response format
- Error cases and messages
- Implementation requirements
