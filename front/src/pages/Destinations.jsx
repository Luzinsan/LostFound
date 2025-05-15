import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import BaseLayout from '../components/Layout/BaseLayout';
import locationsService from '../api/locationsService';
import { 
  CITY_TAGS, 
  CITY_DESCRIPTIONS, 
  DEFAULT_TAGS, 
  getCityImageBySize 
} from '../constants/cityData';

// Значения по умолчанию для городов без данных
const defaultImage = 'https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=600&q=80';
const defaultTags = ['Travel', 'Explore'];

// Дополнительные изображения для городов (временное решение до добавления изображений на бэкенд)
const cityImages = {
  'Москва': 'https://images.unsplash.com/photo-1513326738677-b964603b136d?auto=format&fit=crop&w=600&q=80',
  'Санкт-Петербург': 'https://images.unsplash.com/photo-1556610961-2fecc5927173?auto=format&fit=crop&w=600&q=80',
  'Нижний Новгород': 'https://icdn.lenta.ru/images/2021/03/11/16/20210311164138357/wide_4_3_65e872eb0d009429c7df3a5a48af7af9.jpg',
  'Сочи': 'https://images.unsplash.com/photo-1597591723433-e7b40d988d89?auto=format&fit=crop&w=600&q=80'
};

// Теги для городов (более содержательные и тематические)
const cityTags = {
  'Москва': ['История', 'Культура', 'Столица'],
  'Санкт-Петербург': ['Архитектура', 'Искусство', 'Музеи'],
  'Нижний Новгород': ['История', 'Волга', 'Природа'],
  'Сочи': ['Море', 'Горы', 'Курорт']
};

// Подробные описания городов
const cityDescriptions = {
  'Москва': 'Москва — столица России, один из крупнейших культурных и экономических центров мира. Здесь расположены знаменитые достопримечательности, включая Кремль, Красную площадь, собор Василия Блаженного и Третьяковскую галерею. Город предлагает множество музеев, театров, концертных залов, а также имеет обширную сеть парков и зеленых зон.',
  'Санкт-Петербург': 'Санкт-Петербург — культурная столица России, город музеев и выдающейся архитектуры. Известен разводными мостами, фонтанами Петергофа, Эрмитажем и Русским музеем. Город построен на многочисленных островах в дельте реки Невы и славится своими белыми ночами, каналами и дворцовыми ансамблями.',
  'Нижний Новгород': 'Нижний Новгород — один из старейших и живописнейших городов России, расположенный на слиянии рек Оки и Волги. Нижегородский кремль, основанный в 1221 году, является историческим центром города. Отсюда открывается великолепный вид на речные просторы и старинные храмы. Город славится своей богатой историей, традициями и уникальной архитектурой.',
  'Сочи': 'Сочи — курортный город на побережье Чёрного моря, знаменитый своим уникальным сочетанием пляжного и горнолыжного отдыха. Здесь можно утром купаться в тёплом море, а днём кататься на лыжах в горах Красной Поляны. Город принимал Зимние Олимпийские игры 2014 года и предлагает отличную инфраструктуру: дендрарий, парк "Ривьера", океанариум и многочисленные СПА-курорты.'
};

const Destinations = () => {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCities = async () => {
      try {
        setLoading(true);
        // Получаем детальную информацию о всех городах
        const citiesData = await locationsService.getDetailedCitiesInfo();
        
        if (citiesData && citiesData.length > 0) {
          // Форматируем данные для отображения в UI
          const formattedCities = citiesData.map((cityData, index) => {
            // Используем описание из констант или из Wikipedia как запасной вариант
            let description = CITY_DESCRIPTIONS[cityData.city] || 'Discover this amazing destination with unique attractions and experiences';
            if (!description && cityData.wikipedia?.summary) {
              // Используем больше текста из википедии, первый абзац
              const textContent = cityData.wikipedia.summary.split('\n')[0];
              if (textContent) {
                description = textContent;
              }
            }
            
            // Получаем теги для города или используем дефолтные
            const tags = CITY_TAGS[cityData.city] || DEFAULT_TAGS;
            
            return {
              id: index + 1,
              name: cityData.city,
              description: description,
              tags: tags,
              image: getCityImageBySize(cityData.city, false)
            };
          });
          setCities(formattedCities);
        } else {
          setCities([]);
        }
        setError(null);
      } catch (err) {
        console.error('Failed to load cities:', err);
        setError('Failed to load destinations. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchCities();
  }, []);

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
      </BaseLayout>
    );
  }

  return (
    <BaseLayout title="Explore Destinations">
      <div className="mb-8">
        <p className="text-gray-600">
          Discover popular destinations with rich cultural heritage, scenic views, and unforgettable experiences.
          Our AI-powered recommendations will help you find the perfect match for your interests.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cities.map(destination => (
          <div key={destination.id} className="card overflow-hidden transition-transform hover:shadow-lg hover:-translate-y-1 flex flex-col h-full">
            <div 
              className="h-48 bg-cover bg-center" 
              style={{ backgroundImage: `url(${destination.image})` }}
            ></div>
            <div className="p-4 flex flex-col flex-grow">
              <h3 className="font-semibold text-lg mb-2">{destination.name}</h3>
              
              <div className="relative bg-gradient-to-r from-indigo-50 to-white p-4 pl-10 rounded-md shadow-sm border-l-4 border-indigo-400 mb-4 h-36">
                <svg className="absolute top-4 left-3 w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <div className="h-full overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin', scrollbarColor: '#c7d2fe transparent' }}>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {destination.description}
                  </p>
                </div>
                <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-indigo-50 to-transparent pointer-events-none"></div>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-4 min-h-[32px] overflow-hidden">
                {destination.tags.slice(0, 3).map(tag => (
                  <span key={tag} className="bg-indigo-50 text-indigo-700 font-medium text-xs px-3 py-1 rounded-md shadow-sm border border-indigo-100 inline-flex items-center">
                    {tag}
                  </span>
                ))}
              </div>
              <div className="mt-auto">
                <Link to={`/destinations/${encodeURIComponent(destination.name)}`} className="btn btn-outline w-full">
                  View Details
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </BaseLayout>
  );
};

export default Destinations; 