import React from 'react';
import PropTypes from 'prop-types';
import { Link, useNavigate } from 'react-router-dom';

/**
 * Компонент карточки локации
 */
const LocationCard = ({ location }) => {
  const photoUrl = location.photos && location.photos.length > 0 
    ? location.photos[0] 
    : null;
  
  const navigate = useNavigate();
  
  const handleCardClick = () => {
    navigate(`/locations/${location.doc_id}`);
  };
  const handleGoogleMapsClick = (e) => {
    e.stopPropagation();
  };
    
  return (
    <div 
      className="card overflow-hidden transition-transform hover:shadow-lg hover:-translate-y-1 cursor-pointer"
      onClick={handleCardClick}
    >
      {photoUrl && (
        <div className="h-48 overflow-hidden">
          <img 
            src={photoUrl} 
            alt={location.name} 
            className="w-full h-full object-cover"
          />
        </div>
      )}
      
      <div className="p-5">
        <h3 className="font-semibold text-lg">{location.name}</h3>
        <p className="text-gray-500 text-sm mb-2">{location.city}</p>
        
        {location.address && (
          <p className="text-gray-600 text-sm mb-3">
            <span className="font-medium">Address: </span>{location.address}
          </p>
        )}
        
        {location.summary && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">{location.summary}</p>
        )}
        
        <div className="flex flex-wrap gap-2 mb-4">
          {location.types?.map((tag) => (
            <span 
              key={tag} 
              className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
        
        <div className="flex gap-2">
          {location.googleMapsUri && (
            <a 
              href={location.googleMapsUri}
              target="_blank" 
              rel="noopener noreferrer"
              className="btn btn-outline flex items-center justify-center px-3 ml-auto"
              title="Open in Google Maps"
              onClick={handleGoogleMapsClick}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
              </svg>
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

LocationCard.propTypes = {
  location: PropTypes.shape({
    doc_id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    city: PropTypes.string.isRequired,
    types: PropTypes.arrayOf(PropTypes.string),
    address: PropTypes.string,
    summary: PropTypes.string,
    googleMapsUri: PropTypes.string,
    photos: PropTypes.arrayOf(PropTypes.string)
  }).isRequired
};

export default LocationCard; 