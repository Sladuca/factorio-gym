# Multi-stage build for Factorio headless server
FROM factoriotools/factorio:latest as factorio-base

# Create a custom image with additional tools for debugging and monitoring
FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    procps \
    net-tools \
    htop \
    python3 \
    python3-pip \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy Factorio from the base image
COPY --from=factorio-base /opt/factorio /opt/factorio
COPY --from=factorio-base /docker-entrypoint.sh /docker-entrypoint.sh
COPY --from=factorio-base /scenario.sh /scenario.sh
COPY --from=factorio-base /scenario2map.sh /scenario2map.sh

# Create factorio user (same UID as original image)
RUN groupadd -g 845 factorio && \
    useradd -u 845 -g 845 -d /factorio -s /bin/bash factorio

# Create directories
RUN mkdir -p /factorio && \
    chown -R factorio:factorio /factorio

# Set environment variables
ENV PORT=34197
ENV RCON_PORT=27015
ENV BIND=0.0.0.0

# Expose ports (will be mapped differently for each instance)
EXPOSE 34197/udp 27015/tcp

# Use the original entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
