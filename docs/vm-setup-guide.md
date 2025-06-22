# VM Setup Guide for Factorio Instances

## Quick Start (KVM/QEMU on Ubuntu)

### Prerequisites
```bash
# Install virtualization packages
sudo apt update
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils

# Verify hardware support
egrep -c '(vmx|svm)' /proc/cpuinfo  # Should be > 0
```

### Create Base VM Template

```bash
#!/bin/bash
# create_factorio_template.sh

# Download Ubuntu Server minimal ISO
wget http://releases.ubuntu.com/20.04/ubuntu-20.04.6-live-server-amd64.iso

# Create base disk image
qemu-img create -f qcow2 factorio-template.qcow2 10G

# Install base system
virt-install \
    --name factorio-template \
    --ram 2048 \
    --disk path=factorio-template.qcow2,format=qcow2 \
    --vcpus 1 \
    --os-type linux \
    --os-variant ubuntu20.04 \
    --network bridge=virbr0 \
    --graphics none \
    --console pty,target_type=serial \
    --location ubuntu-20.04.6-live-server-amd64.iso \
    --extra-args 'console=ttyS0,115200n8 serial'
```

### Template Configuration Script

```bash
#!/bin/bash
# configure_factorio_template.sh - Run inside template VM

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y wget unzip python3 python3-pip

# Create factorio user
useradd -m -s /bin/bash factorio
usermod -aG sudo factorio

# Download Factorio
cd /opt
wget https://factorio.com/get-download/stable/headless/linux64
tar -xf factorio_headless_x64_*.tar.xz
chown -R factorio:factorio factorio

# Create systemd service
cat > /etc/systemd/system/factorio.service << 'EOF'
[Unit]
Description=Factorio Headless Server
After=network.target

[Service]
Type=simple
User=factorio
WorkingDirectory=/opt/factorio
ExecStart=/opt/factorio/bin/x64/factorio --start-server-load-scenario freeplay --server-settings /opt/factorio/data/server-settings.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable auto-start
systemctl enable factorio

# Configure RCON
cat > /opt/factorio/data/server-settings.json << 'EOF'
{
  "name": "Factorio Server",
  "description": "Headless Factorio Server",
  "tags": [],
  "max_players": 10,
  "visibility": {
    "public": false,
    "lan": false
  },
  "username": "",
  "password": "",
  "token": "",
  "game_password": "",
  "require_user_verification": false,
  "max_upload_in_kilobytes_per_second": 0,
  "max_upload_slots": 5,
  "minimum_latency_in_ticks": 0,
  "ignore_player_limit_for_returning_players": false,
  "allow_commands": "admins-only",
  "autosave_interval": 10,
  "autosave_slots": 5,
  "afk_autokick_interval": 0,
  "auto_pause": false,
  "only_admins_can_pause_the_game": true,
  "autosave_only_on_server": true,
  "non_blocking_saving": false,
  "minimum_segment_size": 25,
  "minimum_segment_size_peer_count": 20,
  "maximum_segment_size": 100,
  "maximum_segment_size_peer_count": 10
}
EOF

# Shutdown template for cloning
shutdown -h now
```

### Clone VMs from Template

```bash
#!/bin/bash
# clone_factorio_vms.sh

TEMPLATE="factorio-template"
VM_COUNT=4
BASE_PORT=25001

for i in $(seq 1 $VM_COUNT); do
    VM_NAME="factorio-vm-$i"
    RCON_PORT=$((BASE_PORT + i - 1))
    
    echo "Creating $VM_NAME with RCON port $RCON_PORT"
    
    # Clone disk image
    qemu-img create -f qcow2 -b factorio-template.qcow2 "${VM_NAME}.qcow2"
    
    # Create VM
    virt-install \
        --name "$VM_NAME" \
        --ram 2048 \
        --disk path="${VM_NAME}.qcow2",format=qcow2 \
        --vcpus 1 \
        --os-type linux \
        --os-variant ubuntu20.04 \
        --network bridge=virbr0 \
        --graphics none \
        --console pty,target_type=serial \
        --import \
        --noautoconsole
    
    # Wait for VM to start
    sleep 30
    
    # Get VM IP
    VM_IP=$(virsh domifaddr "$VM_NAME" | grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | head -1)
    
    # Configure RCON port forwarding
    iptables -t nat -A PREROUTING -p tcp --dport "$RCON_PORT" \
        -j DNAT --to-destination "$VM_IP:25001"
    
    echo "VM $VM_NAME created with IP $VM_IP, RCON port $RCON_PORT"
done
```

## Network Configuration

### Port Forwarding Setup

```bash
#!/bin/bash
# setup_port_forwarding.sh

# Enable IP forwarding
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
sysctl -p

# Create iptables rules for RCON access
for i in $(seq 1 4); do
    RCON_PORT=$((25000 + i))
    VM_NAME="factorio-vm-$i"
    VM_IP=$(virsh domifaddr "$VM_NAME" | grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | head -1)
    
    # Forward RCON port
    iptables -t nat -A PREROUTING -p tcp --dport "$RCON_PORT" \
        -j DNAT --to-destination "$VM_IP:25001"
    
    # Allow traffic
    iptables -A FORWARD -p tcp -d "$VM_IP" --dport 25001 -j ACCEPT
done

# Save iptables rules
iptables-save > /etc/iptables/rules.v4
```

### Bridge Network Configuration

```bash
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s3:
      dhcp4: false
  bridges:
    br0:
      interfaces: [enp0s3]
      dhcp4: true
      parameters:
        stp: false
        forward-delay: 0
```

## Resource Optimization

### Memory Optimization

```bash
#!/bin/bash
# optimize_vm_memory.sh

# Enable memory ballooning
for vm in $(virsh list --name); do
    if [[ $vm == factorio-vm-* ]]; then
        # Set memory limits
        virsh setmaxmem "$vm" 4G --config
        virsh setmem "$vm" 2G --config
        
        # Enable balloon driver
        virsh attach-device "$vm" --config << EOF
<memballoon model='virtio'>
  <stats period='10'/>
</memballoon>
EOF
    fi
done
```

### CPU Optimization

```bash
#!/bin/bash
# optimize_vm_cpu.sh

# Pin VMs to specific CPU cores
CORE=0
for vm in $(virsh list --name); do
    if [[ $vm == factorio-vm-* ]]; then
        # Pin to specific core
        virsh vcpupin "$vm" 0 "$CORE"
        CORE=$((CORE + 1))
        
        # Set CPU governor
        virsh schedinfo "$vm" --set vcpu_quota=100000
    fi
done
```

## Management Scripts

### Start All VMs

```bash
#!/bin/bash
# start_factorio_cluster.sh

echo "Starting Factorio VM cluster..."

for i in $(seq 1 4); do
    VM_NAME="factorio-vm-$i"
    
    if virsh domstate "$VM_NAME" | grep -q "shut off"; then
        echo "Starting $VM_NAME..."
        virsh start "$VM_NAME"
        sleep 10
    else
        echo "$VM_NAME already running"
    fi
done

# Wait for all VMs to be ready
echo "Waiting for VMs to be ready..."
sleep 30

# Test RCON connections
for i in $(seq 1 4); do
    RCON_PORT=$((25000 + i))
    echo "Testing RCON connection to port $RCON_PORT..."
    
    # Simple RCON test (requires python RCON client)
    python3 -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    result = s.connect_ex(('localhost', $RCON_PORT))
    if result == 0:
        print('Port $RCON_PORT: RCON accessible')
    else:
        print('Port $RCON_PORT: RCON not accessible')
    s.close()
except Exception as e:
    print(f'Port $RCON_PORT: Error - {e}')
"
done

echo "Factorio VM cluster startup complete"
```

### Monitor Resources

```bash
#!/bin/bash
# monitor_vm_resources.sh

echo "Factorio VM Resource Monitor"
echo "============================"

while true; do
    clear
    echo "$(date)"
    echo
    
    printf "%-15s %-8s %-8s %-8s %-10s\n" "VM Name" "CPU%" "Memory" "Disk I/O" "Network"
    printf "%-15s %-8s %-8s %-8s %-10s\n" "-------" "----" "------" "--------" "-------"
    
    for vm in $(virsh list --name); do
        if [[ $vm == factorio-vm-* ]]; then
            # Get CPU usage
            CPU=$(virsh cpu-stats "$vm" --total 2>/dev/null | grep 'cpu_time' | awk '{print $2}')
            
            # Get memory usage
            MEM=$(virsh dommemstat "$vm" 2>/dev/null | grep 'actual' | awk '{print $2}')
            MEM_MB=$((MEM / 1024))
            
            # Get disk I/O
            DISK=$(virsh domblkstat "$vm" vda 2>/dev/null | head -1 | awk '{print $2}')
            
            # Get network I/O
            NET=$(virsh domifstat "$vm" vnet0 2>/dev/null | head -1 | awk '{print $2}')
            
            printf "%-15s %-8s %-8s %-8s %-10s\n" \
                "$vm" \
                "${CPU:-N/A}" \
                "${MEM_MB:-N/A}MB" \
                "${DISK:-N/A}" \
                "${NET:-N/A}"
        fi
    done
    
    echo
    echo "Press Ctrl+C to exit"
    sleep 5
done
```

## Troubleshooting

### Common Issues

1. **VM won't start:** Check available resources
   ```bash
   free -h  # Check memory
   virsh nodeinfo  # Check CPU/resources
   ```

2. **RCON connection refused:** Verify port forwarding
   ```bash
   iptables -t nat -L -n | grep 25001
   netstat -tulpn | grep 25001
   ```

3. **Poor performance:** Check CPU pinning and memory allocation
   ```bash
   virsh vcpuinfo factorio-vm-1
   virsh dommemstat factorio-vm-1
   ```

### Debug Commands

```bash
# Check VM status
virsh list --all

# View VM console
virsh console factorio-vm-1

# Monitor VM resources
virsh domstats factorio-vm-1

# Check network connectivity
virsh domifaddr factorio-vm-1
```

This setup provides a complete VM-based Factorio deployment with automation, monitoring, and optimization features. The approach trades resource efficiency for strong isolation and fault tolerance.
