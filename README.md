
- [Project Overview](#project-overview)
- [Setup and Installation](#setup-and-installation)
  - [Environment Variables](#environment-variables)
  - [Backend Installation and Usage](#backend-installation-and-usage)
  - [Frontend Installation and Usage](#frontend-installation-and-usage)
- [How to Reproduce the Steps](#how-to-reproduce-the-steps)
- [Deployment Options](#deployment-options)
  - [Local Deployment with Uvicorn and Next.js](#local-deployment-with-uvicorn-and-nextjs)
  - [Docker Compose Example](#docker-compose-example)
  - [Other Hosting Environments](#other-hosting-environments)
- [Detailed Code Walkthrough](#detailed-code-walkthrough)
  - [1. FastAPI Application (Backend)](#1-fastapi-application-backend)
    - [Routers and Endpoints](#routers-and-endpoints)
    - [Services](#services)
  - [2. Next.js Application (Frontend)](#2-nextjs-application-frontend)
    - [Global Layout and Styling](#global-layout-and-styling)
    - [Chat Interface](#chat-interface)
- [Additional Notes](#additional-notes)
- [License](#license)

---

## Project Overview

The **Collaborative Writing Tool** allows a user to supply a message or prompt. A pipeline of **three agents** process the text sequentially:

1. **Idea Agent**: Focuses on creativity, humor, or fresh ideas. Factual accuracy is less emphasized 
2. **FactCheck Agent**: Uses Bing Search to validate references found in the text and rewrite or disclaim inaccuracies.  
3. **Editor Agent**: Polishes style, grammar, flow, and overall cohesiveness, while preserving disclaimers and comedic tone if applicable.

The frontend (Next.js) offers a simple chatbot-style interface where the user can input text and see the pipeline steps in the conversation.

---

## Repository Structure


**Key Highlights:**
- **`backend/app/main.py`**: Creates the FastAPI app, sets up CORS, includes `/api/chat` route.
- **`backend/app/routers/chat.py`**: Defines the `POST /api/chat` endpoint that processes user input via `MultiAgentManager`.
- **`backend/app/services/manager.py`**: Orchestrates the pipeline (Idea -> FactCheck -> Editor).
- **`frontend/app/page.tsx`**: Next.js landing page.
- **`frontend/components/ChatBot.tsx`**: The main UI for chatting with the pipeline.



## Setup and Installation

### Environment Variables

This project relies on a few environment variables for Azure OpenAI and Bing Search. In your `.env` (or environment) you may set:

```bash
# Bing Search
BING_SEARCH_SUBSCRIPTION_KEY=YOUR_BING_KEY
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com

# Azure OpenAI
AZURE_OPENAI_API_KEY=YOUR_AZURE_OPENAI_KEY
AZURE_OPENAI_ENDPOINT=https://your-azure-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT= YOUR_AZURE_DEPLOYMENT
AZURE_OPENAI_VERSION=2024-10-21

# Azure Embeddings
AZURE_OPENAI_EMBEDDING_MODEL=YOUR_EMBEDDING_MODE
```

> **Note**: If these keys are not configured, the FactCheck Agent will fail to look up references, and you’ll see fallback behavior.

### Backend Installation and Usage

1. **Clone the repository**:
    
    ```bash
    git clone https://github.com/your-username/your-repo.git
    cd your-repo/backend
    ```
    
2. **Create and activate a virtual environment** (optional but recommended):
    
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Unix/Mac
    # or for Windows: 
    venv\Scripts\activate
    ```
    
3. **Install dependencies**:
    
    ```bash
    pip install -r requirements.txt
    ```
    
4. **Set up environment variables** (if not using a `.env`):
    
    ```bash
    export BING_SEARCH_SUBSCRIPTION_KEY=...
    export BING_SEARCH_ENDPOINT=...
    export AZURE_OPENAI_API_KEY=...
    # ...and so on...
    ```
    
5. **Run the FastAPI server**:
    
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    
    By default, the API is served at [http://localhost:8000](http://localhost:8000).
    
    * The **root route** (`GET /`) returns a simple welcome JSON.. the entry pont 
    * The **chat endpoint** is at `POST /api/chat`.

### Frontend Installation and Usage

1. **Move to the frontend directory**:
    
    ```bash
    cd ../frontend
    ```
    
2. **Install frontend dependencies**:
    
    ```bash
    npm install
    ```
    
    or
    
    ```bash
    yarn install
    ```
    
3. **Run the Next.js development server**:
    
    ```bash
    npm run dev
    ```
    
    or
    
    ```bash
    yarn dev
    #this is more likely to cause problems/bugs, tested properly
    ```
    
4. **Open** [http://localhost:3000](http://localhost:3000) in your browser
    
    * You’ll see a simple home page.
    * To access the chatbot interface, navigate to the appropriate route (depending on your Next.js file structure). For example, if you put your chatbot at `/chat`, open http://localhost:3000/chat.

* * *

## How to Reproduce the Steps

Once both servers are running:

1. **Navigate** to the frontend in your browser (e.g., http://localhost:3000/chat).
2. **Enter a prompt** in the chatbot input.
3. The backend pipeline processes the prompt in three stages:
    * **Idea Agent** → tries to generate creative content.
    * **FactCheck Agent** → identifies references, does Bing search, and corrects or disclaims inaccuracies
    * **Editor Agent** → polishes the final text that's going to be gen

You will see each agent’s output in a separate “assistant” message block, colored distinctly.

* * *

## Deployment Options

### 1. Local Deployment with Uvicorn and Next.js

* **Run the backend** using `uvicorn app.main:app --reload` on port 8000 (or your chosen port).
* **Run the frontend** using `npm run dev` on port 3000 by default.
* Reverse proxy or unify them behind a tool like Nginx or you could set up CORS properly to connect them.

### 2.Docker and Container Deployment
A `docker-compose.yml` file has already been created in the root directory. You can deploy this project with this command:
```
docker-compose build
docker-compose up
```
This will spin up both containers. You can then visit the [http://localhost:3000](http://localhost:3000) for the frontend, which calls the backend at [http://localhost:8000](http://localhost:8000).

> **Note**: **Single Docker Container Approach** (Optional):  
> If you prefer running both the backend and frontend in the same container, you need to install both Python and Node dependencies in one image, then run
them on different ports. However, using separate containers is typically cleaner.


## Detailed Code Walkthrough

### 1. FastAPI Application (Backend)

#### Routers and Endpoints

**File**: `backend/app/routers/chat.py`

```python
@router.post("", response_model=StepsResponse)
async def chat_with_agents(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = manager.process_user_message(req.message)
    return result
```

* Accepts a `POST` request at `/api/chat`.
* Validates the request body to ensure `message` is not empty.
* Delegates logic to `manager.process_user_message(...)`.

#### Services

1. **`MultiAgentManager`** (`manager.py`):
    * Orchestrates the pipeline.
        1. Sends user text to **IdeaAgent**.
        2. Sends that output to **FactCheckAgent**.
        3. Sends that output to **EditorAgent**.
    * Collects each agent’s response in a `steps` array, returning:
        
        ```json
        { "steps": [ { "role": "...", "color": "...", "content": "..." } ] }
        ```
        
2. **`agents.py`**:
    * **`IdeaAgent`**: Primarily for creativity.
    * **`FactCheckAgent`**:
        * Extracts references from text via GPT.
        * Looks up references with Bing Search.
        * Rewrites text with disclaimers or corrections.
    * **`EditorAgent`**: Polishes style, grammar, and tone.
3. **`vector_store.py`**:
    * Demonstrates using a local **Chroma** store with Azure embeddings.
    * `ChromaVectorStore` class can store text and retrieve similar documents.

### 2. Next.js Application (Frontend)

#### Global Layout and Styling

* **`frontend/app/layout.tsx`** and **`frontend/app/chat/global.css`**: Provide global structure and CSS.
* **`globals.css`**: Common Tailwind or other styling definitions.

#### Chat Interface

**File**: `frontend/components/ChatBot.tsx`  
This is the main **React** component that:

1. Maintains local state for messages (`messages` array).
2. Submits user messages to the backend at `POST /api/chat`.
3. Displays each pipeline step as an “assistant” message with a unique color.

Key parts:

```tsx
const [messages, setMessages] = useState<Message[]>([])

async function handleSubmit(e: FormEvent) {
  // 1) Post user message to /api/chat
  // 2) Receive pipeline steps
  // 3) Insert them into 'messages' state
}
```

* If the server returns an error, the user sees an error message.
* Typing indicator (three dots) is shown while waiting for the pipeline response.

* * *

