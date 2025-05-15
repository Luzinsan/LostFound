import React from 'react';
import BaseLayout from '../components/Layout/BaseLayout';

const About = () => {
  return (
    <BaseLayout title="About Lost&Found">
      <div className="max-w-4xl mx-auto">
        <div className="card p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Our Mission</h2>
          <p className="text-gray-600 mb-4">
            Lost&Found is a Telegram-based travel discovery bot that leverages advanced 
            natural language processing (NLP) and aggregated data from trusted sources 
            like Google Places, Wikipedia, and OpenStreetMap to deliver personalized travel recommendations.
          </p>
          <p className="text-gray-600">
            Each recommendation is enriched with historical insights, cultural details, 
            and media references, ensuring users receive a comprehensive and engaging travel planning experience.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">Why Choose Us</h2>
            <ul className="space-y-3">
              <li className="flex items-start">
                <svg className="h-6 w-6 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Personalized recommendations based on your unique interests</span>
              </li>
              <li className="flex items-start">
                <svg className="h-6 w-6 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Aggregated data from multiple trusted sources</span>
              </li>
              <li className="flex items-start">
                <svg className="h-6 w-6 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Rich cultural and historical context for each destination</span>
              </li>
              <li className="flex items-start">
                <svg className="h-6 w-6 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Seamless Telegram integration for easy access</span>
              </li>
            </ul>
          </div>
          
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">Our Technology</h2>
            <p className="text-gray-600 mb-3">
              We combine cutting-edge technologies to provide you with the best travel recommendations:
            </p>
            <ul className="space-y-2 text-gray-600">
              <li><span className="font-medium">NLP Processing:</span> Using spaCy, Transformers, and BERT models</li>
              <li><span className="font-medium">Backend:</span> FastAPI/Flask for robust API creation</li>
              <li><span className="font-medium">Data Storage:</span> PostgreSQL and Elasticsearch</li>
              <li><span className="font-medium">Telegram Bot:</span> Built with python-telegram-bot or Aiogram</li>
            </ul>
          </div>
        </div>
        
        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">Get Started Today</h2>
          <p className="text-gray-600 mb-4">
            Ready to transform your travel planning experience? Try Lost&Found today by accessing our Telegram bot.
          </p>
          <div className="flex justify-center">
            <a 
              href="https://t.me/LostAndFoundBot" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="btn btn-primary"
            >
              Try Our Bot on Telegram
            </a>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default About; 