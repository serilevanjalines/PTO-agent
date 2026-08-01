# PTO Agent

An enterprise-grade AI-powered **Paid Time Off (PTO) Assistant** built using **FastAPI**, **LangGraph**, **Azure OpenAI**, and **Hybrid Retrieval-Augmented Generation (Hybrid RAG)**.

PTO Agent enables employees to interact with their organization's leave management system using natural language. It combines LLM reasoning, tool calling, retrieval-augmented generation, and conversational memory to answer policy questions, retrieve employee information, and automate leave-related workflows.

---

# Overview

PTO Agent is an agentic AI system designed to simplify leave management. Instead of navigating multiple portals or documents, employees can ask questions conversationally, and the agent intelligently determines whether to retrieve company policies, execute backend tools, or request additional information before completing an action.

The project demonstrates modern AI engineering practices including:

* Agentic workflows using LangGraph
* Retrieval-Augmented Generation (RAG)
* Hybrid retrieval with Semantic Search and BM25
* OpenAI Tool Calling
* Persistent conversational memory
* Conversation summarization
* Automated AI evaluation framework

---

# Features

## Leave Policy Assistant (Hybrid RAG)

Answers employee questions using Retrieval-Augmented Generation grounded on company leave policies.

Examples:

* How many annual leave days can employees take?
* What is the sick leave policy?
* Can unused PTO be carried over?

Features:

* Semantic document retrieval
* BM25 keyword retrieval
* Reciprocal Rank Fusion (RRF)
* Country-aware policy retrieval
* Grounded responses using retrieved context

---

## Leave Balance

Retrieves the authenticated employee's leave balance.

Example:

> How many annual leave days do I have?

---

## Leave Request History

Displays previous leave requests for the authenticated employee.

Example:

> Show my previous leave requests.

---

## Leave Submission

Creates new leave requests through natural language.

Example:

> Apply annual leave from August 10 to August 12.

If mandatory information is missing, the agent requests clarification before submitting the request.

---

## Multi-turn Conversations

The agent maintains context across conversations, allowing users to naturally continue previous interactions without repeating information.

Example:

User:

> Apply leave next Monday.

Later:

> The reason is a family event.

---

## Conversation Management

To efficiently support long-running conversations, the agent includes:

* Persistent conversation memory using LangGraph MemorySaver
* Automatic message trimming
* Conversation summarization
* Thread-based conversation state

---

# System Architecture

```text
                          User
                            │
                            ▼
                     FastAPI REST API
                            │
                            ▼
                     LangGraph Agent
                            │
                            ▼
                     Azure OpenAI LLM
                            │
            ┌───────────────┼────────────────┐
            │               │                │
            ▼               ▼                ▼
      search_policy()  check_balance()  Leave Management
                                            Tools
                                             │
                                             ├───────────────┐
                                             ▼               ▼
                                   list_leave_requests() submit_leave_request()
                            │
                            ▼
                   Tool Execution Results
                            │
                            ▼
                     Azure OpenAI LLM
                            │
                            ▼
                    Final AI Response
```

---

# Technology Stack

## Backend

* FastAPI

## Agent Framework

* LangGraph

## Large Language Model

* Azure OpenAI

## Retrieval-Augmented Generation

* ChromaDB

## Embeddings

* SentenceTransformerEmbeddingFunction
* all-MiniLM-L6-v2

## Hybrid Retrieval

* Semantic Search
* BM25
* Reciprocal Rank Fusion (RRF)

## Memory

* LangGraph MemorySaver

## Language

* Python

---

# Why Hybrid Retrieval?

The project combines **Semantic Search** and **BM25** because each retrieval method solves different retrieval problems.

## Semantic Search

Semantic retrieval understands the meaning behind a query rather than relying solely on exact keyword matching.

Example:

> How much PTO do I receive?

can successfully retrieve:

> Annual Leave Policy

even when the wording is different.

Advantages:

* Handles paraphrased questions
* Understands semantic similarity
* Improves retrieval for natural language queries

---

## BM25

BM25 is a keyword-based ranking algorithm.

It performs particularly well when users reference exact policy terminology such as:

* annual leave
* sick leave
* parental leave
* carry over
* PTO

Advantages:

* Excellent keyword matching
* Strong performance for structured policy documents
* Precise retrieval for exact terminology

---

## Reciprocal Rank Fusion (RRF)

Instead of relying on only one retrieval strategy, PTO Agent combines the rankings from Semantic Search and BM25 using Reciprocal Rank Fusion.

Benefits:

* Improves retrieval robustness
* Reduces retrieval failures
* Returns documents consistently ranked highly by both retrieval methods

---

# Retrieval Pipeline

```text
Policy Documents
        │
        ▼
Document Chunking
        │
        ▼
Sentence Embeddings
        │
        ▼
ChromaDB Vector Store
        │
        ├───────────────┐
        ▼               ▼
Semantic Search      BM25 Search
        │               │
        └───────┬───────┘
                ▼
     Reciprocal Rank Fusion
                │
                ▼
      Retrieved Policy Context
                │
                ▼
        Azure OpenAI Response
```

---

# Agent Workflow

1. The user sends a request to the FastAPI API.
2. FastAPI invokes the LangGraph workflow.
3. Azure OpenAI determines whether tool execution is required.
4. If necessary, the agent invokes one or more backend tools.
5. Tool outputs are returned to the language model.
6. The model generates a grounded natural language response.
7. Conversation state is persisted using LangGraph MemorySaver.

---

# Available Tools

| Tool                     | Purpose                                       |
| ------------------------ | --------------------------------------------- |
| `search_policy()`        | Retrieves policy information using Hybrid RAG |
| `check_balance()`        | Returns employee leave balances               |
| `list_leave_requests()`  | Displays previous leave requests              |
| `submit_leave_request()` | Creates new leave requests                    |

---

# AI Evaluation Framework

The project includes a dedicated evaluation framework that executes the **real LangGraph agent** and automatically evaluates its behavior across multiple quality dimensions.

## Evaluation Metrics

### Intent Understanding

Evaluates whether the agent correctly understood the user's objective using an LLM-as-a-Judge approach.

---

### Correctness

Measures whether the final response correctly answers the user's request.

---

### Faithfulness

Ensures every factual statement in the response is supported by retrieved documents or tool outputs, reducing hallucinations.

---

### Response Quality

Evaluates:

* Clarity
* Completeness
* Professionalism
* Readability

---

### Safety & Failure Handling

Evaluates whether the agent:

* Protects sensitive employee information
* Avoids unsupported claims
* Requests missing required information
* Gracefully handles unsupported or ambiguous requests

---

# Evaluation Workflow

```text
Evaluation Dataset
        │
        ▼
Run LangGraph Agent
        │
        ▼
Extract

• Tool Calls
• Tool Outputs
• Final Response

        │
        ▼
Evaluation Rubrics

        │
        ▼
LLM Judge / Rule-based Evaluation

        │
        ▼
JSON Evaluation Reports
```

---

# Project Structure

```text
app/
├── agent_graph.py
├── api.py
├── llm_client.py
├── rag.py
├── state.py
├── tools.py
└── ...

evaluation/
├── datasets/
├── results/
├── agent_runner.py
├── llm_judge.py
├── rubrics.py
├── intent_evaluator.py
├── correctness_evaluator.py
├── faithfulness_evaluator.py
├── response_quality_evaluator.py
└── safety_evaluator.py

data/
├── balances.json
├── employees.json
├── requests.json
└── policy_documents/

README.md
requirements.txt
```

---

# Current Status

## Implemented

* Hybrid Retrieval-Augmented Generation
* ChromaDB Vector Store
* Semantic Search
* BM25 Retrieval
* Reciprocal Rank Fusion
* Azure OpenAI Tool Calling
* LangGraph Agent Workflow
* Leave Policy Assistant
* Leave Balance Retrieval
* Leave Request History
* Leave Submission
* Persistent Conversation Memory
* Message Trimming
* Conversation Summarization
* Automated AI Evaluation Framework

---

# Future Improvements

* Authentication and authorization
* Streaming responses
* Integration with enterprise HR systems
* Support for multiple regional leave policies
* Evaluation dashboard with aggregate metrics
* Performance benchmarking and analytics

---

# Design Principles

The project was developed around the following engineering principles:

* Retrieval-grounded responses to reduce hallucinations
* Modular tool-based agent architecture
* Separation of agent execution and evaluation
* Reusable evaluation pipeline
* Maintainable and extensible codebase
* Production-oriented AI engineering practices

---

# License

This project was developed as part of the **ServiceNow AI.Accelerate Capstone Program** for educational and demonstration purposes.
