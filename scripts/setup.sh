#!/bin/bash
# Setup script for Factorio Docker multi-instance environment

set -e

echo "Setting up Factorio Docker multi-instance environment..."

# Create necessary directories
echo "Creating directory structure..."
mkdir -p data/{server1,server2,server3}/{config,saves,mods}
mkdir -p config/{server1,server2,server3}
mkdir -p logs
mkdir -p mods

# Set proper permissions for Factorio user (UID 845)
echo "Setting proper permissions..."
# Note: On macOS, we'll let Docker handle the permissions
# The setup will work without pre-setting permissions

# Create RCON password files
echo "Creating RCON password files..."
mkdir -p data/server1/config data/server2/config data/server3/config
echo "factorio" > data/server1/config/rconpw
echo "factorio" > data/server2/config/rconpw
echo "factorio" > data/server3/config/rconpw

# Pull Docker image
echo "Pulling Factorio Docker image..."
docker pull factoriotools/factorio:latest

echo "Setup complete!"
echo ""
echo "To start the servers:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To test RCON connectivity:"
echo "  python3 scripts/rcon_test.py"
echo ""
echo "Server ports:"
echo "  Server 1: Game=34197, RCON=27015"
echo "  Server 2: Game=34198, RCON=27016" 
echo "  Server 3: Game=34199, RCON=27017"
