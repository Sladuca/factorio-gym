# End-to-End Demo: Human + Agent Simultaneous Play

This demo showcases the Factorio parallel control system where human players and AI agents can operate simultaneously in the same game world.

## What This Demo Shows

1. **Human Player**: Connects normally via Factorio client, full game control
2. **Agent Player**: Controlled via WASD keys in terminal, appears as separate player
3. **Simultaneous Operation**: Both human and agent can move, interact, and play together
4. **Real-time Control**: Low-latency WASD controls for smooth agent movement

## Prerequisites

### 1. Factorio Installation
- Factorio installed and accessible via command line
- Version 1.1.0+ recommended

### 2. Project Setup
```bash
# Install dependencies (keyboard library for WASD controls)
uv sync

# Or with pip:
pip install keyboard>=0.13.5
```

### 3. Server Configuration
- Factorio server with RCON enabled
- `agent-control` mod loaded
- Accessible network ports (default: 34197 for game, 34198 for RCON)

## Quick Start

### Step 1: Start the Factorio Server
```bash
# In one terminal - start the development server
python3 scripts/dev_server.py
```

Wait for server to fully start (should see "Server started successfully!")

### Step 2: Launch the Demo
```bash
# In another terminal - start the agent demo
python3 scripts/e2e_demo.py

# Or with custom agent name:
python3 scripts/e2e_demo.py --agent-name "MyBot"
```

### Step 3: Connect Human Player
1. Launch Factorio client
2. Multiplayer → Direct Connect
3. Address: `localhost:34197`
4. Connect and join the game

### Step 4: Control the Agent
In the demo terminal:
- **W/A/S/D**: Move agent (North/West/South/East)
- **SPACE**: Show agent status/position
- **Q**: Quit demo

## Demo Features

### Real-time Movement Control
- WASD keys provide immediate agent movement
- Direction changes are instant
- Smooth movement with proper key release handling

### Multi-player Interaction
- Human and agent appear as separate players
- Both can see each other in the game world
- Both can interact with the same environment
- No interference between human and agent controls

### Status Monitoring
- Live agent position tracking
- Movement state monitoring
- Connection status display
- Error handling and recovery

## Troubleshooting

### Permission Issues (Linux/macOS)
If keyboard capture doesn't work:
```bash
# Run with elevated permissions
sudo python3 scripts/e2e_demo.py
```

### Connection Problems
```bash
# Test RCON connection separately
python3 scripts/test_rcon.py --command "/hello"

# Check if server is running
python3 scripts/dev_server.py test
```

### Agent Not Appearing
1. Check server logs: `tail -f logs/server.log`
2. Verify mod is loaded: Look for "Agent Control System loaded" in logs
3. Manual agent creation: Use `/ensure_player Agent` in Factorio console

### Performance Issues
- Reduce movement update frequency in the code
- Check network latency to server
- Monitor CPU usage during simultaneous play

## Architecture

```
┌─────────────────┐    Factorio Client    ┌─────────────────┐
│ Human Player    │ ◄──────────────────── │ Factorio Server │
│ (Normal Client) │      Port 34197       │                 │
└─────────────────┘                       │ ┌─────────────┐ │
                                          │ │ agent-      │ │
┌─────────────────┐       RCON            │ │ control mod │ │
│ WASD Agent Demo │ ◄──────────────────── │ └─────────────┘ │
│ (This Script)   │      Port 34198       │                 │
└─────────────────┘                       └─────────────────┘
```

### Communication Flow
1. **Human Input**: Keyboard/Mouse → Factorio Client → Server
2. **Agent Input**: WASD Keys → Python Script → RCON → Lua Mod → Server
3. **Game State**: Server processes both inputs simultaneously
4. **Visual Output**: Server → Both Human Client and Agent Status

## Configuration Options

### Custom Server Settings
```bash
python3 scripts/e2e_demo.py \
    --host 192.168.1.100 \
    --port 34198 \
    --password mypassword \
    --agent-name "SuperBot"
```

### Advanced Features
- Multiple agents: Run multiple demo instances with different names
- Custom controls: Modify `DIRECTION_MAP` in the script
- Enhanced status: Add more agent information display
- Automated behaviors: Extend script with AI decision-making

## Next Steps

This demo provides the foundation for more advanced agent behaviors:

1. **Pathfinding**: Add A* or other navigation algorithms
2. **Task Planning**: Implement goal-based agent behavior
3. **Resource Management**: Add inventory and crafting control
4. **Multi-agent Coordination**: Synchronize multiple agents
5. **Learning Systems**: Integrate RL/ML models for autonomous play

## Files Used
- `scripts/e2e_demo.py` - Main demo script
- `src/factorio_mcp/rcon.py` - RCON communication
- `mods/agent-control/control.lua` - Factorio mod for agent commands
- `scripts/dev_server.py` - Development server launcher
