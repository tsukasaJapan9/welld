'use client';

import { useState, useEffect } from 'react';
import { Database, Tag, Calendar, TrendingUp, BarChart3 } from 'lucide-react';

interface MemoryStats {
  total_memories: number;
  key_range: {
    earliest: string;
    latest: string;
  };
  tag_counts: Record<string, number>;
  most_used_tags: [string, number][];
  latest_memory_contents: string[];
}

export default function MemoryStats() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMemoryStats();
  }, []);

  const fetchMemoryStats = async () => {
    try {
      setLoading(true);
      // 実際のAPIエンドポイントに置き換える必要があります
      const response = await fetch('/api/memory/stats');
      if (!response.ok) {
        throw new Error('Failed to fetch memory stats');
      }
      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      } else {
        throw new Error(data.message || 'Failed to fetch stats');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(
      parseInt(dateString.slice(0, 4)),
      parseInt(dateString.slice(4, 6)) - 1,
      parseInt(dateString.slice(6, 8)),
      parseInt(dateString.slice(8, 10)),
      parseInt(dateString.slice(10, 12)),
      parseInt(dateString.slice(12, 14))
    );
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Database className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">エラーが発生しました</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">
          <Database className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>メモリの統計情報がありません</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">
        {/* ヘッダー */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">メモリ統計</h1>
          <p className="text-gray-600">蓄積されたメモリの分析結果</p>
        </div>

        {/* 総合統計 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-600">総メモリ数</p>
                <p className="text-2xl font-bold text-blue-900">{stats.total_memories}</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <Tag className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-600">使用タグ数</p>
                <p className="text-2xl font-bold text-green-900">{Object.keys(stats.tag_counts).length}</p>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-purple-600">期間</p>
                <p className="text-sm font-bold text-purple-900">
                  {formatDate(stats.key_range.earliest)} 〜 {formatDate(stats.key_range.latest)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* タグ使用頻度 */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            タグ使用頻度
          </h2>
          <div className="space-y-3">
            {stats.most_used_tags.map(([tag, count], index) => (
              <div key={tag} className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {tag}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    ({Math.round((count / stats.total_memories) * 100)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 全タグ一覧 */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Tag className="h-5 w-5 mr-2" />
            全タグ一覧
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {Object.entries(stats.tag_counts).map(([tag, count]) => (
              <div key={tag} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-sm font-medium text-gray-700">{tag}</span>
                <span className="text-sm text-gray-500">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 最新のメモリ内容 */}
        {stats.latest_memory_contents && stats.latest_memory_contents.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              最新のメモリ内容
            </h2>
            <div className="space-y-4">
              {stats.latest_memory_contents.slice().reverse().map((content, originalIndex) => {
                const displayIndex = stats.latest_memory_contents.length - originalIndex;
                return (
                  <div key={originalIndex} className="p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm text-gray-600 mb-2">
                          メモリ #{displayIndex}
                        </p>
                        <p
                          id={`memory-${originalIndex}`}
                          className={`text-gray-900 leading-relaxed memory-content ${content.length > 200 ? '' : 'expanded'
                            }`}
                        >
                          {content}
                        </p>
                      </div>
                      {content.length > 200 && (
                        <button
                          className="ml-3 text-xs text-blue-600 hover:text-blue-800 font-medium"
                          onClick={() => {
                            const element = document.getElementById(`memory-${originalIndex}`);
                            if (element) {
                              element.classList.toggle('expanded');
                              const button = event?.target as HTMLButtonElement;
                              if (button) {
                                button.textContent = element.classList.contains('expanded') ? '折りたたむ' : '展開';
                              }
                            }
                          }}
                        >
                          展開
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 更新ボタン */}
        <div className="text-center">
          <button
            onClick={fetchMemoryStats}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Database className="h-4 w-4 mr-2" />
            統計を更新
          </button>
        </div>
      </div>
    </div>
  );
}
