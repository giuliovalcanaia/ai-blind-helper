#!/bin/bash

# Interrompe o script se ocorrer algum erro
set -e

echo "🚀 Iniciando a instalação do terminal Kitty..."

# Verifica se o usuário é root; se não for, usa sudo
SUDO=''
if (( $EUID != 0 )); then
    SUDO='sudo'
fi

# Função para detectar o sistema e instalar o pacote
install_kitty() {
    if command -v apt &> /dev/null; then
        echo "📦 Sistema baseado em Debian/Ubuntu detectado."
        $SUDO apt update
        $SUDO apt install -y kitty
        
    elif command -v pacman &> /dev/null; then
        echo "📦 Sistema baseado em Arch Linux detectado."
        $SUDO pacman -Sy --noconfirm kitty
        
    elif command -v dnf &> /dev/null; then
        echo "📦 Sistema baseado em Fedora/RHEL detectado."
        $SUDO dnf install -y kitty
        
    elif command -v zypper &> /dev/null; then
        echo "📦 Sistema baseado em openSUSE detectado."
        $SUDO zypper install -y kitty
        
    else
        echo "⚠️ Gerenciador de pacotes não reconhecido."
        echo "🌐 Instalando via script oficial do Kitty (binário pré-compilado)..."
        curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
        
        # Cria atalhos para que o comando 'kitty' funcione no terminal globalmente
        mkdir -p ~/.local/bin
        ln -sf ~/.local/kitty.app/bin/kitty ~/.local/bin/kitty
        ln -sf ~/.local/kitty.app/bin/kitten ~/.local/bin/kitten
        echo "Para usar esta versão, certifique-se de que ~/.local/bin está no seu PATH."
    fi
}

# Executa a função
install_kitty

echo "✅ Instalação concluída com sucesso! Você pode iniciar o Kitty digitando 'kitty'."