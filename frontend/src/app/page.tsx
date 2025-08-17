'use client';

import { useState } from 'react';
import ChatInterface from '@/components/ChatInterface';
import MemoryStats from '@/components/MemoryStats';
import ScheduleList from '@/components/ScheduleList';
import Layout from '@/components/Layout';

export default function Home() {
  const [currentPage, setCurrentPage] = useState<'chat' | 'memory' | 'schedule'>('chat');

  const renderContent = () => {
    switch (currentPage) {
      case 'memory':
        return <MemoryStats />;
      case 'schedule':
        return <ScheduleList />;
      case 'chat':
      default:
        return <ChatInterface />;
    }
  };

  return (
    <Layout currentPage={currentPage} onPageChange={setCurrentPage}>
      {renderContent()}
    </Layout>
  );
}
