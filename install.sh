#!/bin/bash

# Interrompe o script se ocorrer algum erro crítico
set -e

echo "🚀 Iniciando a atualização do sistema e instalação do terminal Kitty..."

# Verifica se o usuário é root; se não for, define a variável para usar sudo
SUDO=''
if (( $EUID != 0 )); then
    SUDO='sudo'
fi

# Função para detectar o sistema, atualizar e instalar o pacote
setup_system() {
    if command -v apt &> /dev/null; then
        echo "📦 Sistema baseado em Debian/Ubuntu/Raspberry Pi detectado."
        echo "🔄 Buscando e instalando atualizações do sistema (isso pode levar alguns minutos)..."
        $SUDO apt update
        $SUDO apt upgrade -y
        
        echo "⚙️ Instalando o Kitty..."
        $SUDO apt install -y kitty
        
    elif command -v pacman &> /dev/null; then
        echo "📦 Sistema baseado em Arch Linux detectado."
        echo "🔄 Sincronizando repositórios e atualizando o sistema..."
        $SUDO pacman -Syu --noconfirm
        
        echo "⚙️ Instalando o Kitty..."
        $SUDO pacman -S --noconfirm kitty
        
    elif command -v dnf &> /dev/null; then
        echo "📦 Sistema baseado em Fedora/RHEL detectado."
        echo "🔄 Buscando e instalando atualizações do sistema..."
        $SUDO dnf upgrade -y
        
        echo "⚙️ Instalando o Kitty..."
        $SUDO dnf install -y kitty
        
    elif command -v zypper &> /dev/null; then
        echo "📦 Sistema baseado em openSUSE detectado."
        echo "🔄 Buscando e instalando atualizações do sistema..."
        $SUDO zypper update -y
        
        echo "⚙️ Instalando o Kitty..."
        $SUDO zypper install -y kitty
        
    else
        echo "⚠️ Gerenciador de pacotes não reconhecido."
        echo "⚠️ Pulando a atualização do sistema operacional."
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
setup_system

echo "✅ Atualização do sistema e instalação do Kitty concluídas com sucesso!"