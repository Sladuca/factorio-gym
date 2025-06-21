# Environment Architecture & Infrastructure

## System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Planner   │    │  Environment    │    │  RL Policies    │
│                 │    │    Manager      │    │                 │
│ Strategic       │◄──►│                 │◄──►│ Movement        │
│ Planning        │    │ - Server Pool   │    │ Mining          │
│ Task Decomp     │    │ - Scenarios     │    │ Construction    │
│                 │    │ - Coordination  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Factorio Server │
                    │     Pool        │
                    │ ┌─────┐ ┌─────┐ │
                    │ │Srv1 │ │Srv2 │ │
                    │ └─────┘ └─────┘ │
                    │ ┌─────┐ ┌─────┐ │
                    │ │Srv3 │ │Srv4 │ │
                    │ └─────┘ └─────┘ │
                    └─────────────────┘
```

## Environment Manager

### Core Interface
```python
class FactorioEnvironmentManager:
    def __init__(self, config):
        self.server_pool = FactorioServerPool(config.num_servers)
        self.scenario_manager = ScenarioManager()
        self.coordination_layer = CoordinationLayer()
        
    def create_environment(self, env_type: str, config: Dict):
        """Create a new training environment"""
        if env_type == "low_level":
            return self._create_rl_environment(config)
        elif env_type == "high_level":
            return self._create_llm_environment(config)
        elif env_type == "hierarchical":
            return self._create_hierarchical_environment(config)
            
    def _create_rl_environment(self, config):
        """Fast, low-latency environment for RL training"""
        server = self.server_pool.get_server()
        return FastFactorioEnv(
            server=server,
            observation_type="compact",
            action_type="discrete", 
            reward_shaping="dense",
            episode_length=config.get("episode_length", 1000)
        )
        
    def _create_llm_environment(self, config):
        """Rich, semantic environment for LLM planning"""
        server = self.server_pool.get_server()
        return SemanticFactorioEnv(
            server=server,
            observation_type="semantic",
            action_type="natural_language",
            reward_shaping="sparse",
            episode_length=config.get("episode_length", 10000)
        )
```

### Server Pool Management
```python
class FactorioServerPool:
    def __init__(self, num_servers=16):
        self.servers = []
        self.available_servers = Queue()
        self.active_environments = {}
        
        for i in range(num_servers):
            server = self._launch_server(port=25000 + i)
            self.servers.append(server)
            self.available_servers.put(server)
    
    def get_server(self, timeout=60):
        """Get an available server, launch new one if needed"""
        try:
            return self.available_servers.get(timeout=timeout)
        except Empty:
            # All servers busy, launch temporary server
            return self._launch_temporary_server()
    
    def return_server(self, server):
        """Return server to pool after environment cleanup"""
        server.reset_to_clean_state()
        self.available_servers.put(server)
        
    def _launch_server(self, port):
        return FactorioServer(
            port=port,
            headless=True,
            game_speed=64,
            mods_enabled=['factorio-gym-mod'],
            save_file=None  # Fresh world each time
        )
```

### Scenario Configuration
```python
class ScenarioManager:
    def __init__(self):
        self.scenarios = {
            # Low-level skill scenarios (fast episodes)
            'movement_basic': {
                'type': 'movement_training',
                'map_generation': {
                    'size': 'tiny',
                    'terrain': 'flat',
                    'resources': 'none',
                    'enemies': 'none'
                },
                'objectives': ['reach_waypoint'],
                'episode_length': 300,
                'observation_frequency': 10  # 10 FPS
            },
            
            'mining_efficiency': {
                'type': 'resource_gathering',
                'map_generation': {
                    'size': 'small',
                    'resources': {'iron-ore': 'rich'},
                    'enemies': 'none'
                },
                'objectives': ['mine_1000_ore'],
                'episode_length': 600,
                'observation_frequency': 5
            },
            
            'construction_speed': {
                'type': 'building_training',
                'map_generation': {
                    'size': 'small',
                    'terrain': 'flat',
                    'starting_items': 'construction_kit'
                },
                'objectives': ['build_blueprint'],
                'episode_length': 900,
                'observation_frequency': 5
            },
            
            # High-level planning scenarios (longer episodes)
            'base_optimization': {
                'type': 'strategic_planning',
                'map_generation': {
                    'size': 'large',
                    'complexity': 'full_game',
                    'starting_base': 'minimal_automation'
                },
                'objectives': ['optimize_production_chains'],
                'episode_length': 18000,  # 5 hours game time
                'observation_frequency': 0.1  # 6 minutes real time
            }
        }
```

## Multi-Modal Training Support

### Fast RL Environment
```python
class FastFactorioEnv(gym.Env):
    """Optimized for high-throughput RL training"""
    
    def __init__(self, server, scenario_config):
        self.server = server
        self.obs_extractor = CompactObservationExtractor()
        self.action_executor = FastActionExecutor()
        
        # Minimal observation space for speed
        self.observation_space = gym.spaces.Dict({
            'local_map': gym.spaces.Box(0, 255, shape=(32, 32, 8), dtype=np.uint8),
            'player_state': gym.spaces.Box(-np.inf, np.inf, shape=(16,), dtype=np.float32),
            'entities': gym.spaces.Box(-np.inf, np.inf, shape=(16, 4), dtype=np.float32),
            'action_mask': gym.spaces.Box(0, 1, shape=(64,), dtype=bool)
        })
        
        # Discrete actions for speed
        self.action_space = gym.spaces.MultiDiscrete([9, 8, 16, 32])  # move, interact, target, item
        
    def step(self, action):
        # Execute action immediately
        self.action_executor.execute(action)
        
        # Get compact observation
        obs = self.obs_extractor.extract()
        
        # Fast reward calculation
        reward = self._calculate_reward()
        
        # Check termination
        done = self._check_done()
        
        return obs, reward, done, {}
        
    def reset(self):
        self.server.load_scenario(self.scenario_config)
        return self.obs_extractor.extract()
```

### Semantic LLM Environment
```python
class SemanticFactorioEnv:
    """Rich environment for LLM-based planning"""
    
    def __init__(self, server, scenario_config):
        self.server = server
        self.semantic_analyzer = SemanticWorldAnalyzer()
        self.nlp_interface = NaturalLanguageInterface()
        
    def get_world_state(self):
        """Rich semantic description of current state"""
        raw_state = self.server.get_full_game_state()
        
        return {
            'description': self.semantic_analyzer.describe_world(raw_state),
            'production_analysis': self.semantic_analyzer.analyze_production(raw_state),
            'bottlenecks': self.semantic_analyzer.find_bottlenecks(raw_state),
            'opportunities': self.semantic_analyzer.find_opportunities(raw_state),
            'threats': self.semantic_analyzer.assess_threats(raw_state)
        }
    
    def execute_plan(self, natural_language_command: str):
        """Convert LLM command to low-level actions"""
        parsed_command = self.nlp_interface.parse_command(natural_language_command)
        
        # Decompose into executable steps
        action_sequence = self.nlp_interface.plan_execution(parsed_command)
        
        # Execute via coordination layer
        return self.coordination_layer.execute_sequence(action_sequence)
```

## Coordination Layer

### Hierarchical Control
```python
class CoordinationLayer:
    """Coordinates between high-level LLM planning and low-level RL execution"""
    
    def __init__(self):
        self.task_queue = TaskQueue()
        self.skill_library = SkillLibrary()
        self.execution_monitor = ExecutionMonitor()
        
    def execute_llm_command(self, command: str, context: Dict):
        """Break down LLM command into RL-executable tasks"""
        
        # Parse semantic command
        parsed = self.parse_semantic_command(command)
        
        # Decompose into skill-level tasks
        task_sequence = self.decompose_to_skills(parsed, context)
        
        # Queue tasks for RL policies
        for task in task_sequence:
            self.task_queue.add_task(task)
            
        # Monitor execution
        return self.execution_monitor.track_sequence(task_sequence)
    
    def decompose_to_skills(self, high_level_task, context):
        """Convert high-level goals to skill-level tasks"""
        
        if high_level_task.type == "BUILD_SMELTER_ARRAY":
            return [
                SkillTask("NAVIGATE", target=high_level_task.location),
                SkillTask("CLEAR_AREA", size=high_level_task.area),
                SkillTask("PLACE_ENTITIES", blueprint=high_level_task.blueprint),
                SkillTask("CONNECT_POWER", entities=high_level_task.entities),
                SkillTask("CONNECT_LOGISTICS", input_belt=high_level_task.input)
            ]
```

### Skill Library
```python
class SkillLibrary:
    """Library of trained RL policies for specific tasks"""
    
    def __init__(self):
        self.skills = {
            'movement': MovementPolicy.load('movement_v2.pth'),
            'mining': MiningPolicy.load('mining_v3.pth'), 
            'construction': ConstructionPolicy.load('construction_v1.pth'),
            'logistics': LogisticsPolicy.load('logistics_v2.pth')
        }
    
    def execute_skill(self, skill_name: str, parameters: Dict):
        """Execute a specific skill with given parameters"""
        policy = self.skills[skill_name]
        return policy.execute(parameters)
```

This architecture allows you to:
1. **Scale horizontally** with multiple Factorio servers
2. **Train different policy types** simultaneously (RL skills + LLM planning) 
3. **Coordinate between levels** via the coordination layer
4. **Swap out components** independently (different RL algorithms, different LLMs)
5. **Monitor performance** across the entire system
