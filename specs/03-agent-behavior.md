# Agent Behavior & Task System

## Training-Oriented Design

This behavior system is designed as a **Factorio Gym** - an RL training environment where AI models learn to play Factorio effectively. The system supports both scripted behaviors (for bootstrapping) and learned policies.

## High-Level Tasks (Training Scenarios)

The agent should handle commands like:
- "go refill the turrets" (Defense scenario)
- "cut trees to make poles" (Resource gathering)
- "go set up a new iron mine, we're running low" (Expansion task)
- "expand the factory to produce more circuits" (Production scaling)

## Task Hierarchy

### Level 1: Primitive Actions
- Move to position
- Mine entity
- Place entity
- Craft item
- Pick up item

### Level 2: Composite Actions  
- Mine resource patch (move + mine repeatedly)
- Build structure (move + place multiple entities)
- Refill container (move + transfer items)
- Clear area (move + mine trees/rocks)

### Level 3: Complex Tasks
- Set up mining outpost (survey + clear + build + connect)
- Expand production line (analyze + design + build)
- Defend area (build turrets + supply ammo)

## Task Planning System

### Task Decomposition
```
"Set up iron mine" →
  1. Find iron ore patch
  2. Plan mining layout
  3. Clear area of obstacles
  4. Place miners
  5. Set up power connection
  6. Build belt network
  7. Connect to main base
```

### State Machine Approach
```
Task: RefillTurrets
├── State: SCANNING (find turrets needing ammo)
├── State: PLANNING (determine ammo needs)
├── State: GATHERING (collect ammo from storage)
├── State: TRAVELING (move to turret locations)
├── State: REFILLING (insert ammo)
└── State: COMPLETE
```

## Decision Making

### Resource Management
- Monitor inventory levels
- Prioritize critical resources (ammo, fuel, repair packs)
- Balance production vs consumption

### Pathfinding
- Use A* for navigation
- Avoid obstacles (water, cliffs, biters)
- Consider transportation (walking vs vehicle vs train)

### Priority System
```javascript
const priorities = {
  CRITICAL: 1000,  // Base under attack
  HIGH: 100,       // Power shortage
  MEDIUM: 50,      // Resource shortage  
  LOW: 10,         // Optimization tasks
  IDLE: 1          // Exploration, cleanup
}
```

## Behavior Modules

### Scout Module
- Explore map for resources
- Identify expansion opportunities
- Monitor biter activity

### Logistics Module
- Manage item transportation
- Optimize belt/train networks
- Handle supply chains

### Defense Module
- Monitor turret ammo levels
- Respond to attacks
- Expand defensive perimeter

### Production Module
- Balance production ratios
- Expand manufacturing capacity
- Optimize factory layouts

## Reinforcement Learning Integration

### State-Action-Reward Loop
```
State: Game observation (map, inventory, entities, task context)
  ↓
Action: Hierarchical action (primitive or composite)
  ↓
Environment: Factorio game state changes
  ↓
Reward: Task progress + efficiency + survival
  ↓
Next State: Updated game observation
```

### Training Approaches

#### 1. Imitation Learning (Bootstrap)
- Record expert human gameplay
- Train initial policy via behavioral cloning
- Use as starting point for RL

#### 2. Curriculum Learning
- Start with simple tasks (gather iron)
- Gradually increase complexity (build smelters → automation → defense)
- Multi-stage progression

#### 3. Hierarchical RL
- High-level policy: Choose which task to execute
- Mid-level policy: Break tasks into sub-goals
- Low-level policy: Execute primitive actions

#### 4. Multi-Agent RL
- Train multiple specialized agents
- Logistics specialist, combat specialist, builder specialist
- Coordinate via communication/auction mechanisms

### Performance Metrics
- **Task Success Rate**: % of scenarios completed successfully
- **Sample Efficiency**: Steps needed to learn new tasks
- **Resource Efficiency**: Output/input ratios
- **Generalization**: Performance on unseen maps/scenarios
- **Robustness**: Handling of unexpected situations

### Model Architecture Considerations
- **Multi-modal inputs**: Vision (maps) + structured data (inventories)
- **Temporal reasoning**: RNNs/Transformers for sequential decision making
- **Spatial reasoning**: Graph Neural Networks for factory layouts
- **Hierarchical planning**: Goal-conditioned policies at multiple time scales
