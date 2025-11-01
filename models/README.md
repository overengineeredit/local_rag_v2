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

## Model Descriptions

### 1. DeepSeek-R1-Distill-Qwen-1.5B (Currently Active)

- **File:** `deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf`
- **Size:** 1.1GB
- **Strengths:** Excellent reasoning capabilities, multilingual support, efficient performance
- **Best For:** Logical reasoning tasks, code analysis, mathematical problems
- **Context Length:** Extended context support
- **Language Support:** English, Chinese, and other major languages

### 2. Llama 3.2 3B Instruct

- **File:** `llama-3.2-3b-instruct.Q4_K_M.gguf`
- **Size:** 1.9GB
- **Strengths:** General-purpose instruction following, balanced performance
- **Best For:** General chat, question answering, content generation
- **Context Length:** 128K tokens
- **Language Support:** Primarily English with some multilingual capabilities

### 3. Qwen2.5 3B Instruct

- **File:** `qwen2.5-3b-instruct.Q4_K_M.gguf`
- **Size:** 1.8GB
- **Strengths:** Strong instruction following, multilingual capabilities
- **Best For:** Complex instructions, code generation, multilingual tasks
- **Context Length:** 32K tokens
- **Language Support:** English, Chinese, and 25+ other languages

### 4. Phi-3.5 Mini

- **File:** `phi-3.5-mini-instruct.Q4_K_M.gguf`
- **Size:** 2.3GB
- **Strengths:** Code generation, mathematical reasoning, memory efficiency
- **Best For:** Programming tasks, STEM education, constrained environments
- **Context Length:** 128K tokens
- **Language Support:** 20+ languages including English, Spanish, French, German

### 5. Gemma 2 2B IT

- **File:** `gemma-2-2b-it.Q4_K_M.gguf`
- **Size:** 1.6GB
- **Strengths:** Balanced performance, safety-focused training
- **Best For:** General purpose applications, content creation
- **Context Length:** 8K tokens
- **Language Support:** Primarily English

### 6. TinyLlama 1.1B Chat

- **File:** `tinyllama-1.1b-chat.Q4_K_M.gguf`
- **Size:** 638MB
- **Strengths:** Extremely lightweight, fast inference, Llama compatibility
- **Best For:** Resource-constrained environments, edge deployment, rapid prototyping
- **Context Length:** 2K tokens
- **Language Support:** Primarily English

## Licensing Information

### ✅ Commercial Use Allowed (No Restrictions)

#### MIT License

- **DeepSeek-R1-Distill-Qwen-1.5B**: Full commercial use allowed, no restrictions
- **Phi-3.5 Mini**: Full commercial use allowed, attribution required

#### Apache 2.0 License

- **TinyLlama 1.1B Chat**: Full commercial use allowed, attribution required

### ⚠️ Commercial Use with Restrictions

#### Llama 3.2 Custom Commercial License

- **Llama 3.2 3B Instruct**:
  - ✅ Commercial use allowed for applications with <700M monthly active users
  - ❌ Applications with ≥700M MAU require separate license from Meta
  - ✅ Research and development use unrestricted
  - **Note:** Check [Meta's official license](https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE) for full terms

#### Qwen Research License

- **Qwen2.5 3B Instruct**:
  - ✅ Research use allowed
  - ✅ Commercial use generally allowed for most applications
  - ❌ Cannot be used to develop competing foundation models
  - **Note:** Review [Qwen License](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE) for specific terms

#### Gemma Custom License

- **Gemma 2 2B IT**:
  - ✅ Commercial use allowed with attribution
  - ✅ Modification and distribution allowed
  - ❌ Certain prohibited uses outlined in terms
  - **Note:** Must accept Google's usage agreement via Hugging Face

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
