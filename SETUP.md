# Factorio Development Environment Setup

## Prerequisites

### 1. Install Factorio
You need Factorio installed to get the headless server binary.

**Option A: Steam (macOS/Linux/Windows)**
1. Install Factorio through Steam
2. Find the binary location:
   - **macOS**: `~/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio`
   - **Linux**: `~/.steam/steam/steamapps/common/Factorio/bin/x64/factorio`
   - **Windows**: `C:\Program Files (x86)\Steam\steamapps\common\Factorio\bin\x64\factorio.exe`

**Option B: Direct Download**
1. Download from https://www.factorio.com/download
2. Extract and note the binary location

### 2. Python Dependencies
```bash
make dev-install  # Install all dependencies with uv
```

## Configuration

Set the Factorio binary path:

**Option A: Environment Variable**
```bash
export FACTORIO_PATH="/path/to/factorio/binary"
```

**Option B: Command Line**
```bash
python3 scripts/dev_server.py --factorio-path /path/to/factorio/binary
```

## Directory Structure
```
factorio-mcp/
├── mods/
│   └── agent-control/        # Our mod
├── saves/                    # Test save files (auto-created)
├── config/                   # Server configs
├── scripts/                  # Test harness scripts
└── logs/                     # Server logs (auto-created)
```

## Usage

### Start Development Server
```bash
make server
# OR
python3 scripts/dev_server.py
```

### Test RCON Connection Only
```bash
make test-rcon
# OR  
python3 scripts/dev_server.py test
```

### Create Save File Only
```bash
python3 scripts/dev_server.py create
```

## Troubleshooting

**"Factorio binary not found"**
- Make sure Factorio is installed
- Set `FACTORIO_PATH` environment variable
- Use `--factorio-path` argument

**"Connection refused"**
- Server takes ~3-5 seconds to start
- Check `logs/server.log` for errors
- Ensure ports 34197/34198 are available
