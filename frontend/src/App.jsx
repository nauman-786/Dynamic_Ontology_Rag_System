import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import GraphView from './components/GraphView';
import { PanelLeftOpen } from 'lucide-react';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [layoutMode, setLayoutMode] = useState('split'); // 'split', 'chat', or 'graph'

  const handleUploadSuccess = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans text-slate-900 antialiased relative">
      
      {/* Sidebar */}
      {isSidebarOpen && (
        <Sidebar 
          onUploadSuccess={handleUploadSuccess} 
          onClose={() => setIsSidebarOpen(false)} 
        />
      )}

      {/* Button to reopen sidebar when closed */}
      {!isSidebarOpen && (
        <button 
          onClick={() => setIsSidebarOpen(true)}
          className="absolute top-4 left-4 z-50 p-2.5 bg-white shadow-md hover:shadow-lg border border-slate-200 rounded-xl text-slate-600 hover:text-indigo-600 transition-all"
          title="Open Sidebar"
        >
          <PanelLeftOpen size={20} />
        </button>
      )}

      {/* Main Workspace Split View */}
      <div className="flex-1 flex p-4 gap-4 overflow-hidden">
        
        {/* Chat Interface (Hides if layout is 'graph') */}
        {layoutMode !== 'graph' && (
          <div className={`h-full rounded-2xl overflow-hidden shadow-sm border border-slate-200 bg-white transition-all duration-300 ${layoutMode === 'chat' ? 'w-full' : 'w-1/2'}`}>
            <ChatInterface 
              layoutMode={layoutMode} 
              setLayoutMode={setLayoutMode} 
            />
          </div>
        )}

        {/* Force Graph Canvas (Hides if layout is 'chat') */}
        {layoutMode !== 'chat' && (
          <div className={`h-full transition-all duration-300 ${layoutMode === 'graph' ? 'w-full' : 'w-1/2'}`}>
            <GraphView 
              refreshTrigger={refreshTrigger} 
              layoutMode={layoutMode} 
              setLayoutMode={setLayoutMode} 
            />
          </div>
        )}

      </div>
    </div>
  );
}

export default App;