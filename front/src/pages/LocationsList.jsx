import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import BaseLayout from '../components/Layout/BaseLayout';
import LocationCard from '../components/Locations/LocationCard';
import LocationFilters from '../components/Locations/LocationFilters';
import SearchBar from '../components/Locations/SearchBar';
import Pagination from '../components/Common/Pagination';
import locationsService from '../api/locationsService';

/**
 * Страница списка локаций с фильтрами и пагинацией
 */
const LocationsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    perPage: 10,
    totalPages: 1,
    total: 0
  });
  const [searchMode, setSearchMode] = useState(false);
  
  // Используем useRef для отслеживания предыдущих параметров запроса
  // и предотвращения дублирующих запросов
  const prevRequestRef = useRef(null);
  const fetchTimerRef = useRef(null);
  
  // Извлекаем параметры из URL
  const page = parseInt(searchParams.get('page') || '1', 10);
  const city = searchParams.get('city') || undefined;
  const typesParam = searchParams.get('types');
  const types = typesParam ? typesParam.split(',').filter(Boolean) : undefined;
  const query = searchParams.get('query') || '';
  const searchType = searchParams.get('searchType') || 'index';
  
  // Мемоизированная функция запроса данных
  const fetchData = useCallback(async () => {
    // Формируем уникальный ключ запроса для предотвращения дублирования
    const requestKey = `query=${query}&city=${city || ''}&types=${typesParam || ''}&page=${page}&searchType=${searchType}`;
    
    // Предотвращаем дублирующиеся запросы
    if (prevRequestRef.current === requestKey) {
      console.log('[LocationsList] Skipping duplicate request:', requestKey);
      return;
    }
    
    prevRequestRef.current = requestKey;
    setLoading(true);
    setError(null);
    
    try {
      // Проверяем, есть ли поисковый запрос
      if (query && query.trim()) {
        // Используем поиск с выбранным типом
        let searchResult;
        let searchTypeStr = searchType === 'semantic' ? 'Semantic' : 'Index';
        
        console.log(`[LocationsList] Starting ${searchTypeStr} search with params:`, {
          query,
          city,
          types,
          limit: pagination.perPage
        });
        
        try {
          if (searchType === 'semantic') {
            searchResult = await locationsService.searchWithSemantic(query, city, pagination.perPage, types);
          } else {
            searchResult = await locationsService.searchWithIndex(query, city, pagination.perPage, types);
          }
          
          console.log(`[LocationsList] ${searchTypeStr} search results:`, searchResult);
          
          if (searchResult.status === 'success') {
            setLocations(searchResult.results || []);
            setPagination({
              ...pagination,
              total: searchResult.total_found || 0,
              totalPages: Math.ceil((searchResult.total_found || 0) / pagination.perPage)
            });
            setSearchMode(true);
          } else {
            throw new Error(searchResult.message || `${searchTypeStr} search failed`);
          }
        } catch (searchError) {
          console.error(`[LocationsList] ${searchTypeStr} search error:`, searchError);
          
          // Более подробная обработка ошибок поиска
          if (searchError.response) {
            // Серверная ошибка с ответом
            const status = searchError.response.status;
            const errorData = searchError.response.data;
            
            if (status === 404) {
              throw new Error(`API endpoint for ${searchTypeStr} search not found. Check server configuration.`);
            } else if (status === 400) {
              throw new Error(`Invalid search request: ${errorData.detail || 'Check your query parameters'}`);
            } else {
              throw new Error(`${searchTypeStr} search error (${status}): ${errorData.detail || searchError.message}`);
            }
          } else if (searchError.request) {
            // Запрос отправлен, но нет ответа
            throw new Error(`No response from server during ${searchTypeStr} search. Please try again later.`);
          } else {
            // Ошибка при настройке запроса
            throw searchError;
          }
        }
      } else {
        console.log('[LocationsList] Making standard locations request:', requestKey);
        
        // Обычный запрос списка локаций
        const response = await locationsService.getLocations(page, pagination.perPage, {
          city,
          types: types || []
        });
        
        console.log('[LocationsList] Locations response:', response);
        
        // Обновляем состояние компонента
        setLocations(response.results || []);
        setPagination({
          page: response.pagination?.page || 1,
          perPage: response.pagination?.per_page || 10,
          totalPages: response.pagination?.total_pages || 1,
          total: response.total || 0
        });
        setSearchMode(false);
      }
    } catch (err) {
      console.error('[LocationsList] Error fetching data:', err);
      setError(err.message || 'Failed to load locations. Please try again later.');
      setLocations([]);
    } finally {
      setLoading(false);
    }
  }, [page, city, typesParam, types, query, searchType, pagination.perPage]);
  
  // Эффект для загрузки данных при изменении URL параметров с дебаунсингом
  useEffect(() => {
    // Отображаем отладочную информацию
    console.log('[LocationsList] URL params changed:', { 
      page, 
      city, 
      typesParam,
      types,
      query,
      searchType
    });
    
    // Отменяем предыдущий запрос, если он еще не выполнен
    if (fetchTimerRef.current) {
      clearTimeout(fetchTimerRef.current);
    }
    
    // Устанавливаем новый таймер для дебаунсинга
    fetchTimerRef.current = setTimeout(() => {
      fetchData();
    }, 300); // Задержка в 300мс для предотвращения слишком частых запросов
    
    // Очищаем таймер при размонтировании
    return () => {
      if (fetchTimerRef.current) {
        clearTimeout(fetchTimerRef.current);
      }
    };
  }, [fetchData]);
  
  // Обработчик изменения фильтров - объединяем все изменения в одно обновление URL
  const handleFilterChange = (newFilters) => {
    // Объединяем текущие параметры с новыми, отфильтровывая пустые значения
    const newParams = { page: '1' };
    
    if (newFilters.city) {
      newParams.city = newFilters.city;
    }
    
    if (newFilters.types && newFilters.types.length > 0) {
      newParams.types = newFilters.types.join(',');
    }
    
    // Сохраняем поисковый запрос, если он есть
    if (query && query.trim()) {
      newParams.query = query;
    }
    
    if (newFilters.searchType) {
      newParams.searchType = newFilters.searchType;
    }
    
    console.log('[LocationsList] Setting new filters:', newParams);
    setSearchParams(newParams);
  };
  
  // Обработчик изменения страницы
  const handlePageChange = (newPage) => {
    const newParams = { ...Object.fromEntries(searchParams), page: newPage.toString() };
    setSearchParams(newParams);
  };
  
  // Обработчик поиска с сохранением выбранных фильтров
  const handleSearch = (searchQuery) => {
    // Создаем новый объект параметров, начиная с пустого
    const newParams = { page: '1' };
    
    // Явно проверяем и добавляем нужные параметры
    
    // Добавляем поисковый запрос
    if (searchQuery && searchQuery.trim()) {
      newParams.query = searchQuery.trim();
    }
    
    // Всегда сохраняем выбранный город, если он есть
    if (city) {
      newParams.city = city;
      console.log('[LocationsList] Preserving city in search:', city);
    }
    
    // Всегда сохраняем выбранные типы мест, если они есть
    if (typesParam) {
      newParams.types = typesParam;
      console.log('[LocationsList] Preserving place types in search:', typesParam);
    }
    
    // Сохраняем тип поиска
    if (searchType) {
      newParams.searchType = searchType;
    }
    
    console.log('[LocationsList] Setting search params with filters:', newParams);
    setSearchParams(newParams);
  };
  
  return (
    <BaseLayout title="Explore All Locations">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Боковая панель с фильтрами */}
        <div className="lg:col-span-1">
          <LocationFilters 
            onFilterChange={handleFilterChange}
            currentFilters={{ city, types: types || [], searchType }}
          />
        </div>
        
        {/* Основной контент */}
        <div className="lg:col-span-3">
          {/* Поисковая строка */}
          <SearchBar onSearch={handleSearch} initialQuery={query} />
          
          {/* Информация о результатах */}
          <div className="mb-4 flex justify-between items-center">
            <h2 className="text-xl">
              {searchMode && query && (
                <span>Search results for "{query}"</span>
              )}
              {!searchMode && pagination.total > 0 && (
                <span>Found {pagination.total} location{pagination.total !== 1 ? 's' : ''}</span>
              )}
              {!searchMode && !loading && pagination.total === 0 && (
                <span>No locations found</span>
              )}
            </h2>
            {searchMode && (
              <div className="text-sm text-gray-500">
                {searchType === 'semantic' ? 'Semantic Search' : 'Index Search'}
              </div>
            )}
          </div>
          
          {/* Индикатор загрузки */}
          {loading && (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          )}
          
          {/* Сообщение об ошибке */}
          {error && !loading && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <p className="font-medium">Error: {error}</p>
              {query && (
                <p className="mt-2 text-sm">
                  Try using different search terms or switching between Index and Semantic search types.
                </p>
              )}
            </div>
          )}
          
          {/* Список локаций */}
          {!loading && !error && locations.length === 0 ? (
            <div className="text-center p-8 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-medium text-gray-600 mb-2">No locations found</h3>
              <p className="text-gray-500">Try changing your filters or search criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {locations.map(location => (
                <LocationCard key={location.doc_id} location={location} />
              ))}
            </div>
          )}
          
          {/* Активные фильтры (добавляем для наглядности) */}
          {(city || typesParam) && (
            <div className="mt-4 p-2 bg-gray-50 rounded-md">
              <h4 className="text-sm font-medium text-gray-700 mb-1">Active filters:</h4>
              <div className="flex flex-wrap gap-2">
                {city && (
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                    City: {city}
                  </span>
                )}
                {types && types.map(type => (
                  <span key={type} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                    {type}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Пагинация */}
          {!loading && !error && locations.length > 0 && !searchMode && (
            <Pagination
              currentPage={pagination.page}
              totalPages={pagination.totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </div>
      </div>
    </BaseLayout>
  );
};

export default LocationsList; 