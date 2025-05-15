import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

/**
 * Компонент карточки локации
 */
const LocationCard = ({ location }) => {
  return (
    <div className="card overflow-hidden transition-transform hover:shadow-lg hover:-translate-y-1">
      <div className="p-5">
        <h3 className="font-semibold text-lg">{location.name}</h3>
        <p className="text-gray-500 text-sm mb-2">{location.city}</p>
        
        {location.address && (
          <p className="text-gray-600 text-sm mb-3">
            <span className="font-medium">Address: </span>{location.address}
          </p>
        )}
        
        {location.summary && (
          <p className="text-gray-600 text-sm mb-3">{location.summary}</p>
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
        
        <Link 
          to={`/locations/${location.doc_id}`}
          className="btn btn-primary w-full text-center"
        >
          View Details
        </Link>
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
    summary: PropTypes.string
  }).isRequired
};

export default LocationCard; 