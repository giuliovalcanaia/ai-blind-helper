#!/bin/bash

# Interrompe o script se ocorrer algum erro crítico
set -e

echo "🚀 Iniciando atualização do sistema e instalação de ferramentas..."

# Variável para controlar se o sistema precisará ser reiniciado no final
REBOOT_REQUIRED=false

# Verifica se o usuário é root; se não, define o uso do sudo
SUDO=''
if (( $EUID != 0 )); then
    SUDO='sudo'
fi

# Função para detectar o SO, atualizar e instalar dependências
setup_system() {
    if command -v apt &> /dev/null; then
        echo "📦 Sistema baseado em Debian/Ubuntu/Raspberry Pi detectado."
        $SUDO apt update
        $SUDO apt upgrade -y
        
        echo "⚙️ Instalando dependências base (Git, Kitty, Python)..."
        $SUDO apt install -y git kitty python3 python3-venv python3-pip
        
        # --- Seção Específica para Raspberry Pi ---
        if [[ -f /sys/firmware/devicetree/base/model ]] && grep -qi "Raspberry Pi" /sys/firmware/devicetree/base/model; then
            echo "🍓 Raspberry Pi detectado! Instalando drivers WM8960-Audio-HAT..."
            $SUDO apt install bc -y
            
            if [ ! -d "WM8960-Audio-HAT" ]; then
                git clone https://github.com/waveshare/WM8960-Audio-HAT
            fi
            
            (
                cd WM8960-Audio-HAT
                $SUDO ./install.sh
            )
            REBOOT_REQUIRED=true
        fi

    elif command -v pacman &> /dev/null; then
        echo "📦 Sistema baseado em Arch Linux detectado."
        $SUDO pacman -Syu --noconfirm
        echo "⚙️ Instalando dependências base (Git, Kitty, Python)..."
        $SUDO pacman -S --noconfirm git kitty python python-pip
        
    elif command -v dnf &> /dev/null; then
        echo "📦 Sistema baseado em Fedora/RHEL detectado."
        $SUDO dnf upgrade -y
        echo "⚙️ Instalando dependências base (Git, Kitty, Python)..."
        $SUDO dnf install -y git kitty python3 python3-pip
        
    elif command -v zypper &> /dev/null; then
        echo "📦 Sistema baseado em openSUSE detectado."
        $SUDO zypper update -y
        echo "⚙️ Instalando dependências base (Git, Kitty, Python)..."
        $SUDO zypper install -y git kitty python3 python3-pip
        
    else
        echo "⚠️ Gerenciador de pacotes não reconhecido."
        echo "🌐 Tentando instalar Kitty via script oficial..."
        curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
        
        mkdir -p ~/.local/bin
        ln -sf ~/.local/kitty.app/bin/kitty ~/.local/bin/kitty
    fi

    # --- Clonagem e Configuração do ai-blind-helper ---
    echo "📥 Verificando repositório ai-blind-helper..."
    if [ ! -d "ai-blind-helper" ]; then
        git clone https://github.com/giuliovalcanaia/ai-blind-helper.git
        echo "✅ ai-blind-helper clonado com sucesso."
    else
        echo "ℹ️ O diretório 'ai-blind-helper' já existe. Pulando clonagem."
    fi

    echo "🐍 Configurando ambiente Python (venv) e instalando dependências..."
    (
        cd ai-blind-helper
        
        # Define o comando python correto dependendo do sistema (Arch usa 'python', Debian 'python3')
        PYTHON_CMD="python3"
        if ! command -v $PYTHON_CMD &> /dev/null; then
            PYTHON_CMD="python"
        fi

        # Cria o ambiente virtual se não existir
        if [ ! -d "venv" ]; then
            $PYTHON_CMD -m venv venv
            echo "✅ Ambiente virtual (venv) criado."
        else
            echo "ℹ️ Ambiente virtual já existente."
        fi

        # Ativa o venv e instala as dependências
        source venv/bin/activate
        
        if [ -f "requirements.txt" ]; then
            echo "📦 Instalando pacotes do requirements.txt..."
            pip install --upgrade pip
            pip install -r requirements.txt
            echo "✅ Dependências instaladas com sucesso."
        else
            echo "⚠️ Arquivo requirements.txt não encontrado. Nenhuma dependência instalada via pip."
        fi
        
        deactivate
    )
}

# Executa a função principal
setup_system

echo "✅ Processo de instalação concluído!"

# Reinício se necessário
if [ "$REBOOT_REQUIRED" = true ]; then
    echo "🔄 Reiniciando o sistema em 10 segundos para aplicar drivers de áudio... Pressione Ctrl+C para cancelar."
    sleep 10
    $SUDO reboot
fi