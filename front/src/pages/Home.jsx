import React from 'react';
import { Link } from 'react-router-dom';
import BaseLayout from '../components/Layout/BaseLayout';

const Home = () => {
  return (
    <BaseLayout title="Home">
      <div className="max-w-5xl mx-auto py-10 px-2 bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-3xl shadow-2xl animate-fade-in">
        <div className="mb-12 flex justify-center">
          <div className="card w-full max-w-2xl p-10 rounded-2xl shadow-lg bg-white/80 backdrop-blur-md border border-blue-100 animate-fade-in">
            <h2 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-blue-700 via-purple-600 to-pink-500 bg-clip-text text-transparent flex items-center gap-3">
              <svg className="h-9 w-9 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              Welcome to Lost&Found
            </h2>
            <p className="text-gray-700 mb-6 text-lg">
              Lost&Found is a modern travel information search platform. Here you can:
            </p>
            <ul className="space-y-4 mb-8">
              <li className="flex items-start gap-2">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-blue-400 to-green-400 text-white shadow-md mr-2"><svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></span>
                <span><b>Index Search:</b> Fast keyword-based search using classic TF-IDF ranking.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-purple-400 to-pink-400 text-white shadow-md mr-2"><svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></span>
                <span><b>Semantic Search:</b> Advanced natural language search powered by ball-tree vector similarity.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-gradient-to-tr from-yellow-400 to-pink-400 text-white shadow-md mr-2"><svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></span>
                <span><b>LLM Explanation:</b> For semantic search, you can get an AI-powered explanation and ranking of results in chat format.</span>
              </li>
            </ul>
            <div className="flex space-x-4">
              <Link to="/locations" className="px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 shadow-lg transition-all duration-200 hover:scale-105 hover:from-pink-500 hover:to-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-400">Explore All Locations</Link>
            </div>
          </div>
        </div>
        <div className="mt-16 animate-fade-in delay-200">
          <h2 className="text-2xl font-bold mb-8 text-blue-700 flex items-center gap-2 justify-center text-center">
            <svg className="h-7 w-7 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-6a2 2 0 012-2h2a2 2 0 012 2v6" /></svg>
            How it works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card p-8 rounded-2xl shadow-lg bg-white/80 border border-blue-100 flex flex-col items-center text-center">
              <div className="text-4xl text-blue-600 mb-4 font-extrabold">01</div>
              <h3 className="font-semibold text-lg mb-2">Choose your search type</h3>
              <p className="text-gray-700">Select between classic index search or semantic search for more natural queries.</p>
            </div>
            <div className="card p-8 rounded-2xl shadow-lg bg-white/80 border border-blue-100 flex flex-col items-center text-center">
              <div className="text-4xl text-blue-600 mb-4 font-extrabold">02</div>
              <h3 className="font-semibold text-lg mb-2">Get relevant results</h3>
              <p className="text-gray-700">See ranked locations based on your query and selected filters.</p>
            </div>
            <div className="card p-8 rounded-2xl shadow-lg bg-white/80 border border-blue-100 flex flex-col items-center text-center">
              <div className="text-4xl text-blue-600 mb-4 font-extrabold">03</div>
              <h3 className="font-semibold text-lg mb-2">Ask for explanation</h3>
              <p className="text-gray-700">Enable LLM to get an AI-generated explanation and ranking for semantic search results.</p>
            </div>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default Home; 