'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Mic, MicOff } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Web Speech APIの型定義
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

// UUID生成関数（crypto.randomUUID()の代替）
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatSession {
  sessionId: string;
  userId: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);
  const isRecordingRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // セッションの初期化
  useEffect(() => {
    const userId = localStorage.getItem('userId') || generateUUID();
    if (!localStorage.getItem('userId')) {
      localStorage.setItem('userId', userId);
    }

    const sessionId = generateUUID();
    setSession({
      sessionId,
      userId,
    });

    console.log('Session initialized:', { sessionId, userId });
  }, []);

  // 音声認識の初期化
  useEffect(() => {
    if (!session) return;

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        console.error('音声認識がサポートされていません');
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'ja-JP';
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        console.log('🎤 音声認識開始');
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          console.log('📤 最終結果:', finalTranscript);
          // 最終結果を即座に送信
          const userMessage: Message = {
            id: Date.now().toString(),
            content: finalTranscript,
            role: 'user',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, userMessage]);
          sendMessageToAPI(finalTranscript);
          setInputValue('');
        } else if (interimTranscript) {
          // 中間結果を表示
          console.log('📝 中間結果:', interimTranscript);
          setInputValue(interimTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        // 無音エラーは無視して継続
        if (event.error === 'no-speech') {
          console.log('⚠️ 無音検出 - 継続します');
          return;
        }

        // abortedエラーも無視
        if (event.error === 'aborted') {
          console.log('⚠️ 中断エラー - 無視します');
          return;
        }

        console.error('❌ 音声認識エラー:', event.error);

        // 重大なエラーの場合のみ停止
        if (event.error === 'not-allowed' || event.error === 'audio-capture') {
          alert(`音声認識エラー: ${event.error}\nマイクの権限を確認してください。`);
          setIsRecording(false);
          isRecordingRef.current = false;
        }
      };

      recognition.onend = () => {
        console.log('🔚 音声認識終了イベント');

        // 録音中フラグを確認して自動再開
        if (isRecordingRef.current) {
          console.log('🔄 録音継続中のため自動再開');
          setTimeout(() => {
            if (isRecordingRef.current) {
              try {
                recognition.start();
                console.log('✅ 音声認識を再開しました');
              } catch (error) {
                console.error('再開エラー:', error);
                // エラーが発生しても再試行
                if (isRecordingRef.current) {
                  setTimeout(() => {
                    try {
                      recognition.start();
                      console.log('✅ 再試行で音声認識を再開');
                    } catch (e) {
                      console.error('再試行失敗:', e);
                    }
                  }, 500);
                }
              }
            }
          }, 100);
        } else {
          console.log('🛑 録音停止のため終了');
          setInputValue('');
        }
      };

      recognitionRef.current = recognition;
      console.log('✅ 音声認識を初期化しました');
    } catch (error) {
      console.error('❌ 音声認識の初期化に失敗:', error);
    }
  }, [session]);

  // isRecordingの変更を監視してrefを更新
  useEffect(() => {
    isRecordingRef.current = isRecording;
    console.log('📌 isRecordingRef更新:', isRecording);
  }, [isRecording]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading || !session) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    await sendMessageToAPI(inputValue.trim());
  };

  const sendMessageToAPI = async (message: string) => {
    if (!session) {
      console.error('Session is not initialized.');
      return;
    }

    console.log('📤 API送信開始');
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          session_id: session.sessionId,
          user_id: session.userId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        role: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message to API:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: '申し訳ございません。エラーが発生しました。しばらく時間をおいてから再度お試しください。',
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      console.log('📤 API送信完了');
      // フォーカスを入力フィールドに戻す
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('音声認識が初期化されていません。ページを再読み込みしてください。');
      return;
    }

    if (isRecording) {
      // 停止処理
      console.log('🛑 録音停止を要求');
      setIsRecording(false);
      isRecordingRef.current = false;

      // 現在の入力テキストがあれば送信
      if (inputValue && inputValue.trim()) {
        const userMessage: Message = {
          id: Date.now().toString(),
          content: inputValue.trim(),
          role: 'user',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);
        sendMessageToAPI(inputValue.trim());
        setInputValue('');
      }

      // 音声認識を停止
      try {
        recognitionRef.current.stop();
        console.log('✅ 音声認識を停止しました');
      } catch (error) {
        console.error('停止エラー:', error);
      }
    } else {
      // 開始処理
      console.log('🎤 録音開始を要求');
      setInputValue('');
      setIsRecording(true);
      isRecordingRef.current = true;

      try {
        recognitionRef.current.start();
        console.log('✅ 音声認識を開始しました');
      } catch (error) {
        console.error('開始エラー:', error);
        // すでに開始している場合は一度停止してから開始
        try {
          recognitionRef.current.stop();
          setTimeout(() => {
            try {
              recognitionRef.current.start();
              console.log('✅ 音声認識を再開始しました');
            } catch (e) {
              console.error('再開始エラー:', e);
              setIsRecording(false);
              isRecordingRef.current = false;
              alert('音声認識の開始に失敗しました。ページを再読み込みしてください。');
            }
          }, 100);
        } catch (stopError) {
          console.error('停止エラー:', stopError);
          setIsRecording(false);
          isRecordingRef.current = false;
        }
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Bot className="h-5 w-5 text-white" />
            <h2 className="text-lg font-semibold text-white">AI Assistant</h2>
          </div>
          {session && (
            <div className="text-blue-100 text-xs">
              ID: {session.sessionId.slice(0, 8)}...
            </div>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-100">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`flex items-start space-x-2 max-w-2xl lg:max-w-4xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-600'
                  }`}
              >
                {message.role === 'user' ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>
              <div
                className={`px-4 py-2 rounded-lg ${message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-800'
                  }`}
              >
                {message.role === 'assistant' ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                      li: ({ children }) => <li className="mb-1">{children}</li>,
                      code: ({ className, children }) => {
                        const isInline = !className;
                        return isInline ? (
                          <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-sm">
                            {children}
                          </code>
                        ) : (
                          <code className="block bg-gray-200 text-gray-800 p-2 rounded text-sm overflow-x-auto">
                            {children}
                          </code>
                        );
                      },
                      pre: ({ children }) => <pre className="mb-2 last:mb-0">{children}</pre>,
                      h1: ({ children }) => <h1 className="text-xl font-bold mb-2">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-lg font-bold mb-2">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-base font-bold mb-2">{children}</h3>,
                      blockquote: ({ children }) => (
                        <blockquote className="border-l-4 border-gray-300 pl-4 italic mb-2">
                          {children}
                        </blockquote>
                      ),
                      a: ({ href, children }) => (
                        <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                          {children}
                        </a>
                      ),
                      hr: () => <hr className="my-2 border-gray-300" />,
                      table: ({ children }) => (
                        <table className="min-w-full divide-y divide-gray-300 mb-2">
                          {children}
                        </table>
                      ),
                      thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
                      tbody: ({ children }) => <tbody className="divide-y divide-gray-200">{children}</tbody>,
                      tr: ({ children }) => <tr>{children}</tr>,
                      th: ({ children }) => (
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {children}
                        </th>
                      ),
                      td: ({ children }) => (
                        <td className="px-3 py-2 text-sm text-gray-900">{children}</td>
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                ) : (
                  message.content
                )}
                <div className="text-xs opacity-50 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                <Bot className="h-4 w-4 text-gray-600" />
              </div>
              <div className="px-4 py-2 rounded-lg bg-gray-100">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="bg-white px-4 py-3 shadow-lg">
        <div className="flex items-end space-x-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isRecording ? "音声認識中..." : "メッセージを入力... (Shift+Enterで送信)"}
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="flex-shrink-0 bg-blue-500 text-white p-2 rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
          <button
            type="button"
            onClick={toggleRecording}
            className={`flex-shrink-0 p-2 rounded-full transition-colors ${isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
              : 'bg-gray-200 hover:bg-gray-300 text-gray-600'
              }`}
            aria-label={isRecording ? '録音停止' : '録音開始'}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </button>
        </div>
      </form>
    </div>
  );
}
