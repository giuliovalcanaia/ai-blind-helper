#!/bin/bash

# Exit script on critical errors
set -e

echo "Starting system update and tool installation..."

# Variable to track if a system reboot is required at the end
REBOOT_REQUIRED=false

# Check if the user is root; if not, use sudo
SUDO=''
# FIX 1: Replaced (( $EUID != 0 )) with a universal check
if [ "$(id -u)" -ne 0 ]; then
    SUDO='sudo'
fi

# Function to detect OS, update, and install dependencies
setup_system() {
    # FIX 2: Replaced &> /dev/null with > /dev/null 2>&1 to prevent failures if run via 'sh'
    if command -v apt > /dev/null 2>&1; then
        echo "Debian/Ubuntu/Raspberry Pi based system detected."
        $SUDO apt update
        $SUDO apt upgrade -y
        
        echo "Installing base dependencies (Git, Kitty, Python, PortAudio, Xvfb)..."
        $SUDO apt install -y git kitty python3 python3-venv python3-pip portaudio19-dev xvfb
        
        # --- Raspberry Pi Specific Section ---
        if [ -f /sys/firmware/devicetree/base/model ] && grep -qi "Raspberry Pi" /sys/firmware/devicetree/base/model; then
            echo "Raspberry Pi detected. Checking WM8960-Audio-HAT drivers..."
            
            # SAFETY LOCK: Check if the driver is already in DKMS or boot config.txt
            if grep -qi "wm8960" /boot/config.txt /boot/firmware/config.txt 2>/dev/null || (command -v dkms > /dev/null 2>&1 && dkms status | grep -qi "wm8960"); then
                echo "WM8960-Audio-HAT driver is already installed. Skipping installation."
            else
                echo "Driver not found. Starting WM8960-Audio-HAT installation..."
                $SUDO apt install bc -y
                
                if [ ! -d "WM8960-Audio-HAT" ]; then
                    git clone https://github.com/waveshare/WM8960-Audio-HAT
                fi
                
                (
                    cd WM8960-Audio-HAT
                    $SUDO ./install.sh
                )
                
                echo "Driver installation complete. The system will reboot at the end."
                REBOOT_REQUIRED=true
            fi
        fi
        # ------------------------------------------

    elif command -v pacman > /dev/null 2>&1; then
        echo "Arch Linux based system detected."
        $SUDO pacman -Syu --noconfirm
        echo "Installing base dependencies (Git, Kitty, Python, PortAudio, Xvfb)..."
        $SUDO pacman -S --noconfirm git kitty python python-pip portaudio xorg-server-xvfb
        
    elif command -v dnf > /dev/null 2>&1; then
        echo "Fedora/RHEL based system detected."
        $SUDO dnf upgrade -y
        echo "Installing base dependencies (Git, Kitty, Python, PortAudio, Xvfb)..."
        $SUDO dnf install -y git kitty python3 python3-pip portaudio-devel xorg-x11-server-Xvfb
        
    elif command -v zypper > /dev/null 2>&1; then
        echo "openSUSE based system detected."
        $SUDO zypper update -y
        echo "Installing base dependencies (Git, Kitty, Python, PortAudio, Xvfb)..."
        $SUDO zypper install -y git kitty python3 python3-pip portaudio-devel xorg-x11-server-extra
        
    else
        echo "Package manager not recognized."
        echo "Attempting to install Kitty via official script..."
        curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
        
        mkdir -p ~/.local/bin
        ln -sf ~/.local/kitty.app/bin/kitty ~/.local/bin/kitty
    fi

    # --- Cloning and Configuration of ai-blind-helper ---
    echo "Checking ai-blind-helper repository..."
    if [ ! -d "ai-blind-helper" ]; then
        git clone https://github.com/giuliovalcanaia/ai-blind-helper.git
        echo "ai-blind-helper successfully cloned."
    else
        echo "The 'ai-blind-helper' directory already exists. Skipping clone."
    fi

    echo "Configuring Python environment (venv) and installing dependencies..."
    (
        cd ai-blind-helper
        echo "Entering ai-blind-helper directory..."
        
        PYTHON_CMD="python3"
        if ! command -v $PYTHON_CMD > /dev/null 2>&1; then
            PYTHON_CMD="python"
        fi

        if [ ! -d "venv" ]; then
            $PYTHON_CMD -m venv venv
            echo "Virtual environment (venv) created."
        else
            echo "Virtual environment already exists."
        fi

        # Activate virtual environment
        . venv/bin/activate
        
        # Prevent 'set -e' from aborting the script if the structure changes
        if [ -d "ai_blind_helper" ]; then
            cd ai_blind_helper
            echo "Entering ai_blind_helper directory..."
        fi

        if [ -f "requirements.txt" ]; then
            echo "Installing packages from requirements.txt..."
            pip install --upgrade pip
            pip install -r requirements.txt
            echo "Dependencies installed successfully."
        else
            echo "requirements.txt file not found. No dependencies installed via pip."
        fi
        
        deactivate
    )
}

# Execute main function
setup_system

echo "Installation process complete."

# Reboot if necessary
if [ "$REBOOT_REQUIRED" = true ]; then
    echo "Rebooting the system in 10 seconds to apply audio drivers... Press Ctrl+C to cancel."
    sleep 10
    $SUDO reboot
fi