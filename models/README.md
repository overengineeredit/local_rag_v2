# Local RAG v2 - GGUF Model Collection

This directory contains a collection of high-quality quantized GGUF models optimized for local deployment in our Local RAG v2 system. All models are quantized using the Q4_K_M method for optimal balance between performance and file size.

## Downloaded Models Overview

| Model | Size | Architecture | Use Case | License |
|-------|------|-------------|----------|---------|
| DeepSeek-R1-Distill-Qwen-1.5B | 1.1GB | Qwen 1.5B | Fast reasoning & multilingual | MIT |
| Llama 3.2 3B Instruct | 1.9GB | Llama 3.2 | General purpose chat | Llama 3.2 Custom |
| Qwen2.5 3B Instruct | 1.8GB | Qwen2.5 | Instruction following | Qwen Research |
| Phi-3.5 Mini | 2.3GB | Phi-3.5 | Code & reasoning | MIT |
| Gemma 2 2B IT | 1.6GB | Gemma 2 | General purpose | Gemma Custom |
| TinyLlama 1.1B Chat | 638MB | Llama | Lightweight chat | Apache 2.0 |

**Total Collection Size:** 9.4GB

## Available Models

### DeepSeek-R1-Distill-Qwen-1.5B (Currently Active)

**File:** `deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf` | **Size:** 1.1GB

**Description:** A distilled version of DeepSeek's R1 reasoning model with excellent logical capabilities and multilingual support. Optimized for efficiency while maintaining strong performance in reasoning tasks.

**Technical Specifications:**

- **Context Length:** Extended context support
- **Language Support:** English, Chinese, and other major languages
- **Architecture:** Qwen 1.5B base with reasoning distillation

**License:** MIT License - Full commercial use allowed, no restrictions

**Best Use Cases:**

- Logical reasoning and problem-solving
- Code analysis and mathematical problems  
- Multilingual applications (English, Chinese, others)
- Resource-constrained environments requiring reasoning

### Llama 3.2 3B Instruct

**File:** `llama-3.2-3b-instruct.Q4_K_M.gguf` | **Size:** 1.9GB

**Description:** A versatile 3B parameter model from Meta's Llama family, excellent for general-purpose tasks with strong instruction following capabilities. Supports extended context and performs well across diverse applications.

**Technical Specifications:**

- **Context Length:** 128K tokens
- **Language Support:** English and other major languages
- **Architecture:** Llama 3.2 3B parameters

**License:** Llama 2 Custom License - Allows commercial use with some restrictions for large-scale deployment

**Best Use Cases:**

- General chat and conversational AI
- Question answering systems
- Content generation and writing assistance
- Applications with <700M monthly active users

### Qwen2.5 3B Instruct

**File:** `qwen2.5-3b-instruct.Q4_K_M.gguf` | **Size:** 1.8GB

**Description:** A multilingual model from Alibaba's Qwen family with strong performance across 25+ languages. Excellent for international applications and multilingual content generation with good instruction following.

**Technical Specifications:**

- **Context Length:** 32K tokens
- **Language Support:** 25+ languages including English, Chinese, Spanish, French, etc.
- **Architecture:** Qwen2.5 3B parameters

**License:** Apache 2.0 - Full commercial use allowed, very permissive

**Best Use Cases:**

- Complex instruction following
- Code generation and programming tasks
- Multilingual applications (25+ languages)
- Technical content analysis and generation

### Phi-3.5 Mini

**File:** `phi-3.5-mini-instruct.Q4_K_M.gguf` | **Size:** 2.3GB

**Description:** Microsoft's compact yet powerful model optimized for efficiency and mobile deployment. Supports extensive context and multilingual capabilities while maintaining small size. Good for resource-constrained environments.

**Technical Specifications:**

- **Context Length:** 128K tokens
- **Language Support:** 20+ languages including English, Spanish, French, German, etc.
- **Architecture:** Phi-3.5 Mini 3.8B parameters

**License:** MIT License - Full commercial use allowed, no restrictions

**Best Use Cases:**

- Programming and code generation
- Mathematical reasoning and STEM education
- Memory-constrained environments
- Applications requiring strong reasoning with limited resources

### Gemma 2 2B IT

**File:** `gemma-2-2b-it.Q4_K_M.gguf` | **Size:** 1.6GB

**Description:** Google's lightweight model from the Gemma family, offering good performance with moderate resource requirements. Suitable for general-purpose applications with balanced efficiency and capability.

**Technical Specifications:**

- **Context Length:** 8K tokens
- **Language Support:** Primarily English with some multilingual capabilities
- **Architecture:** Gemma 2 2B parameters

**License:** Gemma Terms of Use - Allows commercial use with Google's specific terms

**Best Use Cases:**

- General purpose applications requiring safety focus
- Content creation and creative writing
- Applications where safety and responsible AI are priorities
- Balanced performance across various tasks

### TinyLlama 1.1B Chat

**File:** `tinyllama-1.1b-chat.Q4_K_M.gguf` | **Size:** 638MB

**Description:** An extremely lightweight model ideal for testing, development, and resource-constrained environments. Despite its small size, it provides reasonable performance for basic language tasks and serves as a good starting point.

**Technical Specifications:**

- **Context Length:** 2K tokens
- **Language Support:** Primarily English
- **Architecture:** TinyLlama 1.1B parameters

**License:** Apache 2.0 - Full commercial use allowed, very permissive

**Best Use Cases:**

- Edge deployment and resource-constrained environments
- Rapid prototyping and development
- Applications requiring minimal memory footprint
- Fast inference for simple conversational tasks

## Licensing Summary

### ✅ **Unrestricted Commercial Use**

- **DeepSeek-R1** (MIT) & **Phi-3.5 Mini** (MIT) & **TinyLlama** (Apache 2.0) - No usage restrictions

### ⚠️ **Commercial Use with Conditions**

- **Llama 3.2** - Restricted to <700M monthly active users, separate license required above threshold
- **Qwen2.5** - Cannot be used to develop competing foundation models
- **Gemma 2** - Must accept Google's usage agreement, certain prohibited uses

### 📋 **License Compliance Notes**

- Always verify current license terms from official sources before production use
- Some licenses require attribution in derivative works
- For high-scale deployments (>700M MAU), consult legal counsel regarding Llama restrictions

## Usage Guidelines

### Model Selection Recommendations

**For Production Applications:**

1. **MIT/Apache Licensed Models** (DeepSeek, Phi-3.5, TinyLlama) - No licensing concerns
2. **Check Usage Scale** - If serving >700M MAU, avoid Llama 3.2

**For Research & Development:**

- All models are suitable for research purposes
- Consider performance vs. resource requirements

**For Specific Use Cases:**

- **Code Generation:** Phi-3.5 Mini, Qwen2.5
- **Multilingual:** DeepSeek, Qwen2.5, Phi-3.5
- **Resource Constrained:** TinyLlama, DeepSeek
- **General Purpose:** Llama 3.2, Gemma 2

### Performance Characteristics

**Inference Speed (approximate, hardware dependent):**

1. TinyLlama (fastest - 638MB)
2. DeepSeek (very fast - 1.1GB)
3. Gemma 2 (fast - 1.6GB)
4. Qwen2.5 (moderate - 1.8GB)
5. Llama 3.2 (moderate - 1.9GB)
6. Phi-3.5 (good - 2.3GB)

**Quality vs Size Trade-off:**

- **Best Quality:** Qwen2.5, Phi-3.5, Llama 3.2
- **Best Speed:** TinyLlama, DeepSeek
- **Best Balance:** DeepSeek, Gemma 2

## Configuration Management

Switch between models by editing `local-rag.yaml`:

```yaml
llm:
  model_path: "models/[desired-model-file].gguf"
```

Available model paths (uncomment desired model):

- `models/deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf` (current)
- `models/llama-3.2-3b-instruct.Q4_K_M.gguf`
- `models/qwen2.5-3b-instruct.Q4_K_M.gguf`
- `models/phi-3.5-mini-instruct.Q4_K_M.gguf`
- `models/gemma-2-2b-it.Q4_K_M.gguf`
- `models/tinyllama-1.1b-chat.Q4_K_M.gguf`

## Download Management

Use the included download script for managing models:

```bash
cd models
./download_models.sh
```

The script provides options to:

- Download individual models
- Download all models at once
- Check existing downloads
- Display download progress

## Hardware Requirements

**Minimum Requirements (per model):**

- **RAM:** 4GB+ available
- **Storage:** Model size + 1GB working space
- **CPU:** Modern multi-core processor

**Recommended Setup:**

- **RAM:** 8GB+ for optimal performance
- **Storage:** SSD for faster loading
- **CPU:** 8+ cores for better throughput

**GPU Acceleration (Optional):**

- CUDA-compatible GPU with 4GB+ VRAM
- Metal Performance Shaders (macOS)
- ROCm (AMD GPUs)

## Important Legal Notes

1. **License Compliance:** Always verify license requirements for your specific use case
2. **Attribution:** Some licenses require attribution in derivative works
3. **Distribution:** Check redistribution rights before sharing fine-tuned models
4. **Updates:** License terms may change; verify current terms before deployment
5. **Legal Advice:** Consult legal counsel for complex commercial deployments

## Model Sources and Credits

- **DeepSeek Models:** [DeepSeek AI](https://huggingface.co/deepseek-ai)
- **Llama Models:** [Meta AI](https://huggingface.co/meta-llama)
- **Qwen Models:** [Alibaba Cloud](https://huggingface.co/Qwen)
- **Phi Models:** [Microsoft](https://huggingface.co/microsoft)
- **Gemma Models:** [Google](https://huggingface.co/google)
- **TinyLlama Models:** [TinyLlama Project](https://huggingface.co/TinyLlama)
- **GGUF Quantizations:** [bartowski](https://huggingface.co/bartowski)

## Support and Updates

For model-specific issues:

1. Check the original model repositories
2. Review quantization-specific issues on bartowski's page
3. Consult Local RAG v2 documentation for integration issues

---

*Last Updated: 2025-01-28*
*Models Collection Version: 1.0*
