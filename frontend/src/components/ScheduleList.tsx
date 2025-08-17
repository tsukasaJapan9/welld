'use client';

import { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';

interface Schedule {
  deadline: string;
  content: string;
  priority: 'high' | 'mid' | 'low';
}

export default function ScheduleList() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    try {
      setLoading(true);
      // 実際のAPIエンドポイントに置き換える必要があります
      const response = await fetch('/api/schedule');
      if (!response.ok) {
        throw new Error('Failed to fetch schedules');
      }
      const data = await response.json();
      if (data.success) {
        setSchedules(data.schedules);
      } else {
        throw new Error(data.message || 'Failed to fetch schedules');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      // フォールバック: サンプルデータ
      setSchedules([
        {
          deadline: '2024-01-20',
          content: 'チームミーティング：週次プロジェクト進捗確認',
          priority: 'high'
        },
        {
          deadline: '2024-01-22',
          content: 'クライアント打ち合わせ：新機能の要件確認',
          priority: 'mid'
        },
        {
          deadline: '2024-01-19',
          content: 'コードレビュー：プルリクエストの確認',
          priority: 'low'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      weekday: 'short'
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'mid':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case 'high':
        return '高';
      case 'mid':
        return '中';
      case 'low':
        return '低';
      default:
        return '未設定';
    }
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
              <Calendar className="h-5 w-5 text-red-400" />
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

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">
        {/* ヘッダー */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">予定一覧</h1>
          <p className="text-gray-600">管理している予定の一覧</p>
        </div>



        {/* 予定一覧 */}
        <div className="space-y-4">
          {schedules.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">予定がありません</p>
            </div>
          ) : (
            schedules.map((schedule, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6 transition-all hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(schedule.priority)}`}>
                        {getPriorityLabel(schedule.priority)}
                      </span>
                    </div>

                    <p className="text-gray-900 text-lg mb-2">
                      {schedule.content}
                    </p>

                    <div className="flex items-center text-sm text-gray-500">
                      <Calendar className="h-4 w-4 mr-1" />
                      {formatDate(schedule.deadline)}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* 更新ボタン */}
        <div className="text-center">
          <button
            onClick={fetchSchedules}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Calendar className="h-4 w-4 mr-2" />
            予定を更新
          </button>
        </div>
      </div>
    </div>
  );
}
