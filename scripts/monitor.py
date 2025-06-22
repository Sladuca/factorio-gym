#!/usr/bin/env python3
"""
Factorio Multi-Server Monitor
Monitors multiple Factorio Docker instances and provides health checking and basic stats.
"""

import time
import socket
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FactorioServerMonitor:
    def __init__(self):
        self.servers = {
            'server1': {'host': 'factorio-server-1', 'game_port': 34197, 'rcon_port': 27015},
            'server2': {'host': 'factorio-server-2', 'game_port': 34197, 'rcon_port': 27015},
            'server3': {'host': 'factorio-server-3', 'game_port': 34197, 'rcon_port': 27015},
        }
        self.status_log = []

    def check_port(self, host: str, port: int, protocol: str = 'tcp') -> bool:
        """Check if a port is open on a host."""
        try:
            if protocol == 'tcp':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:  # UDP
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Error checking {protocol} port {port} on {host}: {e}")
            return False

    def check_server_health(self, server_name: str, server_config: Dict) -> Dict:
        """Check the health of a Factorio server."""
        health = {
            'name': server_name,
            'timestamp': datetime.now().isoformat(),
            'game_port_open': False,
            'rcon_port_open': False, 
            'container_running': False,
            'status': 'DOWN'
        }

        try:
            # Check if container is running
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={server_config["host"]}', '--format', '{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0 and 'Up' in result.stdout:
                health['container_running'] = True
                
                # Check ports
                health['game_port_open'] = self.check_port(
                    server_config['host'], server_config['game_port'], 'udp'
                )
                health['rcon_port_open'] = self.check_port(
                    server_config['host'], server_config['rcon_port'], 'tcp'
                )
                
                if health['game_port_open'] and health['rcon_port_open']:
                    health['status'] = 'HEALTHY'
                elif health['game_port_open']:
                    health['status'] = 'PARTIAL'
                else:
                    health['status'] = 'UNHEALTHY'
            
        except Exception as e:
            logger.error(f"Error checking {server_name}: {e}")
            health['error'] = str(e)

        return health

    def get_system_stats(self) -> Dict:
        """Get system resource usage stats."""
        stats = {'timestamp': datetime.now().isoformat()}
        
        try:
            # Docker stats for all Factorio containers
            result = subprocess.run([
                'docker', 'stats', '--no-stream', '--format',
                'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                stats['docker_stats'] = result.stdout
                
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            stats['error'] = str(e)
            
        return stats

    def run_monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Starting Factorio server monitoring...")
        
        while True:
            try:
                status_report = {
                    'timestamp': datetime.now().isoformat(),
                    'servers': {},
                    'system': self.get_system_stats()
                }
                
                # Check each server
                for server_name, server_config in self.servers.items():
                    health = self.check_server_health(server_name, server_config)
                    status_report['servers'][server_name] = health
                    
                    logger.info(f"{server_name}: {health['status']} "
                              f"(Game: {'✓' if health['game_port_open'] else '✗'}, "
                              f"RCON: {'✓' if health['rcon_port_open'] else '✗'})")
                
                # Save status to log
                self.status_log.append(status_report)
                
                # Keep only last 100 entries
                if len(self.status_log) > 100:
                    self.status_log = self.status_log[-100:]
                    
                # Save to file
                with open('/logs/status.json', 'w') as f:
                    json.dump(self.status_log, f, indent=2)
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error

if __name__ == '__main__':
    monitor = FactorioServerMonitor()
    monitor.run_monitoring_loop()
