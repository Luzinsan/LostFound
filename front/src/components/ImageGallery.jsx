import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

/**
 * Компонент галереи изображений со слайдером
 */
const ImageGallery = ({ photos, locationName }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalIndex, setModalIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);
  
  const sliderRef = useRef(null);
  const thumbnailsRef = useRef(null);
  const minSwipeDistance = 50;
  
  const handlePrev = (e) => {
    if (e) e.stopPropagation();
    if (isAnimating) return;
    
    setIsAnimating(true);
    setActiveIndex((prev) => (prev === 0 ? photos.length - 1 : prev - 1));
    setTimeout(() => setIsAnimating(false), 300);
  };
  
  const handleNext = (e) => {
    if (e) e.stopPropagation();
    if (isAnimating) return;
    
    setIsAnimating(true);
    setActiveIndex((prev) => (prev === photos.length - 1 ? 0 : prev + 1));
    setTimeout(() => setIsAnimating(false), 300);
  };
  
  const onTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };
  
  const onTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };
  
  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;
    
    if (isLeftSwipe) {
      handleNext();
    } else if (isRightSwipe) {
      handlePrev();
    }
  };
  
  // Обработчики для модального окна
  const openModal = (index) => {
    setModalIndex(index);
    setIsModalOpen(true);
    document.body.style.overflow = 'hidden';
  };
  
  const closeModal = () => {
    setIsModalOpen(false);
    document.body.style.overflow = 'auto';
  };
  
  const handleModalPrev = () => {
    setModalIndex((prev) => (prev === 0 ? photos.length - 1 : prev - 1));
  };
  
  const handleModalNext = () => {
    setModalIndex((prev) => (prev === photos.length - 1 ? 0 : prev + 1));
  };
  
  // Обработчик клавиатурной навигации
  const handleKeyDown = (e) => {
    if (!isModalOpen) return;
    
    if (e.key === 'ArrowLeft') handleModalPrev();
    else if (e.key === 'ArrowRight') handleModalNext();
    else if (e.key === 'Escape') closeModal();
  };
  
  // Прокрутка миниатюр, чтобы активная была видна
  useEffect(() => {
    if (thumbnailsRef.current && photos.length > 5) {
      const thumbnailWidth = thumbnailsRef.current.children[0].offsetWidth + 8; // ширина + отступ
      thumbnailsRef.current.scrollLeft = activeIndex * thumbnailWidth;
    }
  }, [activeIndex, photos.length]);
  
  // Добавляем обработчик клавиатуры при открытии модального окна
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isModalOpen, modalIndex]);
  
  // Автоматическая смена слайдов
  useEffect(() => {
    if (photos.length <= 1) return;
    
    const interval = setInterval(() => {
      if (!isModalOpen && document.visibilityState === 'visible') {
        handleNext();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [isModalOpen, photos.length]);
  
  return (
    <>
      {/* Основная галерея */}
      <div className="gallery">
        {/* Основное изображение со слайдером */}
        <div 
          ref={sliderRef}
          className="relative rounded-lg overflow-hidden h-60 mb-3 shadow-md"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          <div 
            className="absolute inset-0 w-full h-full transition-transform duration-500 ease-in-out"
            style={{ 
              transform: `translateX(-${activeIndex * 100}%)`,
              display: 'flex' 
            }}
          >
            {photos.map((photo, index) => (
              <div 
                key={index} 
                className="min-w-full h-full flex-shrink-0 bg-gray-100"
                style={{ scrollSnapAlign: 'start' }}
              >
                <img
                  src={photo}
                  alt={`${locationName} - Image ${index + 1}`}
                  className="w-full h-full object-cover cursor-pointer"
                  onClick={() => openModal(index)}
                  loading={index === 0 ? "eager" : "lazy"}
                />
              </div>
            ))}
          </div>
          
          {/* Навигационные кнопки */}
          {photos.length > 1 && (
            <>
              <button
                onClick={handlePrev}
                className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/70 hover:bg-white/90 flex items-center justify-center shadow-md transition-all duration-200 transform hover:scale-105"
                aria-label="Предыдущее фото"
              >
                <svg className="w-5 h-5 text-gray-800" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button
                onClick={handleNext}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/70 hover:bg-white/90 flex items-center justify-center shadow-md transition-all duration-200 transform hover:scale-105"
                aria-label="Следующее фото"
              >
                <svg className="w-5 h-5 text-gray-800" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </>
          )}
          
          {/* Счетчик и кнопка полноэкранного режима */}
          <div className="absolute bottom-3 right-3 flex items-center space-x-2">
            <div className="bg-black/60 text-white text-xs px-3 py-1.5 rounded-full backdrop-blur-sm">
              {activeIndex + 1} / {photos.length}
            </div>
            <button
              onClick={() => openModal(activeIndex)}
              className="bg-black/60 text-white p-1.5 rounded-full backdrop-blur-sm"
              aria-label="Открыть в полноэкранном режиме"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
              </svg>
            </button>
          </div>
        </div>
        
        {/* Миниатюры */}
        {photos.length > 1 && (
          <div 
            ref={thumbnailsRef}
            className="flex overflow-x-auto space-x-2 pb-2 hide-scrollbar snap-x"
            style={{ scrollBehavior: 'smooth' }}
          >
            {photos.map((photo, index) => (
              <div
                key={index}
                className={`relative flex-shrink-0 rounded-md overflow-hidden h-16 w-20 cursor-pointer transition-all duration-200 snap-start ${
                  activeIndex === index 
                    ? 'ring-2 ring-blue-500 opacity-100 transform scale-105' 
                    : 'opacity-70 hover:opacity-100'
                }`}
                onClick={() => setActiveIndex(index)}
              >
                <img
                  src={photo}
                  alt={`${locationName} миниатюра ${index + 1}`}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                {activeIndex === index && (
                  <div className="absolute inset-0 border-2 border-blue-500 rounded-md"></div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Полноэкранный режим */}
      {isModalOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center"
          onClick={closeModal}
        >
          <div 
            className="relative w-full h-full flex flex-col items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Кнопка закрытия */}
            <button
              onClick={closeModal}
              className="absolute top-4 right-4 w-10 h-10 flex items-center justify-center bg-black/50 hover:bg-black/70 rounded-full text-white z-50 transition-colors"
              aria-label="Закрыть"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {/* Счетчик фото */}
            <div className="absolute top-4 left-4 bg-black/50 text-white px-3 py-1.5 rounded-full z-50 backdrop-blur-sm">
              {modalIndex + 1} / {photos.length}
            </div>
            
            {/* Основное изображение */}
            <div className="relative w-full h-full flex items-center justify-center">
              <img
                src={photos[modalIndex]}
                alt={`${locationName} - фото ${modalIndex + 1} (полноэкранный режим)`}
                className="max-h-[85vh] max-w-[90vw] object-contain transition-opacity duration-300"
                style={{ filter: 'drop-shadow(0 0 10px rgba(0,0,0,0.3))' }}
              />
            </div>
            
            {/* Навигационные кнопки */}
            <button
              onClick={handleModalPrev}
              className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center transition-all duration-200 backdrop-blur-sm"
              aria-label="Предыдущее фото"
            >
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={handleModalNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center transition-all duration-200 backdrop-blur-sm"
              aria-label="Следующее фото"
            >
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            
            {/* Миниатюры в модальном окне */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex justify-center items-center space-x-2 overflow-x-auto p-2 max-w-[80vw] hide-scrollbar bg-black/30 rounded-lg backdrop-blur-sm">
              {photos.map((photo, index) => (
                <div 
                  key={index}
                  className={`h-14 w-18 rounded-md overflow-hidden cursor-pointer transition-all duration-200 transform ${
                    modalIndex === index ? 'ring-2 ring-white scale-105' : 'opacity-60 hover:opacity-100'
                  }`}
                  onClick={() => setModalIndex(index)}
                >
                  <img 
                    src={photo} 
                    alt={`Миниатюра ${index + 1}`}
                    className="h-full w-full object-cover"
                    loading="lazy" 
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Скрытие скроллбара */}
      <style jsx="true">{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </>
  );
};

ImageGallery.propTypes = {
  photos: PropTypes.arrayOf(PropTypes.string).isRequired,
  locationName: PropTypes.string.isRequired
};

export default ImageGallery; 