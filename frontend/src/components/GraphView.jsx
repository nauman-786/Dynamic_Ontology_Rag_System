import React, { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import axios from 'axios';
import { RefreshCw, Maximize2, Minimize2 } from 'lucide-react';

const GraphView = ({ refreshTrigger, layoutMode, setLayoutMode }) => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Update canvas dimensions dynamically (important for maximize/minimize)
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    
    window.addEventListener('resize', updateDimensions);
    const timeoutId = setTimeout(updateDimensions, 350); // slight delay for flexbox transition
    updateDimensions(); 
    
    return () => {
      window.removeEventListener('resize', updateDimensions);
      clearTimeout(timeoutId);
    };
  }, [layoutMode]);

  const fetchGraphData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/graph');
      setGraphData(response.data);
    } catch (error) {
      console.error("Failed to fetch graph data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, [refreshTrigger]);

  const toggleExpand = () => {
    setLayoutMode(layoutMode === 'graph' ? 'split' : 'graph');
  };

  return (
    <div className="relative w-full h-full bg-[#f8fafc] rounded-2xl overflow-hidden shadow-sm border border-slate-200" ref={containerRef}>
      
      {/* Floating Toolbar */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between pointer-events-none">
        
        <div className="flex items-center gap-3 bg-white/90 backdrop-blur px-4 py-2 rounded-xl border border-slate-200 shadow-sm pointer-events-auto">
          <span className="text-sm font-semibold text-slate-800">Ontology Graph</span>
          <button 
            onClick={fetchGraphData}
            className="p-1.5 hover:bg-slate-100 text-slate-500 hover:text-indigo-600 rounded-lg transition-colors"
            title="Refresh Graph"
          >
            <RefreshCw size={16} className={`${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <button 
          onClick={toggleExpand}
          className="p-2.5 bg-white/90 backdrop-blur shadow-sm hover:shadow-md border border-slate-200 rounded-xl text-slate-500 hover:text-indigo-600 transition-all pointer-events-auto"
          title={layoutMode === 'graph' ? "Restore Split View" : "Maximize Graph"}
        >
          {layoutMode === 'graph' ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
        </button>

      </div>

      {loading && graphData.nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-50/80 backdrop-blur-sm z-10">
          <span className="text-indigo-600 font-medium flex items-center gap-3 px-6 py-3 bg-white rounded-2xl shadow-lg border border-indigo-100">
            <RefreshCw size={20} className="animate-spin" />
            Mapping Universe...
          </span>
        </div>
      )}

      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeAutoColorBy="group"
        
        // Beautiful flowing data bubbles on links
        linkDirectionalParticles={4}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleSpeed={0.008}
        linkDirectionalParticleColor={() => '#818cf8'} 
        
        linkWidth={1.5}
        linkColor={() => '#cbd5e1'} 
        
        // Custom canvas drawing to permanently show labels below nodes
        nodeCanvasObject={(node, ctx, globalScale) => {
          const radius = 6;
          
          // 1. Draw node circle
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
          ctx.fillStyle = node.color || '#4F46E5';
          ctx.fill();
          
          // Subtle outline around node
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.5 / globalScale;
          ctx.stroke();

          // 2. Always draw permanent label below the node
          const label = node.name;
          const fontSize = 11 / globalScale;
          ctx.font = `500 ${fontSize}px Inter, sans-serif`;
          const textWidth = ctx.measureText(label).width;
          const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.6);

          // Label background (pill shape)
          ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
          ctx.beginPath();
          ctx.roundRect(
            node.x - bckgDimensions[0] / 2, 
            node.y + radius + (2 / globalScale), 
            bckgDimensions[0], 
            bckgDimensions[1], 
            4 / globalScale // border radius
          );
          ctx.fill();

          // Label text
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = '#334155'; // Slate 700
          ctx.fillText(label, node.x, node.y + radius + (bckgDimensions[1]/2) + (2 / globalScale));
        }}
      />
    </div>
  );
};

export default GraphView;