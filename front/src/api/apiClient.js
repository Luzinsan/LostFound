import axios from 'axios';

// Создаем экземпляр axios с базовым URL
const apiClient = axios.create({
  baseURL: '/api/v1', // Обновленный URL с версией API
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Счетчик активных запросов для отладки
let activeRequests = 0;

// Функция для логирования подробной информации запроса
const logRequestDetails = (config) => {
  console.group(`[API] Request details for: ${config.method.toUpperCase()} ${config.url}`);
  console.log('Full URL:', `${config.baseURL}${config.url}`);
  console.log('Headers:', config.headers);
  if (config.params) console.log('Query params:', config.params);
  if (config.data) console.log('Request body:', config.data);
  console.groupEnd();
};

// Функция для логирования подробной информации ответа
const logResponseDetails = (response) => {
  console.group(`[API] Response details for: ${response.config.method.toUpperCase()} ${response.config.url}`);
  console.log('Status:', response.status, response.statusText);
  console.log('Headers:', response.headers);
  console.log('Data:', response.data);
  console.groupEnd();
};

// Добавляем глобальные перехватчики запросов и ответов
apiClient.interceptors.request.use(
  (config) => {
    activeRequests++;
    console.log(`[API] Request started: ${config.method.toUpperCase()} ${config.url}`, {
      params: config.params,
      activeRequests
    });
    
    // Подробное логирование запроса
    logRequestDetails(config);
    
    // Очищаем undefined и null значения из параметров запроса
    if (config.params) {
      Object.keys(config.params).forEach(key => {
        if (config.params[key] === undefined || config.params[key] === null) {
          delete config.params[key];
        }
      });
    }
    
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Добавляем глобальную обработку ответов
apiClient.interceptors.response.use(
  (response) => {
    activeRequests--;
    console.log(`[API] Request completed: ${response.config.method.toUpperCase()} ${response.config.url}`, {
      status: response.status,
      activeRequests
    });
    
    // Подробное логирование успешного ответа
    logResponseDetails(response);
    
    return response;
  },
  (error) => {
    activeRequests--;
    // Централизованная обработка ошибок
    console.error('[API] Response error:', {
      url: error.config?.url,
      method: error.config?.method?.toUpperCase(),
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
      activeRequests
    });
    
    // Подробное логирование ошибки
    if (error.response) {
      console.group('[API] Error response details');
      console.log('Status:', error.response.status, error.response.statusText);
      console.log('Headers:', error.response.headers);
      console.log('Data:', error.response.data);
      console.groupEnd();
    } else if (error.request) {
      console.error('[API] No response received', error.request);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient; 