# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a clinical trials coordinator application built with LangGraph that helps match patients with relevant clinical trials. The system consists of:

- **Backend**: Python-based LangGraph workflow using FastAPI with WebSocket communication
- **Frontend**: React application built with Vite and Ant Design
- **Vector Database**: ChromaDB for embedding and searching clinical trial data
- **LLM Integration**: Groq API for language model operations

## Development Commands

### Backend (Python)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Run the main workflow directly
python main.py
```

### Frontend (React)
```bash
cd clinical-trials-researcher

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm preview
```

### Docker Deployment
```bash
# Local development
docker-compose -f docker-compose-local.yml up

# Cloudflare deployment
docker-compose -f docker-compose-cf.yml up

# Production deployment
docker-compose up
```

## Architecture Overview

### Backend Workflow (LangGraph)
The application uses a state-based workflow with these key nodes:

1. **consultant**: Initial patient consultation and medical report analysis
2. **prompt_distiller**: Extracts search terms from medical reports
3. **trials_search**: Searches for relevant clinical trials
4. **research_info_search**: RAG-based research using vector database
5. **evaluate_research_info**: Evaluates trial relevance and determines next steps
6. **state_printer**: Final output formatting

**State Structure** (`graph.py:16-41`):
- `medical_report`: Patient medical information
- `search_term`: Generated search terms for trials
- `chat_history`: Conversation history
- `research_info`: RAG search results
- `follow_up`: Follow-up recommendations
- `num_steps`: Workflow step counter
- `next_step`: Next workflow action
- `did_find_trials`: Trial discovery status
- `rag_questions`: Generated research questions

### Communication Layer
- **WebSocket Server** (`server.py`): FastAPI application with CORS support
- **WebSocket Routes** (`websocket_routes.py`): Handles real-time communication with heartbeat
- **Command Handlers** (`command_handlers.py`): Processes WebSocket commands
- **State Manager** (`state_manager.py`): Manages workflow state persistence

### Data Processing
- **RAG System** (`rag.py`): ChromaDB vector database for clinical trial embeddings
- **LLM Integration** (`LLMs/llm.py`): Groq API configuration and embedding models
- **Chains** (`chains/`): LangChain prompt templates and processing chains
- **Nodes** (`nodes/`): Individual workflow node implementations

### Frontend Architecture
- **React + Vite**: Modern build tooling with hot reload
- **Ant Design**: UI component library
- **WebSocket Client**: Real-time communication with backend
- **Component Structure**:
  - `App.jsx`: Main application component
  - `WebSocketClient.jsx`: WebSocket connection management
  - `ChatList.jsx`: Chat interface
  - `FileUploader.jsx`: Medical report upload
  - `ReportCard.jsx`: Trial results display

## Development Workflow

1. **File Upload**: Users upload medical reports (PDF/text)
2. **Consultation**: System analyzes patient information
3. **Search Term Generation**: Extracts relevant medical terms
4. **Trial Search**: Queries clinical trials database
5. **RAG Enhancement**: Uses vector search for additional context
6. **Trial Evaluation**: Assesses trial relevance and eligibility
7. **Results Presentation**: Displays matched trials with explanations

## Key Dependencies

### Backend
- `langgraph`: Workflow orchestration
- `langchain`: LLM integration and document processing
- `chromadb`: Vector database for embeddings
- `fastapi`: Web framework with WebSocket support
- `groq`: LLM API client
- `sentence-transformers`: Text embeddings

### Frontend
- `react`: UI framework
- `antd`: Component library
- `react-markdown`: Markdown rendering
- `uuid`: Unique identifier generation

## File Organization

- `/` - Backend Python application
- `/clinical-trials-researcher/` - React frontend
- `/nodes/` - LangGraph workflow nodes
- `/chains/` - LangChain prompt templates
- `/LLMs/` - Language model configurations
- `/studies/` - Clinical trial data storage (by session)
- `/db/` - ChromaDB vector database (by session)
- `/rag_data/` - Processed RAG documents

## Environment Configuration

The application requires environment variables for:
- Groq API keys
- Database configurations
- Cloudflare tunnel tokens (for deployment)
- CORS origins for development

Sessions are managed by UUID to maintain user isolation and data persistence.

Try to keep code changes as small as reasonably possible.