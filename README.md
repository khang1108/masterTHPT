# MASTER

> **Multi-Agent System for Teaching, Evaluating & Reviewing**
> 
> An autonomous EdTech platform driven by a deeply collaborative multi-agent architecture. Designed for high school students, MASTER transcends traditional static logic by orchestrating a cohesive ecosystem of 5 specialized AI agents: the **Manager**, **Parser**, **Teacher**, **Verifier**, and **Adaptive Agent**. Exhibiting true agentic capabilities, these entities reason and collaborate dynamically to ingest complex materials, provide cognitive step-by-step hints, cross-verify AI outputs to eliminate hallucinations, and autonomously map out hyper-personalized learning paths using real-time performance data.

<p align="center">
  <a href="https://github.com/khang1108/MASTER---Multi-Agent-System-for-Teaching-Evaluating-Reviewing/stargazers"><img src="https://img.shields.io/github/stars/khang1108/MASTER---Multi-Agent-System-for-Teaching-Evaluating-Reviewing?style=for-the-badge" alt="GitHub stars"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js" alt="Next.js"></a>
  <a href="https://nestjs.com/"><img src="https://img.shields.io/badge/NestJS-10-E0234E?style=for-the-badge&logo=nestjs" alt="NestJS"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python" alt="Python"></a>
  <a href="https://azure.microsoft.com/en-us/products/container-apps"><img src="https://img.shields.io/badge/Deploy-Azure%20Container%20Apps-0078D4?style=for-the-badge&logo=microsoftazure" alt="Azure Container Apps"></a>
</p>

This repository constitutes the primary codebase for the MASTER system. The following sections provide an in-depth understanding of the platform's architecture, underlying technologies, deployment protocols, and knowledge graph integration processes.

## Star History

Tracking the community interest and growth of the repository over time:

[![Star History Chart](https://api.star-history.com/svg?repos=khang1108/MASTER---Multi-Agent-System-for-Teaching-Evaluating-Reviewing&type=Date)](https://star-history.com/#khang1108/MASTER---Multi-Agent-System-for-Teaching-Evaluating-Reviewing&Date)

## Overview and Core Value Proposition

MASTER is developed to address the growing need for personalized learning among high school students. It serves as a centralized repository for examination papers and practice tests categorized by subject, grade level, and exam type. The system supports entrance assessments, maintains a comprehensive history of attempted exams, and allows students to review their performance at any time. Based on previous results and individual learner profiles, MASTER generates tailored recommendations for subsequent study sessions. To ensure seamless development, testing, and deployment, the architecture is decoupled into independent services: the web interface, the API backend, and the sophisticated AI agent service. The current implementation evaluates objective tests deterministically at the API layer, while the agent service is dedicated to advanced tasks such as providing strategic hints, analyzing student mistakes, generating adaptive practice sessions, and orchestrating various AI-driven workflows.

## Key Features and User Interface

The platform offers a robust set of features designed to enhance the educational experience. Users can authenticate securely via email and password or Google OAuth. Upon logging in, students are greeted by a comprehensive dashboard that aggregates their academic profile, exam history, and overall learning performance. The exam library allows students to browse available tests, enter a simulated examination room, and submit their answers. For new students, the system can automatically generate entrance exams tailored to assess their initial proficiency. 

Furthermore, a dedicated practice mode continuously updates the student's backlog of exercises using a specialized adaptive AI agent. During practice, students can request AI-generated hints for specific questions and receive detailed explanations for their mistakes. All exam submissions are recorded in the history module, enabling students to revisit past results, review correct answers, and read question-specific feedback.

![Dashboard Preview Placeholder](assets/overview_page.png)
![Room](assets/room.png)

## System Architecture & Agentic Pipeline

The system architecture follows a modern, decoupled microservices pattern to guarantee scalability and maintainability, driven by an advanced multi-agent orchestration pipeline.

```mermaid
flowchart TD
    %% Define styles
    classDef frontend fill:#1e3a8a,stroke:#ce93d8,stroke-width:2px,color:#fff
    classDef backend fill:#880e4f,stroke:#ffb74d,stroke-width:2px,color:#fff
    classDef agent fill:#ff6f00,stroke:#333,stroke-width:2px,color:#fff,font-weight:bold
    classDef db fill:#004d40,stroke:#80cbc4,stroke-width:2px,color:#fff
    classDef user fill:#33691e,stroke:#a5d6a7,stroke-width:2px,color:#fff
    classDef tools fill:#424242,stroke:#bdbdbd,stroke-width:2px,color:#fff

    subgraph UserLayer [User Layer]
        U(["Student / User"]):::user
    end

    subgraph ServiceLayer [Service Layer : Next.js & NestJS]
        W["Web Frontend<br/>Next.js 14"]:::frontend
        A["API Backend<br/>NestJS 10"]:::backend
        
        U <-->|Interact: Exams, Practice| W
        W <-->|REST API| A
    end

    subgraph AIEcosystem [Multi-Agent AI Ecosystem : Python FastAPI]
        MG["Manager Agent<br/>Orchestrator"]:::agent
        PA["Parser Agent<br/>Extraction"]:::agent
        TE["Teacher Agent<br/>Hints & Review"]:::agent
        VE["Verifier Agent<br/>Anti-Hallucination"]:::agent
        AD["Adaptive Agent<br/>Learning Path"]:::agent
        
        A <-->|Invoke AI Flow| MG
        
        MG -->|Delegate: Structuring Knowledge| PA
        MG -->|Delegate: Tutoring| TE
        TE -->|Cross Check Drafts| VE
        VE -->|Validated Outputs| MG
        MG -->|Delegate: Profiling| AD
    end

    subgraph Persistence [Persistence & External Resources]
        DB[("MongoDB<br/>Prisma ORM")]:::db
        KG[("Knowledge Graph<br/>Concepts & Prereqs")]:::db
        LLM(("LLMs<br/>Gemini / FPT")):::tools
        LS["LangSmith<br/>Tracing & Observability"]:::tools
        Raw["Educational Data<br/>Scrapers"]:::tools

        A <--> DB
        Raw -->|Input Docs| PA
        PA -->|Writes| KG
        AD <-->|Reads Logic Map| KG
        
        MG -.-> LLM
        PA -.-> LLM
        TE -.-> LLM
        VE -.-> LLM
        AD -.-> LLM
        LLM -.-> LS
    end
```

High school students interact with the Next.js App Router-based frontend. These frontend interactions are routed through an internal API proxy to the backend NestJS REST API, securely handling authentication, document management, exam submissions, and profile updates. This data is seamlessly persisted to a MongoDB database leveraging the Prisma ORM. For intelligent functional operations, the NestJS backend communicates with a robust Python-based AI Agent Service. This segment operates via a FastAPI endpoint and coordinates specialized cognitive agents including a Manager, Parser, Teacher, Verifier, and Adaptive logic agent, dynamically integrating Large Language Models (LLMs) and LangSmith tracing.

## Knowledge Graph Construction and Deployment

Building the educational Knowledge Graph is a foundational step in enabling the adaptive learning capabilities of MASTER. The system ingests raw educational materials, such as the digital textbooks stored within the `data/` directory (e.g., mathematics textbooks for varying high school grade levels). Constructing the graph requires initializing the data parsing pipeline located in the `data/scrapers/` module. 

By executing the configured extraction scripts, the system processes these markdown and document files, identifying key educational concepts, logical prerequisites, and learning objectives. The `Parser` AI agent systematically cross-references these newly identified concepts to establish semantic linkages, constructing a definitive network of knowledge. This resulting graph is subsequently persisted into the database, serving as the core reference model for the `Adaptive` agent. When a student takes an exam, the Adaptive agent traverses this Knowledge Graph to pinpoint the exact foundational gaps in their understanding, automatically queuing targeted practice content synchronized with their specific developmental needs.

![Knowledge Graph](assets/knowledge_graph.png)

## Usage and Local Development Instructions

To begin utilizing the platform in a local development context, Docker Compose provides the most stable methodology. Developers must first configure their environment variables by duplicating the `infra/.env.example` templates into specific file environments for the API, Web, and AI segments.

1. **Configure Environment Variables:**
```bash
cp infra/.env.example infra/.env.api
cp infra/.env.example infra/.env.web
cp infra/.env.example infra/.env.ai
```
*(Ensure you update the newly created files with your MongoDB keys, Google OAuth client secrets, and preferred LLM provider details)*

2. **Initialize the Docker Stack:**
```bash
docker compose -f infra/docker-compose-web.yml up --build
```
When the containers successfully deploy, the user interface immediately becomes accessible via the standard local port 3000, while the API health statuses can be monitored at ports 3001 and 8000 respectively.

3. **Alternative Manual Setup (Without Docker):**
Engineers seeking to focus on distinct subsystems can instantiate the services manually.

**For the Backend API (NestJS):**
```bash
cd master/apps/api
npm install
npx prisma generate
npm run start:dev
```

**For the Frontend Web (Next.js):**
```bash
cd master/apps/web
npm install
npm run dev
```

**For the AI Agent Service (Python):**
```bash
cd master/agents
pip install -r requirements.txt
pytest
```

## Comprehensive Technology Stack

| Layer              | Technology                       | Key Features & Responsibilities                                                |
| ------------------ | -------------------------------- | ------------------------------------------------------------------------------ |
| **Frontend**       | Next.js 14, React 18, TypeScript | App Router, type-safety, responsive user interface                             |
| **Backend**        | NestJS 10                        | Modular architecture, secure RESTful API, validation pipes, JWT                |
| **Database**       | MongoDB, Prisma ORM              | Relational and document-based concepts mapping, secure clustering              |
| **AI Service**     | Python 3.12, FastAPI             | Endpoint orchestration for Manager, Parser, Teacher, Verifier, Adaptive agents |
| **AI Framework**   | LangChain, LangGraph             | Complex multi-agent workflow orchestration                                     |
| **Infrastructure** | Docker, Docker Compose           | Container-native ideology, local development configuration                     |
| **Deployment**     | Azure Container Apps             | Robust execution environments, seamless transitions                            |

## Production Azure Deployment

The repository integrates an automated Continuous Integration and Continuous Deployment pipeline using GitHub Actions, tailored directly for Microsoft Azure. Triggered by a primary branch push or a manual workflow dispatch, the pipeline actively builds the distinct Docker images and securely pushes them into an Azure Container Registry (ACR).

Subsequently, the Azure Container Apps are thoroughly updated with the latest revisions alongside their isolated secure environment variables via GitHub Secrets. Required keys include Azure subscription identifiers, registry login paths, database uniform resource identifiers, and LLM access tokens. This serverless container deployment strictly guarantees isolated execution, rapid scaling capabilities during high-traffic examination periods, and built-in observability with an integrated LangSmith tracing protocol activated natively across the AI containers.

## Contributors

We welcome and appreciate all contributions to the MASTER platform. Thank you to everyone who has helped build this project!

<a href="https://github.com/khang1108/MASTER---Multi-Agent-System-for-Teaching-Evaluating-Reviewing/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=khang1108/MASTER---Multi-Agent-System-for-Teaching-Evaluating-Reviewing&max=400&columns=10&anon=1" alt="Contributors list" />
</a>
