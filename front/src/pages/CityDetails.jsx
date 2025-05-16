import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import BaseLayout from '../components/Layout/BaseLayout';
import locationsService from '../api/locationsService';
import { CITY_IMAGES, DEFAULT_IMAGE } from '../constants/cityData';

// Функция для извлечения разделов из текста Wikipedia
const extractSections = (text) => {
  if (!text) return { introduction: '' };
  
  // Разделяем текст на абзацы
  const paragraphs = text.split('\n').filter(p => p.trim().length > 0);
  
  // Первый абзац - вступление
  const introduction = paragraphs[0] || '';
  
  // Извлекаем историю (обычно содержит ключевые слова об основании, истории)
  const historyParagraphs = paragraphs.filter(p => 
    p.toLowerCase().includes('основан') || 
    p.toLowerCase().includes('истори') || 
    p.toLowerCase().includes('возник') ||
    p.toLowerCase().includes('създан')
  );
  const history = historyParagraphs.length > 0 ? historyParagraphs[0] : '';
  
  // Ищем достопримечательности - предложения, содержащие определенные слова
  const fullText = paragraphs.join(' ');
  const sentences = fullText.split(/[.!?]+/).filter(s => s.trim().length > 0);
  
  const attractionSentences = sentences.filter(s => {
    const lowerS = s.toLowerCase();
    return lowerS.includes('достопримечательност') || 
           lowerS.includes('музе') || 
           lowerS.includes('памятник') || 
           lowerS.includes('храм') ||
           lowerS.includes('собор') ||
           lowerS.includes('дворец') ||
           lowerS.includes('театр') ||
           lowerS.includes('парк');
  });
  
  // Извлекаем интересные факты - короткие предложения с цифрами и интересными деталями
  const factSentences = sentences.filter(s => {
    const trimmed = s.trim();
    const lowerS = trimmed.toLowerCase();
    
    // Интересный факт часто содержит цифры и не слишком длинный
    const hasNumbers = /\d/.test(trimmed);
    const isShort = trimmed.length < 150 && trimmed.length > 20;
    
    // Часто содержит интересные ключевые слова
    const hasInterestingKeywords = 
      lowerS.includes('интерес') || 
      lowerS.includes('уникаль') || 
      lowerS.includes('известен') ||
      lowerS.includes('самый') ||
      lowerS.includes('единственный');
    
    return (hasNumbers || hasInterestingKeywords) && isShort && !lowerS.includes('население');
  });
  
  return {
    introduction,
    history,
    attractions: attractionSentences.map(s => s.trim() + '.').slice(0, 5),
    facts: factSentences.map(s => s.trim() + '.').slice(0, 4)
  };
};

const CityDetails = () => {
  const { cityName } = useParams();
  const [cityInfo, setCityInfo] = useState(null);
  const [structuredInfo, setStructuredInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchCityInfo = async () => {
      try {
        setLoading(true);
        
        // Используем параметр city для получения информации о конкретном городе
        const decodedCityName = decodeURIComponent(cityName);
        console.log("[CityDetails] Fetching info for:", decodedCityName);
        
        const cityData = await locationsService.getCityInfo(decodedCityName);
        console.log("[CityDetails] Received data:", cityData);
        
        if (cityData && cityData.city) {
          setCityInfo(cityData);
          
          // Структурируем информацию из Wikipedia
          if (cityData.wikipedia && cityData.wikipedia.summary) {
            const structured = extractSections(cityData.wikipedia.summary);
            setStructuredInfo(structured);
          }
          
          setError(null);
        } else {
          throw new Error(`City ${decodedCityName} not found`);
        }
      } catch (err) {
        console.error('Failed to load city details:', err);
        setError(`Failed to load city information for "${decodeURIComponent(cityName)}". Please try again later.`);
      } finally {
        setLoading(false);
      }
    };
    
    if (cityName) {
      fetchCityInfo();
    }
  }, [cityName]);
  
  if (loading) {
    return (
      <BaseLayout title="Loading...">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </BaseLayout>
    );
  }
  
  if (error || !cityInfo) {
    return (
      <BaseLayout title="Error">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error || `City ${cityName} not found`}
        </div>
        <Link to="/destinations" className="btn btn-primary">
          Back to Destinations
        </Link>
      </BaseLayout>
    );
  }
  
  const { city, wikipedia } = cityInfo;
  const cityImage = CITY_IMAGES[city] || DEFAULT_IMAGE;
  
  return (
    <BaseLayout title={city}>
      <div className="mb-6">
        <Link to="/destinations" className="text-blue-600 hover:underline flex items-center">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Destinations
        </Link>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Основная информация */}
        <div className="lg:col-span-2">
          <div className="card p-6 mb-6">
            <h1 className="text-2xl font-bold mb-3">{city}</h1>
            
            {/* Изображение города */}
            <div className="mb-6">
              <img 
                src={cityImage} 
                alt={city} 
                className="w-full h-80 object-cover rounded-lg shadow-md"
              />
            </div>
            
            {structuredInfo ? (
              <>
                <div className="mb-6">
                  {/* Вступление */}
                  <div className="bg-indigo-50 border-l-4 border-indigo-500 p-4 mb-6 rounded-r-md">
                    <p className="text-gray-800 font-medium">{structuredInfo.introduction}</p>
                  </div>
                  
                  {/* История */}
                  {structuredInfo.history && (
                    <>
                      <h2 className="text-xl font-semibold mb-2 text-indigo-800">История</h2>
                      <p className="text-gray-700 mb-6">{structuredInfo.history}</p>
                    </>
                  )}
                  
                  {/* Достопримечательности */}
                  {structuredInfo.attractions && structuredInfo.attractions.length > 0 && (
                    <>
                      <h2 className="text-xl font-semibold mb-2 text-indigo-800">Достопримечательности</h2>
                      <ul className="list-disc pl-5 mb-6 space-y-1">
                        {structuredInfo.attractions.map((attraction, index) => (
                          <li key={index} className="text-gray-700">{attraction}</li>
                        ))}
                      </ul>
                    </>
                  )}
                  
                  {/* Интересные факты */}
                  {structuredInfo.facts && structuredInfo.facts.length > 0 && (
                    <>
                      <h2 className="text-xl font-semibold mb-2 text-indigo-800">Интересные факты</h2>
                      <ul className="list-disc pl-5 space-y-1">
                        {structuredInfo.facts.map((fact, index) => (
                          <li key={index} className="text-gray-700">{fact}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </>
            ) : wikipedia && wikipedia.summary ? (
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2">About {city}</h2>
                <p className="text-gray-700 whitespace-pre-line">{wikipedia.summary}</p>
              </div>
            ) : (
              <p className="text-gray-700">No detailed information available for this city.</p>
            )}
          </div>
        </div>
        
        {/* Боковая панель */}
        <div className="lg:col-span-1">
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold mb-3">Explore {city}</h2>
            <p className="text-gray-600 mb-4">
              Discover interesting places and attractions in {city}. Find museums, restaurants, parks, and more.
            </p>
            <Link to={`/locations?city=${encodeURIComponent(city)}`} className="btn btn-primary w-full">
              View Places in {city}
            </Link>
          </div>
          
          {wikipedia && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold mb-3">Learn More</h2>
              <p className="text-gray-600 mb-4">
                Want to learn more about {city}? Visit the Wikipedia page for comprehensive information.
              </p>
              <a 
                href={wikipedia.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-outline w-full text-center"
              >
                Read on Wikipedia
              </a>
            </div>
          )}
        </div>
      </div>
    </BaseLayout>
  );
};

export default CityDetails; 