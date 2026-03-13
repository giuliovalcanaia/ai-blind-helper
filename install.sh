#!/bin/bash

# Exit the script if any critical error occurs
set -e

echo "🚀 Starting system update and Kitty terminal installation..."

# Variável para controlar se o sistema precisará ser reiniciado no final
REBOOT_REQUIRED=false

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
        
        # ====================================================================
        # NOVA SESSÃO: Detecção de Raspberry Pi e instalação dos drivers de áudio
        # ====================================================================
        if [[ -f /sys/firmware/devicetree/base/model ]] && grep -qi "Raspberry Pi" /sys/firmware/devicetree/base/model; then
            echo "🍓 Raspberry Pi detected! Installing WM8960-Audio-HAT drivers..."
            
            # Instala as dependências necessárias
            $SUDO apt install git bc -y
            
            # Evita erro de diretório já existente caso o script seja rodado mais de uma vez
            if [ ! -d "WM8960-Audio-HAT" ]; then
                git clone https://github.com/waveshare/WM8960-Audio-HAT
            fi
            
            # Executa a instalação dentro de uma subshell (...) para que o 'cd'
            # não altere o diretório de trabalho do resto do script
            (
                cd WM8960-Audio-HAT
                $SUDO ./install.sh
            )
            
            echo "✅ Audio drivers installed. A reboot has been scheduled."
            # Sinaliza que o reboot deve ocorrer no final do script
            REBOOT_REQUIRED=true
        fi
        # ====================================================================
        
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

echo "✅ System update and Kitty installation completed successfully!"

# ====================================================================
# NOVA SESSÃO: Reinício automático do sistema (se aplicável)
# ====================================================================
if [ "$REBOOT_REQUIRED" = true ]; then
    echo "🔄 Rebooting the system in 10 seconds to apply audio driver changes... Press Ctrl+C to cancel."
    sleep 10
    $SUDO reboot
fi