'use client';

import { useState } from 'react';
import { Menu, X, MessageSquare, Settings, HelpCircle, History, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Sidebar() {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);

  const menuItems = [
    { icon: MessageSquare, label: 'チャット', href: '#', active: true },
    { icon: History, label: '履歴', href: '#', active: false },
    { icon: Settings, label: '設定', href: '#', active: false },
    { icon: HelpCircle, label: 'ヘルプ', href: '#', active: false },
  ];

  return (
    <>
      {/* モバイル用ハンバーガーメニュー */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-md shadow-md"
      >
        {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* オーバーレイ（モバイル用） */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* サイドバー */}
      <div
        className={`relative lg:static inset-y-0 left-0 z-40 bg-white shadow-lg transition-all duration-150 ease-in-out ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          } ${isCollapsed ? 'w-16' : 'w-40'
          } fixed lg:relative`}
      >
        {/* 折りたたみボタン（デスクトップのみ） */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="hidden lg:block absolute -right-3 top-6 z-50 p-1 bg-white rounded-full shadow-md hover:shadow-lg transition-shadow"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
        <div className="flex flex-col h-full">
          {/* サイドバーヘッダー */}
          <div className={`${isCollapsed ? 'px-4' : 'px-6'} py-4`}>
            <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-2'}`}>
              <span className="text-xl">🤖</span>
              {!isCollapsed && <h2 className="text-xl font-bold text-gray-800">Welld</h2>}
            </div>
          </div>

          {/* メニューアイテム */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {menuItems.map((item, index) => {
              const Icon = item.icon;
              return (
                <a
                  key={index}
                  href={item.href}
                  className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'} px-4 py-3 rounded-lg transition-colors ${item.active
                    ? 'bg-blue-50 text-blue-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  onClick={() => setIsMobileOpen(false)}
                  title={isCollapsed ? item.label : undefined}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {!isCollapsed && <span>{item.label}</span>}
                </a>
              );
            })}
          </nav>

          {/* サイドバーフッター */}
          {!isCollapsed && (
            <div className="px-6 py-4">
              <div className="text-sm text-gray-500">
                <p className="font-medium">バージョン</p>
                <p>v1.0.0</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
