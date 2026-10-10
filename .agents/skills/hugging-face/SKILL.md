---
name: hugging-face
description: >-
  Autonomous Hugging Face integration for J.A.R.V.I.S. Supports model discovery,
  model card inspection, dataset & spaces search, GGUF/model downloading,
  serverless inference, text generation, and embeddings via huggingface_hub.
---

# J.A.R.V.I.S. Hugging Face Integration Skill

## Overview
The Hugging Face Integration Skill provides J.A.R.V.I.S. with seamless access to the open-source AI ecosystem on the Hugging Face Hub (huggingface.co). It enables autonomous discovery, model card evaluation, GGUF weight downloading, serverless inference, text summarization, and vector embeddings using `huggingface_hub` (1.33.0).

---

## Core Capabilities

### 1. Model Discovery & Metadata Inspection
- **Search Models**: Queries thousands of open models by keyword, architecture, task tag (`text-generation`, `sentence-similarity`, `automatic-speech-recognition`, `image-to-text`), and sort order (downloads, likes).
- **Model Card Telemetry**: Retrieves model pipeline tags, download counts, community likes, parameter scales, licensing, and security audits (`safetensors`).
- **Datasets & Spaces Search**: Discovers curated open datasets and interactive Gradio / Streamlit Spaces.

### 2. Serverless Inference & Cognitive Execution
- **Text Generation**: Dispatches generation prompts to premier open models (e.g. `meta-llama/Llama-3.2-3B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3`, `microsoft/Phi-3.5-mini-instruct`).
- **Text Summarization**: Distills documents into structured executive summaries using models like `facebook/bart-large-cnn`.
- **Vector Feature Extraction**: Computes dense sentence embeddings using models like `sentence-transformers/all-MiniLM-L6-v2`.
- **Fault-Tolerant Fallback**: In the absence of an API token or during upstream rate limits, gracefully falls back to local neural SLMs and the Free AI Matrix.

### 3. Model Weight & GGUF Artifact Management
- **GGUF Download**: Fetches quantized weights directly to the local cache directory (`assets/models/huggingface/`).
- **Cache Audit**: Scans and reports locally cached Hugging Face repositories.

---

## Directive Reference

| Directive / Voice Command | Purpose |
|---------------------------|---------|
| `hugging face status` / `hf status` | Reports Hugging Face client status, token presence, cache path, and default models. |
| `hugging face search model <query>` | Searches the Hugging Face Hub for matching open-source models. |
| `hugging face model info <model_id>` | Fetches detailed model card metadata (downloads, likes, pipeline, license). |
| `hugging face generate <prompt>` | Generates text or answers queries via Hugging Face Serverless Inference. |
| `hugging face summarize <text>` | Produces an executive summary of the provided text. |
| `hugging face embed <text>` | Extracts dense vector embeddings for semantic search. |
| `hugging face search dataset <query>` | Searches open datasets on the Hub. |
| `hugging face search spaces <query>` | Searches interactive AI Spaces on the Hub. |
| `download hf model <repo_id> filename <filename>` | Downloads a specific model weight, GGUF, or config file to local storage. |

---

## Configuration & Credentials
- **Free Plan**: Public model searches, dataset queries, spaces exploration, and public file downloads operate 100% free with zero authentication.
- **Serverless Inference Token (Optional)**: To enable authenticated serverless inference, set `HUGGINGFACE_TOKEN=hf_...` in `.env` or system environment. Tokens can be generated for free at `https://huggingface.co/settings/tokens`.
