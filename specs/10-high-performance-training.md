# High-Performance Training Infrastructure

## Performance Requirements

**Target**: 1000+ environment steps/second per GPU for RL training
**Current bottleneck**: File I/O + full game simulation

## Speed Optimizations

### 1. Ultra-Fast Communication

#### Shared Memory Interface
```cpp
// factorio-gym-bridge.cpp (C++ extension)
#include <boost/interprocess/shared_memory_object.hpp>

struct FactorioState {
    float player_pos[2];
    uint8_t local_map[32][32][8];  // Compact binary format
    uint16_t inventory[64];
    uint32_t entities[16][4];
    uint64_t timestamp;
};

struct FactorioAction {
    uint8_t action_type;
    float parameters[8];
    uint64_t command_id;
};

class SharedMemoryBridge {
    boost::interprocess::shared_memory_object shm_state;
    boost::interprocess::shared_memory_object shm_action;
    FactorioState* state_ptr;
    FactorioAction* action_ptr;
    
public:
    void write_action(const FactorioAction& action) {
        *action_ptr = action;
    }
    
    FactorioState read_state() {
        return *state_ptr;
    }
};
```

#### Direct TCP Socket (Lua side)
```lua
-- Ultra-fast binary protocol
local socket = require("socket.core")

local bridge = {
    sock = nil,
    buffer = {}
}

function bridge.init()
    bridge.sock = socket.tcp()
    bridge.sock:connect("127.0.0.1", 25001)
    bridge.sock:settimeout(0)  -- Non-blocking
end

function bridge.read_actions()
    local data, err = bridge.sock:receive(4096)  -- Binary data
    if data then
        return bridge.decode_binary_actions(data)
    end
    return {}
end

function bridge.write_state(state)
    local binary_data = bridge.encode_binary_state(state)
    bridge.sock:send(binary_data)
end
```

### 2. Simplified Game Environments

#### Movement-Only Environment
```lua
-- Minimal environment for movement training
local minimal_env = {}

function minimal_env.init_scenario()
    -- Tiny 64x64 map
    -- Flat terrain only
    -- No entities except player
    -- No crafting/building
    
    game.create_surface("training_movement", {
        width = 64,
        height = 64,
        terrain_segmentation = 1,
        water = "none"
    })
end

function minimal_env.step(action)
    local player = game.get_player(1)
    
    -- Only movement actions
    if action.type == 0 then  -- MOVE
        player.character.walking_state = {
            walking = true,
            direction = action.direction
        }
    end
    
    -- Minimal state extraction
    return {
        pos_x = player.position.x,
        pos_y = player.position.y,
        walking = player.character.walking_state.walking,
        direction = player.character.walking_state.direction
    }
end
```

#### Mining-Only Environment
```lua
local mining_env = {}

function mining_env.init_scenario()
    -- Small map with only iron ore
    -- Pre-placed mining patches
    -- No crafting, no building
    
    local surface = game.create_surface("training_mining", {
        width = 128,
        height = 128
    })
    
    -- Place abundant iron ore patches
    for x = 0, 128, 16 do
        for y = 0, 128, 16 do
            surface.create_entity({
                name = "iron-ore",
                position = {x, y},
                amount = 1000
            })
        end
    end
end
```

### 3. Vectorized Environments

#### Multi-Server Architecture
```python
class VectorizedFactorioEnv:
    def __init__(self, num_envs=64):
        self.envs = []
        
        # Launch multiple Factorio servers
        for i in range(num_envs):
            server = FactorioServer(
                port=25000 + i,
                scenario="movement_training",
                game_speed=256,  # 256x speed
                save_interval=0,  # Disable saves
                autosave_interval=0
            )
            
            env = FastFactorioEnv(
                server=server,
                communication=SharedMemoryComm(f"factorio_{i}")
            )
            self.envs.append(env)
    
    def step(self, actions):
        # Parallel action execution
        results = []
        with ThreadPoolExecutor(max_workers=64) as executor:
            futures = [
                executor.submit(env.step, action) 
                for env, action in zip(self.envs, actions)
            ]
            results = [f.result() for f in futures]
        
        return zip(*results)  # obs, rewards, dones, infos
```

### 4. Ultra-Compact Observations

#### Binary State Encoding
```lua
function extract_compact_state(player)
    -- Pack everything into minimal bytes
    local state = {}
    
    -- Position (8 bytes)
    state.pos_x = math.floor(player.position.x * 100)  -- 2 decimal precision
    state.pos_y = math.floor(player.position.y * 100)
    
    -- Local map (32x32x4 = 4KB)
    local map = {}
    for x = -16, 15 do
        for y = -16, 15 do
            local pos = {player.position.x + x, player.position.y + y}
            local tile = player.surface.get_tile(pos)
            local entities = player.surface.find_entities_in_area({
                {pos[1] - 0.5, pos[2] - 0.5},
                {pos[1] + 0.5, pos[2] + 0.5}
            })
            
            -- Pack into 4 bytes per cell
            map[(x+16)*32 + (y+16)] = encode_cell(tile, entities)
        end
    end
    
    return state
end

function encode_cell(tile, entities)
    -- Pack tile + entity info into 32 bits
    local value = 0
    
    -- Tile type (4 bits)
    value = value | (tile_type_to_id(tile.name) << 28)
    
    -- Resource amount (12 bits)
    local resource = entities[1]
    if resource and resource.type == "resource" then
        value = value | ((resource.amount & 0xFFF) << 16)
    end
    
    -- Entity type (4 bits)
    if entities[1] then
        value = value | (entity_type_to_id(entities[1].name) << 12)
    end
    
    -- Walkable (1 bit)
    value = value | (tile.collides_with("player-layer") and 1 or 0)
    
    return value
end
```

### 5. Game Speed Optimizations

#### Factorio Server Configuration
```ini
# factorio-training.cfg
[graphics]
graphics-quality=very-low
video-memory-usage=low
sprite-quality=low

[other]
show-fps=false
show-detailed-info=false
autosave-interval=0
non-blocking-saving=false
```

#### Training-Specific Mod
```lua
-- training-optimizations.lua
script.on_init(function()
    -- Disable unnecessary game features
    game.map_settings.enemy_evolution.enabled = false
    game.map_settings.enemy_expansion.enabled = false
    game.map_settings.pollution.enabled = false
    
    -- Disable graphics-heavy features
    for _, player in pairs(game.players) do
        player.show_on_map = false
        player.enable_flashlight = false
    end
    
    -- Disable automatic saves
    game.autosave_enabled = false
end)

-- Skip complex calculations
script.on_nth_tick(1, function(event)
    -- Only process essential game logic
    -- Skip decoratives, particles, etc.
end)
```

### 6. Scenario Templates

#### Speed Benchmarks
```python
training_scenarios = {
    'movement_micro': {
        'map_size': (32, 32),
        'entities': 'none',
        'target_fps': 1000,
        'observation_size': 64,  # bytes
        'episode_length': 100
    },
    
    'mining_micro': {
        'map_size': (64, 64), 
        'entities': 'iron_ore_only',
        'target_fps': 500,
        'observation_size': 256,
        'episode_length': 300
    },
    
    'building_micro': {
        'map_size': (128, 128),
        'entities': 'construction_materials',
        'target_fps': 200,
        'observation_size': 512,
        'episode_length': 500
    }
}
```

### 7. Performance Monitoring

#### Benchmarking Suite
```python
class PerformanceBenchmark:
    def __init__(self):
        self.metrics = {
            'steps_per_second': [],
            'communication_latency': [],
            'observation_size': [],
            'memory_usage': []
        }
    
    def benchmark_environment(self, env_type, duration=60):
        """Run performance test for 60 seconds"""
        env = create_environment(env_type)
        
        start_time = time.time()
        step_count = 0
        
        while time.time() - start_time < duration:
            action = env.action_space.sample()
            obs, reward, done, info = env.step(action)
            
            step_count += 1
            
            if done:
                obs = env.reset()
        
        steps_per_second = step_count / duration
        return {
            'env_type': env_type,
            'steps_per_second': steps_per_second,
            'avg_latency': info.get('latency', 0),
            'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
        }
```

## Target Performance Goals

| Environment Type | Target SPS | Observation Size | Communication |
|-----------------|-----------|------------------|---------------|
| Movement        | 1000      | 64 bytes         | Shared Memory |
| Mining          | 500       | 256 bytes        | TCP Socket    |
| Construction    | 200       | 512 bytes        | TCP Socket    |
| Full Game       | 50        | 2KB              | File/TCP      |

**Key insight**: Start with ultra-simple environments (movement-only) to train basic skills fast, then progressively add complexity. Use different communication methods based on performance needs.
