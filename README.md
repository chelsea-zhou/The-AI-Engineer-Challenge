# 🎙️ Podcast Digest Agent

> AI agent that transforms podcast transcripts into digestible content.

Transform any podcast transcript into golden quotes, engaging summaries, and professional newsletters using advanced AI tools powered by LangGraph and OpenAI.

## Video 
- Demo: https://www.loom.com/share/816c43ba00124d669b755765732200ff
- Architecture & Next step: https://www.loom.com/share/ce849eb64e6f407d92b1a98b024b704e

## Slides
- https://drive.google.com/file/d/11pVXcPR-07YwH3qsEHZ9-wa-VnInbsbl/view

## ✨ Features

- **💎 Quote Extraction** - Find the most memorable and impactful quotes
- **📋 Smart Summaries** - Generate story-driven, engaging podcast summaries  
- **📰 Newsletter Creation** - Transform content into professional newsletters
- **🔄 Real-time Streaming** - Watch AI tools work in real-time with live indicators
- **📱 Responsive Design** - Beautiful, modern interface that works on all devices
- **🎯 One-click Actions** - Quick action cards for instant content generation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key
- Tavily API key (for web search)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/The-AI-Engineer-Challenge.git
   cd The-AI-Engineer-Challenge
   ```

2. **Start the application**
   ```bash
   # Option 1: Use the convenience script
   ./start-app.sh
   
   # Option 2: Run manually
   # Terminal 1 - Backend
   cd api && python -m uvicorn app:app --reload
   
   # Terminal 2 - Frontend
   cd frontend && npm install && npm run dev
   ```

3. **Open your browser**
   ```
   http://localhost:3000
   ```

## 🎯 How to Use

1. **Upload** a podcast transcript (PDF format)
2. **Configure** your API keys in the settings
3. **Choose** from quick actions:
   - Extract golden quotes
   - Summarize the podcast  
   - Write newsletter
4. **Watch** the AI agent work with real-time tool indicators
5. **Get** beautifully formatted results with markdown support

## 🏗️ Architecture

- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **AI Engine**: LangGraph + OpenAI GPT-4
- **Tools**: PDF RAG, Summary Generator, Quote Extractor, Newsletter Writer
- **Caching**: Smart vector database caching for faster responses

## 🔧 Configuration

Set your API keys in the frontend interface:
- **OpenAI API Key**: For AI processing
- **Tavily API Key**: For web search capabilities

## 📁 Project Structure

```
├── api/                 # FastAPI backend
│   ├── app.py          # Main application
│   ├── langgraph_agent.py # AI agent logic
│   └── cache_manager.py # Caching system
├── frontend/           # Next.js frontend
│   └── app/           # Application pages and components
└── start-app.sh       # Quick start script
```

## 🎨 Features in Action

- **Real-time Tool Indicators**: See exactly which AI tool is working
- **Collapsible Cards**: Clean, organized interface
- **Dynamic Chat Height**: Interface adapts as you collapse sections  
- **Streaming Responses**: Watch content generate in real-time
- **Beautiful Markdown**: Rich formatting for all outputs
