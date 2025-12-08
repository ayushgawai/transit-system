import { useState } from 'react'
import { getApiBaseUrl } from '../utils/api'
import clsx from 'clsx'
import axios from 'axios'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  data?: {
    type: 'chart' | 'table' | 'metric'
    content: unknown
  }
}

const sampleQueries = [
  "What's the on-time performance for each route?",
  "Show me the reliability scores by route",
  "Which routes have the highest delays?",
  "What's the estimated daily revenue?",
  "How does demand vary by hour?",
  "Which routes need attention?",
]

const initialMessages: Message[] = [
  {
    id: '1',
    type: 'assistant',
    content: "👋 Hello! I'm your Transit Analytics Assistant, powered by AI.\n\nI can help you understand your transit data, analyze performance metrics, and provide actionable insights. Try asking me:\n\n• Route performance and reliability\n• On-time metrics and delays\n• Revenue analysis\n• Demand patterns\n\nWhat would you like to know about your transit system?",
    timestamp: new Date(),
  },
]

export default function DataQuery() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isConnected, setIsConnected] = useState(true)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages([...messages, userMessage])
    setInput('')
    setIsTyping(true)

    try {
      // Call the API backend
      const response = await axios.post(`${getApiBaseUrl()}/chat`, {
        message: input
      })

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
        data: response.data.data ? {
          type: 'table',
          content: response.data.data
        } : undefined
      }
      setMessages((prev) => [...prev, aiResponse])
      setIsConnected(true)
    } catch (error) {
      console.error('Chat error:', error)
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "⚠️ I'm having trouble connecting to the AI service. Please make sure:\n\n1. The API server is running (`python api/main.py`)\n2. The Perplexity API key is configured\n\nPlease try again.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorResponse])
      setIsConnected(false)
    } finally {
      setIsTyping(false)
    }
  }

  const handleSampleQuery = (query: string) => {
    setInput(query)
  }

  const clearChat = () => {
    setMessages(initialMessages)
  }

  return (
    <div className="h-[calc(100vh-180px)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Data Query Assistant</h1>
          <p className="text-dark-muted">Ask questions about your transit data in natural language</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={clearChat}
            className="px-3 py-1.5 rounded-lg border border-dark-border text-dark-muted hover:text-white hover:border-transit-500 transition-colors text-sm"
          >
            Clear Chat
          </button>
          <div className={clsx(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm',
            isConnected 
              ? 'bg-severity-success/20 text-severity-success' 
              : 'bg-severity-danger/20 text-severity-danger'
          )}>
            <span className={clsx(
              'w-2 h-2 rounded-full',
              isConnected ? 'bg-severity-success animate-pulse' : 'bg-severity-danger'
            )}></span>
            {isConnected ? 'AI Connected' : 'Disconnected'}
          </div>
        </div>
      </div>

      <div className="flex-1 flex gap-6">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col rounded-xl bg-dark-surface border border-dark-border overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={clsx(
                  'flex gap-3',
                  message.type === 'user' ? 'flex-row-reverse' : ''
                )}
              >
                <div
                  className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                    message.type === 'user'
                      ? 'bg-gradient-to-br from-transit-500 to-severity-info'
                      : 'bg-dark-bg border border-dark-border'
                  )}
                >
                  {message.type === 'user' ? (
                    <span className="text-white text-sm font-semibold">AG</span>
                  ) : (
                    <span className="text-xl">🤖</span>
                  )}
                </div>
                <div
                  className={clsx(
                    'max-w-[80%] p-4 rounded-xl',
                    message.type === 'user'
                      ? 'bg-transit-500/20 border border-transit-500/30'
                      : 'bg-dark-bg border border-dark-border'
                  )}
                >
                  <p className="text-white whitespace-pre-wrap">{message.content}</p>
                  {message.data?.type === 'metric' && (
                    <div className="mt-3 p-3 rounded-lg bg-transit-500/10 border border-transit-500/30">
                      <div className="text-3xl font-bold text-transit-500">
                        {(message.data.content as { value: number; unit: string }).value}
                        {(message.data.content as { value: number; unit: string }).unit}
                      </div>
                      <div className="text-sm text-dark-muted">
                        {(message.data.content as { label: string }).label}
                      </div>
                    </div>
                  )}
                  {message.data?.type === 'table' && Array.isArray(message.data.content) && (
                    <div className="mt-3 overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr>
                            {Object.keys(message.data.content[0] || {}).map((key) => (
                              <th key={key} className="px-3 py-2 text-left text-dark-muted border-b border-dark-border">
                                {key}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {message.data.content.slice(0, 5).map((row: Record<string, unknown>, i: number) => (
                            <tr key={i}>
                              {Object.values(row).map((value, j) => (
                                <td key={j} className="px-3 py-2 text-white border-b border-dark-border/50">
                                  {String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <p className="text-xs text-dark-muted mt-2">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-dark-bg border border-dark-border flex items-center justify-center">
                  <span className="text-xl">🤖</span>
                </div>
                <div className="p-4 rounded-xl bg-dark-bg border border-dark-border">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-dark-muted animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 rounded-full bg-dark-muted animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 rounded-full bg-dark-muted animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-dark-border">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your transit data..."
                className="flex-1 px-4 py-3 rounded-xl bg-dark-bg border border-dark-border text-white placeholder-dark-muted focus:outline-none focus:border-transit-500 transition-colors"
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
                className="px-6 py-3 rounded-xl bg-transit-500 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-transit-600 transition-colors"
              >
                Send
              </button>
            </div>
          </form>
        </div>

        {/* Sidebar */}
        <div className="w-80 space-y-4">
          {/* Sample Queries */}
          <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
            <h3 className="text-sm font-semibold text-white mb-3">Try asking:</h3>
            <div className="space-y-2">
              {sampleQueries.map((query, i) => (
                <button
                  key={i}
                  onClick={() => handleSampleQuery(query)}
                  className="w-full p-2.5 rounded-lg bg-dark-bg border border-dark-border text-left text-sm text-dark-text hover:bg-dark-hover hover:border-transit-500/50 transition-colors"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>

          {/* Capabilities */}
          <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
            <h3 className="text-sm font-semibold text-white mb-3">Capabilities</h3>
            <ul className="space-y-2 text-sm text-dark-muted">
              <li className="flex items-center gap-2">
                <span className="text-transit-500">✓</span>
                Natural language queries
              </li>
              <li className="flex items-center gap-2">
                <span className="text-transit-500">✓</span>
                Real-time data from Snowflake
              </li>
              <li className="flex items-center gap-2">
                <span className="text-transit-500">✓</span>
                Severity analysis (🟢🟡🔴)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-transit-500">✓</span>
                SQL query generation
              </li>
              <li className="flex items-center gap-2">
                <span className="text-transit-500">✓</span>
                Actionable insights
              </li>
            </ul>
          </div>

          {/* AI Info */}
          <div className="p-4 rounded-xl bg-transit-500/10 border border-transit-500/30">
            <h4 className="text-sm font-semibold text-white mb-2">🤖 Powered by Perplexity AI</h4>
            <p className="text-xs text-dark-muted">
              This assistant uses Perplexity's Sonar model with context about your Snowflake data warehouse 
              to provide accurate answers about transit operations.
            </p>
          </div>

          {/* Credit */}
          <div className="p-3 rounded-lg bg-dark-bg border border-dark-border text-center">
            <p className="text-xs text-dark-muted">
              SJSU Applied Data Science | MSDA Capstone Project © 2025
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
