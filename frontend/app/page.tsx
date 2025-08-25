'use client'

import { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon, SparklesIcon, DocumentArrowUpIcon, DocumentTextIcon, TrashIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { DEFAULT_OPENAI_API_KEY, DEFAULT_TAVILY_API_KEY } from './api/constants'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface UploadedPDF {
  pdf_id: string
  filename: string
  chunks_count: number
}

// Custom markdown renderer component
const MarkdownRenderer = ({ content }: { content: string }) => {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({inline, className, children, ...props}: any) {
            const match = /language-(\w+)/.exec(className || '')
            return !inline && match ? (
              <SyntaxHighlighter
                style={oneDark as any}
                language={match[1]}
                PreTag="div"
                className="rounded-md"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className="bg-gray-200 dark:bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>
                {children}
              </code>
            )
          },
          h1: ({children}) => <h1 className="text-xl font-bold mb-2">{children}</h1>,
          h2: ({children}) => <h2 className="text-lg font-semibold mb-2">{children}</h2>,
          h3: ({children}) => <h3 className="text-md font-medium mb-1">{children}</h3>,
          p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
          ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
          ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
          img: ({src, alt, ...props}) => (
            <img 
              src={src} 
              alt={alt} 
              className="max-w-full h-auto rounded-lg shadow-md my-4 mx-auto block" 
              {...props}
            />
          ),
          blockquote: ({children}) => (
            <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 dark:text-gray-400 mb-2">
              {children}
            </blockquote>
          ),
          a: ({children, href}) => (
            <a href={href} className="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
          table: ({children}) => (
            <div className="overflow-x-auto mb-2">
              <table className="min-w-full border border-gray-300 dark:border-gray-600">
                {children}
              </table>
            </div>
          ),
          th: ({children}) => (
            <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 bg-gray-100 dark:bg-gray-700 font-semibold text-left">
              {children}
            </th>
          ),
          td: ({children}) => (
            <td className="border border-gray-300 dark:border-gray-600 px-2 py-1">
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [userMessage, setUserMessage] = useState('')
  const [developerMessage, setDeveloperMessage] = useState('')
  const [apiKey, setApiKey] = useState(DEFAULT_OPENAI_API_KEY)
  const [tavilyApiKey, setTavilyApiKey] = useState(DEFAULT_TAVILY_API_KEY)
  const [model, setModel] = useState('gpt-4o-mini')
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedPDFs, setUploadedPDFs] = useState<UploadedPDF[]>([])
  const [selectedPDF, setSelectedPDF] = useState<string>('')
  const [isPDFSectionCollapsed, setIsPDFSectionCollapsed] = useState(false)
  const [isConfigSectionCollapsed, setIsConfigSectionCollapsed] = useState(false)
  const [currentTool, setCurrentTool] = useState<string>('')
  const [isUsingTool, setIsUsingTool] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Load uploaded PDFs on component mount
    loadUploadedPDFs()
  }, [])

  const loadUploadedPDFs = async () => {
    try {
      const response = await fetch('/api/pdfs')
      if (response.ok) {
        const pdfs = await response.json()
        console.log('Loaded PDFs:', pdfs) // Debug log
        setUploadedPDFs(pdfs)
      }
    } catch (error) {
      console.error('Error loading PDFs:', error)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!apiKey.trim()) {
      alert('Please enter your OpenAI API key first')
      return
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please select a PDF file')
      return
    }

    setIsUploading(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('api_key', apiKey)

      const response = await fetch('/api/upload-pdf', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Upload result:', result) // Debug log
        
        // Refresh the PDF list first
        await loadUploadedPDFs()
        
        // Auto-select the newly uploaded PDF
        console.log('Setting selected PDF to:', result.pdf_id) // Debug log
        setSelectedPDF(result.pdf_id)
        
        // Show success message
        alert(`PDF uploaded successfully! ${result.message}`)
      } else {
        const error = await response.json()
        console.error('Upload error:', error) // Debug log
        alert(`Upload failed: ${error.detail}`)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDeletePDF = async (pdfId: string) => {
    if (!confirm('Are you sure you want to delete this PDF?')) return

    try {
      const response = await fetch(`/api/pdfs/${pdfId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        await loadUploadedPDFs() // Refresh the PDF list
        if (selectedPDF === pdfId) {
          setSelectedPDF('') // Deselect if currently selected
        }
        alert('PDF deleted successfully')
      } else {
        const error = await response.json()
        alert(`Delete failed: ${error.detail}`)
      }
    } catch (error) {
      console.error('Delete error:', error)
      alert('Delete failed. Please try again.')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validation checks
    if (!userMessage.trim() || !apiKey.trim()) return
    
    // If using PDF chat, Tavily API key is required for web search capabilities
    if (selectedPDF && !tavilyApiKey.trim()) {
      alert('Tavily API key is required for PDF chat with web search capabilities')
      return
    }

    const newUserMessage: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, newUserMessage])
    setUserMessage('')
    setIsLoading(true)
    setIsStreaming(true)

    try {
      // Determine which endpoint to use based on PDF selection
      const endpoint = selectedPDF ? '/api/chat-pdf' : '/api/chat'
      
      // Prepare request body based on endpoint
      const requestBody = selectedPDF 
        ? {
            message: userMessage,
            system_message: developerMessage || 'You are a helpful assistant that can answer questions about uploaded PDF documents and search the web for additional information when needed. Format your responses using markdown for better readability - use headers, bullet points, code blocks, and emphasis where appropriate.',
            model: model,
            api_key: apiKey,
            tavily_api_key: tavilyApiKey,
            pdf_id: selectedPDF
          }
        : {
            developer_message: developerMessage || 'You are a helpful AI assistant. Format your responses using markdown for better readability.',
            user_message: userMessage,
            model: model,
            api_key: apiKey
          }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      let assistantMessage = ''
      const newAssistantMessage: Message = {
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, newAssistantMessage])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        
        // Add debugging to see what chunks we're receiving
        console.log('Received chunk:', JSON.stringify(chunk))
        
        // Check if this chunk contains tool usage information
        if (chunk.includes('__TOOL_USAGE__')) {
          const toolMatch = chunk.match(/__TOOL_USAGE__(.+?)__TOOL_USAGE__/)
          if (toolMatch) {
            const toolName = toolMatch[1]
            console.log('Tool detected:', toolName)
            setCurrentTool(toolName)
            setIsUsingTool(true)
            
            // Don't add tool usage markers to the message content
            continue
          }
        }
        
        // Only clear tool usage state if we have actual content (not empty chunks)
        if (chunk.trim() && isUsingTool) {
          console.log('Clearing tool usage state due to content chunk')
          setIsUsingTool(false)
          setCurrentTool('')
        }
        
        assistantMessage += chunk

        setMessages(prev => 
          prev.map((msg, index) => 
            index === prev.length - 1 && msg.role === 'assistant'
              ? { ...msg, content: assistantMessage }
              : msg
          )
        )
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date()
      }])
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
      setIsUsingTool(false)
      setCurrentTool('')
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const getSelectedPDFName = () => {
    const pdf = uploadedPDFs.find(p => p.pdf_id === selectedPDF)
    return pdf ? pdf.filename : 'None'
  }

  // Calculate dynamic chat height based on collapsed sections
  const getChatHeight = () => {
    // Base height when both sections are expanded
    let baseHeight = 'h-96' // 24rem = 384px
    
    // If both sections are collapsed, use viewport height minus header and padding
    if (isPDFSectionCollapsed && isConfigSectionCollapsed) {
      return 'h-[calc(100vh-250px)]' // Full screen minus header and minimal padding
    }
    
    // If only one section is collapsed, give some extra height
    if (isPDFSectionCollapsed || isConfigSectionCollapsed) {
      return 'h-[calc(100vh-400px)]' // Partial expansion
    }
    
    // Default height when both sections are expanded
    return baseHeight
  }

  // Get user-friendly tool names and icons
  const getToolDisplayInfo = (toolName: string) => {
    const toolMap: { [key: string]: { name: string; icon: string; description: string } } = {
      'pdf_rag_tool': { 
        name: 'PDF Search', 
        icon: '📄', 
        description: 'Searching podcast transcript content...' 
      },
      'podcast_summary_tool': { 
        name: 'Summary Generator', 
        icon: '📋', 
        description: 'Generating podcast summary...' 
      },
      'podcast_quotes_tool': { 
        name: 'Quote Extractor', 
        icon: '💎', 
        description: 'Finding memorable quotes...' 
      },
      'newsletter_writer_tool': { 
        name: 'Newsletter Writer', 
        icon: '📰', 
        description: 'Creating newsletter content...' 
      },
      'tavily_search_tool': { 
        name: 'Web Search', 
        icon: '🌐', 
        description: 'Searching the web for additional information...' 
      }
    }
    
    return toolMap[toolName] || { 
      name: toolName, 
      icon: '🔧', 
      description: 'Processing with AI tool...' 
    }
  }

  // Handle quick action button clicks
  const handleQuickAction = async (message: string) => {
    if (isLoading || !selectedPDF || !apiKey.trim()) return
    
    setUserMessage(message)
    
    // Create and dispatch form submission event
    const formSubmitEvent = {
      preventDefault: () => {},
    } as React.FormEvent
    
    await handleSubmit(formSubmitEvent)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <SparklesIcon className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Podcast Digest Agent
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-300">
            Upload podcast transcripts and digest it better with AI
          </p>
        </div>

        {/* PDF Upload and Management Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Podcast Transcript Management
            </h2>
            <button
              onClick={() => setIsPDFSectionCollapsed(!isPDFSectionCollapsed)}
              className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
              title={isPDFSectionCollapsed ? "Expand section" : "Collapse section"}
            >
              {isPDFSectionCollapsed ? (
                <ChevronDownIcon className="h-5 w-5" />
              ) : (
                <ChevronUpIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          
          <div 
            className={`transition-all duration-300 overflow-hidden ${
              isPDFSectionCollapsed ? 'max-h-0 opacity-0' : 'max-h-none opacity-100'
            }`}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Upload Section */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Upload PDF
              </label>
              <div className="flex items-center space-x-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading || !apiKey.trim() || !tavilyApiKey.trim()}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <DocumentArrowUpIcon className="h-5 w-5 mr-2" />
                  {isUploading ? 'Processing...' : 'Upload PDF'}
                </button>
              </div>
              {(!apiKey.trim() || !tavilyApiKey.trim()) && (
                <p className="text-xs text-red-500 mt-1">
                  Please enter both OpenAI and Tavily API keys first
                </p>
              )}
            </div>

            {/* PDF Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select PDF for Chat
              </label>
              <select
                value={selectedPDF}
                onChange={(e) => setSelectedPDF(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">Chat without PDF (Regular AI)</option>
                {uploadedPDFs.map((pdf) => (
                  <option key={pdf.pdf_id} value={pdf.pdf_id}>
                    {pdf.filename} ({pdf.chunks_count} chunks)
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Uploaded PDFs List */}
          {uploadedPDFs.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Uploaded PDFs
              </h3>
              <div className="space-y-2">
                {uploadedPDFs.map((pdf) => (
                  <div
                    key={pdf.pdf_id}
                    className={`flex items-center justify-between p-3 rounded-md border ${
                      selectedPDF === pdf.pdf_id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center">
                      <DocumentTextIcon className="h-5 w-5 text-gray-500 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {pdf.filename}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {pdf.chunks_count} chunks
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeletePDF(pdf.pdf_id)}
                      className="p-1 text-red-500 hover:text-red-700 transition-colors"
                      title="Delete PDF"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Current Selection Display */}
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
            <div className="flex items-center">
              <DocumentTextIcon className="h-5 w-5 text-gray-500 mr-2" />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Current PDF: <strong>{getSelectedPDFName()}</strong>
              </span>
            </div>
          </div>
          </div>
        </div>

        {/* Settings Panel */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Configuration
            </h2>
            <button
              onClick={() => setIsConfigSectionCollapsed(!isConfigSectionCollapsed)}
              className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
              title={isConfigSectionCollapsed ? "Expand section" : "Collapse section"}
            >
              {isConfigSectionCollapsed ? (
                <ChevronDownIcon className="h-5 w-5" />
              ) : (
                <ChevronUpIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          <div 
            className={`transition-all duration-300 overflow-hidden ${
              isConfigSectionCollapsed ? 'max-h-0 opacity-0' : 'max-h-none opacity-100'
            }`}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tavily API Key
              </label>
              <input
                type="password"
                value={tavilyApiKey}
                onChange={(e) => setTavilyApiKey(e.target.value)}
                placeholder="tvly-..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                System Message (Optional)
              </label>
              <input
                type="text"
                value={developerMessage}
                onChange={(e) => setDeveloperMessage(e.target.value)}
                placeholder="You are a helpful assistant. Use markdown formatting..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
          {/* Messages */}
          <div className={`${getChatHeight()} overflow-y-auto p-6 space-y-4 transition-all duration-300`}>
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                <SparklesIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Start a conversation by typing a message below!</p>
                {selectedPDF && (
                  <p className="text-sm mt-2">
                    💡 You're chatting with: <strong>{getSelectedPDFName()}</strong>
                  </p>
                )}
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`${
                      message.role === 'user' 
                        ? 'max-w-xs lg:max-w-md' 
                        : 'max-w-sm lg:max-w-2xl'
                    } px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                  >
                    {message.role === 'assistant' ? (
                      <div className="text-sm">
                        <MarkdownRenderer content={message.content} />
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}
                    <p className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {formatTime(message.timestamp)}
                    </p>
                  </div>
                </div>
              ))
            )}
            {isUsingTool && currentTool && (
              <div className="flex justify-start">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 px-4 py-3 rounded-lg max-w-sm">
                  <div className="flex items-center space-x-2">
                    <div className="text-lg animate-pulse">{getToolDisplayInfo(currentTool).icon}</div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-blue-800 dark:text-blue-200">
                        {getToolDisplayInfo(currentTool).name}
                      </div>
                      <div className="text-xs text-blue-600 dark:text-blue-300">
                        {getToolDisplayInfo(currentTool).description}
                      </div>
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {isStreaming && !isUsingTool && (
              <div className="flex justify-start">
                <div className="bg-gray-100 dark:bg-gray-700 px-4 py-2 rounded-lg">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Sample Usage Cards */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-4 border-b">
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  onClick={() => handleQuickAction('Extract the most memorable and impactful quotes from this podcast')}
                  disabled={isLoading || !selectedPDF}
                  className="flex items-center justify-center space-x-2 px-3 py-2 w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm rounded-lg hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
                >
                  <span>💎</span>
                  <span>Extract golden quotes</span>
                </button>
                
                <button
                  onClick={() => handleQuickAction('Provide a comprehensive summary of this podcast episode')}
                  disabled={isLoading || !selectedPDF}
                  className="flex items-center justify-center space-x-2 px-3 py-2 w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm rounded-lg hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
                >
                  <span>📋</span>
                  <span>Summarize the podcast</span>
                </button>
                
                <button
                  onClick={() => handleQuickAction('Create an engaging newsletter based on this podcast content')}
                  disabled={isLoading || !selectedPDF}
                  className="flex items-center justify-center space-x-2 px-3 py-2 w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white text-sm rounded-lg hover:from-green-600 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
                >
                  <span>📰</span>
                  <span>Write newsletter</span>
                </button>
              </div>
              
              {!selectedPDF && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                  💡 Select a podcast transcript above to use these quick actions
                </p>
              )}
            </div>
          </div>

          {/* Input Form */}
          <div className="p-4">
            <form onSubmit={handleSubmit} className="flex space-x-4">
              <div className="flex-1">
                <textarea
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSubmit(e)
                    }
                  }}
                  placeholder="Type your message..."
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white resize-none"
                  rows={2}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading || !userMessage.trim() || !apiKey.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <PaperAirplaneIcon className="h-5 w-5" />
                )}
              </button>
            </form>
            {selectedPDF && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                💡 Chatting with PDF: {getSelectedPDFName()}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 