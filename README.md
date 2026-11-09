
# A.M.I. — Autonomous Maid Intelligence

**A Personal Local AI Assistant**

A.M.I. is a personal AI assistant project designed to run locally on a personal computer using open-source language models.

The project explores local LLM integration, conversational memory, persistent storage, and personalized AI interactions without depending on cloud-based LLM APIs.

> Status: Work in Progress

## About the Project

A.M.I. was created as an experiment in building a personal AI assistant that can operate locally.

The system uses Ollama to run language models and Python to handle backend communication and memory management.

Its conversational persona is called **Yona**.

## Features

- Local LLM integration through Ollama.
- Python-based backend communication.
- Persistent conversation storage using SQLite.
- Basic memory extraction.
- Keyword-based memory retrieval.
- Customizable model configuration.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Ollama | Local LLM runtime |
| Qwen3 4B | Language model |
| SQLite | Persistent storage |
| REST API | Local model communication |

## System Architecture

```text
User Input
    |
    v
Python Backend
    |
    +----> Memory Retrieval
    |          |
    |          v
    |        SQLite
    |
    v
Ollama API
    |
    v
Local Language Model
    |
    v
Yona Response
```

## Project Structure

```text
A.M.I/
├── AI/
├── Backend/
│   ├── main.py
│   ├── memory.py
│   ├── ollama_client.py
│   ├── memory_extractor.py
│   └── check_database.py
├── Config/
├── Database/
├── .gitignore
└── README.md
```

## Planned Improvements

- Improved long-term memory retrieval.
- Better conversational context management.
- More efficient memory storage and indexing.
- Improved response consistency and personality.
- Performance optimization for local hardware.

## Development Notes

A.M.I. is currently an experimental prototype.

Features and architecture may change as development progresses. The project is intended for personal experimentation and learning.

