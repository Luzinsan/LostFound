import React from 'react';
import PropTypes from 'prop-types';

/**
 * Компонент пагинации
 */
const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  // Если страниц меньше 2, не показываем пагинацию
  if (totalPages < 2) return null;
  
  // Генерируем массив страниц для отображения
  const getPageNumbers = () => {
    const range = [];
    const maxPagesToShow = 5; // Максимальное количество кнопок страниц для отображения
    
    // Если общее количество страниц меньше или равно максимальному, отображаем все
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        range.push(i);
      }
    } else {
      // Иначе отображаем текущую страницу в центре, если возможно
      let start = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
      let end = start + maxPagesToShow - 1;
      
      // Корректируем, если end выходит за пределы
      if (end > totalPages) {
        end = totalPages;
        start = Math.max(1, end - maxPagesToShow + 1);
      }
      
      for (let i = start; i <= end; i++) {
        range.push(i);
      }
      
      // Добавляем многоточие, если начало не с 1
      if (start > 1) {
        range.unshift('...');
        range.unshift(1);
      }
      
      // Добавляем многоточие, если конец не до totalPages
      if (end < totalPages) {
        range.push('...');
        range.push(totalPages);
      }
    }
    
    return range;
  };
  
  const pageNumbers = getPageNumbers();
  
  return (
    <nav className="flex justify-center mt-8" aria-label="Pagination">
      <ul className="flex items-center space-x-1">
        {/* Кнопка "Назад" */}
        <li>
          <button
            className={`px-3 py-2 rounded-md border ${
              currentPage === 1
                ? 'text-gray-400 border-gray-200 cursor-not-allowed'
                : 'text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
            onClick={() => currentPage > 1 && onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            aria-label="Previous page"
          >
            &laquo;
          </button>
        </li>
        
        {/* Кнопки страниц */}
        {pageNumbers.map((page, index) => (
          <li key={index}>
            {page === '...' ? (
              <span className="px-3 py-2 text-gray-500">...</span>
            ) : (
              <button
                className={`px-3 py-2 rounded-md ${
                  currentPage === page
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
                onClick={() => onPageChange(page)}
                aria-current={currentPage === page ? 'page' : undefined}
              >
                {page}
              </button>
            )}
          </li>
        ))}
        
        {/* Кнопка "Вперед" */}
        <li>
          <button
            className={`px-3 py-2 rounded-md border ${
              currentPage === totalPages
                ? 'text-gray-400 border-gray-200 cursor-not-allowed'
                : 'text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
            onClick={() => currentPage < totalPages && onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            aria-label="Next page"
          >
            &raquo;
          </button>
        </li>
      </ul>
    </nav>
  );
};

Pagination.propTypes = {
  currentPage: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired
};

export default Pagination; 