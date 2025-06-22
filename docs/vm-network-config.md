# VM Network Configuration for Factorio RCON

## Overview

This document details network configurations for accessing Factorio RCON services running inside virtual machines from the host system.

## Network Architecture Options

### Option 1: NAT with Port Forwarding (Recommended)

**Pros:** Simple, secure, works with any VM count  
**Cons:** Requires port mapping management  

```
Host Machine (192.168.1.100)
├── VM1 (10.0.2.15) → Port 25001 → RCON 25001
├── VM2 (10.0.2.16) → Port 25002 → RCON 25001  
├── VM3 (10.0.2.17) → Port 25003 → RCON 25001
└── VM4 (10.0.2.18) → Port 25004 → RCON 25001
```

### Option 2: Bridge Network

**Pros:** Direct IP access, no port conflicts  
**Cons:** Requires bridge setup, more complex  

```
Host Machine (192.168.1.100)
├── VM1 (192.168.1.101:25001)
├── VM2 (192.168.1.102:25001)
├── VM3 (192.168.1.103:25001)
└── VM4 (192.168.1.104:25001)
```

### Option 3: Host-Only Network

**Pros:** Isolated, direct access, secure  
**Cons:** No external access, requires host routing  

```
Host Machine (192.168.56.1)
├── VM1 (192.168.56.101:25001)
├── VM2 (192.168.56.102:25001)  
├── VM3 (192.168.56.103:25001)
└── VM4 (192.168.56.104:25001)
```

## Implementation Details

### NAT with Port Forwarding (KVM/QEMU)

#### Manual iptables Configuration

```bash
#!/bin/bash
# setup_nat_forwarding.sh

# Enable IP forwarding
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
sysctl -p

# Create forwarding rules for each VM
create_rcon_forward() {
    local VM_NAME="$1"
    local HOST_PORT="$2"
    local VM_RCON_PORT="${3:-25001}"
    
    # Get VM IP address
    local VM_IP=$(virsh domifaddr "$VM_NAME" | grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | head -1)
    
    if [ -z "$VM_IP" ]; then
        echo "Error: Could not determine IP for $VM_NAME"
        return 1
    fi
    
    echo "Forwarding host port $HOST_PORT to $VM_NAME ($VM_IP:$VM_RCON_PORT)"
    
    # DNAT rule for incoming connections
    iptables -t nat -A PREROUTING -p tcp --dport "$HOST_PORT" \
        -j DNAT --to-destination "$VM_IP:$VM_RCON_PORT"
    
    # Allow forwarded traffic
    iptables -A FORWARD -p tcp -d "$VM_IP" --dport "$VM_RCON_PORT" -j ACCEPT
    iptables -A FORWARD -p tcp -s "$VM_IP" --sport "$VM_RCON_PORT" -j ACCEPT
    
    # SNAT for return traffic (if needed)
    iptables -t nat -A POSTROUTING -p tcp -s "$VM_IP" --sport "$VM_RCON_PORT" \
        -j MASQUERADE
}

# Configure forwarding for each Factorio VM
create_rcon_forward "factorio-vm-1" 25001
create_rcon_forward "factorio-vm-2" 25002  
create_rcon_forward "factorio-vm-3" 25003
create_rcon_forward "factorio-vm-4" 25004

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

echo "Port forwarding configured. Test with:"
echo "nc -zv localhost 25001"
```

#### Libvirt XML Configuration

```xml
<!-- factorio-vm-network.xml -->
<network>
  <name>factorio-network</name>
  <forward mode='nat'>
    <nat>
      <port start='1024' end='65535'/>
    </nat>
  </forward>
  <bridge name='virbr-factorio' stp='on' delay='0'/>
  <ip address='192.168.100.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.100.10' end='192.168.100.50'/>
      <!-- Static leases for predictable IPs -->
      <host mac='52:54:00:11:11:01' name='factorio-vm-1' ip='192.168.100.11'/>
      <host mac='52:54:00:11:11:02' name='factorio-vm-2' ip='192.168.100.12'/>
      <host mac='52:54:00:11:11:03' name='factorio-vm-3' ip='192.168.100.13'/>
      <host mac='52:54:00:11:11:04' name='factorio-vm-4' ip='192.168.100.14'/>
    </dhcp>
  </ip>
  <!-- Port forwarding rules -->
  <forward mode='nat'>
    <nat>
      <port start='25001' end='25010'/>
    </nat>
  </forward>
</network>
```

### Bridge Network Configuration

#### Create Bridge Interface

```bash
#!/bin/bash
# setup_bridge_network.sh

# Install bridge utilities
apt install -y bridge-utils

# Create bridge configuration
cat > /etc/netplan/01-bridge.yaml << 'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s3:
      dhcp4: false
      dhcp6: false
  bridges:
    br0:
      interfaces: [enp0s3]
      dhcp4: true
      parameters:
        stp: false
        forward-delay: 0
EOF

# Apply configuration
netplan apply

# Verify bridge
ip addr show br0
brctl show
```

#### VM Bridge Configuration

```xml
<!-- VM network interface for bridge mode -->
<interface type='bridge'>
  <mac address='52:54:00:11:11:01'/>
  <source bridge='br0'/>
  <model type='virtio'/>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
</interface>
```

### Host-Only Network Setup

#### Create Host-Only Network

```bash
#!/bin/bash
# setup_hostonly_network.sh

# Create host-only network definition
cat > /tmp/hostonly-network.xml << 'EOF'
<network>
  <name>factorio-hostonly</name>
  <bridge name='virbr-hostonly' stp='on' delay='0'/>
  <ip address='192.168.56.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.56.100' end='192.168.56.200'/>
      <!-- Static assignments for Factorio VMs -->
      <host mac='52:54:00:56:56:01' name='factorio-vm-1' ip='192.168.56.101'/>
      <host mac='52:54:00:56:56:02' name='factorio-vm-2' ip='192.168.56.102'/>
      <host mac='52:54:00:56:56:03' name='factorio-vm-3' ip='192.168.56.103'/>
      <host mac='52:54:00:56:56:04' name='factorio-vm-4' ip='192.168.56.104'/>
    </dhcp>
  </ip>
</network>
EOF

# Define and start network
virsh net-define /tmp/hostonly-network.xml
virsh net-autostart factorio-hostonly
virsh net-start factorio-hostonly

# Verify network
virsh net-list
ip addr show virbr-hostonly
```

## Network Testing and Validation

### RCON Connection Test Script

```python
#!/usr/bin/env python3
# test_vm_rcon.py

import socket
import sys
import time
from typing import List, Tuple

def test_rcon_connection(host: str, port: int, timeout: int = 5) -> Tuple[bool, str]:
    """Test RCON connection to a Factorio server."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True, "Connection successful"
        else:
            return False, f"Connection failed (error {result})"
            
    except socket.timeout:
        return False, "Connection timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_vm_cluster(config: List[Tuple[str, int]]) -> None:
    """Test RCON connections to all VMs in cluster."""
    print("Testing Factorio VM Cluster RCON Connections")
    print("=" * 50)
    
    all_success = True
    
    for host, port in config:
        print(f"Testing {host}:{port}... ", end="", flush=True)
        
        success, message = test_rcon_connection(host, port)
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            all_success = False
        
        time.sleep(0.1)  # Brief delay between tests
    
    print("\n" + "=" * 50)
    if all_success:
        print("✓ All RCON connections successful")
        sys.exit(0) 
    else:
        print("✗ Some RCON connections failed")
        sys.exit(1)

if __name__ == "__main__":
    # Configuration for different network setups
    
    # NAT with port forwarding
    nat_config = [
        ("localhost", 25001),
        ("localhost", 25002), 
        ("localhost", 25003),
        ("localhost", 25004),
    ]
    
    # Bridge network
    bridge_config = [
        ("192.168.1.101", 25001),
        ("192.168.1.102", 25001),
        ("192.168.1.103", 25001), 
        ("192.168.1.104", 25001),
    ]
    
    # Host-only network
    hostonly_config = [
        ("192.168.56.101", 25001),
        ("192.168.56.102", 25001),
        ("192.168.56.103", 25001),
        ("192.168.56.104", 25001),
    ]
    
    # Determine which configuration to test
    if len(sys.argv) > 1:
        network_type = sys.argv[1].lower()
        if network_type == "bridge":
            test_vm_cluster(bridge_config)
        elif network_type == "hostonly":
            test_vm_cluster(hostonly_config)
        else:
            test_vm_cluster(nat_config)
    else:
        test_vm_cluster(nat_config)
```

### Network Diagnostics Script

```bash
#!/bin/bash
# diagnose_vm_network.sh

echo "Factorio VM Network Diagnostics"
echo "==============================="

# Check host networking
echo "Host Network Configuration:"
echo "---------------------------"
ip addr show | grep -E "(inet|virbr|br0)"
echo

# Check VM status
echo "VM Status:"
echo "----------"
virsh list --all | grep factorio
echo

# Check libvirt networks  
echo "Libvirt Networks:"
echo "-----------------"
virsh net-list --all
echo

# Test VM IP addresses
echo "VM IP Addresses:"
echo "----------------"
for vm in $(virsh list --name | grep factorio); do
    ip=$(virsh domifaddr "$vm" 2>/dev/null | grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | head -1)
    echo "$vm: ${ip:-N/A}"
done
echo

# Check port forwarding rules
echo "Port Forwarding Rules:"
echo "----------------------"
iptables -t nat -L PREROUTING -n | grep -E "(25001|25002|25003|25004)" || echo "No forwarding rules found"
echo

# Test RCON port accessibility
echo "RCON Port Tests:"
echo "----------------"
for port in 25001 25002 25003 25004; do
    if nc -z localhost "$port" 2>/dev/null; then
        echo "Port $port: OPEN"
    else
        echo "Port $port: CLOSED"  
    fi
done
echo

# Check firewall status
echo "Firewall Status:"
echo "----------------"
if command -v ufw >/dev/null; then
    ufw status
elif command -v firewall-cmd >/dev/null; then
    firewall-cmd --list-all
else
    echo "No common firewall found"
fi
```

## Performance Optimization

### Network Performance Tuning

```bash
#!/bin/bash
# optimize_vm_network.sh

# Increase network buffer sizes
echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 12582912 16777216' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 12582912 16777216' >> /etc/sysctl.conf

# Apply changes
sysctl -p

# Optimize VM network interfaces
for vm in $(virsh list --name | grep factorio); do
    # Set network interface to virtio for better performance
    virsh attach-interface "$vm" --type network --source default \
        --model virtio --config --persistent 2>/dev/null || true
done
```

### Monitoring Network Performance

```bash
#!/bin/bash
# monitor_vm_network.sh

echo "VM Network Performance Monitor"
echo "=============================="

while true; do
    clear
    echo "$(date)"
    echo
    
    printf "%-15s %-12s %-12s %-12s %-12s\n" \
        "VM Name" "RX Bytes" "TX Bytes" "RX Packets" "TX Packets"
    printf "%-15s %-12s %-12s %-12s %-12s\n" \
        "-------" "--------" "--------" "----------" "----------"
    
    for vm in $(virsh list --name | grep factorio); do
        stats=$(virsh domifstat "$vm" vnet0 2>/dev/null)
        if [ $? -eq 0 ]; then
            rx_bytes=$(echo "$stats" | grep 'rx_bytes' | awk '{print $2}')
            tx_bytes=$(echo "$stats" | grep 'tx_bytes' | awk '{print $2}')
            rx_packets=$(echo "$stats" | grep 'rx_packets' | awk '{print $2}')
            tx_packets=$(echo "$stats" | grep 'tx_packets' | awk '{print $2}')
            
            printf "%-15s %-12s %-12s %-12s %-12s\n" \
                "$vm" \
                "${rx_bytes:-0}" \
                "${tx_bytes:-0}" \
                "${rx_packets:-0}" \
                "${tx_packets:-0}"
        fi
    done
    
    echo
    echo "Press Ctrl+C to exit"
    sleep 3
done
```

## Troubleshooting Common Issues

### Port Forwarding Not Working

```bash
# Check iptables rules
iptables -t nat -L -n | grep 25001

# Verify VM IP address
virsh domifaddr factorio-vm-1

# Test direct VM connection
VM_IP=$(virsh domifaddr factorio-vm-1 | grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | head -1)
nc -zv "$VM_IP" 25001

# Check if RCON is listening inside VM
virsh console factorio-vm-1
# Inside VM: netstat -tlpn | grep 25001
```

### Bridge Network Issues

```bash
# Check bridge status
brctl show

# Verify bridge IP
ip addr show br0

# Test VM connectivity 
ping 192.168.1.101  # VM IP
```

### Performance Issues

```bash
# Monitor network bandwidth
iftop -i virbr0

# Check packet loss
ping -c 100 192.168.56.101

# Monitor VM network stats
watch virsh domifstat factorio-vm-1 vnet0
```

This comprehensive network configuration ensures reliable RCON access across different virtualization setups while maintaining performance and troubleshooting capabilities.
