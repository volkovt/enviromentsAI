#!/usr/bin/env bash
set -e

# Ajusta para o diretório onde o script está
cd "$(dirname "$0")"

echo "==============================================="
echo " TaskAI Build Script"
echo "==============================================="
echo "1) Gerar Onedir (pasta + _internal)"
echo "2) Gerar Onefile (unico EXE)"
echo "3) Gerar Ambos"
echo
read -p "Escolha uma opcao [1-3]: " escolha

case "$escolha" in
  1)
    echo
    echo "[1] Gerando Onedir..."
    pyinstaller --clean --noconfirm TaskAI_onedir.spec
    ;;
  2)
    echo
    echo "[2] Gerando Onefile..."
    pyinstaller --clean --noconfirm TaskAI.spec
    ;;
  3)
    echo
    echo "[1] Gerando Onedir..."
    pyinstaller --clean --noconfirm TaskAI_onedir.spec

    echo
    echo "[2] Gerando Onefile..."
    pyinstaller --clean --noconfirm TaskAI.spec
    ;;
  *)
    echo "Opcao invalida. Saindo..."
    exit 1
    ;;
esac

echo
echo "Build(s) concluido(s)."
