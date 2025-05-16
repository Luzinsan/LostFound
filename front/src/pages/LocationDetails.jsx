import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import BaseLayout from '../components/Layout/BaseLayout';
import locationsService from '../api/locationsService';

/**
 * Компонент для отображения отзыва
 */
const ReviewCard = ({ review }) => (
  <div className="border-b border-gray-200 pb-4 mb-4 last:border-0">
    <div className="flex items-center mb-2">
      {review.profile_photo_url ? (
        <img 
          src={review.profile_photo_url} 
          alt={review.author_name} 
          className="w-10 h-10 rounded-full mr-3"
        />
      ) : (
        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center mr-3">
          <span className="text-gray-500 font-medium">{review.author_name.charAt(0)}</span>
        </div>
      )}
      <div>
        <h4 className="font-medium">{review.author_name}</h4>
        <div className="text-sm text-gray-500">{review.relative_time_description}</div>
      </div>
    </div>
    
    <div className="flex items-center mb-2">
      {/* Звезды рейтинга */}
      {Array.from({ length: 5 }).map((_, index) => (
        <svg 
          key={index}
          className={`w-5 h-5 ${index < review.rating ? 'text-yellow-400' : 'text-gray-300'}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
    
    <p className="text-gray-700">{review.text}</p>
  </div>
);

/**
 * Страница детальной информации о локации
 */
const LocationDetails = () => {
  const { locationId } = useParams();
  const [location, setLocation] = useState(null);
  const [cityInfo, setCityInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cityInfoLoading, setCityInfoLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchLocationDetails = async () => {
      try {
        setLoading(true);
        const response = await locationsService.getLocationById(locationId);
        setLocation(response);
        setError(null);
        
        // Если у локации есть город, загружаем информацию о нем
        if (response && response.city) {
          fetchCityInfo(response.city);
        }
      } catch (err) {
        console.error('Failed to load location details:', err);
        setError('Failed to load location details. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    // Отдельная функция для загрузки информации о городе
    const fetchCityInfo = async (cityName) => {
      try {
        setCityInfoLoading(true);
        const cityData = await locationsService.getCityInfo(cityName);
        console.log('[LocationDetails] City info:', cityData);
        setCityInfo(cityData);
      } catch (err) {
        console.error(`Failed to load city info for ${cityName}:`, err);
        // Не показываем ошибку пользователю, просто логируем
      } finally {
        setCityInfoLoading(false);
      }
    };
    
    if (locationId) {
      fetchLocationDetails();
    }
  }, [locationId]);
  
  if (loading) {
    return (
      <BaseLayout title="Loading...">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </BaseLayout>
    );
  }
  
  if (error) {
    return (
      <BaseLayout title="Error">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <Link to="/locations" className="btn btn-primary">
          Back to Locations
        </Link>
      </BaseLayout>
    );
  }
  
  if (!location) {
    return (
      <BaseLayout title="Location Not Found">
        <div className="text-center p-8">
          <h3 className="text-lg font-medium text-gray-600 mb-2">Location not found</h3>
          <p className="text-gray-500 mb-4">The location you're looking for doesn't exist or has been removed.</p>
          <Link to="/locations" className="btn btn-primary">
            Browse All Locations
          </Link>
        </div>
      </BaseLayout>
    );
  }
  
  return (
    <BaseLayout title={location.name}>
      <div className="mb-6">
        <Link to="/locations" className="text-blue-600 hover:underline flex items-center">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Locations
        </Link>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Основная информация */}
        <div className="lg:col-span-2">
          <div className="card p-6 mb-6">
            <h1 className="text-2xl font-bold mb-2">{location.name}</h1>
            
            <div className="flex items-center mb-4">
              <div className="flex mr-3">
                {Array.from({ length: 5 }).map((_, index) => (
                  <svg 
                    key={index}
                    className={`w-5 h-5 ${index < Math.round(location.rating || 0) ? 'text-yellow-400' : 'text-gray-300'}`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              {location.rating && (
                <span className="text-gray-600 mr-3">
                  {location.rating.toFixed(1)} ({location.user_ratings_total} reviews)
                </span>
              )}
              {location.price_level && (
                <span className="text-gray-600">
                  Price: {'$'.repeat(parseInt(location.price_level))}
                </span>
              )}
            </div>
            
            <div className="mb-4">
              <h3 className="font-medium text-gray-700">Address:</h3>
              <p className="text-gray-600">{location.address || 'Not available'}</p>
            </div>
            
            {location.summary && (
              <div className="mb-4">
                <h3 className="font-medium text-gray-700">Description:</h3>
                <p className="text-gray-600">{location.summary}</p>
              </div>
            )}
            
            <div className="mb-4">
              <h3 className="font-medium text-gray-700">Categories:</h3>
              <div className="flex flex-wrap gap-2 mt-1">
                {location.types.map(type => (
                  <span 
                    key={type} 
                    className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                  >
                    {type}
                  </span>
                ))}
              </div>
            </div>
          </div>
          
          {/* Отзывы */}
          {location.reviews && location.reviews.length > 0 && (
            <div className="card p-6">
              <h2 className="text-xl font-semibold mb-4">Reviews</h2>
              <div>
                {location.reviews.map((review, index) => (
                  <ReviewCard key={index} review={review} />
                ))}
              </div>
            </div>
          )}
        </div>
        
        {/* Боковая панель */}
        <div className="lg:col-span-1">
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold mb-3">Location</h2>
            
            {/* Карта или фотографии */}
            {location.photos && location.photos.length > 0 ? (
              <div className="mb-4">
                <div className="bg-gray-200 rounded overflow-hidden h-48 mb-2">
                  <img 
                    src={location.photos[0]} 
                    alt={location.name} 
                    className="w-full h-full object-cover"
                  />
                </div>
                {location.photos.length > 1 && (
                  <div className="grid grid-cols-3 gap-2">
                    {location.photos.slice(1, 4).map((photo, index) => (
                      <div key={index} className="bg-gray-200 rounded overflow-hidden h-20">
                        <img 
                          src={photo} 
                          alt={`${location.name} ${index + 2}`} 
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-200 h-48 flex items-center justify-center mb-4">
                <span className="text-gray-600">Map Preview</span>
              </div>
            )}
            
            {/* Информация о городе */}
            <div className="mb-4">
              <p className="text-gray-600 mb-2">
                <span className="font-medium">City: </span>{location.city}
              </p>
              
              {/* Показываем информацию из Wikipedia, если она доступна */}
              {cityInfo && cityInfo.wikipedia && (
                <div className="mt-3 border-t pt-3">
                  <h3 className="font-medium text-gray-700 mb-2">About {location.city}</h3>
                  
                  {cityInfo.wikipedia.summary && (
                    <p className="text-sm text-gray-600 mb-2">
                      {cityInfo.wikipedia.summary.length > 200 
                        ? `${cityInfo.wikipedia.summary.substring(0, 200)}...` 
                        : cityInfo.wikipedia.summary}
                    </p>
                  )}
                  
                  {cityInfo.wikipedia.url && (
                    <a 
                      href={cityInfo.wikipedia.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="text-blue-600 text-sm hover:underline inline-flex items-center"
                    >
                      Read more on Wikipedia
                      <svg className="h-3 w-3 ml-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                      </svg>
                    </a>
                  )}
                </div>
              )}
            </div>
            
            <a 
              href={location.googleMapsUri || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(location.name)}`} 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn btn-primary w-full text-center"
            >
              View on Google Maps
            </a>
          </div>
          
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-3">Telegram Bot</h2>
            <p className="text-gray-600 mb-4">
              Get more recommendations like this by using our Telegram bot. Share your interests and receive personalized travel suggestions.
            </p>
            <a 
              href="https://t.me/LostAndFoundBot" 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn btn-outline w-full text-center"
            >
              Open in Telegram
            </a>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default LocationDetails; 