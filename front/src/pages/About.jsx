import React from 'react';
import BaseLayout from '../components/Layout/BaseLayout';

const About = () => {
  return (
    <BaseLayout title="About Lost&Found">
      <div className="max-w-4xl mx-auto py-8 px-2 bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-3xl shadow-2xl animate-fade-in">
        <div className="card p-8 mb-10 rounded-2xl shadow-lg bg-white/80 backdrop-blur-md border border-blue-100">
          <h2 className="text-3xl font-extrabold mb-4 bg-gradient-to-r from-blue-700 via-purple-600 to-pink-500 bg-clip-text text-transparent flex items-center gap-2">
            <svg className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01" /></svg>
            About the Project
          </h2>
          <p className="text-gray-700 mb-4 text-lg">
            <b>Lost&Found</b> is a modern travel information search platform developed by a group of students from Innopolis University.
            The project is open-source and available on <a href="https://github.com/Luzinsan/LostFound" target="_blank" rel="noopener noreferrer" className="text-blue-700 underline transition-colors duration-200 hover:text-pink-500 hover:underline-offset-4">GitHub</a>.
          </p>
          <p className="text-gray-700 mb-4 text-lg">
            Our system provides powerful search and explanation tools for discovering places of interest, using both classic and state-of-the-art AI methods.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
          <div className="card p-8 rounded-2xl shadow-lg bg-gradient-to-br from-green-50 via-white to-blue-50 border border-green-100 animate-fade-in delay-100">
            <h2 className="text-2xl font-bold mb-4 text-green-700 flex items-center gap-2">
              <svg className="h-7 w-7 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              Key Features
            </h2>
            <ul className="space-y-4">
              <li className="flex items-start gap-2">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-blue-400 to-green-400 text-white shadow-md mr-2"><svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></span>
                <span><b>Index Search:</b> Fast keyword-based search with TF-IDF ranking, wildcard support, and type/city filters.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-purple-400 to-pink-400 text-white shadow-md mr-2"><svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></span>
                <span><b>Semantic Search:</b> Natural language search using BERT embeddings, ball-tree similarity, and combined scoring (semantic + type match).</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-yellow-400 to-pink-400 text-white shadow-md mr-2"><svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></span>
                <span><b>LLM Explanation:</b> For semantic search, get an AI-generated explanation and ranking of results in chat format (RAG, GPT-like models).</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-blue-400 to-purple-400 text-white shadow-md mr-2"><svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></span>
                <span><b>Open Data Sources:</b> All information is aggregated from <b>Wikipedia</b> and <b>Google Places</b>.</span>
              </li>
            </ul>
          </div>
          <div className="card p-8 rounded-2xl shadow-lg bg-gradient-to-br from-purple-50 via-white to-pink-50 border border-purple-100 animate-fade-in delay-200">
            <h2 className="text-2xl font-bold mb-4 text-purple-700 flex items-center gap-2">
              <svg className="h-7 w-7 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-6a2 2 0 012-2h2a2 2 0 012 2v6" /></svg>
              Technology Stack
            </h2>
            <ul className="space-y-3 text-gray-700">
              <li><span className="font-semibold text-blue-700">Frontend:</span> React, Vite, Tailwind CSS, React Router, Leaflet, Axios, React Markdown</li>
              <li><span className="font-semibold text-green-700">Backend:</span> FastAPI, Celery, PyTorch, Transformers, NLTK, Pydantic, Uvicorn, Redis, MongoDB</li>
              <li><span className="font-semibold text-purple-700">NLP/AI:</span> BERT, ball-tree, TF-IDF, RAG (Retrieval Augmented Generation)</li>
              <li><span className="font-semibold text-pink-700">Other:</span> BeautifulSoup, Wikipedia-API, python-multipart</li>
            </ul>
          </div>
        </div>

        <div className="card p-8 rounded-2xl shadow-lg bg-white/80 border border-blue-100 animate-fade-in delay-300">
          <h2 className="text-2xl font-bold mb-4 text-blue-700 flex items-center gap-2">
            <svg className="h-7 w-7 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 7.165 6 9.388 6 12v2.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
            Implemented Search Functions
          </h2>
          <ul className="list-none pl-0 space-y-3 text-gray-800">
            <li className="flex items-start gap-2"><span className="inline-block h-4 w-4 mt-1 rounded-full bg-blue-400"></span><span><b>Index Search:</b> Classic inverted index with TF-IDF ranking, wildcard support, city/type filters, and query correction.</span></li>
            <li className="flex items-start gap-2"><span className="inline-block h-4 w-4 mt-1 rounded-full bg-purple-400"></span><span><b>Semantic Search:</b> Ball-tree based search using BERT embeddings, combined scoring (semantic + type), supports multi-city and type filters.</span></li>
            <li className="flex items-start gap-2"><span className="inline-block h-4 w-4 mt-1 rounded-full bg-pink-400"></span><span><b>LLM Explanation (RAG):</b> For semantic search, generates a detailed, ranked explanation of results using a large language model (LLM) with context from search results.</span></li>
          </ul>
        </div>

        <div className="card p-8 mt-10 rounded-2xl shadow-lg bg-gradient-to-br from-blue-50 via-white to-green-50 border border-blue-100 animate-fade-in delay-400">
          <h2 className="text-2xl font-bold mb-4 text-green-700 flex items-center gap-2">
            <svg className="h-7 w-7 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c0-1.104.896-2 2-2s2 .896 2 2-.896 2-2 2-2-.896-2-2z" /></svg>
            Team & Open Source
          </h2>
          <p className="text-gray-700 mb-2 text-lg">
            This project is developed by a group of students from <b>Innopolis University</b> as part of an academic initiative.
          </p>
          <p className="text-gray-700 mb-2 text-lg">
            Source code is available on <a href="https://github.com/Luzinsan/LostFound" target="_blank" rel="noopener noreferrer" className="text-blue-700 underline transition-colors duration-200 hover:text-pink-500 hover:underline-offset-4">GitHub</a>.
          </p>
        </div>
      </div>
    </BaseLayout>
  );
};

export default About; 
// Tailwind animation utility (add to your global CSS if not present):
// .animate-fade-in { animation: fadeIn 0.8s ease-in; }
// @keyframes fadeIn { from { opacity: 0; transform: translateY(24px);} to { opacity: 1; transform: none;} } 