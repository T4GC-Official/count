#!/bin/bash

echo "🚀 Starting Count setup process..."

# Update package list if it's older than 1 hour
if [ ! -f "/var/cache/apt/pkgcache.bin" ] || [ $(find /var/cache/apt/pkgcache.bin -mmin +60) ]; then
    echo "📦 Updating package lists..."
    sudo apt-get update
fi

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "📥 Installing git..."
    sudo apt-get install -y git
fi

# Check if python3.11-venv is installed
if ! dpkg -l | grep -q python3.11-venv; then
    echo "📥 Installing Python virtual environment..."
    sudo apt-get install -y python3.11-venv
fi

# Install build dependencies if not present
echo "📥 Installing build dependencies..."
sudo apt-get install -y build-essential libffi-dev libssl-dev python3-dev python3-pip libyaml-dev

# Setup virtual environment if not already created
if [ ! -d "venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" != *"venv"* ]]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Upgrade pip and install requirements
echo "📥 Upgrading pip and installing Python packages..."
pip3 install --upgrade pip setuptools wheel Cython
pip3 install ansible

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    # Add Docker's official GPG key
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Test Docker installation
echo "🧪 Testing Docker installation..."
if ! sudo docker run hello-world &> /dev/null; then
    echo "❌ Docker test failed. Please check Docker installation."
    exit 1
fi
echo "✅ Docker test successful!"

# Add user to docker group if not already added
# NB: we don't run newgrp docker because it creates a new shell and that would 
# interfere with the current script execution flow. 
if ! groups $USER | grep -q docker; then
    echo "👥 Adding user to docker group..."
    sudo groupadd -f docker
    sudo usermod -aG docker $USER
    echo "🔄 Please log out and log back in for docker group changes to take effect"
    echo "   Alternatively, run: newgrp docker"
fi

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. If this is your first time running this script, please log out and log back in"
echo "   (or run 'newgrp docker') to use Docker without sudo"
echo "2. Run 'docker compose up -d --build' from the root directory to start Count"
