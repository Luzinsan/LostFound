import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import '../styles/markdown.css';

export default function RagChat({ query = '', city = '', types = '', searchType = 'index' }) {
  const [mainContent, setMainContent] = useState('');
  const [thinkingContent, setThinkingContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [thinkingFinished, setThinkingFinished] = useState(false);
  const [showThinking, setShowThinking] = useState(true);
  const controllerRef = useRef(null);

  useEffect(() => {
    console.log('[RagChat] useEffect', { query, city, types, searchType });
    if (searchType !== 'semantic' || !query) {
      setMainContent('');
      setThinkingContent('');
      setLoading(false);
      setThinkingFinished(false);
      return;
    }
    setMainContent('');
    setThinkingContent('');
    setLoading(true);
    setThinkingFinished(false);
    controllerRef.current = new AbortController();
    const fetchStream = async () => {
      try {
        const body = new URLSearchParams({
          stream: 'true',
          top_p: '1',
          model: 'deepseek-ai/DeepSeek-R1',
          city,
          types,
          temperature: '0.7',
          max_tokens: '3000',
          limit: '30',
          messages_json: JSON.stringify([
            { role: 'user', content: query }
          ]),
        });
        console.log('[RagChat] fetch body:', body.toString());
        const res = await fetch('/api/v1/rag/chat-completion', {
          method: 'POST',
          headers: {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body,
          signal: controllerRef.current.signal,
        });
        if (!res.body) throw new Error('No stream');
        const reader = res.body.getReader();
        let decoder = new TextDecoder('utf-8');
        let inThinking = false;
        let thinkBuffer = '';
        let mainBuffer = '';
        let partial = '';
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          let chunk = decoder.decode(value, { stream: true });
          partial += chunk;
          let lines = partial.split(/\r?\n/);
          partial = lines.pop();
          for (let line of lines) {
            line = line.trim();
            if (!line.startsWith('data:')) continue;
            let jsonStr = line.slice(5).trim();
            if (!jsonStr) continue;
            let content = '';
            try {
              const obj = JSON.parse(jsonStr);
              content = obj.choices?.[0]?.delta?.content || '';
            } catch (e) {
              continue;
            }
            while (content.length > 0) {
              if (!inThinking) {
                const thinkStart = content.indexOf('<think>');
                if (thinkStart !== -1) {
                  mainBuffer += content.slice(0, thinkStart);
                  content = content.slice(thinkStart + 7);
                  inThinking = true;
                  thinkBuffer = '';
                  setThinkingFinished(false);
                } else {
                  mainBuffer += content;
                  content = '';
                }
              } else {
                const thinkEnd = content.indexOf('</think>');
                if (thinkEnd !== -1) {
                  thinkBuffer += content.slice(0, thinkEnd);
                  content = content.slice(thinkEnd + 8);
                  inThinking = false;
                  setThinkingFinished(true);
                } else {
                  thinkBuffer += content;
                  content = '';
                }
              }
              if (inThinking || thinkBuffer) {
                const decoded = thinkBuffer.replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) => String.fromCharCode(parseInt(grp, 16)));
                setThinkingContent(decoded);
              }
            }
            const decodedMain = mainBuffer.replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) => String.fromCharCode(parseInt(grp, 16)));
            setMainContent(decodedMain);
          }
        }
      } catch (e) {
        if (e.name === 'AbortError') {
          return;
        }
        setMainContent('Ошибка: ' + e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchStream();
    return () => {
      controllerRef.current?.abort();
      setLoading(false);
    };
  }, [query, city, types, searchType]);

  const handleStop = () => {
    controllerRef.current?.abort();
    setLoading(false);
  };

  if (searchType !== 'semantic') {
    return (
      <div className="rounded-lg bg-gray-100 border border-gray-300 p-6 text-center shadow-md mt-4">
        <span className="text-gray-500 text-lg font-medium">LLM-дополнение доступно только для Semantic Search</span>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-gradient-to-br from-white via-blue-50 to-purple-50 border border-blue-200 shadow-2xl p-8 mt-6 mb-8 transition-all animate-fade-in">
      <div className="flex items-center mb-4">
        <span className="text-2xl font-extrabold bg-gradient-to-r from-blue-700 via-purple-600 to-pink-500 bg-clip-text text-transparent mr-3">LLM Chat</span>
        {loading && (
          <>
            <span className="ml-2">
              <span className="inline-block w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin align-middle"></span>
            </span>
            <button className="ml-auto px-3 py-1 rounded-lg border border-yellow-300 bg-gradient-to-r from-white to-yellow-50 text-yellow-700 font-semibold shadow hover:bg-yellow-100 transition-all text-xs" onClick={handleStop}>
              Остановить
            </button>
          </>
        )}
      </div>
      {thinkingContent && (
        <div className={`mb-4 p-4 rounded-xl relative shadow transition-all ${showThinking ? (thinkingFinished ? 'bg-gray-100 border-l-4 border-gray-300' : 'bg-yellow-50 border-l-4 border-yellow-400 animate-pulse') : 'bg-gray-50 border-l-4 border-gray-100'}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-yellow-100 text-yellow-800 text-xs font-semibold shadow-sm">
              <span role="img" aria-label="think">💭</span>
              Размышления LLM
            </span>
            <button
              className="text-yellow-700 hover:text-yellow-900 transition p-1 rounded"
              style={{ fontSize: 18 }}
              onClick={() => setShowThinking(v => !v)}
              aria-label={showThinking ? 'Скрыть размышление' : 'Показать размышление'}
            >
              {showThinking
                ? <svg xmlns="http://www.w3.org/2000/svg" className="inline w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.336-3.234.938-4.675M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                : <svg xmlns="http://www.w3.org/2000/svg" className="inline w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.336-3.234.938-4.675M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3l18 18" /></svg>
              }
            </button>
          </div>
          {showThinking && (
            <div className="flex items-center gap-2">
              <span role="img" aria-label="think" className="text-2xl">💭</span>
              <span className={`whitespace-pre-wrap flex-1 ${thinkingFinished ? 'text-gray-500' : 'text-yellow-900'}`}>{thinkingContent}</span>
              {thinkingFinished && (
                <span className="ml-2 text-xs text-gray-400">Мышление завершено</span>
              )}
            </div>
          )}
        </div>
      )}
      <div className="whitespace-pre-wrap bg-gradient-to-r from-gray-50 via-white to-blue-50 p-5 rounded-xl shadow-inner min-h-[60px] text-base text-gray-800 markdown-body animate-fade-in">
        {mainContent
          ? <ReactMarkdown>{mainContent}</ReactMarkdown>
          : (loading ? <span className="text-gray-400">Генерация ответа...</span> : <span className="text-gray-400">Нет ответа</span>)}
      </div>
    </div>
  );
} 