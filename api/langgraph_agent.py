"""
LangGraph Agent Implementation for PDF RAG
"""

import os
import base64
import requests
import uuid
from typing import List, Annotated, TypedDict, Dict, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END, START, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from tavily import TavilyClient
from openai import OpenAI
from pathlib import Path

# LangSmith tracing imports
try:
    from langsmith import traceable
    from langchain.callbacks.tracers import LangChainTracer
    LANGSMITH_AVAILABLE = True
except ImportError:
    # Create a no-op decorator if LangSmith is not available
    def traceable(name=None, run_type=None, **kwargs):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False

class AgentState(TypedDict):
    """State of the agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    newsletter_content: str = ""

class PDFAgent:
    """LangGraph-based agent for PDF Q&A with tool calling"""
    
    def __init__(self, pdf_databases: dict):
        self.pdf_databases = pdf_databases
        self.summary = None
        self.quotes = None
    
    def create_tavily_tool(self, tavily_api_key: str):
        """Create a Tavily web search tool"""
        @tool
        def tavily_search_tool(query: str):
            """Use this tool to search the web for current information, news, or topics not covered in the PDF"""
            try:
                print(f"🌐 Tavily Search: Searching web for '{query[:50]}...'")
                
                # Initialize Tavily client
                client = TavilyClient(api_key=tavily_api_key)
                
                # Search the web
                results = client.search(query, max_results=3)
                
                # Format results
                search_results = []
                for result in results.get('results', []):
                    search_results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'content': result.get('content', '')[:500] + '...' if len(result.get('content', '')) > 500 else result.get('content', '')
                    })
                
                formatted_results = {
                    "web_results": search_results,
                    "query": query,
                    "results_count": len(search_results),
                    "status": "success"
                }
                
                print(f"🌐 Tavily Search: Found {len(search_results)} web results")
                
                return formatted_results
                
            except Exception as e:
                error_result = {
                    "error": f"Error searching web: {str(e)}",
                    "status": "error",
                    "query": query
                }
                print(f"❌ Tavily Error: {str(e)}")
                return error_result
        
        return tavily_search_tool
    
    def create_pdf_rag_tool(self, pdf_id: str):
        """Create a RAG tool specific to the transcript of podcast"""
        @tool
        def pdf_rag_tool(question: str):
            """Use this tool to answer questions about the uploaded transcript of podcast"""
            try:
                print(f"📄 PDF RAG Tool: Searching PDF for '{question[:50]}...'")
                
                if pdf_id not in self.pdf_databases:
                    print(f"❌ PDF RAG Tool: PDF {pdf_id} not found")
                    return {"error": "PDF not found"}
                
                pdf_data = self.pdf_databases[pdf_id]
                vector_db = pdf_data['vector_db']
                
                # Retrieve relevant chunks
                relevant_chunks = vector_db.search_by_text(question, k=3, return_as_text=True)
                context = "\n\n".join(relevant_chunks)
                
                print(f"📄 PDF RAG Tool: Found {len(relevant_chunks)} relevant chunks from '{pdf_data['filename']}'")
                
                return {
                    "context": context,
                    "source": pdf_data['filename'],
                    "chunks_found": len(relevant_chunks)
                }
            except Exception as e:
                return {"error": f"Error retrieving PDF context: {str(e)}"}
        
        return pdf_rag_tool
    
    def create_podcast_summary_tool(self, pdf_id: str, openai_api_key: str):
        """Create a podcast summary tool that uses OpenAI to summarize podcast transcript content"""
        @tool
        def podcast_summary_tool(summary_request: str = "Please provide a comprehensive summary of this podcast"):
            """Use this tool to get a summary of the entire podcast transcript. Useful when the user asks for an overview, key insights, main topics, or wants to understand what the podcast episode is about without listening to the full episode."""
            if self.summary:
                return {"summary": self.summary, "source": pdf_id, "status": "success"}
            try:
                print(f"📋 Podcast Summary Tool: Generating summary for podcast '{pdf_id}'")
                
                if pdf_id not in self.pdf_databases:
                    print(f"❌ Podcast Summary Tool: Podcast {pdf_id} not found")
                    return {"error": "Podcast transcript not found"}
                
                pdf_data = self.pdf_databases[pdf_id]
                original_text = pdf_data.get('original_text', '')
                
                if not original_text:
                    print(f"❌ Podcast Summary Tool: No transcript text found for podcast {pdf_id}")
                    return {"error": "Podcast transcript not available"}
                
                truncated_text = original_text
                
                # Create podcast summary prompt
                system_prompt = """You are a skilled storyteller and summarizer. Your task is to take a podcast transcript and create a story-based summary about the guest that feels engaging, inspiring, and educational — not just a recap.

Steps to follow:
Introduction: Start with who the guest is (background, achievements, why they are notable/famous/successful).
Hero's Journey Story: Write the guest's story as a narrative arc:
Early beginnings / struggles
Key turning points or breakthroughs
Major successes and failures
Where they are today
Philosophy & Insights: Explain the guest's core beliefs, mindset, and strategies that contributed to their success.How/why did the guest have this philosophy? 
Tone & Style:
Story-driven, engaging, and motivational
Concise but vivid
Written for someone who hasn't heard the podcast
Output Format Example:
Who is [Guest]? (short intro)
Their Story (narrative arc)
Philosophy & Key Learnings (summary of their mindset/approach)

Format your summary using markdown with clear headers, bullet points, and emojis for easy scanning. Make it engaging and help the reader decide if they want to listen to the full episode."""

                user_prompt = f"""Please create an engaging podcast summary of the following transcript:

**Podcast File**: {pdf_data['filename']}

**Transcript Content**:
{truncated_text}
"""

                # Use OpenAI to generate summary
                from langchain_openai import ChatOpenAI
                
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    openai_api_key=openai_api_key,
                    temperature=0.3
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = llm.invoke(messages)
                summary = response.content
                
                # Save summary to class member field
                self.summary = summary
                
                print(f"📋 Podcast Summary Tool: Generated and saved summary for '{pdf_data['filename']}' ({len(summary)} characters)")
                
                return {
                    "summary": summary,
                    "source": pdf_data['filename'],
                    "original_length": len(original_text),
                    "summary_length": len(summary),
                    "truncated": "false"
                }
                
            except Exception as e:
                print(f"❌ Podcast Summary Tool Error: {str(e)}")
                return {"error": f"Error generating podcast summary: {str(e)}"}
        
        return podcast_summary_tool
    
    def create_podcast_quotes_tool(self, pdf_id: str, openai_api_key: str):
        """Create a podcast quotes extraction tool that finds the most impactful quotes"""
        @tool
        def podcast_quotes_tool(quotes_request: str = "Extract the most memorable and impactful quotes from this podcast"):
            """Use this tool to extract golden quotes and memorable statements from the podcast transcript. Perfect for when users want the most quotable moments, wisdom, or standout insights from the conversation."""
            if self.quotes:
                return {"quotes": self.quotes, "source": pdf_id, "status": "success"} 
            try:
                print(f"💎 Podcast Quotes Tool: Extracting golden quotes from podcast '{pdf_id}'")
                
                if pdf_id not in self.pdf_databases:
                    print(f"❌ Podcast Quotes Tool: Podcast {pdf_id} not found")
                    return {"error": "Podcast transcript not found"}
                
                pdf_data = self.pdf_databases[pdf_id]
                original_text = pdf_data.get('original_text', '')
                
                if not original_text:
                    print(f"❌ Podcast Quotes Tool: No transcript text found for podcast {pdf_id}")
                    return {"error": "Podcast transcript not available"}
                
                # Create quotes extraction prompt
                system_prompt = """You are an expert quote curator and podcast analyst. Your task is to identify and extract the most impactful, memorable, and quotable statements from podcast transcripts.

Focus on quotes that are:
- **💡 Insightful**: Contain wisdom, unique perspectives, or profound observations
- **🎯 Actionable**: Provide practical advice or life principles
- **💭 Thought-provoking**: Challenge conventional thinking or spark reflection
- **🌟 Memorable**: Particularly well-articulated or emotionally resonant
- **🔥 Controversial/Bold**: Strong statements that stand out from typical conversation
- **📈 Success-oriented**: About growth, achievement, or overcoming challenges

For each quote:
1. Extract the exact quote with proper context
2. Identify the speaker if possible
3. Categorize the quote (wisdom, advice, insight, etc.)
4. Provide a brief explanation of why it's significant

Return exactly 10 of the best quotes, ordered by impact and memorability."""

                user_prompt = f"""Please extract the top 10 golden quotes from the following podcast transcript:

**Podcast File**: {pdf_data['filename']}

**Transcript Content**:
{original_text}

**Request**: {quotes_request}

Format each quote as:
## Quote [Number]: [Category]
> "[Exact Quote]"
**Speaker**: [Name if identifiable]
**Context**: [Brief explanation of significance]

Focus on finding the most quotable, shareable, and impactful moments from this conversation."""

                # Use OpenAI to extract quotes
                from langchain_openai import ChatOpenAI
                
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    openai_api_key=openai_api_key,
                    temperature=0.2  # Lower temperature for more consistent quote extraction
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = llm.invoke(messages)
                quotes_content = response.content
                
                # Save quotes to class member field
                self.quotes = quotes_content
                
                print(f"💎 Podcast Quotes Tool: Extracted and saved quotes from '{pdf_data['filename']}' ({len(quotes_content)} characters)")
                
                return {
                    "quotes": quotes_content,
                    "source": pdf_data['filename'],
                    "transcript_length": len(original_text),
                    "quotes_length": len(quotes_content),
                    "status": "success"
                }
                
            except Exception as e:
                print(f"❌ Podcast Quotes Tool Error: {str(e)}")
                return {"error": f"Error extracting podcast quotes: {str(e)}"}
        
        return podcast_quotes_tool
    

    def create_newsletter_writer_tool(self, openai_api_key: str):
        """Create a newsletter writing tool """
        @tool
        def newsletter_writer_tool(newsletter_request: str = "Create an engaging newsletter from the podcast summary"):
            """Generate a newsletter based on the podcast summary. Should only be invoked after podcast summary tool has been called."""
            try:
                print(f"📰 Newsletter Writer Tool: Creating newsletter from podcast summary")
                
                if not self.summary:
                    return {"error": "No podcast summary available. Please generate a summary first."}
                
                system_prompt = """You are a professional newsletter writer. Create an engaging, well-structured newsletter based on a podcast summary. Don't ask user any questions, just write the newsletter.

The newsletter should include:
1. **Catchy headline** - attention-grabbing title
2. **Introduction** - hook the reader 
3. **Key insights** - main takeaways from the podcast
4. **Guest highlights** - interesting facts about the guest
5. **Actionable advice** - practical tips readers can apply
6. **Call to action** - encourage engagement

Style: Professional yet conversational, scannable with headers, bullet points, and emojis."""

                user_prompt = f"""Create an engaging newsletter based on this podcast summary:

**Podcast Summary and Quotes**:
{self.summary}
{self.quotes}

**Request**: {newsletter_request}

Generate a complete newsletter that would engage readers and make them want to listen to the full podcast."""

                from langchain_openai import ChatOpenAI
                
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    openai_api_key=openai_api_key,
                    temperature=0.6
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = llm.invoke(messages)
                newsletter = response.content
                
                print(f"📰 Newsletter Writer Tool: Generated newsletter ({len(newsletter)} characters)")
                
                return {
                    "newsletter": newsletter,
                    "newsletter_length": len(newsletter),
                    "status": "success"
                }
                
            except Exception as e:
                print(f"❌ Newsletter Writer Tool Error: {str(e)}")
                return {"error": f"Error generating newsletter: {str(e)}"}
        
        return newsletter_writer_tool
    
    def create_simple_agent_graph(self, pdf_id: str, openai_api_key: str, tavily_api_key: str, model_name: str = "gpt-4o-mini"):
        """Create an agent graph with main tools and newsletter sub-agent"""
        
        # Create main tools
        pdf_tool = self.create_pdf_rag_tool(pdf_id)
        summary_tool = self.create_podcast_summary_tool(pdf_id, openai_api_key)
        quotes_tool = self.create_podcast_quotes_tool(pdf_id, openai_api_key)
        # tavily_tool = self.create_tavily_tool(tavily_api_key)

        # Create newsletter sub-agent tools
        newsletter_writer_tool = self.create_newsletter_writer_tool(openai_api_key)
        
        main_tools = [pdf_tool, summary_tool, quotes_tool, newsletter_writer_tool]

        # Create LLMs with their respective tools
        main_llm = ChatOpenAI(
            model=model_name,
            openai_api_key=openai_api_key,
            temperature=0
        ).bind_tools(main_tools)

        # Define main agent node
        def call_model(state):
            messages = state["messages"]
            response = main_llm.invoke(messages)
            return {"messages": [response]}
        
        # Create graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("agent", call_model)
        graph.add_node("action", ToolNode(main_tools))
        # Add edges
        graph.add_edge(START, "agent")
        
        def should_continue(state):
            messages = state["messages"]
            last_message = messages[-1]
            
            # Check for main tool calls
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                print("invoking action")
                return "action"
            
            return END
        
        graph.add_conditional_edges("agent", should_continue)
        graph.add_edge("action", "agent")
        
        # Compile the graph
        return graph.compile()
    
    @traceable(name="pdf_agent_run")
    async def run_agent(self, pdf_id: str, user_message: str, system_message: str, 
                       openai_api_key: str, tavily_api_key: str, model_name: str = "gpt-4o-mini"):
        """Run the agent and return the final response"""
        
        # Add tracing metadata
        trace_metadata = {
            "pdf_id": pdf_id,
            "model": model_name,
            "user_message_length": len(user_message),
            "system_message_length": len(system_message),
            "session_id": str(uuid.uuid4())
        }
        
        if LANGSMITH_AVAILABLE:
            print(f"🔍 LangSmith trace started for PDF agent run: {trace_metadata}")
        
        # Create the agent graph
        agent_graph = self.create_simple_agent_graph(pdf_id, openai_api_key, tavily_api_key, model_name)
        
        # Prepare messages
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]
        
        # Run the agent
        inputs = {"messages": messages}
        response = await agent_graph.ainvoke(inputs)
        
        # Get the final message
        final_message = response["messages"][-1]
        return final_message.content

    @traceable(name="pdf_agent_stream")
    async def stream_agent(self, pdf_id: str, user_message: str, system_message: str, 
                          openai_api_key: str, tavily_api_key: str, model_name: str = "gpt-4o-mini"):
        """Stream the agent response"""
        
        # Add tracing metadata
        trace_metadata = {
            "pdf_id": pdf_id,
            "model": model_name,
            "user_message_length": len(user_message),
            "streaming": True,
            "session_id": str(uuid.uuid4())
        }
        
        if LANGSMITH_AVAILABLE:
            print(f"🔍 LangSmith trace started for PDF agent stream: {trace_metadata}")
        
        # Create the agent graph
        agent_graph = self.create_simple_agent_graph(pdf_id, openai_api_key, tavily_api_key, model_name)
        
        # Prepare messages
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]
        
        # Stream the agent
        inputs = {"messages": messages}
        
        # Stream updates and yield content
        async for chunk in agent_graph.astream(inputs, stream_mode="updates"):
            for node, values in chunk.items():
                if node == "action":
                    # Extract tool information and yield it to frontend
                    tool_message = values['messages'][0]
                    tool_name = tool_message.name if hasattr(tool_message, 'name') else "Unknown Tool"
                    print(f"Tool Used: {tool_name}")
                    
                    # Send tool information to frontend as a special message
                    yield f"__TOOL_USAGE__{tool_name}__TOOL_USAGE__"
                    
                if node == "agent" and values.get("messages"):
                    message = values["messages"][-1]
                    if hasattr(message, 'content') and message.content:
                        # Yield content incrementally
                        yield message.content 