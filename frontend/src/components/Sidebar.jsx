import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, PanelLeftClose } from 'lucide-react';

const Sidebar = ({ onUploadSuccess, onClose }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  
  // New state variables for tracking progress
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');

  // Poll the backend for progress every 1 second while uploading
  useEffect(() => {
    let interval;
    if (uploading) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get('http://localhost:8000/api/progress');
          setProgress(res.data.percent);
          setStatusMessage(res.data.message);
        } catch (err) {
          console.error("Failed to fetch progress", err);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [uploading]);

  // Automatically trigger upload when file is selected
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
      setIsSuccess(false);
      setProgress(0);
      setStatusMessage('Initializing upload...');
      await processUpload(selectedFile);
    }
  };

  const processUpload = async (fileToUpload) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const response = await axios.post('http://localhost:8000/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.success) {
        setProgress(100);
        setStatusMessage('Successfully Processed');
        setIsSuccess(true);
        if (onUploadSuccess) onUploadSuccess(); 
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Check backend server.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-80 h-full bg-slate-900 text-slate-100 flex flex-col p-6 border-r border-slate-800 relative">
      
      {/* Close Sidebar Button */}
      <button 
        onClick={onClose}
        className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        title="Close Sidebar"
      >
        <PanelLeftClose size={20} />
      </button>

      <div className="flex items-center gap-3 mb-10 mt-2">
        <div className="p-2.5 bg-indigo-500 rounded-xl shadow-[0_0_15px_rgba(99,102,241,0.4)]">
          <FileText size={22} className="text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg text-white tracking-wide">Ontology RAG</h1>
          <p className="text-xs text-slate-400 font-medium">Knowledge Graph Assistant</p>
        </div>
      </div>

      <div className="flex-1 space-y-6">
        <div>
          <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">
            Data Ingestion
          </label>
          
          <div className={`relative border-2 border-dashed rounded-2xl p-6 text-center transition-all duration-500 overflow-hidden ${
            uploading ? 'border-indigo-500 bg-indigo-500/10 scale-[1.02] shadow-[0_0_20px_rgba(99,102,241,0.2)]' : 
            isSuccess ? 'border-emerald-500 bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.2)]' :
            'border-slate-700 hover:border-indigo-400 bg-slate-800/50 hover:bg-slate-800'
          }`}>
            
            {/* Background Fill showing the progress percentage */}
            {uploading && (
              <div 
                className="absolute left-0 top-0 bottom-0 bg-indigo-500/20 transition-all duration-500 ease-out z-0"
                style={{ width: `${progress}%` }}
              ></div>
            )}

            {/* Input is hidden, triggers file browser */}
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            
            <label htmlFor="file-upload" className={`${uploading ? 'cursor-default' : 'cursor-pointer'} flex flex-col items-center gap-3 relative z-10 w-full h-full`}>
              {isSuccess ? (
                <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400 mb-1">
                  <CheckCircle size={28} />
                </div>
              ) : uploading ? (
                <div className="w-full flex flex-col items-center mt-2">
                  <Loader2 size={28} className="animate-spin text-indigo-400 mb-4" />
                  <div className="flex justify-between w-full text-xs font-semibold text-indigo-300 mb-2 px-1">
                    <span className="truncate mr-2">{statusMessage || 'Extracting Ontology...'}</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-indigo-400 h-1.5 rounded-full transition-all duration-500" 
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              ) : (
                <div className="w-12 h-12 bg-slate-700/50 rounded-full flex items-center justify-center text-slate-300 mb-1 transition-colors hover:text-indigo-400">
                  <Upload size={24} />
                </div>
              )}
              
              {!uploading && (
                <div className="flex flex-col gap-1">
                  <span className={`text-sm font-semibold ${isSuccess ? 'text-emerald-400' : 'text-slate-200'}`}>
                    {isSuccess ? 'Successfully Processed' : 'Select Document'}
                  </span>
                  {!isSuccess && (
                    <span className="text-xs text-slate-500">Auto-processes on selection</span>
                  )}
                </div>
              )}
            </label>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/50 border border-rose-800/50 rounded-xl flex items-start gap-2 text-xs text-rose-300 animate-in fade-in slide-in-from-top-2">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;