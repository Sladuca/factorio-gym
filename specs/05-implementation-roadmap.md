# Implementation Roadmap - Simplified Architecture

## Phase 1: Direct RCON Control (MVP)
**Goal**: Get basic player movement working via direct RCON

### Deliverables
1. **Minimal Factorio Mod (Optional)**
   - Helper functions for common commands
   - JSON response formatting utilities
   - Error handling wrappers

2. **Direct RCON Agent**
   - Python RCON client with connection pooling
   - Send Lua commands directly to Factorio
   - Receive JSON responses via `game.table_to_json()`
   - Smart state caching to minimize queries

3. **Core Commands**
   - `set_walking_state()` for movement
   - `get_player_state()` for position/status
   - `teleport()` for testing/training

### Success Criteria
- Agent can control player movement via RCON
- 5-20ms command latency (localhost)
- No file I/O dependencies
- Achieve 60 commands/second sustained

## Phase 2: Actions & State Management
**Goal**: Add mining, inventory, and efficient state queries

### Deliverables
1. **Extended Command Set**
   - `start_mining(x, y)` for resource extraction
   - `get_inventory()` and `transfer_items()` for item management
   - `find_entities(area, filters)` for world scanning

2. **Smart State Management**
   - Agent-side caching of entity data
   - Selective state queries (position vs full state)
   - Event-driven updates (inventory after mining)

3. **Compound Tasks**
   - "Mine resource patch" with pathfinding
   - Inventory-aware behavior (stop when full)
   - Basic obstacle detection

### Success Criteria
- Agent can mine resources autonomously
- State queries are efficient (<2KB typical)
- Agent maintains situational awareness without constant polling

## Phase 3: Construction & Crafting
**Goal**: Build and craft items

### Deliverables
1. **Construction System (with API workarounds)**
   - Use `surface.create_entity` + manual inventory deduction
   - Handle building placement validation
   - Implement realistic item consumption

2. **Crafting System**
   - Queue crafting recipes via RCON
   - Monitor crafting progress via script-output
   - Auto-craft missing components logic

### Success Criteria
- Agent can place buildings with inventory management
- Crafting integration works end-to-end
- Can build mining outpost with 5-10 SPS performance

## Phase 4: Task Planning
**Goal**: High-level task decomposition

### Deliverables
1. **Task System**
   - Hierarchical task breakdown
   - Priority-based scheduling
   - State machine execution

2. **Complex Behaviors**
   - "Refill turrets" end-to-end
   - "Set up mining outpost" 
   - Resource shortage detection

### Success Criteria
- Agent responds to high-level commands
- Tasks are broken down automatically
- Agent operates semi-autonomously

## Phase 5: Intelligence & Optimization
**Goal**: Smart decision making

### Deliverables
1. **World Analysis**
   - Resource patch evaluation
   - Factory layout optimization
   - Threat assessment

2. **Learning System**
   - Performance metrics collection
   - Adaptive behavior
   - Strategy improvement

### Success Criteria
- Agent makes intelligent choices about expansion
- Performance improves over time
- Agent handles unexpected situations

## Technical Milestones

### Milestone 1: Hello World
- [ ] Factorio mod loads successfully
- [ ] Agent can start/stop
- [ ] Basic file communication works

### Milestone 2: Remote Control
- [ ] Agent controls player movement
- [ ] Player state is reported accurately
- [ ] Commands are executed reliably

### Milestone 3: Resource Gathering
- [ ] Agent can mine resources autonomously  
- [ ] Inventory management works
- [ ] Basic obstacle avoidance

### Milestone 4: Construction
- [ ] Agent can build structures
- [ ] Power and logistics connections
- [ ] Recipe-based crafting

### Milestone 5: Task Automation
- [ ] "Refill turrets" works end-to-end
- [ ] "Expand mining" works automatically
- [ ] Multiple tasks can be queued

## Risk Mitigation

### Technical Risks (Updated)
- **RCON latency**: 5-20ms per command, requires smart caching
- **API limitations**: Building API removed, need workarounds
- **State query costs**: Large entity scans could slow performance
- **Connection limits**: 5 RCON connections max per server

### Design Risks
- **Over-engineering**: Start simple, add complexity incrementally
- **Poor task decomposition**: Test with simple tasks first
- **Communication bottlenecks**: Monitor and optimize protocol

## Next Steps
1. Set up development environment
2. Create basic Factorio mod structure
3. Implement Phase 1 MVP
4. Test with simple movement commands
