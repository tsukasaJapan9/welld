'use client';

import { useState } from 'react';
import ChatInterface from '@/components/ChatInterface';
import MemoryStats from '@/components/MemoryStats';
import Layout from '@/components/Layout';

export default function Home() {
  const [currentPage, setCurrentPage] = useState<'chat' | 'memory'>('chat');

  const renderContent = () => {
    switch (currentPage) {
      case 'memory':
        return <MemoryStats />;
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
