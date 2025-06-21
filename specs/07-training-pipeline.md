# Training Pipeline & Infrastructure

## Training Environment Setup

### Factorio Server Configuration
```yaml
# factorio-training.yaml
server:
  headless: true
  game_speed: 64  # Accelerated training
  graphics: minimal
  audio: disabled
  
map_generation:
  seed: configurable  # For reproducible scenarios
  size: small_to_large  # Curriculum progression
  resource_richness: configurable
  enemy_bases: configurable

mods:
  - factorio-agent-mod
  - training-scenarios
```

### Training Scenarios

#### Scenario Templates
```python
scenarios = {
    'survival_basic': {
        'objective': 'survive_and_gather',
        'map_size': 'tiny',
        'time_limit': 300,  # 5 minutes
        'success_criteria': {
            'iron_ore': 200,
            'copper_ore': 100,
            'wood': 50,
            'survival_time': 300
        }
    },
    
    'automation_intro': {
        'objective': 'build_automation',
        'map_size': 'small', 
        'time_limit': 600,  # 10 minutes
        'starting_items': {
            'burner-mining-drill': 2,
            'stone-furnace': 2,
            'transport-belt': 20
        },
        'success_criteria': {
            'iron_plates_produced': 100,
            'automation_active': True
        }
    },
    
    'defense_scenario': {
        'objective': 'survive_attack',
        'map_size': 'medium',
        'time_limit': 1200,  # 20 minutes
        'enemy_settings': {
            'evolution_factor': 0.3,
            'attack_frequency': 'high'
        },
        'success_criteria': {
            'base_integrity': 0.8,  # 80% of structures intact
            'survival_time': 1200
        }
    }
}
```

## Model Training Architecture

### Multi-Scale Learning
```python
class FactorioTrainingPipeline:
    def __init__(self):
        # Different models for different time scales
        self.reactive_policy = ReactivePolicy()      # Immediate actions (1-10 steps)
        self.tactical_policy = TacticalPolicy()      # Short-term goals (100-1000 steps)  
        self.strategic_policy = StrategicPolicy()    # Long-term planning (1000+ steps)
        
        # Shared representations
        self.world_model = WorldModel()              # Predict environment dynamics
        self.value_function = ValueFunction()        # Estimate state values
        
    def train_hierarchical(self):
        # Train from bottom up
        self.train_reactive_layer()
        self.train_tactical_layer() 
        self.train_strategic_layer()
```

### Reactive Policy (Low-Level)
```python
class ReactivePolicy(nn.Module):
    """Handles immediate actions: move, mine, place"""
    
    def forward(self, observation):
        # Process local map (64x64 around player)
        local_features = self.cnn_local(observation['local_map'])
        
        # Process player state
        player_features = self.player_encoder(observation['player_state'])
        
        # Combine and predict actions
        combined = torch.cat([local_features, player_features], dim=1)
        
        return {
            'movement': self.movement_head(combined),
            'interaction': self.interaction_head(combined),
            'primitive_action': self.action_head(combined)
        }
```

### Tactical Policy (Mid-Level)
```python
class TacticalPolicy(nn.Module):
    """Handles task execution: complete mining operation, build structure"""
    
    def forward(self, observation, task_context):
        # Process broader area (256x256)
        tactical_features = self.cnn_tactical(observation['minimap'])
        
        # Encode current task
        task_embedding = self.task_encoder(task_context)
        
        # Attention over relevant entities
        entity_context = self.entity_attention(observation['entities_nearby'])
        
        combined = torch.cat([tactical_features, task_embedding, entity_context], dim=1)
        
        return {
            'subtask_selection': self.subtask_head(combined),
            'resource_allocation': self.resource_head(combined),
            'coordination_signal': self.coord_head(combined)
        }
```

### Strategic Policy (High-Level)
```python
class StrategicPolicy(nn.Module):
    """Handles long-term planning: base layout, tech progression, expansion"""
    
    def forward(self, world_state, production_stats, tech_tree):
        # Process full map understanding
        strategic_map = self.map_encoder(world_state['full_map'])
        
        # Production analysis
        production_features = self.production_analyzer(production_stats)
        
        # Technology tree reasoning
        tech_features = self.tech_encoder(tech_tree)
        
        # Graph reasoning over factory layout
        factory_graph = self.build_factory_graph(world_state)
        graph_features = self.gnn(factory_graph)
        
        combined = torch.cat([strategic_map, production_features, tech_features, graph_features], dim=1)
        
        return {
            'expansion_plan': self.expansion_head(combined),
            'tech_priorities': self.tech_head(combined),
            'resource_strategy': self.resource_strategy_head(combined),
            'task_assignment': self.task_assignment_head(combined)
        }
```

## Training Process

### Phase 1: Imitation Learning
```python
def collect_expert_demonstrations():
    """Record human expert gameplay"""
    demonstrations = []
    
    # Record at multiple skill levels
    for skill_level in ['beginner', 'intermediate', 'expert']:
        for scenario in training_scenarios:
            demo = record_human_gameplay(scenario, skill_level)
            demonstrations.append(demo)
    
    return demonstrations

def train_behavioral_cloning():
    """Train initial policy from demonstrations"""
    for epoch in range(num_epochs):
        for batch in demonstration_loader:
            states, actions = batch
            predicted_actions = policy(states)
            loss = behavioral_cloning_loss(predicted_actions, actions)
            loss.backward()
            optimizer.step()
```

### Phase 2: Reinforcement Learning
```python
def train_with_rl():
    """Improve policy through environment interaction"""
    
    # Proximal Policy Optimization (PPO) 
    for iteration in range(num_iterations):
        # Collect rollouts
        rollouts = collect_rollouts(policy, env, num_steps=2048)
        
        # Compute advantages
        advantages = compute_gae(rollouts, value_function)
        
        # Update policy
        for epoch in range(ppo_epochs):
            policy_loss = compute_policy_loss(rollouts, advantages)
            value_loss = compute_value_loss(rollouts)
            
            total_loss = policy_loss + value_loss
            total_loss.backward()
            optimizer.step()
```

### Phase 3: Curriculum Learning
```python
class CurriculumManager:
    def __init__(self):
        self.current_level = 0
        self.success_threshold = 0.8
        self.scenarios = training_scenarios
        
    def should_advance(self, recent_performance):
        """Advance to next level if current level is mastered"""
        success_rate = np.mean(recent_performance[-100:])  # Last 100 episodes
        return success_rate > self.success_threshold
        
    def get_current_scenario(self):
        return self.scenarios[self.current_level]
        
    def advance_curriculum(self):
        if self.current_level < len(self.scenarios) - 1:
            self.current_level += 1
            print(f"Advanced to curriculum level {self.current_level}")
```

## Evaluation & Testing

### Automated Testing Suite
```python
test_scenarios = {
    'regression_tests': [
        'basic_movement_test',
        'mining_efficiency_test', 
        'building_accuracy_test'
    ],
    'integration_tests': [
        'full_automation_test',
        'defense_capability_test',
        'resource_management_test'
    ],
    'stress_tests': [
        'large_map_performance',
        'high_enemy_density',
        'resource_scarcity'
    ]
}

def run_evaluation_suite():
    results = {}
    for category, tests in test_scenarios.items():
        category_results = []
        for test in tests:
            result = run_test_scenario(test, num_episodes=10)
            category_results.append(result)
        results[category] = np.mean(category_results)
    return results
```

### Performance Monitoring
```python
class TrainingMonitor:
    def __init__(self):
        self.metrics = {
            'episode_reward': [],
            'task_completion_rate': [],
            'resource_efficiency': [],
            'survival_time': [],
            'actions_per_minute': []
        }
        
    def log_episode(self, episode_data):
        for metric, value in episode_data.items():
            if metric in self.metrics:
                self.metrics[metric].append(value)
                
        # Log to tensorboard/wandb
        self.logger.log(episode_data)
        
    def should_save_checkpoint(self):
        # Save model if performance improved
        current_performance = np.mean(self.metrics['episode_reward'][-10:])
        return current_performance > self.best_performance
```

This creates a complete training pipeline that can scale from simple reactive behaviors to complex strategic planning, with proper evaluation and monitoring throughout.
