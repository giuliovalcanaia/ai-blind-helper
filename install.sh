#!/bin/bash

# Exit the script if any critical error occurs
set -e

echo "🚀 Starting system update and Kitty terminal installation..."

# Check if the user is root; if not, set the variable to use sudo
SUDO=''
if (( $EUID != 0 )); then
    SUDO='sudo'
fi

# Function to detect the OS, update it, and install the package
setup_system() {
    if command -v apt &> /dev/null; then
        echo "📦 Debian/Ubuntu/Raspberry Pi-based system detected."
        echo "🔄 Fetching and installing system updates (this may take a few minutes)..."
        $SUDO apt update
        $SUDO apt upgrade -y
        
        echo "⚙️ Installing Kitty..."
        $SUDO apt install -y kitty
        
    elif command -v pacman &> /dev/null; then
        echo "📦 Arch Linux-based system detected."
        echo "🔄 Synchronizing repositories and updating the system..."
        $SUDO pacman -Syu --noconfirm
        
        echo "⚙️ Installing Kitty..."
        $SUDO pacman -S --noconfirm kitty
        
    elif command -v dnf &> /dev/null; then
        echo "📦 Fedora/RHEL-based system detected."
        echo "🔄 Fetching and installing system updates..."
        $SUDO dnf upgrade -y
        
        echo "⚙️ Installing Kitty..."
        $SUDO dnf install -y kitty
        
    elif command -v zypper &> /dev/null; then
        echo "📦 openSUSE-based system detected."
        echo "🔄 Fetching and installing system updates..."
        $SUDO zypper update -y
        
        echo "⚙️ Installing Kitty..."
        $SUDO zypper install -y kitty
        
    else
        echo "⚠️ Package manager not recognized."
        echo "⚠️ Skipping operating system update."
        echo "🌐 Installing via official Kitty script (pre-compiled binary)..."
        curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
        
        # Create shortcuts so the 'kitty' command works globally in the terminal
        mkdir -p ~/.local/bin
        ln -sf ~/.local/kitty.app/bin/kitty ~/.local/bin/kitty
        ln -sf ~/.local/kitty.app/bin/kitten ~/.local/bin/kitten
        echo "To use this version, ensure that ~/.local/bin is in your PATH."
    fi
}

# Execute the function
setup_system

echo "✅ System update and Kitty installation completed successfully!"# Interrompe o script se ocorrer algum erro crítico