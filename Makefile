# Factorio Docker Multi-Instance Makefile

.PHONY: help setup build start stop restart logs status test-rcon clean

help: ## Show this help message
	@echo "Factorio Docker Multi-Instance Management"
	@echo "Usage: make <target>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Set up directories and permissions
	@echo "Setting up Factorio multi-instance environment..."
	@./scripts/setup.sh

build: ## Build Docker images
	@echo "Building Docker images..."
	@docker-compose build

start: ## Start all Factorio servers
	@echo "Starting Factorio servers..."
	@docker-compose up -d
	@echo "Servers starting... Use 'make status' to check progress"

stop: ## Stop all Factorio servers
	@echo "Stopping Factorio servers..."
	@docker-compose down

restart: ## Restart all Factorio servers
	@echo "Restarting Factorio servers..."
	@docker-compose restart

logs: ## Show logs from all services
	@docker-compose logs -f

status: ## Show status of all containers
	@echo "Container Status:"
	@docker-compose ps
	@echo ""
	@echo "Port Status:"
	@echo "Server 1 - Game: 34197, RCON: 27015"
	@echo "Server 2 - Game: 34198, RCON: 27016"
	@echo "Server 3 - Game: 34199, RCON: 27017"
	@echo ""
	@echo "Testing connectivity..."
	@python3 scripts/rcon_test.py || echo "RCON test failed (servers may still be starting)"

test-rcon: ## Test RCON connectivity to all servers
	@python3 scripts/rcon_test.py

monitor: ## Show monitoring logs
	@tail -f logs/monitor.log

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

full-setup: setup build start ## Complete setup from scratch
	@echo "Full setup completed!"
	@echo "Waiting 30 seconds for servers to initialize..."
	@sleep 30
	@make status

# Development targets
dev-logs: ## Show logs for development
	@docker-compose logs -f factorio-server-1

dev-shell: ## Open shell in server 1 container
	@docker-compose exec factorio-server-1 /bin/bash

dev-rcon: ## Open RCON connection to server 1
	@echo "Connecting to Server 1 RCON (localhost:27015)..."
	@python3 -c "
import socket, struct, sys
def rcon_connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 27015))
    # Send auth packet
    auth = struct.pack('<iii', 10, 1, 3) + b'factorio\x00\x00'
    s.send(auth)
    response = s.recv(1024)
    print('Connected to RCON. Type /help for commands.')
    while True:
        try:
            cmd = input('RCON> ')
            if cmd == 'quit': break
            packet = struct.pack('<iii', len(cmd)+10, 2, 2) + cmd.encode() + b'\x00\x00'
            s.send(packet)
            resp = s.recv(4096)
            if len(resp) > 12:
                print(resp[12:-2].decode('utf-8', errors='ignore'))
        except KeyboardInterrupt:
            break
    s.close()
rcon_connect()
"
