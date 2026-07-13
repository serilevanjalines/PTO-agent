#  PaidTimeOff Agent

An AI-powered Time-Off Management Agent built with FastAPI, Azure OpenAI, and Hybrid Retrieval.

The assistant helps employees answer leave policy questions, check leave balances, and view leave requests using Retrieval-Augmented Generation (RAG) and OpenAI Tool Calling.

---

## Features

###   Leave Policy Assistant
- Answers company leave policy questions using Hybrid RAG
- Country-aware policy retrieval
- Supports Annual Leave, Sick Leave and Parental Leave policies

###  Leave Balance
- Retrieves employee leave balances
- Automatically identifies the authenticated employee

###  Leave Requests
- Lists previous leave requests
- Filters results based on the authenticated employee

###  Planned
- Leave request submission
- Multi-tool reasoning
- Conversation memory
- LangGraph workflow orchestration
- AI Evaluation framework

---

## Tech Stack

- FastAPI
- Azure OpenAI
- ChromaDB
- BM25
- Sentence Transformers
- Python
- LangGraph (WIP)

---

# Workflow

```
                   User
                     │
                     ▼
             Azure OpenAI
                     │
         ┌───────────┴───────────┐
         │                       │
    Normal Response         Tool Required
                                 │
                                 ▼
                     ┌────────────────────┐
                     │ Tool Calling       │
                     └────────────────────┘
                                 │
        ┌──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼
 Search Policy   Check Balance   Leave Requests
        │
        ▼
   Hybrid Retrieval
        │
   ┌───────────────┐
   │ Semantic      │
   │ Retrieval     │
   ├───────────────┤
   │ BM25 Search   │
   └───────────────┘
        │
        ▼
 Reciprocal Rank Fusion
        │
        ▼
 Retrieved Context
        │
        ▼
 Azure OpenAI Response
```

---

# Why Hybrid Retrieval?

The project combines **Semantic Search** and **BM25** because each approach solves a different problem.

### Semantic Search
- Understands the meaning of a query
- Finds conceptually similar policies
- Handles paraphrased questions

Example:

> "How much PTO do I receive?"

can still retrieve

> "Annual Leave Policy"

even if the words don't exactly match.

---

### BM25

BM25 is a keyword-based ranking algorithm.

It excels when users mention exact policy names or important keywords such as

- annual leave
- maternity leave
- sick leave
- carry over
- PTO

Keyword matching often outperforms embeddings for these cases.

---

### Reciprocal Rank Fusion (RRF)

Instead of relying on only one retrieval method, the project combines the rankings from both Semantic Search and BM25 using Reciprocal Rank Fusion.

This improves retrieval robustness by returning documents that are consistently ranked highly by both methods.

---

# Current Status

-  Tool Calling
-  Hybrid RAG
-  Country-aware Retrieval
-  ChromaDB
-  BM25
-  Reciprocal Rank Fusion
-  Leave Balance
-  Leave Requests

 # Pending :

-  Leave Submission
-  LangGraph
-  Conversation Memory
-  Multi-tool Reasoning
