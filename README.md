# AI Q/A Chatbot

An open source conversational AI assistant, featuring text-to-speech capabilities.

## Project Overview

This repository contains four interconnected projects:

1. **server** - Backend server application
2. **examples** - Sample applications using the server api
3. **chroma** - Vector database for embeddings
4. **api** - JavaScript/TypeScript client library

## Architecture

![Architecture Overview](llm-chatbot-architecture.png)

## Prerequisites

- Node.js (v16 or higher)
- Python (for ChromaDB)
- An ElevenLabs API key (for text-to-speech)
- Ollama installed locally
- ChromaDB installed locally or in a server or in a container

## Server

The server component is a Node.js application for Q/A chatbots with text-to-speech capabilities.

### Setup and Installation

```bash
cd server
npm install
```

### Configuration

Create a `.env` file in the server directory based on the provided `.env.example` template.

### Setting up ChromaDB

Chroma is a vector database used for storing and retrieving embeddings for semantic search and AI operations.

```bash
cd chroma
python -m venv venv 
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** If you have Conda installed and see `(base)` in your terminal prompt, it may interfere with Python venv creation. Run `conda deactivate` before creating venv environments or use `conda config --set auto_activate_base false` to prevent automatic activation.

### Running ChromaDB

```bash
chroma run --host localhost --port 8000 --path ./chroma_db # use 0.0.0.0 is you want to expose the server
```
By default, Chroma will run on port 8000. You can access the Chroma dashboard at `http://localhost:8000`.

To check your ChromaDB version:
```bash
python -c "import chromadb; print(chromadb.__version__)"
```

### Ingesting Data

```bash
python create-chroma-collection.py qa-pairs.json
```

You can test the ingested data with:
```bash
python query-chroma-collection.py "Your test query here"
```

### Testing Text-to-Speech

You can test your ElevenLabs API key with:
```bash
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/XrExE9yKIg1WjnnlVkGX" \
  -H "xi-api-key: $ELEVEN_LABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test audio generation", "model_id": "eleven_monolingual_v1"}' \
  --output test.mp3
```

### Running the Server

```bash
cd server
npm run server -- ollama #or hf for hugging face
```

## API

The API is a JavaScript/TypeScript client library for interacting with the Chatbot server, not a RESTful API service. It provides a convenient interface for applications to communicate with the server.

### Setup and Installation

```bash
cd api
npm install
npm run build
```

The API will be available at `http://localhost:3001`.

## Examples

These are simple web chatbots that interacts with the server using the API.

### Setup and Installation

```bash
cd examples/simple-chatbot
npm install
npm run dev
```
The application will be available at `http://localhost:5173`.


## Integrated Usage

The four components work together as follows:

1. **Client** makes requests to both the **Server** and **API**
2. **API** processes requests and communicates with **Chroma** for vector operations
3. **Server** handles business logic and may also interact with **Chroma**

### Example Workflow

1. User interacts with the **Client** interface
2. **Client** sends requests to the **API**
3. **API** processes the request, potentially querying **Chroma** for vector similarity
4. **API** may communicate with the **Server** for additional processing
5. Results are returned to the **Client** for display

## Development

To run the entire system locally for development:

1. Start Chroma: `cd chroma && chroma run --host localhost --port 8000 --path ./chroma_db`
2. Start the Server: `cd server && npm run server -- ollama`
3. Build the API: `cd api && npm run build`
4. Start the Client: `cd client && npm run dev`

## License

See LICENSE file in the project.
