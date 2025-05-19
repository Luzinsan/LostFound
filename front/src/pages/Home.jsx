import React from 'react';
import { Link } from 'react-router-dom';
import BaseLayout from '../components/Layout/BaseLayout';
import RagStreamingTest from '../components/RagStreamingTest';

const Home = () => {
  return (
    <BaseLayout title="Home">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="card p-6">
          <h2 className="text-2xl font-semibold mb-4">Welcome to Lost&Found</h2>
          <p className="text-gray-600 mb-6">
            Your personal travel discovery assistant powered by advanced natural language processing.
            Get personalized travel recommendations based on your unique interests.
          </p>
          <div className="flex space-x-4">
            <Link to="/locations" className="btn btn-primary">Explore All Locations</Link>
            <a href="https://t.me/LostAndFoundBot" target="_blank" rel="noopener noreferrer" className="btn btn-outline">
              Try the Bot
            </a>
          </div>
        </div>
        <div className="hidden md:block">
          <div className="h-full bg-gradient-to-tr from-blue-500 to-indigo-600 rounded-lg shadow-lg flex items-center justify-center">
            <span className="text-4xl text-white font-bold">Lost&Found</span>
          </div>
        </div>
      </div>
      
      <div className="mt-12">
        <h2 className="text-xl font-semibold mb-6">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card p-6">
            <div className="text-3xl text-blue-600 mb-4">01</div>
            <h3 className="font-medium text-lg mb-2">Tell us your interests</h3>
            <p className="text-gray-600">Share your travel preferences and interests with our AI-powered bot.</p>
          </div>
          <div className="card p-6">
            <div className="text-3xl text-blue-600 mb-4">02</div>
            <h3 className="font-medium text-lg mb-2">Get personalized suggestions</h3>
            <p className="text-gray-600">Our NLP algorithms analyze your preferences to find perfect matches.</p>
          </div>
          <div className="card p-6">
            <div className="text-3xl text-blue-600 mb-4">03</div>
            <h3 className="font-medium text-lg mb-2">Explore with confidence</h3>
            <p className="text-gray-600">Travel with detailed information from trusted sources like Google Places and Wikipedia.</p>
          </div>
        </div>
      </div>
      {/* Тестовый компонент для стримингового RAG запроса */}
      <div className="mt-12 p-6 card">
        <h2 className="text-lg font-semibold mb-4">Тест RAG LLM Streaming</h2>
        <RagStreamingTest />
      </div>
    </BaseLayout>
  );
};

export default Home; 