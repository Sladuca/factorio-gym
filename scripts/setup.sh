#!/bin/bash
"""
Setup script for Factorio Docker multi-instance environment
"""

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
sudo chown -R 845:845 data/
sudo chown -R 845:845 config/
sudo chown -R 845:845 mods/

# Create RCON password files
echo "Creating RCON password files..."
echo "factorio" | sudo tee data/server1/config/rconpw > /dev/null
echo "factorio" | sudo tee data/server2/config/rconpw > /dev/null
echo "factorio" | sudo tee data/server3/config/rconpw > /dev/null

sudo chown 845:845 data/server*/config/rconpw
sudo chmod 600 data/server*/config/rconpw

# Build Docker image
echo "Building Docker image..."
docker build -t factorio-multi .

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
