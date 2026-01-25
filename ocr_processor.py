import os
import base64
from datetime import datetime
from dotenv import load_dotenv
import requests
from PIL import Image
import ollama
import psycopg2
from typing import Optional, Tuple
import unicodedata
from paddleocr import PaddleOCR
import logging

# Disable PaddleOCR logging to keep console clean
logging.getLogger("ppocr").setLevel(logging.ERROR)

# Initialize PaddleOCR (Using CPU mode - reliable and fast enough for this use case)
# GPU mode requires CUDA 11.8, but CPU mode works well (~3-5s per image)
ocr_engine = PaddleOCR(use_angle_cls=True, lang='korean', use_gpu=False, show_log=False)

# Load variables from .env
load_dotenv()

def are_models_loaded():
    """For Ollama, we assume it's running if we can reach it."""
    try:
        ollama.list()
        return True
    except Exception:
        return False

def are_models_loading():
    """Ollama models load on demand."""
    return False

class OllamaClient:
    """Client for Ollama API interactions and bge-m3 embeddings."""

    def __init__(self, host: str = None):
        self.host = host or os.getenv("LOCAL_LLM_API_URL")
        self.model = os.getenv("LOCAL_LLM_MODEL", "qwen3-vl:30b")
        self.embedding_model_name = "bge-m3:latest"

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """List available models."""
        try:
            return [m.model for m in ollama.list().models]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def generate_embedding(self, text: str) -> Optional[list[float]]:
        """Generate embedding for text using Ollama's bge-m3."""
        if not text or not text.strip():
            return None

        import time
        start_time = time.time()
        try:
            response = ollama.embeddings(
                model=self.embedding_model_name, 
                prompt=text,
                options={'num_ctx': 2048},
                keep_alive="10m"
            )
            elapsed = time.time() - start_time
            if elapsed > 0.5: # Only log slow ones
                print(f"    Embedding took {elapsed:.2f}s")
            return response['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def generate_embeddings_with_chunks(self, text: str) -> list[Tuple[int, list[float]]]:
        """Generate embeddings for text chunks using Ollama."""
        if not text or not text.strip():
            return []

        chunks = self.chunk_text(text)
        print(f"Text divided into {len(chunks)} chunks")

        results = []
        try:
            for i, chunk in enumerate(chunks):
                emb = self.generate_embedding(chunk)
                if emb:
                    results.append((i, emb))
            return results
        except Exception as e:
            print(f"Batch embedding error: {e}")
            return []

    def chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 100) -> list[str]:
        """Split long text into overlapping chunks for embedding."""
        if not text or len(text) <= max_chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            end = start + max_chunk_size

            if end < len(text):
                for break_char in ['\n\n', '\n', '. ', ', ']:
                    break_pos = text.rfind(break_char, start + max_chunk_size // 2, end)
                    if break_pos > start:
                        end = break_pos + len(break_char)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap


        return chunks

def get_paddle_ocr_text(image_path: str) -> str:
    """Extract text using PaddleOCR with GPU acceleration."""
    import time
    import cv2
    import numpy as np
    start_time = time.time()
    try:
        print(f"  PaddleOCR Extraction...")
        # Use cv2.imdecode to safely read paths with non-ASCII characters
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"    Error: Could not read image at {image_path}")
            return ""
            
        result = ocr_engine.ocr(img, cls=True)
        
        elapsed = time.time() - start_time
        if not result or not result[0]:
            print(f"    PaddleOCR returned no text (took {elapsed:.2f}s)")
            return ""
            
        # Extract text and join with spaces
        lines = []
        for line in result[0]:
            lines.append(line[1][0])
            
        full_text = " ".join(lines)
        print(f"    PaddleOCR complete in {elapsed:.2f}s ({len(lines)} lines)")
        
        # Print OCR results for verification
        print("\n--- OCR RESULTS START ---")
        for idx, line in enumerate(lines, 1):
            print(f"{idx:2d}. {line}")
        print("--- OCR RESULTS END ---\n")
        
        return full_text
    except Exception as e:
        print(f"PaddleOCR error: {e}")
        return ""

def get_ai_description(image_path: str) -> Tuple[str, str]:
    """Retrieve only a description from the vision model."""
    import time
    from PIL import Image
    import io
    
    start_time = time.time()
    try:
        model = os.getenv("LOCAL_LLM_MODEL", "qwen3-vl-4b-gpu-only")
        print(f"  AI Vision Description using {model}...")
        
        # 1. Optimize Image for Vision
        with Image.open(image_path) as img:
            max_size = 1620 
            if max(img.size) > max_size:
                scale = max_size / max(img.size)
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            image_data = buf.getvalue()
            
        # 2. Optimized Description Prompt
        prompt = (
            "Provide a clear and professional summary of this screenshot in 8-10 sentences as well as texts up to 100 words. "
            "Identify the primary application(s) visible and describe the user’s main activity. "
            "Highlight key on-screen content with specificity. "
            "Ensure the description is accurate, concise, and contextually informative."
        )
        
        response_stream = ollama.chat(
            model=model,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_data]
            }],
            options={
                'num_ctx': 4096, 
                'num_gpu': 99,
            },
            keep_alive="10m",
            stream=True
        )
        
        description = ""
        print("\n--- AI DESCRIPTION START ---")
        for chunk in response_stream:
            chunk_content = chunk['message']['content']
            description += chunk_content
            print(chunk_content, end='', flush=True)
        print("\n--- AI DESCRIPTION END ---\n")
        
        elapsed = time.time() - start_time
        print(f"    Vision Description complete in {elapsed:.2f}s")
        
        return description.strip(), model
    except Exception as e:
        print(f"Error during vision analysis: {e}")
        return "", ""

def get_ocr_confidence(image_path: str) -> float:
    """Ollama doesn't return per-token confidence easily. Returning 1.0 for now."""
    return 1.0

def check_for_duplicate_image(filepath: str) -> Optional[int]:
    """Check if an image with the given filepath already exists and return its ID."""
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        
        select_query = "SELECT id FROM images WHERE filepath = %s"
        cursor.execute(select_query, (filepath,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return None

    except Exception as e:
        print(f"Error checking for duplicate image: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def store_image_data(filename: str, filepath: str, timestamp: datetime, ai_description: str = None, model_name: str = None) -> int:
    """Store image metadata in database and return the image_id."""
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO images (filename, filepath, timestamp, ai_description, model_name) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING id
        """
        cursor.execute(insert_query, (filename, filepath, timestamp, ai_description, model_name))
        image_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Stored image metadata with ID: {image_id}")
        return image_id

    except Exception as e:
        print(f"Error storing image metadata: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return None
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

def store_ocr_results(image_id: int, text: str, confidence: float) -> bool:
    """Store OCR results in database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO ocr_results (image_id, text, confidence) VALUES (%s, %s, %s)",
            (image_id, text, float(confidence))
        )
        conn.commit()
        print(f"Stored OCR results for image {image_id}")
        return True

    except Exception as e:
        print(f"Error storing OCR results: {e}")
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

def store_embeddings(image_id: int, embeddings: list[Tuple[int, list[float]]]) -> bool:
    """Store embeddings with chunk indices in database."""
    if not embeddings:
        return False

    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cursor = conn.cursor()

        for chunk_index, embedding in embeddings:
            embedding_list = [float(x) for x in embedding]
            cursor.execute(
                "INSERT INTO text_embedding (image_id, embedding, chunk_index) VALUES (%s, %s, %s)",
                (image_id, embedding_list, chunk_index)
            )

        conn.commit()
        print(f"Stored {len(embeddings)} embeddings for image {image_id}")
        return True

    except Exception as e:
        print(f"Error storing embeddings: {e}")
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

def process_image_to_db(image_path: str) -> tuple[bool, str]:
    """
    Process image and store in database.
    Returns: (success: bool, reason: str)
    """
    image_id = check_for_duplicate_image(image_path)
    if image_id:
        print(f"Skipping duplicate image: {image_path}")
        return True, "duplicate"
    
    # 1. OCR Step (PaddleOCR)
    text = get_paddle_ocr_text(image_path)
    
    # 2. Vision Description Step (Qwen3-VL)
    description, model_name = get_ai_description(image_path)
    
    if not text.strip() and not description.strip():
        print("Both OCR and description failed for the image")
        return False, "ocr_and_vision_failed"

    confidence = get_ocr_confidence(image_path)
    timestamp = datetime.fromtimestamp(os.path.getmtime(image_path))

    # 2. Store Image Meta (including description)
    image_id = store_image_data(os.path.basename(image_path), image_path, timestamp, description, model_name)
    if not image_id:
        return False, "database_error"

    # 4. Store OCR
    if text.strip():
        if not store_ocr_results(image_id, text, confidence):
            print(f"Failed to store OCR for {image_id}")
            # Even if OCR fails, we might still want to proceed with description/embeddings
            # For now, we'll just log and continue.
    else:
        # Create an empty OCR record to satisfy foreign keys
        store_ocr_results(image_id, "[No text extracted]", 0.0)

    # 5. Embeddings
    client = OllamaClient()
    all_embeddings = []
    
    # Embed description as chunk_index -1 (initial/special chunk)
    if description:
        desc_emb = client.generate_embedding(description)
        if desc_emb:
            all_embeddings.append((-1, desc_emb))
            
    # Embed OCR text in chunks (0, 1, 2...)
    if text.strip():
        ocr_embeddings = client.generate_embeddings_with_chunks(text)
        all_embeddings.extend(ocr_embeddings)
        
    if all_embeddings:
        if not store_embeddings(image_id, all_embeddings):
            return False, "embedding_error"
        return True, "success"
    else:
        print("Warning: No embeddings generated for image")
        return False, "no_embeddings"

def search_images(query: str, mode: str = 'hybrid', limit: int = 12) -> list[dict]:
    """Search for images using semantic or keyword search."""
    query = unicodedata.normalize('NFC', query)
    
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()

        results = []
        similarity_threshold = 0.35  # Only show results with at least this similarity
        
        if mode in ['semantic', 'hybrid']:
            client = OllamaClient()
            query_embedding = client.generate_embedding(query)
            
            if query_embedding:
                semantic_query = """
                SELECT 
                    i.id, i.filename, i.filepath, i.timestamp, 
                    COALESCE(o.text, '') as text, COALESCE(o.confidence, 0) as confidence,
                    1 - (te.embedding <=> %s::vector) as similarity,
                    i.ai_description
                FROM images i
                LEFT JOIN ocr_results o ON i.id = o.image_id
                JOIN text_embedding te ON i.id = te.image_id
                WHERE 1 - (te.embedding <=> %s::vector) >= %s
                ORDER BY te.embedding <=> %s::vector
                LIMIT %s
                """
                cursor.execute(semantic_query, (query_embedding, query_embedding, similarity_threshold, query_embedding, limit))
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "filename": row[1],
                        "filepath": row[2],
                        "timestamp": row[3],
                        "text": row[4],
                        "confidence": row[5],
                        "score": row[6],
                        "ai_description": row[7],
                        "type": "semantic"
                    })

        if mode in ['keyword', 'hybrid']:
            keyword_query = """
            SELECT 
                i.id, i.filename, i.filepath, i.timestamp, 
                o.text, o.confidence,
                i.ai_description
            FROM images i
            JOIN ocr_results o ON i.id = o.image_id
            WHERE o.text ILIKE %s OR i.ai_description ILIKE %s
            LIMIT %s
            """
            cursor.execute(keyword_query, (f"%{query}%", f"%{query}%", limit))
            keyword_results = cursor.fetchall()
            
            for row in keyword_results:
                if not any(r['id'] == row[0] for r in results):
                    results.append({
                        "id": row[0],
                        "filename": row[1],
                        "filepath": row[2],
                        "timestamp": row[3],
                        "text": row[4],
                        "confidence": row[5],
                        "score": 1.0,
                        "ai_description": row[6],
                        "type": "keyword"
                    })

        if mode != 'keyword':
            # Deduplicate by image ID (highest score wins)
            unique_results = {}
            for res in results:
                if res['id'] not in unique_results or res['score'] > unique_results[res['id']]['score']:
                    unique_results[res['id']] = res
            
            results = list(unique_results.values())
            results.sort(key=lambda x: x['score'], reverse=True)

        return results[:limit]

    except Exception as e:
        print(f"Search error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
