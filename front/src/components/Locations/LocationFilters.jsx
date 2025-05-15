import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import locationsService from '../../api/locationsService';

/**
 * Компонент фильтров для списка локаций
 */
const LocationFilters = ({ onFilterChange, currentFilters }) => {
  const [cities, setCities] = useState([]);
  const [placeTypes, setPlaceTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Локальное состояние фильтров без немедленной отправки запросов
  const [localFilters, setLocalFilters] = useState({
    city: currentFilters.city || '',
    types: currentFilters.types || [],
    searchType: currentFilters.searchType || 'index' // Добавляем тип поиска, по умолчанию индексный
  });
  
  // Загрузка городов и типов мест при монтировании компонента
  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        setLoading(true);
        // Получаем базовую информацию о системе (типы мест)
        const systemResponse = await locationsService.getSystemInfo();
        
        // Устанавливаем типы мест из системной информации
        setPlaceTypes(systemResponse.place_types || []);
        
        // Используем массив строк с названиями городов из системной информации для простоты
        if (systemResponse.cities && Array.isArray(systemResponse.cities)) {
          setCities(systemResponse.cities || []);
        } else {
          setCities([]);
        }
        
        setError(null);
      } catch (err) {
        console.error('Failed to load system info:', err);
        setError('Failed to load filters. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSystemInfo();
  }, []);
  
  // Обновляем локальное состояние, когда изменяются пропсы
  useEffect(() => {
    setLocalFilters({
      city: currentFilters.city || '',
      types: currentFilters.types || [],
      searchType: currentFilters.searchType || 'index'
    });
  }, [currentFilters]);
  
  // Мемоизированный обработчик применения фильтров
  const applyFilters = useCallback(() => {
    const newFilters = {
      city: localFilters.city || null,
      types: localFilters.types.length > 0 ? localFilters.types : null,
      searchType: localFilters.searchType
    };
    onFilterChange(newFilters);
  }, [localFilters, onFilterChange]);
  
  // Обработчик изменения города
  const handleCityChange = (e) => {
    setLocalFilters(prev => ({
      ...prev,
      city: e.target.value
    }));
  };
  
  // Обработчик изменения типов мест
  const handleTypeChange = (type) => {
    setLocalFilters(prev => {
      const newTypes = prev.types.includes(type)
        ? prev.types.filter(t => t !== type)
        : [...prev.types, type];
      
      return {
        ...prev,
        types: newTypes
      };
    });
  };
  
  // Обработчик изменения типа поиска
  const handleSearchTypeChange = (e) => {
    setLocalFilters(prev => ({
      ...prev,
      searchType: e.target.value
    }));
  };
  
  // Сброс всех фильтров
  const handleReset = () => {
    setLocalFilters({ city: '', types: [], searchType: 'index' });
    onFilterChange({ city: null, types: null, searchType: 'index' });
  };
  
  if (loading) {
    return <div className="p-4 text-center">Loading filters...</div>;
  }
  
  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }
  
  return (
    <div className="card p-4 mb-6">
      <h3 className="text-lg font-semibold mb-4">Filters</h3>
      
      {/* Выбор типа поиска */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Search Type</label>
        <div className="flex flex-col space-y-2">
          <label className="inline-flex items-center">
            <input
              type="radio"
              className="form-radio"
              name="searchType"
              value="index"
              checked={localFilters.searchType === 'index'}
              onChange={handleSearchTypeChange}
            />
            <span className="ml-2">Index Search</span>
            <span className="ml-2 text-xs text-gray-500">(Keyword-based with TF-IDF ranking)</span>
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              className="form-radio"
              name="searchType"
              value="semantic"
              checked={localFilters.searchType === 'semantic'}
              onChange={handleSearchTypeChange}
            />
            <span className="ml-2">Semantic Search</span>
            <span className="ml-2 text-xs text-gray-500">(Natural language understanding)</span>
          </label>
        </div>
      </div>
      
      {/* Фильтр по городу */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
        <select
          className="input"
          value={localFilters.city || ''}
          onChange={handleCityChange}
        >
          <option value="">All Cities</option>
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>
      
      {/* Фильтр по типам мест */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Place Types</label>
        <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-2 border border-gray-200 rounded-md">
          {placeTypes.map(type => (
            <div key={type} className="flex items-center">
              <input
                type="checkbox"
                id={`type-${type}`}
                checked={localFilters.types.includes(type)}
                onChange={() => handleTypeChange(type)}
                className="mr-1"
              />
              <label htmlFor={`type-${type}`} className="text-sm cursor-pointer">
                {type}
              </label>
            </div>
          ))}
        </div>
      </div>
      
      {/* Кнопки управления */}
      <div className="flex space-x-2">
        <button 
          className="btn btn-primary flex-1"
          onClick={applyFilters}
        >
          Apply Filters
        </button>
        
        <button 
          className="btn btn-outline flex-1"
          onClick={handleReset}
        >
          Reset
        </button>
      </div>
    </div>
  );
};

LocationFilters.propTypes = {
  onFilterChange: PropTypes.func.isRequired,
  currentFilters: PropTypes.shape({
    city: PropTypes.string,
    types: PropTypes.arrayOf(PropTypes.string),
    searchType: PropTypes.string
  })
};

LocationFilters.defaultProps = {
  currentFilters: { city: null, types: [], searchType: 'index' }
};

export default LocationFilters; 