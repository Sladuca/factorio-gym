# Virtual Machine Approach Analysis

## Overview

This document analyzes using virtual machines as a fallback approach for running multiple Factorio instances. This provides stronger isolation than processes but with higher resource overhead.

## Lightweight VM Solutions Comparison

### 1. KVM/QEMU (Recommended)
**Pros:**
- Native Linux hypervisor (Type 1)
- Near-native performance (2-5% overhead)
- Excellent automation support
- Hardware acceleration support
- Memory overcommitment capabilities

**Cons:**
- Linux host required
- More complex initial setup
- Requires hardware virtualization support

**Resource Overhead:** ~64-128MB RAM + 10-20MB disk per VM

### 2. VirtualBox
**Pros:**
- Cross-platform compatibility
- Simple GUI management
- Good networking options
- Snapshot functionality

**Cons:**
- Higher performance overhead (10-15%)
- Type 2 hypervisor limitations
- Less efficient for headless workloads

**Resource Overhead:** ~128-256MB RAM + 50-100MB disk per VM

### 3. LXC/LXD (Container-based)
**Pros:**
- Minimal overhead (~1-2%)
- Fast startup times
- Native Linux performance
- Easy automation

**Cons:**
- Shared kernel (less isolation)
- Linux-specific
- Not true virtualization

**Resource Overhead:** ~8-16MB RAM + minimal disk

## Factorio Resource Requirements

### Per Instance (Based on Research)
- **Minimum RAM:** 1GB (small factory)
- **Recommended RAM:** 2-4GB (medium factory)
- **CPU:** Single core at 2GHz+ (CPU-bound on large factories)
- **Disk:** 50MB-1GB (save files grow with factory size)
- **Network:** Minimal (RCON only ~1KB/s)

### Scaling Estimates
| VM Count | Total RAM | Total CPU Cores | Disk Space |
|----------|-----------|-----------------|------------|
| 4 VMs    | 8-16GB    | 4-8 cores      | 2-4GB      |
| 8 VMs    | 16-32GB   | 8-16 cores     | 4-8GB      |
| 16 VMs   | 32-64GB   | 16-32 cores    | 8-16GB     |

## Network Configuration

### RCON Access Pattern
```
Host Machine (Port Range: 25001-25016)
├── VM1: 25001 → 127.0.0.1:25001 (NAT/Bridge)
├── VM2: 25002 → 127.0.0.1:25002
└── VM3: 25003 → 127.0.0.1:25003
```

### Network Options
1. **NAT with Port Forwarding** (Simplest)
2. **Bridge Network** (Direct access)
3. **Host-only Network** (Isolated but accessible)

## Performance Analysis

### VM Overhead Comparison
| Solution | CPU Overhead | Memory Overhead | Disk I/O Impact |
|----------|--------------|-----------------|-----------------|
| KVM/QEMU | 2-5%         | 64-128MB       | Minimal         |
| VirtualBox | 10-15%     | 128-256MB      | 5-10%           |
| LXC/LXD  | 1-2%         | 8-16MB         | Minimal         |

### Bottleneck Analysis
- **CPU:** Factorio is single-threaded, so many VMs on fewer cores
- **RAM:** Each instance needs dedicated memory (no sharing)
- **I/O:** Save game writes can cause disk contention
- **Network:** RCON traffic is negligible

## Automation Strategy

### VM Provisioning Script Outline
```bash
#!/bin/bash
# create_factorio_vm.sh

VM_NAME="factorio-${1}"
RCON_PORT="${2}"
MEMORY="2048"  # 2GB RAM

# Create VM with QEMU/KVM
qemu-img create -f qcow2 "${VM_NAME}.qcow2" 10G
virt-install \
    --name "${VM_NAME}" \
    --memory "${MEMORY}" \
    --vcpus 1 \
    --disk "${VM_NAME}.qcow2" \
    --network network:default \
    --os-variant ubuntu20.04 \
    --install headless

# Configure port forwarding for RCON
iptables -t nat -A PREROUTING -p tcp --dport "${RCON_PORT}" \
    -j DNAT --to-destination "${VM_IP}:25001"
```

### Management Scripts Needed
- `create_vm_cluster.sh` - Provision multiple VMs
- `start_factorio_cluster.sh` - Start all instances
- `monitor_vm_resources.sh` - Resource monitoring
- `backup_vm_saves.sh` - Save game backup

## Cost/Benefit Analysis

### Benefits
✅ **Strong Isolation:** Complete process/memory separation  
✅ **Fault Tolerance:** VM crashes don't affect others  
✅ **Resource Limits:** Hard memory/CPU boundaries  
✅ **Snapshot Support:** Easy backup/restore of entire state  
✅ **Platform Independence:** Works on any hypervisor  

### Drawbacks
❌ **High Resource Overhead:** 64MB-256MB per instance  
❌ **Complex Management:** VM lifecycle management  
❌ **Slower Startup:** 10-30 seconds vs 1-2 seconds  
❌ **Storage Waste:** Duplicate OS files  
❌ **Network Complexity:** Port forwarding/routing  

### Comparison vs Alternatives

| Approach | Isolation | Resource Efficiency | Complexity | Scalability |
|----------|-----------|-------------------|------------|-------------|
| **Process** | Low | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Container** | Medium | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **VM** | High | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

## Recommendations

### When to Use VMs
- **Security-critical environments** requiring strong isolation
- **Mixed OS requirements** (Windows/Linux hosts)
- **Regulatory compliance** demanding VM-level separation
- **Fault tolerance priority** over resource efficiency

### When NOT to Use VMs
- **Resource-constrained environments** (<16GB RAM)
- **High-density deployments** (>10 instances per host)
- **Development/testing** where overhead isn't justified
- **Simple multi-tenancy** where process isolation suffices

## Implementation Priority

Given the AGENT.md directive for simplicity-first approach:

1. **Primary:** Direct process management (current approach)
2. **Secondary:** Container-based deployment (Docker/LXC)
3. **Fallback:** VM-based deployment (documented here)

VMs should be considered only when other approaches prove insufficient for the specific use case requirements.

## Resource Requirements Summary

**Minimum Host for 4 Factorio VMs:**
- CPU: 8 cores (4 for Factorio + 4 for VMs)
- RAM: 16GB (8GB for Factorio + 8GB for VMs)
- Disk: 100GB (OS + saves + overhead)
- Network: Gigabit (RCON + management)

**Recommended Host for 8 Factorio VMs:**
- CPU: 16 cores 
- RAM: 32GB
- Disk: 200GB SSD
- Network: Gigabit + management interface
