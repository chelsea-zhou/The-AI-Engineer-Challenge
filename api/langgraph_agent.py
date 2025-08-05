"""
LangGraph Agent Implementation for PDF RAG
"""

import os
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

class AgentState(TypedDict):
    """State of the agent."""
    messages: Annotated[List[BaseMessage], add_messages]

class PDFAgent:
    """LangGraph-based agent for PDF Q&A with tool calling"""
    
    def __init__(self, pdf_databases: dict):
        self.pdf_databases = pdf_databases
    
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
        """Create a RAG tool specific to a PDF"""
        @tool
        def pdf_rag_tool(question: str):
            """Use this tool to answer questions about the uploaded PDF content"""
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
    
    def create_simple_agent_graph(self, pdf_id: str, openai_api_key: str, tavily_api_key: str, model_name: str = "gpt-4o-mini"):
        """Create a simple agent graph with PDF RAG and web search tools"""
        
        # Create tools
        pdf_tool = self.create_pdf_rag_tool(pdf_id)
        tavily_tool = self.create_tavily_tool(tavily_api_key)
        tools = [pdf_tool, tavily_tool]
        
        # Create the LLM with tools
        llm = ChatOpenAI(
            model=model_name,
            openai_api_key=openai_api_key,
            temperature=0
        ).bind_tools(tools)
        
        # Define agent node
        def call_model(state):
            messages = state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response]}
        
        # Create graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("agent", call_model)
        graph.add_node("action", ToolNode(tools))
        
        # Add edges
        graph.add_edge(START, "agent")
        
        def should_continue(state):
            messages = state["messages"]
            last_message = messages[-1]
            if last_message.tool_calls:
                return "action"
            return END
        
        graph.add_conditional_edges("agent", should_continue)
        graph.add_edge("action", "agent")
        
        # Compile the graph
        return graph.compile()
    
    async def run_agent(self, pdf_id: str, user_message: str, system_message: str, 
                       openai_api_key: str, tavily_api_key: str, model_name: str = "gpt-4o-mini"):
        """Run the agent and return the final response"""
        
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

    async def stream_agent(self, pdf_id: str, user_message: str, system_message: str, 
                          openai_api_key: str, tavily_api_key: str, model_name: str = "gpt-4o-mini"):
        """Stream the agent response"""
        
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
                    print(f"Tool Used: {values['messages'][0].name}")
                if node == "agent" and values.get("messages"):
                    message = values["messages"][-1]
                    if hasattr(message, 'content') and message.content:
                        # Yield content incrementally
                        yield message.content 
                