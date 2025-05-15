import apiClient from './apiClient';

/**
 * Сервис для работы с API локаций
 */
const locationsService = {
  /**
   * Получить список локаций с фильтрацией и пагинацией
   * 
   * @param {number} page - Номер страницы (начиная с 1)
   * @param {number} perPage - Количество записей на страницу
   * @param {Object} filters - Фильтры
   * @param {string} [filters.city] - Город (название города)
   * @param {Array<string>} [filters.types] - Типы мест
   * @returns {Promise<Object>} - Список локаций с информацией о пагинации
   */
  getLocations: async (page = 1, perPage = 10, filters = {}) => {
    try {
      // Формируем URL запроса напрямую, как в успешном curl-запросе
      let url = `/locations?page=${page}&per_page=${perPage}`;
      
      // Город всегда передается как простая строка (название города)
      if (filters.city) {
        url += `&city=${encodeURIComponent(filters.city)}`;
      }
      
      // Добавляем типы мест в формате &types=value1&types=value2
      if (filters.types && Array.isArray(filters.types) && filters.types.length > 0) {
        // Добавляем каждый тип как отдельный параметр
        filters.types.forEach(type => {
          url += `&types=${encodeURIComponent(type)}`;
        });
        console.log("[Locations] Using direct URL with multiple types:", url);
      }
      
      console.log("[Locations] Final request URL:", url);
      
      // Отправляем запрос напрямую с URL
      const response = await apiClient.get(url);
      
      // Проверяем формат ответа
      if (!response.data || !Array.isArray(response.data.results)) {
        console.warn('[Locations] Unexpected API response format:', response.data);
        return {
          results: [],
          pagination: { page, per_page: perPage, total_pages: 0 },
          total: 0
        };
      }
      
      return response.data;
    } catch (error) {
      console.error('[Locations] Error fetching locations:', error);
      throw error;
    }
  },

  /**
   * Поиск локаций с использованием индексного поиска
   * 
   * @param {string} query - Поисковый запрос
   * @param {string} [city] - Город для поиска (опционально)
   * @param {number} [limit=10] - Максимальное количество результатов
   * @param {Array<string>} [types] - Типы мест для фильтрации (опционально)
   * @returns {Promise<Object>} - Результаты поиска
   */
  searchWithIndex: async (query, city = null, limit = 10, types = null) => {
    try {
      if (!query || !query.trim()) {
        throw new Error('Search query cannot be empty');
      }
      
      let url;
      const params = new URLSearchParams();
      params.append('query', query);
      params.append('limit', limit);
      
      // Добавляем параметры типов
      if (types && Array.isArray(types) && types.length > 0) {
        types.forEach(type => {
          params.append('types', type);
        });
      }
      
      if (city) {
        url = `/index_search/city/${encodeURIComponent(city)}?${params.toString()}`;
      } else {
        url = `/index_search/all?${params.toString()}`;
      }
      
      console.log("[Search] Index search request URL:", url);
      const response = await apiClient.get(url);
      
      // Валидация ответа
      if (!response.data) {
        throw new Error('Empty response from index search');
      }
      
      // Если сервер вернул статус ошибки
      if (response.data.status === 'error') {
        throw new Error(response.data.message || 'Index search failed');
      }
      
      return response.data;
    } catch (error) {
      console.error('[Search] Error during index search:', error);
      
      // Преобразование ошибки в удобный формат
      if (error.response) {
        // Добавить информацию из ответа сервера
        const errorDetails = error.response.data?.detail || error.response.statusText;
        error.message = `Index search failed: ${errorDetails}`;
      } else if (!error.message) {
        error.message = 'Index search failed. Please try again later.';
      }
      
      throw error;
    }
  },
  
  /**
   * Поиск локаций с использованием семантического поиска
   * 
   * @param {string} query - Поисковый запрос
   * @param {string} [city] - Город для поиска (опционально)
   * @param {number} [limit=10] - Максимальное количество результатов
   * @param {Array<string>} [types] - Типы мест для фильтрации (опционально)
   * @returns {Promise<Object>} - Результаты поиска
   */
  searchWithSemantic: async (query, city = null, limit = 10, types = null) => {
    try {
      if (!query || !query.trim()) {
        throw new Error('Search query cannot be empty');
      }
      
      let url;
      const params = new URLSearchParams();
      params.append('query', query);
      params.append('limit', limit);
      
      // Добавляем параметры типов
      if (types && Array.isArray(types) && types.length > 0) {
        types.forEach(type => {
          params.append('types', type);
        });
      }
      
      if (city) {
        url = `/semantic/city/${encodeURIComponent(city)}?${params.toString()}`;
      } else {
        url = `/semantic/all?${params.toString()}`;
      }
      
      console.log("[Search] Semantic search request URL:", url);
      const response = await apiClient.get(url);
      
      // Валидация ответа
      if (!response.data) {
        throw new Error('Empty response from semantic search');
      }
      
      // Если сервер вернул статус ошибки
      if (response.data.status === 'error') {
        throw new Error(response.data.message || 'Semantic search failed');
      }
      
      return response.data;
    } catch (error) {
      console.error('[Search] Error during semantic search:', error);
      
      // Преобразование ошибки в удобный формат
      if (error.response) {
        // Добавить информацию из ответа сервера
        const errorDetails = error.response.data?.detail || error.response.statusText;
        error.message = `Semantic search failed: ${errorDetails}`;
      } else if (!error.message) {
        error.message = 'Semantic search failed. Please try again later.';
      }
      
      throw error;
    }
  },

  /**
   * Получить детальную информацию о локации по ID
   * 
   * @param {string} locationId - Уникальный идентификатор локации
   * @returns {Promise<Object>} - Детальная информация о локации
   */
  getLocationById: async (locationId) => {
    if (!locationId) {
      throw new Error('Location ID is required');
    }
    
    try {
      const response = await apiClient.get(`/locations/${locationId}`);
      return response.data;
    } catch (error) {
      console.error(`[Locations] Error fetching location details for ID ${locationId}:`, error);
      throw error;
    }
  },
  
  /**
   * Получить доступные города и типы мест
   * 
   * @returns {Promise<Object>} - Информация о системе, включая доступные города и типы мест
   */
  getSystemInfo: async () => {
    try {
      const response = await apiClient.get('/system/status');
      return response.data;
    } catch (error) {
      console.error('[Locations] Error fetching system info:', error);
      throw error;
    }
  },
  
  /**
   * Получить детальную информацию о городе из Wikipedia
   * 
   * @param {string} cityName - Название города
   * @returns {Promise<Object>} - Детальная информация о городе, включая данные из Wikipedia
   */
  getCityInfo: async (cityName) => {
    if (!cityName) {
      throw new Error('City name is required');
    }
    
    try {
      // Использование параметра city для фильтрации данных на сервере
      const response = await apiClient.get(`/system/cities?city=${encodeURIComponent(cityName)}`);
      
      if (response.data && response.data.cities && Array.isArray(response.data.cities) && response.data.cities.length > 0) {
        // Возвращаем первый элемент
        return response.data.cities[0];
      }
      
      // Если город не найден, возвращаем только название
      return { city: cityName };
    } catch (error) {
      console.error(`[Locations] Error fetching city info for ${cityName}:`, error);
      throw error;
    }
  },
  
  /**
   * Получить детальную информацию о всех городах
   * 
   * @returns {Promise<Array>} - Массив с детальной информацией о всех городах
   */
  getDetailedCitiesInfo: async () => {
    try {
      const response = await apiClient.get('/system/cities');
      
      if (response.data && response.data.cities && Array.isArray(response.data.cities)) {
        return response.data.cities;
      }
      
      return [];
    } catch (error) {
      console.error('[Locations] Error fetching detailed cities info:', error);
      throw error;
    }
  }
};

export default locationsService; 