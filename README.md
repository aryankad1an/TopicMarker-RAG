# TopicMarker-RAG

A powerful Retrieval-Augmented Generation (RAG) backend for generating comprehensive lesson plans and educational content. This application leverages crawl4ai for web scraping and Google's Gemini LLM for content generation.

## Features

- Generate structured topic hierarchies for lesson plans
- Create MDX content from web sources
- Refine content with LLM assistance
- Direct crawling-to-LLM pipeline
- Multiple refinement options with web crawling integration

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TopicMarker-RAG.git
   cd TopicMarker-RAG
   ```

2. Create and activate a virtual environment:

   For Linux/macOS:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   For Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` file contains all the necessary dependencies for this project:
   ```
   fastapi
   uvicorn[standard]
   python-dotenv
   pydantic
   pydantic-settings
   pinecone
   google-generativeai
   crawl4ai
   duckduckgo-search
   requests
   googlesearch-python
   langchain
   langchain-community
   langchain-openai
   openai
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX_NAME=your_pinecone_index_name
   ```

### Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Base Route

- **GET /** - Welcome message
  - Returns: `{"message": "Welcome to the Lesson Plan RAG Backend!"}`

### RAG Routes

#### Topic Generation

- **POST /rag/search-topics**
  - Input: `{"query": "string", "limit": int}` (default limit: 2)
  - Returns: A structured list of main topics and subtopics suitable for a lesson plan
  - Example: `{"status": "success", "data": {"topics": [...]}}`

#### MDX Generation

- **POST /rag/single-topic**
  - Input: `{"topic": "string", "num_results": int}` (default num_results: 2)
  - Returns: Comprehensive MDX content for a single topic
  - Example: `{"status": "success", "data": {"mdx_content": "string", "crawled_websites": [...]}}`

- **POST /rag/single-topic-raw**
  - Input: `{"topic": "string", "num_results": int}` (default num_results: 2)
  - Returns: Raw MDX content as plain text (not JSON)

#### URL-based MDX Generation

- **POST /rag/generate-mdx-from-url**
  - Input: `{"url": "string", "topic": "string", "use_llm_knowledge": bool}`
  - Returns: MDX content generated from the specified URL
  - Example: `{"status": "success", "url": "string", "topic": "string", "mdx_content": "string"}`

- **POST /rag/generate-mdx-from-url-raw**
  - Input: `{"url": "string", "topic": "string", "use_llm_knowledge": bool}`
  - Returns: Raw MDX content as plain text (not JSON)

- **POST /rag/generate-mdx-from-urls**
  - Input: `{"urls": ["string"], "topic": "string", "use_llm_knowledge": bool}`
  - Returns: MDX content generated from multiple URLs
  - Example: `{"status": "success", "urls": [...], "topic": "string", "mdx_content": "string"}`

- **POST /rag/generate-mdx-from-urls-raw**
  - Input: `{"urls": ["string"], "topic": "string", "use_llm_knowledge": bool}`
  - Returns: Raw MDX content as plain text (not JSON)

#### Content Refinement

- **POST /rag/refine**
  - Input: `{"mdx": "string", "question": "string"}`
  - Returns: Refined content using the LLM
  - Example: `{"status": "success", "data": {"answer": "string"}}`

- **POST /rag/refine-with-selection**
  - Input: `{"mdx": "string", "question": "string", "selected_text": "string", "topic": "string"}`
  - Returns: Refined content using the LLM with selected text and topic context
  - Example: `{"status": "success", "data": {"answer": "string"}}`

- **POST /rag/refine-with-selection-raw**
  - Input: `{"mdx": "string", "question": "string", "selected_text": "string", "topic": "string"}`
  - Returns: Raw refined content as plain text (not JSON)

- **POST /rag/refine-with-crawling**
  - Input: `{"mdx": "string", "question": "string", "selected_text": "string", "topic": "string", "num_results": int}` (default num_results: 2)
  - Returns: Refined content by first crawling relevant websites and then using the LLM
  - Example: `{"status": "success", "data": {"answer": "string", "crawled_websites": [...]}}`

- **POST /rag/refine-with-crawling-raw**
  - Input: `{"mdx": "string", "question": "string", "selected_text": "string", "topic": "string", "num_results": int}` (default num_results: 2)
  - Returns: Raw refined content as plain text (not JSON)

- **POST /rag/refine-with-urls**
  - Input: `{"mdx": "string", "question": "string", "selected_text": "string", "topic": "string", "urls": ["string"]}`
  - Returns: Refined content by crawling specific URLs provided by the user
  - Example: `{"status": "success", "data": {"answer": "string", "crawled_websites": [...]}}`

- **POST /rag/refine-with-urls-raw**
  - Input: `{"mdx": "string", "question": "string", "selected_text": "string", "topic": "string", "urls": ["string"]}`
  - Returns: Raw refined content as plain text (not JSON)



## Testing

You can test the API endpoints using the provided test scripts:

```bash
python test_direct_crawl.py
```

To serve a test page for frontend testing:

```bash
python serve_test_page.py
```

## Dependencies

- FastAPI - Web framework
- Uvicorn - ASGI server
- Pydantic - Data validation
- Pinecone - Vector database
- Google Generative AI (Gemini) - LLM
- crawl4ai - Web crawling
- duckduckgo-search - Web search
- googlesearch-python - Google search API
- langchain - LLM framework
- OpenAI - Embeddings for vector search

## License

[MIT License](LICENSE)