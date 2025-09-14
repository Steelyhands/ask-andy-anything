import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from chromadb.config import Settings
import shutil

# Error handling for optional dependencies
try:
    import tiktoken
    print("tiktoken available")
except ImportError:
    print("tiktoken not available - running without token counting")
    tiktoken = None

try:
    import langchain
    print("langchain available")
except ImportError:
    print("langchain not available - running without langchain features")
    langchain = None

try:
    import transformers
    print("transformers available")
except ImportError:
    print("transformers not available")
    transformers = None

# Load environment variables
def load_environment():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, '.env')
    
    print(f"Loading .env from: {env_path}")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists(env_path)}")
    
    load_dotenv(env_path)
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    print(f"DEEPSEEK_API_KEY from env: {repr(api_key)}")
    
    if not api_key or api_key == 'your_deepseek_api_key_here':
        print("ERROR: DEEPSEEK_API_KEY not properly set in .env file")
        return False
    return True

# Test DeepSeek API key
def test_deepseek_key(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Hello, are you working?"}],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("API key is working!")
            return True
        else:
            print(f"API error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# ChromaDB setup - Fixed version
def setup_chromadb():
    try:
        # Use absolute path to avoid issues
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chroma_path = os.path.join(current_dir, "chroma_db")
        
        # Clean up any existing problematic database
        if os.path.exists(chroma_path):
            try:
                shutil.rmtree(chroma_path)
                print("Removed old ChromaDB database due to version incompatibility")
            except Exception as e:
                print(f"Error removing old database: {e}")
        
        client = chromadb.PersistentClient(path=chroma_path)
        
        # List all available collections
        collections = client.list_collections()
        print(f"Available collections: {[col.name for col in collections]}")
        
        # Try to get existing collection or create new one
        try:
            collection = client.get_collection("andy_knowledge_base")
            print("Connected to existing collection: andy_knowledge_base")
        except:
            collection = client.create_collection("andy_knowledge_base")
            print("Created new collection: andy_knowledge_base")
        
        return collection
        
    except Exception as e:
        print(f"Error setting up ChromaDB: {e}")
        # Try to create a simple client without complex operations
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            chroma_path = os.path.join(current_dir, "chroma_db")
            client = chromadb.PersistentClient(path=chroma_path)
            collection = client.create_collection("andy_knowledge_base")
            print("Created basic ChromaDB collection after initial error")
            return collection
        except Exception as inner_e:
            print(f"Failed to create ChromaDB collection: {inner_e}. Running without vector database.")
            return None

# Load document into ChromaDB - UPDATED TO CHECK my_data FOLDER
def load_document_to_chroma(collection):
    try:
        # Look for MLTrainingDoc.txt in my_data folder first, then current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        doc_paths = [
            os.path.join(current_dir, "my_data", "MLTrainingDoc.txt"),  # First check my_data folder
            os.path.join(current_dir, "MLTrainingDoc.txt")  # Then check current directory
        ]
        
        doc_path = None
        for path in doc_paths:
            if os.path.exists(path):
                doc_path = path
                break
        
        if not doc_path:
            print("MLTrainingDoc.txt not found in my_data folder or current directory. Running without document context.")
            return
        
        print(f"Found document at: {doc_path}")
        
        with open(doc_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if not content.strip():
            print("MLTrainingDoc.txt is empty. Running without document context.")
            return
        
        # Split into chunks (simple implementation)
        chunk_size = 1000
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        chunks = [chunk for chunk in chunks if chunk.strip()]  # Remove empty chunks
        
        # Add to ChromaDB if not already loaded
        try:
            existing_ids = collection.get()['ids']
            if not existing_ids:
                ids = [f"chunk_{i}" for i in range(len(chunks))]
                collection.add(
                    documents=chunks,
                    ids=ids
                )
                print(f"Loaded {len(chunks)} chunks into ChromaDB from {os.path.basename(doc_path)}")
            else:
                print(f"Document already loaded with {len(existing_ids)} chunks")
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}. Continuing without document context.")
            
    except Exception as e:
        print(f"Error loading document: {e}. Running without document context.")

# Initialize Flask app
app = Flask(__name__)

frontend_url = "https://andy-chatbot-frontend.onrender.com"
backend_url = "https://andy-chatbot-backend.onrender.com"

if os.environ.get('FLASK_ENV')== "production":
    CORS(app, origins=[frontend_url, backend_url])
else:
    CORS(app)

# Load environment and test API
print("=" * 50)
print("Initializing backend...")
print("=" * 50)

if load_environment():
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        print("Testing DeepSeek API key...")
        test_deepseek_key(api_key)
    else:
        print("No API key found")
else:
    print("Failed to load environment variables")

# Setup ChromaDB
print("Setting up ChromaDB...")
chroma_collection = setup_chromadb()

# Load document if ChromaDB is available
if chroma_collection:
    print("Loading document into ChromaDB...")
    load_document_to_chroma(chroma_collection)
else:
    print("Running without ChromaDB vector database")

# DeepSeek API function
def ask_deepseek(question, context=""):
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return "Error: API key not configured. Please check your .env file."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_content = "You are Andy. Answer questions about yourself based on the provided context. If the context doesn't contain relevant information, say you don't have that information rather than making things up."
    if context:
        system_content += f" Context: {context}"
    else:
        system_content += " Since no specific context was provided, answer based on your general knowledge but identify yourself as Andy."
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_msg = f"API Error: Status {response.status_code}"
            if response.status_code == 401:
                error_msg += " - Invalid API key. Please check your DEEPSEEK_API_KEY in .env file."
            elif response.status_code == 429:
                error_msg += " - Rate limit exceeded or insufficient credits."
            else:
                error_msg += f" - {response.text}"
            return error_msg
            
    except Exception as e:
        return f"Network Error: {str(e)}"

# Flask routes
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({
                'response': "Please provide a question",
                'success': False
            })
        
        print(f"Received question: {question}")
        
        # Search for relevant context in ChromaDB if available
        context = ""
        if chroma_collection:
            try:
                results = chroma_collection.query(
                    query_texts=[question],
                    n_results=3
                )
                
                # Combine the context
                if results['documents'] and results['documents'][0]:
                    context = "\n".join(results['documents'][0])
                    print(f"Found context: {context[:100]}..." if context else "No context found")
                else:
                    print("No relevant context found in ChromaDB")
            except Exception as e:
                print(f"Error querying ChromaDB: {e}. Continuing without context.")
        else:
            print("No ChromaDB available - using general knowledge")
        
        # Use context when asking DeepSeek
        response = ask_deepseek(question, context)
        
        print(f"Generated response: {response[:100]}..." if len(response) > 100 else f"Generated response: {response}")
        
        return jsonify({
            'response': response,
            'success': True
        })
        
    except Exception as e:
        error_msg = f"Server Error: {str(e)}"
        print(error_msg)
        return jsonify({
            'response': error_msg,
            'success': False
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    api_key = os.getenv('DEEPSEEK_API_KEY')
    
    # Check if document exists in either location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    doc_exists_my_data = os.path.exists(os.path.join(current_dir, "my_data", "MLTrainingDoc.txt"))
    doc_exists_current = os.path.exists(os.path.join(current_dir, "MLTrainingDoc.txt"))
    doc_exists = doc_exists_my_data or doc_exists_current
    
    return jsonify({
        'status': 'healthy',
        'api_configured': bool(api_key),
        'api_key_valid': api_key is not None and api_key != 'your_deepseek_api_key_here',
        'chromadb_connected': chroma_collection is not None,
        'document_loaded': chroma_collection is not None and bool(chroma_collection.get()['ids']) if chroma_collection else False,
        'document_exists': doc_exists,
        'document_location': 'my_data' if doc_exists_my_data else 'current' if doc_exists_current else 'not_found'
    })

@app.route('/api/debug', methods=['GET'])
def debug_info():
    api_key = os.getenv('DEEPSEEK_API_KEY')
    
    # Check document locations
    current_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path_my_data = os.path.join(current_dir, "my_data", "MLTrainingDoc.txt")
    doc_path_current = os.path.join(current_dir, "MLTrainingDoc.txt")
    
    doc_exists_my_data = os.path.exists(doc_path_my_data)
    doc_exists_current = os.path.exists(doc_path_current)
    doc_size_my_data = os.path.getsize(doc_path_my_data) if doc_exists_my_data else 0
    doc_size_current = os.path.getsize(doc_path_current) if doc_exists_current else 0
    
    return jsonify({
        'api_key_exists': bool(api_key),
        'api_key_prefix': api_key[:10] + '...' if api_key else None,
        'current_directory': os.getcwd(),
        'env_file_exists': os.path.exists('.env'),
        'chromadb_status': 'connected' if chroma_collection else 'disconnected',
        'document_exists_my_data': doc_exists_my_data,
        'document_exists_current': doc_exists_current,
        'document_size_my_data': doc_size_my_data,
        'document_size_current': doc_size_current,
        'chromadb_path': os.path.join(os.getcwd(), "chroma_db") if chroma_collection else None
    })

@app.route('/api/reset-chroma', methods=['POST'])
def reset_chroma():
    """Endpoint to reset ChromaDB (useful for development)"""
    try:
        global chroma_collection
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chroma_path = os.path.join(current_dir, "chroma_db")
        
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            print("Reset ChromaDB database")
        
        chroma_collection = setup_chromadb()
        if chroma_collection:
            load_document_to_chroma(chroma_collection)
        
        return jsonify({
            'success': True,
            'message': 'ChromaDB reset successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resetting ChromaDB: {str(e)}'
        })

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Flask server...")
    print("Server will be available at: http://localhost:5000")
    print("API endpoints:")
    print("  - POST /api/chat")
    print("  - GET  /api/health")
    print("  - GET  /api/debug")
    print("  - POST /api/reset-chroma")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)