#!/bin/bash

# Download GGUF Models for Local RAG v2
# This script downloads various GGUF models optimized for RAG systems

set -e  # Exit on any error

echo "🚀 Local RAG v2 - Model Download Script"
echo "========================================"
echo

# Check if we're in the models directory
if [[ ! $(basename "$PWD") == "models" ]]; then
    echo "❌ Please run this script from the models/ directory"
    echo "   cd models && ./download_models.sh"
    exit 1
fi

# Function to download a model if it doesn't exist
download_model() {
    local name="$1"
    local url="$2"
    local filename="$3"
    local size="$4"
    
    if [[ -f "$filename" ]]; then
        echo "✅ $name ($size) - Already downloaded"
        return 0
    fi
    
    echo "📥 Downloading $name ($size)..."
    wget -q --show-progress "$url" -O "$filename"
    echo "✅ $name downloaded successfully"
    echo
}

echo "Available models to download:"
echo
echo "1. DeepSeek-R1-Distill-Qwen-1.5B (1.1GB) - Fast, efficient reasoning"
echo "2. Qwen2.5 3B Instruct (1.8GB) - Excellent for technical content"
echo "3. Llama 3.2 3B Instruct (1.9GB) - Meta's latest, balanced performance"
echo "4. Phi-3.5 Mini (2.3GB) - Microsoft's efficient architecture"
echo "5. Gemma 2 2B (1.6GB) - Google's optimized model"
echo "6. TinyLlama 1.1B (638MB) - Ultra fast, minimal memory"
echo "7. All models (total ~9.4GB)"
echo "8. Rename existing models to match configuration"
echo

read -p "Enter your choice (1-8): " choice

case $choice in
    1)
        download_model "DeepSeek-R1-Distill-Qwen-1.5B" \
            "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf" \
            "deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf" \
            "1.1GB"
        ;;
    2)
        download_model "Qwen2.5 3B Instruct" \
            "https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf" \
            "qwen2.5-3b-instruct.Q4_K_M.gguf" \
            "1.8GB"
        ;;
    3)
        download_model "Llama 3.2 3B Instruct" \
            "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" \
            "llama-3.2-3b-instruct.Q4_K_M.gguf" \
            "1.9GB"
        ;;
    4)
        download_model "Phi-3.5 Mini Instruct" \
            "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf" \
            "phi-3.5-mini-instruct.Q4_K_M.gguf" \
            "2.3GB"
        ;;
    5)
        download_model "Gemma 2 2B Instruct" \
            "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf" \
            "gemma-2-2b-it.Q4_K_M.gguf" \
            "1.6GB"
        ;;
    6)
        download_model "TinyLlama 1.1B Chat" \
            "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
            "tinyllama-1.1b-chat.Q4_K_M.gguf" \
            "638MB"
        ;;
    7)
        echo "📦 Downloading all models..."
        echo
        
        download_model "DeepSeek-R1-Distill-Qwen-1.5B" \
            "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf" \
            "deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf" \
            "1.1GB"
            
        download_model "Qwen2.5 3B Instruct" \
            "https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf" \
            "qwen2.5-3b-instruct.Q4_K_M.gguf" \
            "1.8GB"
            
        download_model "Llama 3.2 3B Instruct" \
            "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" \
            "llama-3.2-3b-instruct.Q4_K_M.gguf" \
            "1.9GB"
            
        download_model "Phi-3.5 Mini Instruct" \
            "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf" \
            "phi-3.5-mini-instruct.Q4_K_M.gguf" \
            "2.3GB"
            
        download_model "Gemma 2 2B Instruct" \
            "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf" \
            "gemma-2-2b-it.Q4_K_M.gguf" \
            "1.6GB"
            
        download_model "TinyLlama 1.1B Chat" \
            "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
            "tinyllama-1.1b-chat.Q4_K_M.gguf" \
            "638MB"
            
        echo "🔄 Renaming models to match configuration paths..."
        # Rename files to match the expected naming pattern in local-rag.yaml
        [[ -f "Qwen2.5-3B-Instruct-Q4_K_M.gguf" ]] && mv "Qwen2.5-3B-Instruct-Q4_K_M.gguf" "qwen2.5-3b-instruct.Q4_K_M.gguf" && echo "✅ Renamed Qwen2.5"
        [[ -f "Llama-3.2-3B-Instruct-Q4_K_M.gguf" ]] && mv "Llama-3.2-3B-Instruct-Q4_K_M.gguf" "llama-3.2-3b-instruct.Q4_K_M.gguf" && echo "✅ Renamed Llama 3.2"
        [[ -f "Phi-3.5-mini-instruct-Q4_K_M.gguf" ]] && mv "Phi-3.5-mini-instruct-Q4_K_M.gguf" "phi-3.5-mini-instruct.Q4_K_M.gguf" && echo "✅ Renamed Phi-3.5"
        [[ -f "gemma-2-2b-it-Q4_K_M.gguf" ]] && mv "gemma-2-2b-it-Q4_K_M.gguf" "gemma-2-2b-it.Q4_K_M.gguf" && echo "✅ Renamed Gemma 2"
        [[ -f "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]] && mv "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" "tinyllama-1.1b-chat.Q4_K_M.gguf" && echo "✅ Renamed TinyLlama"
        ;;
    8)
        echo "🔄 Renaming existing models to match configuration..."
        
        # Rename files to match the expected naming pattern in local-rag.yaml
        [[ -f "Qwen2.5-3B-Instruct-Q4_K_M.gguf" ]] && mv "Qwen2.5-3B-Instruct-Q4_K_M.gguf" "qwen2.5-3b-instruct.Q4_K_M.gguf" && echo "✅ Renamed Qwen2.5"
        [[ -f "Llama-3.2-3B-Instruct-Q4_K_M.gguf" ]] && mv "Llama-3.2-3B-Instruct-Q4_K_M.gguf" "llama-3.2-3b-instruct.Q4_K_M.gguf" && echo "✅ Renamed Llama 3.2"
        [[ -f "Phi-3.5-mini-instruct-Q4_K_M.gguf" ]] && mv "Phi-3.5-mini-instruct-Q4_K_M.gguf" "phi-3.5-mini-instruct.Q4_K_M.gguf" && echo "✅ Renamed Phi-3.5"
        [[ -f "gemma-2-2b-it-Q4_K_M.gguf" ]] && mv "gemma-2-2b-it-Q4_K_M.gguf" "gemma-2-2b-it.Q4_K_M.gguf" && echo "✅ Renamed Gemma 2"
        [[ -f "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]] && mv "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" "tinyllama-1.1b-chat.Q4_K_M.gguf" && echo "✅ Renamed TinyLlama"
        
        echo "✅ Model renaming complete!"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again and choose 1-8."
        exit 1
        ;;
esac

echo
echo "🎉 Download complete!"
echo
echo "📝 To switch models:"
echo "   1. Edit local-rag.yaml"
echo "   2. Uncomment your preferred model_path"
echo "   3. Restart the server"
echo
echo "💡 Model recommendations:"
echo "   • Qwen2.5 3B: Best for technical content and coding"
echo "   • Llama 3.2 3B: Most reliable, balanced performance"
echo "   • TinyLlama: Fastest, minimal resources"
echo "   • DeepSeek-R1: Current default, efficient reasoning"
echo

ls -lah *.gguf 2>/dev/null || echo "No models found in current directory"