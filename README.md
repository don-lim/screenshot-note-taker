# Screenshot Note Taker - Searchable Screenshot Database

## Overview
AI-powered searchable database for your screenshots using local OCR and semantic search. Process screenshots with Korean and English text support, generate AI descriptions, and search your activities using natural language queries.

## Key Features
- **🔍 Advanced OCR**: PaddleOCR (CPU mode) for Korean + English text extraction
- **🧠 Semantic Search**: bge-m3 embeddings (1024-dim) via Ollama for multilingual semantic understanding
- **🤖 AI Vision**: Qwen3-VL for intelligent screenshot descriptions
- **💾 PostgreSQL Storage**: Local database with pgvector for similarity search
- **🎨 Modern UI**: Flet-based desktop app with search and detail views
- **🔄 Smart Processing**: Automatic duplicate detection and failure tracking

## Tech Stack
- **OCR**: PaddleOCR 2.8.1 (CPU mode, Korean + English)
- **Vision Model**: Qwen3-VL (4B, GPU-only) via Ollama
- **Embeddings**: bge-m3 (1024-dimensional) via Ollama
- **Database**: PostgreSQL with pgvector extension
- **UI**: Flet (Python desktop framework)
- **LLM Provider**: Ollama (local inference)

## Project Structure
```
screenshot-note-taker/
├── .env                          # Environment configuration
├── schema.sql                    # Database schema (VECTOR(1024))
├── requirements.txt              # Python dependencies
│
├── ocr_processor.py             # Core OCR & AI processing functions
├── batch_processor.py           # Interactive batch processor
├── auto_processor_service.py    # Background file watcher
├── app.py                       # Flet UI application
│
└── tests/
    ├── test_single_file.py      # Single file test
    └── ...
```

## Setup

### 1. Prerequisites
- **Python 3.11**
- **PostgreSQL** with pgvector extension
- **Ollama** with models installed:
  - `qwen3-vl:4b` (vision model)
  - `bge-m3:latest` (embeddings)
- **NVIDIA GPU** recommended for Ollama (RTX 5060 Ti or better)
- **16GB RAM** minimum

### 2. Install Ollama Models

**Option A: Use Pre-built Model (if available)**
```powershell
# Install vision model
ollama pull qwen3-vl:4b

# Install embedding model
ollama pull bge-m3:latest

# Verify models are available
ollama list
```

**Option B: Build Custom GPU-Optimized Model (Recommended)**

The repository includes a custom modelfile optimized for your RTX 5060 Ti:

```powershell
# First, pull the base model
ollama pull qwen3-vl:4b-instruct

# Build custom model from modelfile
ollama create qwen3-vl-4b-gpu-only -f qwen3-vl-4b-gpu-only.modelfile

# Install embedding model
ollama pull bge-m3:latest

# Verify models are available
ollama list
```

**What the custom model does:**
- Forces all layers to GPU (`num_gpu 99`)
- Optimized 8K context for faster screenshot processing
- Custom system prompt for concise descriptions
- Performance tuned for i7 + RTX 5060 Ti

**Modelfile contents** (`qwen3-vl-4b-gpu-only.modelfile`):
```
FROM qwen3-vl:4b-instruct
PARAMETER num_gpu 99
PARAMETER num_ctx 8192
PARAMETER num_batch 512
PARAMETER num_thread 8
SYSTEM """You are a specialized visual analysis assistant. 
Your ONLY task is to provide a concise 5-6 sentence description of screenshots.
Identify the main application, the activity, and the key context.
Do NOT output OCR text.
Do NOT show any internal reasoning, thoughts, or <think> tags."""
```

### 3. Install Python Dependencies
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 4. Environment Configuration
Create `.env` file with:
```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=image_search_db
POSTGRES_USER=screuser235
POSTGRES_PASSWORD=screp235@#!^

# Ollama Configuration
LOCAL_LLM_API_URL=http://localhost:11434
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_MODEL=qwen3-vl:4b-gpu-only
LOCAL_TOKENIZER_MODEL=bge-m3:latest
```

### 5. Database Setup
```powershell
# Create database and schema
psql -U postgres
CREATE DATABASE image_search_db;
\c image_search_db
CREATE EXTENSION vector;
\i schema.sql
```

## Usage

### Initial Batch Processing (First Time Setup)

When you first set up the system, process all existing screenshots:

```powershell
python batch_processor.py
```

**Interactive Menu:**
1. **Process all screenshots** - Process every PNG in your Screenshots folder
2. **Process only new screenshots** - Skip files already in database
3. **Show database stats** - View current database status
4. **Exit**

**Features:**
- ✅ Tracks failed/skipped files with reasons
- ✅ Shows duplicates separately from errors
- ✅ Displays detailed failure reasons:
  - `Duplicate` - Already in database
  - `Ocr And Vision Failed` - Both OCR and AI description failed
  - `Database Error` - Failed to store in database
  - `Embedding Error` - Failed to generate embeddings
  - `No Embeddings` - No embeddings generated

**Example Output:**
```
✅ Complete: 245 processed, 12 skipped (duplicates), 3 failed

============================================================
FAILED FILES (3):
============================================================
  1. screenshot_001.png
      Reason: Ocr And Vision Failed
  2. screenshot_042.png
      Reason: Database Error
  3. screenshot_099.png
      Reason: No Embeddings
```

### Real-Time Auto-Processing (Background Service)

For automatic processing of new screenshots as they're created:

```powershell
python auto_processor_service.py
```

**Features:**
- 👀 Watches `C:\Users\user\Pictures\Screenshots` for new files
- ⚡ Automatically processes new screenshots
- 📊 Shows processing status with reasons
- 🔄 Runs continuously until stopped (Ctrl+C)

**Example Output:**
```
============================================================
Screenshot Auto-Processor Service (Ollama)
============================================================
✅ Ollama is connected and ready!
👀 Watching: C:\Users\user\Pictures\Screenshots

Service is running. Press Ctrl+C to stop.
============================================================

[19:30:45] New screenshot detected: screenshot_123.png
  PaddleOCR Extraction...
    PaddleOCR complete in 8.2s (45 lines)
  AI Vision Description using qwen3-vl:4b-gpu-only...
    Vision Description complete in 1.5s
  ✅ Processed successfully - Total: 1
```

### Search UI (Desktop App)

Launch the Flet desktop application:

```powershell
python app.py
```

**Features:**
- 🔍 Search with Korean or English queries
- 🎯 Hybrid search (semantic + keyword)
- 🖼️ Image preview with OCR text
- 🤖 AI-generated descriptions
- ✨ Highlighted search results

## How It Works

### Processing Pipeline

1. **OCR Extraction** (PaddleOCR on CPU)
   - Reads image with Korean filename support
   - Extracts text using PaddleOCR
   - Takes ~7-8 seconds per image
   - Prints extracted text to terminal for verification

2. **AI Vision Description** (Qwen3-VL via Ollama on GPU)
   - Generates concise 3-5 sentence description
   - Identifies main applications and user activity
   - Takes ~1-2 seconds per image
   - GPU-accelerated via Ollama

3. **Embedding Generation** (bge-m3 via Ollama on GPU)
   - Creates embeddings for AI description (chunk index -1)
   - Creates embeddings for OCR text (chunk indices 0, 1, 2...)
   - Text chunked into 1000-char segments with 100-char overlap
   - Takes ~4 seconds per image

4. **Database Storage**
   - Stores image metadata with AI description
   - Stores OCR results
   - Stores embeddings (1024-dim vectors)
   - Automatic duplicate detection

### Search

1. **Query Embedding**: Generate embedding for search query via Ollama
2. **Semantic Search**: Cosine similarity using pgvector `<=>` operator
3. **Keyword Search**: PostgreSQL ILIKE for exact matches
4. **Hybrid Mode**: Combines both methods, deduplicated by image ID

## Performance

### Processing Speed (Per Image)
- **OCR Extraction**: ~7-8 seconds (CPU)
- **AI Description**: ~1-2 seconds (GPU via Ollama)
- **Embeddings**: ~4 seconds (GPU via Ollama)
- **Total**: ~12-14 seconds per image

### System Requirements
- **CPU**: i7 or better (for PaddleOCR)
- **GPU**: RTX 5060 Ti 16GB (for Ollama vision & embeddings)
- **RAM**: 16GB minimum
- **VRAM**: 16GB (for Ollama models)

## Database Schema

### images
- `id`: Primary key
- `filename`: Screenshot filename
- `filepath`: Full path (with Korean support)
- `timestamp`: File modification time
- `ai_description`: AI-generated description
- `model_name`: Vision model used
- `inserted_at`: Database insertion time

### ocr_results
- `id`: Primary key
- `image_id`: Foreign key to images
- `text`: Extracted text (multilingual)
- `confidence`: OCR confidence (0.0-1.0)

### text_embedding
- `id`: Primary key
- `image_id`: Foreign key to images
- `embedding`: VECTOR(1024) - bge-m3 embedding
- `chunk_index`: -1 for description, 0+ for OCR chunks

## Troubleshooting

### OCR Issues

**Q: OCR is producing garbled text**
- **A**: This happens if GPU mode is used with incompatible CUDA versions. The system is configured to use CPU mode which produces clean, accurate text.

**Q: OCR is slow**
- **A**: CPU mode takes ~7-8 seconds per image, which is acceptable. For GPU acceleration, you would need to install CUDA 11.8 + cuDNN 8.6 (see `CUDA_INSTALLATION_GUIDE.md`).

### Ollama Issues

**Q: "Ollama not detected" error**
- **A**: Ensure Ollama is running: `ollama serve`
- Verify models are installed: `ollama list`

**Q: Vision description fails**
- **A**: Check Ollama logs for VRAM issues
- Ensure `qwen3-vl:4b` is pulled

### Database Issues

**Q: PostgreSQL connection error**
- **A**: Check environment variables match `.env`
- Verify PostgreSQL is running
- Check password and user permissions

**Q: Vector dimension mismatch**
- **A**: Ensure schema uses `VECTOR(1024)` for bge-m3 embeddings

## Development

### Running Tests
```powershell
python test_single_file.py          # Test one image with full output
```

### Clear Database
```sql
TRUNCATE TABLE text_embedding CASCADE;
TRUNCATE TABLE ocr_results CASCADE;
TRUNCATE TABLE images CASCADE;
```

## Why These Technologies?

### PaddleOCR (CPU Mode)
- ✅ Excellent Korean text recognition
- ✅ No CUDA version conflicts
- ✅ Reliable and accurate
- ✅ ~7-8s per image is acceptable

### Ollama for Vision & Embeddings
- ✅ Local inference (no API calls)
- ✅ GPU-accelerated
- ✅ Easy model management
- ✅ Consistent interface

### PostgreSQL + pgvector
- ✅ Robust vector similarity search
- ✅ Hybrid search capabilities
- ✅ Local data storage
- ✅ ACID compliance

## Credits
- **PaddleOCR**: PaddlePaddle Team
- **Qwen3-VL**: Alibaba Cloud
- **bge-m3**: BAAI (Beijing Academy of AI)
- **Ollama**: Ollama.ai
- **Flet**: Flet.dev
- **pgvector**: PostgreSQL extension

## License
Creative Commons NonCommercial (CC BY-NC, CC BY-NC-SA, CC BY-NC-ND)