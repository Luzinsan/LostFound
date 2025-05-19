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
    searchType: currentFilters.searchType || 'index', // Добавляем тип поиска, по умолчанию индексный
    useLLM: currentFilters.useLLM || false,
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
      searchType: currentFilters.searchType || 'index',
      useLLM: currentFilters.useLLM || false,
    });
  }, [currentFilters]);
  
  // Мемоизированный обработчик применения фильтров
  const applyFilters = useCallback(() => {
    const newFilters = {
      city: localFilters.city || null,
      types: localFilters.types.length > 0 ? localFilters.types : null,
      searchType: localFilters.searchType,
      useLLM: localFilters.useLLM,
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
    setLocalFilters({ city: '', types: [], searchType: 'index', useLLM: false });
    onFilterChange({ city: null, types: null, searchType: 'index', useLLM: false });
  };
  
  if (loading) {
    return <div className="p-4 text-center">Loading filters...</div>;
  }
  
  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }
  
  return (
    <div className="card p-6 mb-6 rounded-2xl shadow-lg bg-gradient-to-br from-white via-blue-50 to-purple-50 border border-blue-100 animate-fade-in min-h-[420px]">
      <h3 className="text-xl font-bold mb-4 text-blue-700 flex items-center gap-2">
        <svg className="h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v16a1 1 0 01-1 1H4a1 1 0 01-1-1V4z" /></svg>
        Filters
      </h3>
      
      {/* Search Type selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Search Type</label>
        <div className="flex flex-col space-y-2">
          <label className="inline-flex items-center cursor-pointer">
            <input
              type="radio"
              className="form-radio accent-blue-600"
              name="searchType"
              value="index"
              checked={localFilters.searchType === 'index'}
              onChange={handleSearchTypeChange}
            />
            <span className="ml-2 font-medium">Index Search</span>
            <span className="ml-2 text-xs text-gray-500">(Keyword-based with TF-IDF ranking)</span>
          </label>
          <label className="inline-flex items-center cursor-pointer">
            <input
              type="radio"
              className="form-radio accent-purple-600"
              name="searchType"
              value="semantic"
              checked={localFilters.searchType === 'semantic'}
              onChange={handleSearchTypeChange}
            />
            <span className="ml-2 font-medium">Semantic Search</span>
            <span className="ml-2 text-xs text-gray-500">(Natural language understanding)</span>
          </label>
        </div>
        {localFilters.searchType === 'semantic' && (
          <div className="mt-2">
            <label className="inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="form-checkbox accent-pink-500"
                checked={localFilters.useLLM}
                onChange={e => setLocalFilters(prev => ({ ...prev, useLLM: e.target.checked }))}
              />
              <span className="ml-2 font-medium">Use LLM</span>
            </label>
          </div>
        )}
      </div>
      
      {/* City filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
        <select
          className="input rounded-lg border-blue-200 focus:ring-2 focus:ring-blue-400"
          value={localFilters.city || ''}
          onChange={handleCityChange}
        >
          <option value="">All Cities</option>
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>
      
      {/* Place Types filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">Place Types</label>
        <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-2 border border-blue-100 rounded-lg bg-white/60">
          {placeTypes.map(type => (
            <div key={type} className="flex items-center">
              <input
                type="checkbox"
                id={`type-${type}`}
                checked={localFilters.types.includes(type)}
                onChange={() => handleTypeChange(type)}
                className="accent-blue-500 mr-1"
              />
              <label htmlFor={`type-${type}`} className="text-sm cursor-pointer">
                {type}
              </label>
            </div>
          ))}
        </div>
      </div>
      
      {/* Control buttons */}
      <div className="flex justify-between items-center mt-6 gap-2">
        <button
          className="px-4 py-2 rounded-lg border border-blue-300 bg-gradient-to-r from-white to-blue-50 text-blue-700 font-semibold shadow hover:bg-blue-100 transition-all text-sm"
          type="button"
          onClick={handleReset}
        >
          Reset Filters
        </button>
        <button
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold shadow hover:scale-105 hover:from-pink-500 hover:to-blue-500 transition-all text-sm"
          type="button"
          onClick={applyFilters}
        >
          Apply Filters
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
    searchType: PropTypes.string,
    useLLM: PropTypes.bool
  })
};

LocationFilters.defaultProps = {
  currentFilters: { city: null, types: [], searchType: 'index', useLLM: false }
};

export default LocationFilters; 