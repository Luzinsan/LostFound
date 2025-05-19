import React, { useState, useRef, useEffect } from 'react';

const TEST_BODY = new URLSearchParams({
  stream: 'true',
  top_p: '1',
  model: 'Qwen/Qwen3-235B-A22B',
  city: '',
  temperature: '0.7',
  max_tokens: '3000',
  types: '',
  limit: '5',
  messages_json: JSON.stringify([
    { role: 'user', content: 'Tell me about places in Moscow' }
  ]),
});

export default function RagStreamingTest({ city = '', types = '', query = '' }) {
  const [response, setResponse] = useState('');
  const [thinking, setThinking] = useState(false);
  const [loading, setLoading] = useState(false);
  const controllerRef = useRef(null);
  const [thinkingContent, setThinkingContent] = useState('');
  const [mainContent, setMainContent] = useState('');
  const [thinkingHistory, setThinkingHistory] = useState([]);
  const [showThinking, setShowThinking] = useState(true);

  const handleStart = async () => {
    setResponse('');
    setThinkingContent('');
    setMainContent('');
    setShowThinking(true);
    setThinking(false);
    setLoading(true);
    controllerRef.current = new AbortController();
    try {
      const body = new URLSearchParams({
        ...Object.fromEntries(TEST_BODY),
        city,
        types,
        messages_json: JSON.stringify([
          { role: 'user', content: query }
        ]),
      });
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
        // Разбиваем по data: ...\n\n
        let lines = partial.split(/\r?\n/);
        // Если последний элемент не пустой, это незавершённая строка, оставим в partial
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
          // Обработка <think> ... </think> внутри контента
          while (content.length > 0) {
            if (!inThinking) {
              const thinkStart = content.indexOf('<think>');
              if (thinkStart !== -1) {
                // Есть начало <think>
                mainBuffer += content.slice(0, thinkStart);
                content = content.slice(thinkStart + 7);
                inThinking = true;
                setThinking(true);
                thinkBuffer = '';
              } else {
                mainBuffer += content;
                content = '';
              }
            } else {
              const thinkEnd = content.indexOf('</think>');
              if (thinkEnd !== -1) {
                // Есть конец </think>
                thinkBuffer += content.slice(0, thinkEnd);
                content = content.slice(thinkEnd + 8);
                setThinking(false);
                inThinking = false;
                // После завершения размышлений оставляем содержимое в thinkingContent
                // thinkBuffer не сбрасываем, чтобы оно осталось видимым
              } else {
                thinkBuffer += content;
                content = '';
              }
            }
            if (inThinking || thinkBuffer) {
              // Декодируем юникод
              const decoded = thinkBuffer.replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) => String.fromCharCode(parseInt(grp, 16)));
              setThinkingContent(decoded);
            }
          }
          // Декодируем юникод для основного текста
          const decodedMain = mainBuffer.replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) => String.fromCharCode(parseInt(grp, 16)));
          setMainContent(decodedMain);
        }
      }
    } catch (e) {
      setResponse('Ошибка: ' + e.message);
    } finally {
      setLoading(false);
      setThinking(false);
      setThinkingContent('');
    }
  };

  const handleStop = () => {
    controllerRef.current?.abort();
    setLoading(false);
    setThinking(false);
  };

  return (
    <div>
      <div className="flex gap-2 mb-2">
        <button className="btn btn-primary" onClick={handleStart} disabled={loading || !query}>
          {loading ? 'Запрос...' : 'Старт'}
        </button>
        {loading && (
          <button className="btn btn-outline" onClick={handleStop}>
            Остановить
          </button>
        )}
      </div>
      {/* Блок размышлений */}
      {thinkingContent && (
        <div className="mb-2">
          <button
            className="mb-1 text-xs text-yellow-700 underline"
            onClick={() => setShowThinking(v => !v)}
          >
            {showThinking ? 'Свернуть размышления' : 'Показать размышления'}
          </button>
          {showThinking && (
            <div className="p-3 rounded bg-yellow-100 border-l-4 border-yellow-400 flex items-center gap-2 animate-pulse">
              <span role="img" aria-label="think">💭</span>
              <span className="text-yellow-900 whitespace-pre-wrap">{thinkingContent}</span>
            </div>
          )}
        </div>
      )}
      <div className="whitespace-pre-wrap bg-gray-100 p-3 rounded min-h-[60px]">
        {mainContent}
      </div>
      {thinkingHistory.length > 0 && (
        <div className="mt-4">
          <div className="font-semibold mb-2 text-yellow-700">История размышлений:</div>
          <ul className="space-y-2">
            {thinkingHistory.map((item, idx) => (
              <li key={idx} className="p-3 rounded bg-yellow-50 border-l-4 border-yellow-300 flex items-center gap-2">
                <span role="img" aria-label="think">💭</span>
                <span className="text-yellow-900">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
} 