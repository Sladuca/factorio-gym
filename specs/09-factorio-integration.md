# Factorio Game Integration

## Overview

How the training environment actually plugs into and controls Factorio at the lowest level.

## Integration Architecture

```
┌─────────────────────────────────────────┐
│           Training Environment          │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ RL Policies │  │ LLM Planners    │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────┬───────────────────────┘
                  │ Python/Node.js
                  │
    ┌─────────────▼───────────────┐
    │     Factorio Gym Mod       │ ◄── Lua control.lua
    │                            │
    │ ┌─────────┐ ┌────────────┐ │
    │ │ Command │ │ State      │ │
    │ │ Handler │ │ Extractor  │ │
    │ └─────────┘ └────────────┘ │
    └─────────────┬──────────────┘
                  │ Factorio Lua API
                  │
    ┌─────────────▼──────────────┐
    │      Factorio Game         │
    │                            │
    │ Player Character ──────────┼──► World State
    │ Game World       ──────────┼──► Entities  
    │ Production       ──────────┼──► Resources
    └────────────────────────────┘
```

## Factorio Mod Implementation

### Core Mod Structure
```
factorio-gym-mod/
├── info.json                 # Mod metadata
├── control.lua              # Main mod entry point
├── gym/
│   ├── init.lua             # Gym interface initialization
│   ├── communication.lua    # External communication
│   ├── state_extractor.lua  # Game state extraction
│   ├── action_executor.lua  # Command execution
│   └── scenarios.lua        # Training scenario management
└── data.lua                 # Game data modifications (if needed)
```

### control.lua (Main Entry Point)
```lua
-- factorio-gym-mod/control.lua
require("gym.init")

script.on_init(function()
    gym.initialize()
end)

script.on_nth_tick(1, function(event)  -- Every game tick
    gym.process_tick(event.tick)
end)

script.on_nth_tick(60, function(event)  -- Every second
    gym.heartbeat(event.tick)
end)
```

### Communication Layer
```lua
-- gym/communication.lua
local communication = {}

-- File-based communication (simple but works)
communication.COMMAND_DIR = "gym_commands/"
communication.STATE_DIR = "gym_state/"

function communication.read_commands()
    local commands = {}
    local files = game.file_system.list_files(communication.COMMAND_DIR)
    
    for _, filename in pairs(files) do
        if filename:match("%.json$") then
            local content = game.file_system.read_file(communication.COMMAND_DIR .. filename)
            local command = game.json.parse(content)
            table.insert(commands, command)
            
            -- Move to processed directory
            game.file_system.move_file(
                communication.COMMAND_DIR .. filename,
                communication.COMMAND_DIR .. "processed/" .. filename
            )
        end
    end
    
    return commands
end

function communication.write_state(state_data)
    local timestamp = game.tick
    local filename = communication.STATE_DIR .. "state_" .. timestamp .. ".json"
    local json_data = game.json.stringify(state_data)
    game.file_system.write_file(filename, json_data)
end

-- Alternative: TCP socket communication (faster)
function communication.init_socket()
    -- Requires socket mod or external process
    communication.socket = socket.tcp()
    communication.socket:connect("127.0.0.1", 8888)
end

return communication
```

### State Extraction
```lua
-- gym/state_extractor.lua
local state_extractor = {}

function state_extractor.extract_player_state(player)
    local character = player.character
    if not character then return nil end
    
    return {
        position = {x = character.position.x, y = character.position.y},
        health = character.health,
        walking_state = {
            walking = character.walking_state.walking,
            direction = character.walking_state.direction
        },
        mining_state = {
            mining = character.mining_state and character.mining_state.mining,
            mining_target = character.mining_target and character.mining_target.name
        },
        inventory = state_extractor.extract_inventory(character.get_main_inventory()),
        current_activity = state_extractor.determine_activity(character)
    }
end

function state_extractor.extract_inventory(inventory)
    local items = {}
    for name, count in pairs(inventory.get_contents()) do
        table.insert(items, {name = name, count = count})
    end
    return items
end

function state_extractor.extract_local_map(player, radius)
    local surface = player.surface
    local position = player.position
    
    -- Create a grid representation around player
    local map_data = {}
    local size = radius * 2
    
    for x = -radius, radius do
        map_data[x + radius] = {}
        for y = -radius, radius do
            local world_pos = {x = position.x + x, y = position.y + y}
            local tile = surface.get_tile(world_pos)
            local entities = surface.find_entities_in_area({
                {world_pos.x - 0.5, world_pos.y - 0.5},
                {world_pos.x + 0.5, world_pos.y + 0.5}
            })
            
            map_data[x + radius][y + radius] = {
                tile_type = tile.name,
                entities = state_extractor.encode_entities(entities),
                walkable = tile.collides_with("player-layer") == false
            }
        end
    end
    
    return map_data
end

function state_extractor.extract_nearby_entities(player, radius)
    local surface = player.surface
    local area = {
        {player.position.x - radius, player.position.y - radius},
        {player.position.x + radius, player.position.y + radius}
    }
    
    local entities = surface.find_entities_in_area(area)
    local entity_data = {}
    
    for _, entity in pairs(entities) do
        table.insert(entity_data, {
            name = entity.name,
            position = {x = entity.position.x, y = entity.position.y},
            health = entity.health,
            type = entity.type,
            -- Add type-specific data
            amount = entity.amount,  -- for resources
            energy = entity.energy,  -- for power entities
            crafting_progress = entity.crafting_progress  -- for assemblers
        })
    end
    
    return entity_data
end

return state_extractor
```

### Action Execution
```lua
-- gym/action_executor.lua
local action_executor = {}

function action_executor.execute_command(player, command)
    if command.type == "MOVE" then
        action_executor.execute_movement(player, command)
    elseif command.type == "MINE" then
        action_executor.execute_mining(player, command)
    elseif command.type == "BUILD" then
        action_executor.execute_building(player, command)
    elseif command.type == "CRAFT" then
        action_executor.execute_crafting(player, command)
    end
end

function action_executor.execute_movement(player, command)
    local character = player.character
    if not character then return end
    
    if command.params.method == "walk" then
        -- Set walking state directly
        character.walking_state = {
            walking = true,
            direction = command.params.direction or defines.direction.north
        }
    elseif command.params.method == "teleport" then
        -- Instant movement for faster training
        character.teleport(command.params.target)
    end
end

function action_executor.execute_mining(player, command)
    local character = player.character
    local surface = player.surface
    
    if command.params.target then
        -- Mine specific entity
        local target = surface.find_entity(command.params.entity_name, command.params.target)
        if target and target.minable then
            character.mine_entity(target)
        end
    elseif command.params.area then
        -- Mine everything in area
        local area = command.params.area
        local entities = surface.find_entities_in_area(area)
        
        for _, entity in pairs(entities) do
            if entity.minable then
                character.mine_entity(entity)
            end
        end
    end
end

function action_executor.execute_building(player, command)
    local character = player.character
    local surface = player.surface
    
    -- Check if player has the item
    local inventory = character.get_main_inventory()
    if inventory.get_item_count(command.params.entity) == 0 then
        return {error = "insufficient_items", needed = command.params.entity}
    end
    
    -- Try to place the entity
    local created = surface.create_entity({
        name = command.params.entity,
        position = command.params.position,
        direction = command.params.direction or defines.direction.north,
        force = player.force,
        raise_built = true
    })
    
    if created then
        -- Remove item from inventory
        inventory.remove({name = command.params.entity, count = 1})
        return {success = true, entity = created}
    else
        return {error = "cannot_place", reason = "collision_or_invalid_position"}
    end
end

return action_executor
```

### Gym Interface
```lua
-- gym/init.lua
local communication = require("gym.communication")
local state_extractor = require("gym.state_extractor")
local action_executor = require("gym.action_executor")

local gym = {}

function gym.initialize()
    global.gym = {
        active = true,
        tick_count = 0,
        command_queue = {},
        last_state_export = 0
    }
    
    -- Initialize communication
    communication.init()
    
    -- Set up directories
    game.file_system.create_directory(communication.COMMAND_DIR)
    game.file_system.create_directory(communication.STATE_DIR)
end

function gym.process_tick(tick)
    if not global.gym.active then return end
    
    global.gym.tick_count = tick
    
    -- Process new commands (every tick for responsiveness)
    local commands = communication.read_commands()
    for _, command in pairs(commands) do
        gym.execute_command(command)
    end
    
    -- Export state (configurable frequency)
    if tick % global.gym.state_export_frequency == 0 then
        gym.export_state()
    end
end

function gym.execute_command(command)
    local player = game.get_player(1)  -- Assume single player for training
    if not player then return end
    
    local result = action_executor.execute_command(player, command)
    
    -- Log command execution
    table.insert(global.gym.command_queue, {
        command = command,
        result = result,
        tick = global.gym.tick_count
    })
end

function gym.export_state()
    local player = game.get_player(1)
    if not player then return end
    
    local state = {
        tick = global.gym.tick_count,
        player = state_extractor.extract_player_state(player),
        local_map = state_extractor.extract_local_map(player, 16),
        nearby_entities = state_extractor.extract_nearby_entities(player, 32),
        command_history = global.gym.command_queue
    }
    
    communication.write_state(state)
    
    -- Clear command history to prevent memory bloat
    global.gym.command_queue = {}
    global.gym.last_state_export = global.gym.tick_count
end

return gym
```

## Python Integration Layer

### Environment Interface
```python
class FactorioEnv(gym.Env):
    def __init__(self, server_config):
        self.server = FactorioServer(server_config)
        self.communication = FileCommunication(self.server.save_directory)
        self.command_id = 0
        
    def step(self, action):
        # Convert gym action to Factorio command
        command = self._action_to_command(action)
        
        # Send command to Factorio
        self.communication.send_command(command)
        
        # Wait for state update
        state = self.communication.wait_for_state(timeout=1.0)
        
        # Convert to gym observation
        obs = self._state_to_observation(state)
        reward = self._calculate_reward(state)
        done = self._check_termination(state)
        
        return obs, reward, done, {}
    
    def _action_to_command(self, action):
        """Convert gym action array to Factorio command"""
        if isinstance(action, np.ndarray):
            # Discrete action space: [movement, interaction, target, item]
            return {
                "id": f"cmd_{self.command_id}",
                "type": "COMPOUND",
                "params": {
                    "movement": MOVEMENT_ACTIONS[action[0]],
                    "interaction": INTERACTION_ACTIONS[action[1]],
                    "target": action[2],
                    "item": action[3]
                }
            }
```

### Communication Handler
```python
class FileCommunication:
    def __init__(self, factorio_save_dir):
        self.command_dir = Path(factorio_save_dir) / "gym_commands"
        self.state_dir = Path(factorio_save_dir) / "gym_state"
        
        # Ensure directories exist
        self.command_dir.mkdir(exist_ok=True)
        self.state_dir.mkdir(exist_ok=True)
        
    def send_command(self, command):
        """Write command file for Factorio mod to read"""
        filename = f"cmd_{command['id']}.json"
        filepath = self.command_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(command, f)
    
    def wait_for_state(self, timeout=1.0):
        """Wait for Factorio to write new state file"""
        start_time = time.time()
        latest_state = None
        
        while time.time() - start_time < timeout:
            # Find newest state file
            state_files = list(self.state_dir.glob("state_*.json"))
            if state_files:
                newest_file = max(state_files, key=lambda x: x.stat().st_mtime)
                if newest_file != latest_state:
                    with open(newest_file, 'r') as f:
                        return json.load(f)
            
            time.sleep(0.01)  # 10ms polling
        
        raise TimeoutError("No state update received from Factorio")
```

This gives you the complete pipeline from Python gym actions all the way down to controlling the actual Factorio game character through the Lua API!
