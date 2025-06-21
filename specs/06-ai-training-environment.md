# Factorio Training Environment

## Overview

A scalable training environment that supports both:
- **Low-level RL policies** (PufferLib-style): Fast reactive skills like movement, mining, building
- **High-level LLM planners**: Strategic reasoning and task decomposition

## Multi-Server Infrastructure

### Environment Pool
```python
class FactorioEnvironmentPool:
    def __init__(self, num_servers=16):
        self.servers = []
        for i in range(num_servers):
            server = FactorioServer(
                port=25000 + i,
                scenario_config=None,  # Will be set dynamically
                headless=True,
                game_speed=64
            )
            self.servers.append(server)
    
    def get_available_server(self):
        return next(server for server in self.servers if server.is_idle())
    
    def spawn_environment(self, scenario_type):
        server = self.get_available_server()
        return FactorioEnv(server, scenario_type)
```

### Scenario Management
```python
scenario_configs = {
    # Low-level skill training
    'movement_training': {
        'map_size': 'tiny',
        'obstacles': 'minimal',
        'objective': 'reach_waypoints',
        'episode_length': 300
    },
    
    'mining_training': {
        'map_size': 'small', 
        'resources': {'iron-ore': 'abundant'},
        'objective': 'extract_resources',
        'episode_length': 600
    },
    
    'construction_training': {
        'map_size': 'small',
        'starting_items': 'construction_kit',
        'objective': 'build_structures',
        'episode_length': 900
    },
    
    # High-level planning scenarios
    'base_planning': {
        'map_size': 'large',
        'complexity': 'full_game',
        'objective': 'optimize_production',
        'episode_length': 18000  # 5 hours game time
    }
}
```

## Environment Design

### State Representation

#### Low-Level Observation Space (RL Policies)
```python
low_level_obs = {
    # High-frequency spatial data (optimized for speed)
    'local_map': np.array(shape=(32, 32, 8), dtype=np.uint8),  # Immediate surroundings
    'player_state': {
        'position': np.array([x, y], dtype=np.float32),
        'health': np.float32,
        'inventory_summary': np.array(shape=(64,), dtype=np.uint16),  # Compact encoding
        'walking_state': np.array([dx, dy], dtype=np.float32),
    },
    'immediate_entities': np.array(shape=(16, 4), dtype=np.float32),  # [type, x, y, state]
    'action_mask': np.array(shape=(N_ACTIONS,), dtype=bool),  # Valid actions
}
```

#### High-Level Observation Space (LLM Planners)
```python
high_level_obs = {
    # Rich semantic information
    'world_description': str,  # Natural language description of current state
    'base_layout': {
        'production_chains': [{'input': 'iron-ore', 'output': 'iron-plate', 'rate': 30.5}],
        'bottlenecks': ['coal shortage at furnaces', 'belt saturation near mines'],
        'inefficiencies': ['idle inserters', 'overflow at copper chest']
    },
    'resource_status': {
        'iron_ore': {'reserves': 50000, 'mining_rate': 45.2, 'projected_depletion': 18.5},
        'copper_ore': {'reserves': 30000, 'mining_rate': 32.1, 'projected_depletion': 15.6}
    },
    'objectives': {
        'current_goal': 'increase_iron_plate_production',
        'constraints': ['limited_space_north', 'biter_threat_east'],
        'priorities': ['defense', 'production', 'expansion']
    }
}
```

#### Map Encoding Channels
```python
MAP_CHANNELS = {
    0: 'terrain',           # Land, water, cliffs
    1: 'resources',         # Ore deposits (intensity = richness)
    2: 'entities',          # Buildings, trees, rocks
    3: 'player_structures', # Player-built items
    4: 'power_network',     # Electrical grid
    5: 'logistics',         # Belts, inserters
    6: 'threats',           # Biters, spawners
    7: 'accessibility',     # Walkable areas
}
```

### Action Space

#### Low-Level Actions (RL Policies)
```python
# Fast, discrete actions for reactive policies
low_level_actions = {
    'movement': Discrete(9),  # 8 directions + stop
    'interaction': Discrete(8),  # mine, pickup, place, rotate, etc.
    'target_selection': Discrete(16),  # Which nearby entity to interact with
    'item_selection': Discrete(32),  # Which item to use/craft (limited set)
}

# Or continuous for smoother control
continuous_actions = {
    'move_vector': Box(low=-1, high=1, shape=(2,)),  # dx, dy
    'interaction_strength': Box(low=0, high=1, shape=(1,)),  # How long to hold action
}
```

#### High-Level Actions (LLM Planners)
```python
# Semantic actions that get decomposed into low-level commands
high_level_actions = {
    'task_command': str,  # Natural language: "Build 5 iron furnaces near the iron mine"
    'priority_adjustment': Dict[str, float],  # {'defense': 0.8, 'production': 0.6}
    'resource_allocation': Dict[str, int],  # {'iron_ore': 500, 'coal': 200}
    'blueprint_placement': {
        'blueprint_name': str,
        'position': Tuple[float, float],
        'rotation': int
    }
}
```

### Reward Design

#### Multi-Objective Rewards
```python
def calculate_reward(prev_state, action, new_state):
    reward = 0.0
    
    # Task completion rewards
    if task_completed(new_state):
        reward += TASK_COMPLETION_BONUS
    
    # Progress rewards (shaped)
    reward += task_progress_delta(prev_state, new_state) * PROGRESS_WEIGHT
    
    # Efficiency rewards
    reward += resource_efficiency_bonus(action, new_state)
    reward -= time_penalty(action)  # Encourage fast completion
    
    # Survival rewards
    if player_died(new_state):
        reward -= DEATH_PENALTY
    
    # Exploration rewards (sparse)
    reward += new_area_discovered(prev_state, new_state) * EXPLORATION_BONUS
    
    return reward
```

#### Task-Specific Rewards
```python
TASK_REWARDS = {
    'MINE_IRON': lambda state: state.inventory['iron-ore'] * 0.1,
    'BUILD_SMELTER': lambda state: 100.0 if 'stone-furnace' in state.built_entities else 0.0,
    'REFILL_TURRETS': lambda state: sum(turret.ammo for turret in state.turrets) * 0.5,
    'EXPAND_POWER': lambda state: state.power_production - state.power_consumption,
}
```

## Training Scenarios

### Curriculum Learning

#### Level 1: Basic Survival
- **Objective**: Stay alive, gather basic resources
- **Map**: Small, safe area with iron/copper/coal
- **Success**: Survive 10 minutes, gather 100 iron ore
- **Duration**: 1000 steps

#### Level 2: Automation Basics
- **Objective**: Build first automated production
- **Map**: Resource-rich starting area
- **Success**: Create iron plates automatically
- **Duration**: 2000 steps

#### Level 3: Logistics
- **Objective**: Transport resources efficiently
- **Map**: Scattered resource patches
- **Success**: Connect 3 resource patches with belts
- **Duration**: 3000 steps

#### Level 4: Defense
- **Objective**: Defend base from biters
- **Map**: Biter-infested area
- **Success**: Survive 20 minutes with active defense
- **Duration**: 5000 steps

#### Level 5: Expansion
- **Objective**: Scale production, expand territory
- **Map**: Large map with distant resources
- **Success**: Achieve target production rates
- **Duration**: 10000 steps

### Training Variants

#### Speed Challenges
```python
scenarios = {
    'iron_rush': {'objective': 'mine_1000_iron', 'time_limit': 300},
    'smelter_challenge': {'objective': 'build_10_furnaces', 'time_limit': 600},
    'belt_master': {'objective': 'transport_items_100_tiles', 'time_limit': 400},
}
```

#### Resource Constraints
```python
constraints = {
    'limited_inventory': {'max_stack_size': 50},
    'tool_decay': {'tools_break_faster': True},
    'resource_scarcity': {'ore_patches_smaller': 0.5},
}
```

## Model Architecture Considerations

### Multi-Modal Input Processing
```python
class FactorioNet(nn.Module):
    def __init__(self):
        # Vision encoders
        self.map_cnn = ResNet(input_channels=8, output_dim=512)
        self.minimap_cnn = ResNet(input_channels=8, output_dim=256)
        
        # Structured data encoders
        self.player_mlp = MLP(input_dim=64, output_dim=128)
        self.inventory_embed = nn.Embedding(N_ITEMS, 32)
        
        # Attention mechanisms
        self.entity_attention = MultiHeadAttention(d_model=256)
        self.task_attention = MultiHeadAttention(d_model=256)
        
        # Policy heads
        self.action_type_head = nn.Linear(1024, 6)
        self.movement_head = nn.Linear(1024, 3)  # direction_x, direction_y, distance
        self.building_head = nn.Linear(1024, N_BUILDABLE_ITEMS + 2 + 8)  # item + pos + direction
```

### Memory and Planning
```python
# Recurrent components for temporal reasoning
self.lstm = nn.LSTM(1024, 512, num_layers=2)

# Graph neural networks for spatial reasoning
self.factory_gnn = GraphAttentionNetwork(node_features=64, edge_features=32)

# Hierarchical planning
self.task_planner = HierarchicalPlanner(levels=3)
```

## Training Infrastructure

### Parallel Environment
```python
env_configs = [
    {'scenario': 'iron_rush', 'seed': i, 'map_size': 'small'}
    for i in range(NUM_PARALLEL_ENVS)
]

# Run multiple Factorio instances
envs = [FactorioEnv(config) for config in env_configs]
vec_env = SubprocVecEnv(envs)
```

### Evaluation Metrics
```python
metrics = {
    'task_success_rate': float,
    'average_completion_time': float,
    'resource_efficiency': float,  # output / input ratio
    'death_rate': float,
    'exploration_coverage': float,  # % of map explored
    'building_efficiency': float,   # structures built / resources used
}
```

## Integration with Factorio

### Fast Training Mode
- Accelerated game speed (64x normal)
- Reduced graphics/audio
- Headless server mode
- Deterministic random seeds

### State Extraction Optimization
- Efficient binary serialization
- Incremental updates (delta compression)
- Spatial indexing for entity queries
- Cached computations for common observations

This creates a proper RL environment where models can learn complex Factorio strategies through trial and error, with carefully designed observations, actions, and rewards.
