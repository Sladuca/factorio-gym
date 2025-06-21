# Communication Protocol

## Command Structure

### Command Format
```json
{
  "id": "unique-command-id",
  "timestamp": 1640995200,
  "type": "MOVE|MINE|BUILD|CRAFT|SCAN",
  "priority": 1-1000,
  "params": { /* type-specific parameters */ },
  "status": "PENDING|IN_PROGRESS|COMPLETED|FAILED"
}
```

### Movement Commands
```json
{
  "type": "MOVE",
  "params": {
    "target": {"x": 100, "y": 50},
    "method": "walk|vehicle|train",
    "precision": 1.0  // how close to get
  }
}
```

### Mining Commands
```json
{
  "type": "MINE",
  "params": {
    "target": {"x": 100, "y": 50},
    "entity_name": "iron-ore",
    "count": 100,  // optional: stop after mining X
    "area": {"x1": 90, "y1": 40, "x2": 110, "y2": 60}  // optional: mine area
  }
}
```

### Building Commands
```json
{
  "type": "BUILD",
  "params": {
    "entity": "electric-mining-drill",
    "position": {"x": 100, "y": 50},
    "direction": 0,  // optional
    "recipe": "iron-ore"  // for assemblers
  }
}
```

## State Reporting

### Player State
```json
{
  "timestamp": 1640995200,
  "player": {
    "position": {"x": 123.5, "y": 67.2},
    "health": 100,
    "walking_state": {"walking": true, "direction": 2},
    "current_activity": "mining",
    "inventory_full": false
  }
}
```

### Inventory State
```json
{
  "inventory": {
    "main": [
      {"name": "iron-plate", "count": 50},
      {"name": "copper-plate", "count": 30}
    ],
    "quickbar": [
      {"name": "inserter", "count": 10}
    ]
  }
}
```

### World State
```json
{
  "world": {
    "nearby_entities": [
      {
        "name": "iron-ore",
        "position": {"x": 125, "y": 70},
        "amount": 500  // for resources
      }
    ],
    "resource_patches": [
      {
        "type": "iron-ore", 
        "center": {"x": 200, "y": 100},
        "size": 5000,
        "richness": "medium"
      }
    ]
  }
}
```

## File Organization

### Command Queue
```
commands/
├── pending/
│   ├── cmd_001.json
│   └── cmd_002.json
├── active/
│   └── cmd_003.json
└── completed/
    └── cmd_004.json
```

### State Snapshots
```
state/
├── current/
│   ├── player.json
│   ├── inventory.json
│   └── world.json
└── history/
    ├── 2024-01-01T10-00-00_player.json
    └── 2024-01-01T10-00-00_world.json
```

## Error Handling

### Command Failures
```json
{
  "id": "cmd_001",
  "status": "FAILED",
  "error": {
    "code": "INSUFFICIENT_RESOURCES",
    "message": "Cannot build: missing iron-plate x5",
    "retry": true
  }
}
```

### Recovery Strategies
- Retry with exponential backoff
- Alternative command suggestions
- Fallback to manual intervention prompt

## Performance Optimization

### Batching
- Group similar commands
- Process multiple moves as waypoints
- Batch inventory operations

### Caching
- Cache entity scans for 5 seconds
- Reuse pathfinding results
- Debounce state updates

### Rate Limiting
- Max 10 commands per second
- Prioritize by urgency
- Queue overflow handling
