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
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);
  const [permissionStatus, setPermissionStatus] = useState<string>('unknown');
  const [autoSendTimer, setAutoSendTimer] = useState<NodeJS.Timeout | null>(null);
  const [pendingTranscript, setPendingTranscript] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初期メッセージをクライアントサイドでのみ設定
  useEffect(() => {
    setMessages([
      {
        id: '1',
        content: 'こんにちは！何かお手伝いできることはありますか？',
        role: 'assistant',
        timestamp: new Date(),
      },
    ]);
  }, []);

  // マイク権限の確認
  useEffect(() => {
    const checkMicrophonePermission = async () => {
      try {
        if (navigator.permissions && navigator.permissions.query) {
          const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
          setPermissionStatus(permission.state);

          permission.onchange = () => {
            setPermissionStatus(permission.state);
          };
        } else {
          setPermissionStatus('not-supported');
        }
      } catch (error) {
        console.error('Permission check failed:', error);
        setPermissionStatus('error');
      }
    };

    checkMicrophonePermission();
  }, []);

  // セッションの初期化
  useEffect(() => {
    if (!session) {
      const newSessionId = generateUUID();
      setSession({
        sessionId: newSessionId,
        userId: 'web_user',
      });
    }
  }, [session]);

  // 音声認識の初期化（セッション作成後に実行）
  useEffect(() => {
    // セッションが作成されるまで待機
    if (!session) {
      return;
    }

    // ブラウザの対応状況をチェック
    const isSpeechRecognitionSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;

    if (!isSpeechRecognitionSupported) {
      console.warn('Speech Recognition API is not supported in this browser');
      return;
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();

      recognitionInstance.continuous = true; // 継続的な音声認識を有効化
      recognitionInstance.interimResults = true; // 中間結果を有効化
      recognitionInstance.lang = 'ja-JP';

      recognitionInstance.onresult = (event) => {
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
          // 最終結果がある場合は即座に送信
          console.log('🎯 最終結果検出:', finalTranscript);
          setInputValue(finalTranscript);
          setPendingTranscript('');
          // isRecordingはfalseにしない（継続的な音声認識のため）
          // setIsRecording(false); // この行を削除
          // 自動送信（関数内で直接処理）
          const userMessage: Message = {
            id: Date.now().toString(),
            content: finalTranscript,
            role: 'user',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, userMessage]);
          // 音声認識の結果を直接送信
          sendMessageToAPI(finalTranscript);
        } else if (interimTranscript) {
          // 中間結果がある場合は一時保存し、テキストボックスにも表示
          console.log('📝 中間結果更新:', interimTranscript);
          setPendingTranscript(interimTranscript);
          setInputValue(interimTranscript); // 中間結果をテキストボックスに表示
        }
      };

      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error);

        // abortedエラーの場合は特別な処理
        if (event.error === 'aborted') {
          console.log('🛑 音声認識が中断されました');
          setIsRecording(false);
          setPendingTranscript('');
          return; // abortedエラーの場合はアラートを表示しない
        }

        let errorMessage = '音声認識でエラーが発生しました。';

        switch (event.error) {
          case 'not-allowed':
            errorMessage = 'マイクへのアクセスが拒否されました。\n\n対処法：\n1. ブラウザのアドレスバーの左側にある🔒アイコンをクリック\n2. 「マイク」の許可を「許可」に変更\n3. ページを再読み込みしてから再度お試しください';
            break;
          case 'no-speech':
            errorMessage = '音声が検出されませんでした。\n\n対処法：\n1. マイクに向かって話してください\n2. マイクの音量を確認してください\n3. 静かな環境でお試しください';
            break;
          case 'audio-capture':
            errorMessage = 'マイクの音声キャプチャに失敗しました。\n\n対処法：\n1. マイクが正しく接続されているか確認\n2. 他のアプリでマイクが使用されていないか確認\n3. ブラウザを再起動してから再度お試しください';
            break;
          case 'network':
            errorMessage = 'ネットワークエラーが発生しました。\n\n対処法：\n1. インターネット接続を確認\n2. ページを再読み込み\n3. しばらく時間をおいてから再度お試しください';
            break;
          default:
            errorMessage = `音声認識でエラーが発生しました: ${event.error}\n\n対処法：\n1. ページを再読み込み\n2. ブラウザを再起動\n3. 別のブラウザでお試しください`;
        }

        alert(errorMessage);
        setIsRecording(false);
        setPendingTranscript('');
      };

      recognitionInstance.onend = () => {
        console.log('🔚 音声認識終了, pendingTranscript:', pendingTranscript);

        // 録音終了時にpendingTranscriptがあれば自動送信
        if (pendingTranscript && pendingTranscript.trim()) {
          console.log('📤 録音終了時の自動送信:', pendingTranscript);
          setInputValue(pendingTranscript);
          setPendingTranscript('');
          // 自動送信（関数内で直接処理）
          const userMessage: Message = {
            id: Date.now().toString(),
            content: pendingTranscript,
            role: 'user',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, userMessage]);
          // 音声認識の結果を直接送信
          sendMessageToAPI(pendingTranscript);
        }

        // 継続的音声認識の場合、自動的に再開を試みる
        if (isRecording) {
          console.log('🔄 継続的音声認識のため再開を試みます');
          setTimeout(() => {
            try {
              if (isRecording) {
                recognitionInstance.start();
                console.log('✅ 音声認識を再開しました');
              }
            } catch (error) {
              console.error('音声認識の再開に失敗:', error);
              // 再開に失敗した場合のみisRecordingをfalseにする
              setIsRecording(false);
            }
          }, 100); // 100ms後に再開を試行
        } else {
          // isRecordingがfalseの場合、音声認識が意図的に停止された
          console.log('🛑 音声認識が意図的に停止されました');
        }
      };

      setRecognition(recognitionInstance);
      console.log('✅ Speech Recognition initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize Speech Recognition:', error);
    }
  }, [session]); // pendingTranscriptの依存関係を削除

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
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputValue.trim(),
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
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: '申し訳ございません。エラーが発生しました。しばらく時間をおいてから再度お試しください。',
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      // 送信完了後にフォーカスを入力フィールドに戻す
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  // 自動送信タイマーの管理
  useEffect(() => {
    // 既存のタイマーをクリア
    if (autoSendTimer) {
      clearTimeout(autoSendTimer);
      setAutoSendTimer(null);
    }

    // pendingTranscriptがあり、録音中でない場合にタイマーを設定
    if (pendingTranscript && pendingTranscript.trim() && !isRecording) {
      console.log('🕐 自動送信タイマー開始:', pendingTranscript);
      const timer = setTimeout(() => {
        console.log('✅ 自動送信実行:', pendingTranscript);
        if (pendingTranscript.trim()) {
          setInputValue(pendingTranscript);
          setPendingTranscript('');
          // 自動送信（関数内で直接処理）
          const userMessage: Message = {
            id: Date.now().toString(),
            content: pendingTranscript,
            role: 'user',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, userMessage]);
          // 音声認識の結果を直接送信
          sendMessageToAPI(pendingTranscript);
        }
      }, 2000); // 2秒後に自動送信

      setAutoSendTimer(timer);
    }

    // クリーンアップ関数
    return () => {
      if (autoSendTimer) {
        clearTimeout(autoSendTimer);
      }
    };
  }, [pendingTranscript, isRecording]); // handleSubmitの依存関係を削除

  const toggleRecording = () => {
    if (!recognition) {
      alert('お使いのブラウザは音声認識をサポートしていません。Chrome、Edge、Safariなどの最新のブラウザをご利用ください。');
      return;
    }

    if (isRecording) {
      // 音声認識を停止
      console.log('🛑 音声認識を停止します');
      recognition.stop();
      setIsRecording(false);
      setPendingTranscript('');

      // 録音終了時にpendingTranscriptがあれば自動送信
      if (pendingTranscript && pendingTranscript.trim()) {
        console.log('📤 手動停止時の自動送信:', pendingTranscript);
        setInputValue(pendingTranscript);
        setPendingTranscript('');
        // 自動送信（関数内で直接処理）
        const userMessage: Message = {
          id: Date.now().toString(),
          content: pendingTranscript,
          role: 'user',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);
        // 音声認識の結果を直接送信
        sendMessageToAPI(pendingTranscript);
      }
    } else {
      // 音声認識を開始
      try {
        console.log('🎤 音声認識を開始します');
        // 既存の音声認識をクリア
        setPendingTranscript('');
        setInputValue('');
        recognition.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
        alert('音声認識の開始に失敗しました。\n\n対処法：\n1. ページを再読み込み\n2. ブラウザを再起動\n3. 別のブラウザでお試しください');
        setIsRecording(false);
      }
    }
  };

  const sendMessageToAPI = async (message: string) => {
    if (!session) {
      console.error('Session is not initialized.');
      return;
    }

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
      // テキストボックスをクリア
      setInputValue('');
      // 送信完了後にフォーカスを入力フィールドに戻す
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
        <div className="flex items-center space-x-3">
          <Bot className="h-6 w-6 text-white" />
          <h2 className="text-xl font-semibold text-white">AI Assistant</h2>
        </div>
        {session && (
          <div className="text-blue-100 text-sm mt-2">
            Session ID: {session.sessionId.slice(0, 8)}...
          </div>
        )}
      </div>
      <div className="h-[600px] overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`flex items-start space-x-2 max-w-xs lg:max-w-md ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
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
                <div className="text-sm">
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap m-0">{message.content}</p>
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // マークダウンのスタイリングをカスタマイズ
                        p: ({ children }) => <p className="m-0 mb-2 last:mb-0">{children}</p>,
                        h1: ({ children }) => <h1 className="text-lg font-bold m-0 mb-2">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-base font-bold m-0 mb-2">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-sm font-bold m-0 mb-2">{children}</h3>,
                        ul: ({ children }) => <ul className="list-disc list-inside m-0 mb-2 space-y-1">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside m-0 mb-2 space-y-1">{children}</ol>,
                        li: ({ children }) => <li className="m-0">{children}</li>,
                        code: ({ children, className }) => (
                          <code className={`bg-gray-200 px-1 py-0.5 rounded text-xs font-mono ${className || ''}`}>
                            {children}
                          </code>
                        ),
                        pre: ({ children }) => (
                          <pre className="bg-gray-200 p-2 rounded text-xs font-mono overflow-x-auto m-0 mb-2">
                            {children}
                          </pre>
                        ),
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-gray-300 pl-3 italic m-0 mb-2">
                            {children}
                          </blockquote>
                        ),
                        strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                        em: ({ children }) => <em className="italic">{children}</em>,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  )}
                </div>
                <p
                  className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}
                >
                  {typeof window !== 'undefined' ? message.timestamp.toLocaleTimeString() : ''}
                </p>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-2">
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                <Bot className="h-4 w-4 text-gray-600" />
              </div>
              <div className="px-4 py-2 rounded-lg bg-gray-100">
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                  <span className="text-sm text-gray-500">考え中...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="メッセージを入力してください..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            disabled={isLoading || !session}
            ref={inputRef}
            rows={1}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading || !session}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={toggleRecording}
            disabled={isLoading || !session || !recognition}
            className={`px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${isRecording
              ? 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500' // 音声認識中は赤色
              : permissionStatus === 'denied'
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed' // 権限拒否時はグレー（無効）
                : 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500' // 通常時はグレー
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={
              isRecording
                ? '音声認識を停止（再度クリック）'
                : permissionStatus === 'denied'
                  ? 'マイクへのアクセスが拒否されています。ブラウザの設定で許可してください。'
                  : '音声入力開始'
            }
          >
            {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>
        </form>

        {/* デバッグ情報 */}
        <div className="mt-2 text-xs text-gray-500">
          <div>権限状況: {permissionStatus}</div>
          <div>音声認識: {recognition ? '対応' : '非対応'}</div>
          <div>セッション: {session ? '有効' : '無効'}</div>
          {permissionStatus === 'denied' && (
            <div className="mt-1 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800">
              <strong>マイクの権限が拒否されています</strong><br />
              対処法：<br />
              1. ブラウザのアドレスバーの左側にある🔒アイコンをクリック<br />
              2. 「マイク」の許可を「許可」に変更<br />
              3. ページを再読み込み
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
