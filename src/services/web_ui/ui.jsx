import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  ExternalLink,
  Newspaper,
  Check,
  ChevronRight,
  ChevronLeft,
  LogOut,
  AlertCircle
} from 'lucide-react';

const InfoGuidesApp = () => {
  // Для продакшена лучше вынести в .env
  const API_URL = 'http://localhost:8000/api/v1';

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [userData, setUserData] = useState({
    user_id: '',
    username: '',
    password: '',
    themes: [],
    sources: []
  });
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [usernameCheckLoading, setUsernameCheckLoading] = useState(false);
  const [usernameAvailable, setUsernameAvailable] = useState(null);

  const availableThemes = [
    { id: 'politics', name: '🏛️ Политика', description: 'Государственные события и решения' },
    { id: 'sports', name: '⚽ Спорт', description: 'Спортивные новости и события' },
    { id: 'tech', name: '💻 Технологии', description: 'IT и инновации' },
    { id: 'science', name: '🔬 Наука', description: 'Научные открытия' },
    { id: 'economy', name: '💰 Экономика', description: 'Финансы и бизнес' },
    { id: 'culture', name: '🎭 Культура', description: 'Искусство и развлечения' },
    { id: 'health', name: '⚕️ Здоровье', description: 'Медицина и здоровый образ жизни' },
    { id: 'world', name: '🌍 Мировые события', description: 'Международные новости' }
  ];

  const availableSources = [
    { id: 'rbc', name: 'РБК' },
    { id: 'tass', name: 'ТАСС' },
    { id: 'interfax', name: 'Интерфакс' },
    { id: 'kommersant', name: 'Коммерсантъ' },
    { id: 'vedomosti', name: 'Ведомости' },
    { id: 'ria', name: 'РИА Новости' },
    { id: 'meduza', name: 'Meduza' },
    { id: 'lenta', name: 'Lenta.ru' }
  ];

  // Проверка доступности никнейма с debounce 500ms
  useEffect(() => {
    if (!userData.username || userData.username.length < 3) {
      setUsernameAvailable(null);
      return;
    }

    let cancelled = false;
    setUsernameCheckLoading(true);
    const timeoutId = setTimeout(async () => {
      try {
        const response = await fetch(
          `${API_URL}/check_username?username=${encodeURIComponent(userData.username)}`
        );
        if (!response.ok) {
          // если сервер вернул ошибку — пометим как недоступно или null
          setUsernameAvailable(null);
        } else {
          const data = await response.json();
          if (!cancelled) setUsernameAvailable(Boolean(data.available));
        }
      } catch (err) {
        console.error('Ошибка проверки никнейма:', err);
        if (!cancelled) setUsernameAvailable(null);
      } finally {
        if (!cancelled) setUsernameCheckLoading(false);
      }
    }, 500);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userData.username]);

  const handleLogin = async () => {
    // локальная валидация
    if (!userData.username || !userData.password) {
      setError('Заполните все поля');
      return;
    }

    if (userData.username.length < 3) {
      setError('Никнейм должен содержать минимум 3 символа');
      return;
    }

    if (userData.password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов');
      return;
    }

    setError(null);

    // Здесь можно добавить реальный запрос логина.
    // Пока — считаем, что шаг прошёл и переходим к выбору тем/источников
    setCurrentStep(2);
  };

  const handleRegister = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: userData.username,
          password: userData.password,
          themes: userData.themes,
          sources: userData.sources
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Ошибка регистрации');
      }

      setUserData(prev => ({
        ...prev,
        user_id: data.user?.user_id || data.user_id || prev.user_id
      }));

      setIsAuthenticated(true);
      setCurrentStep(1);
      setError(null);
    } catch (err) {
      setError(err.message || 'Ошибка регистрации');
    } finally {
      setLoading(false);
    }
  };

  const toggleTheme = (themeId) => {
    setUserData(prev => ({
      ...prev,
      themes: prev.themes.includes(themeId)
        ? prev.themes.filter(t => t !== themeId)
        : [...prev.themes, themeId]
    }));
  };

  const toggleSource = (sourceId) => {
    setUserData(prev => ({
      ...prev,
      sources: prev.sources.includes(sourceId)
        ? prev.sources.filter(s => s !== sourceId)
        : [...prev.sources, sourceId]
    }));
  };

  const fetchGuides = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/info_guides`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userData.user_id,
          limit: 10,
          themes: userData.themes,
          sources: userData.sources
        })
      });

      if (!response.ok) {
        throw new Error('Ошибка загрузки инфоповодов');
      }

      const data = await response.json();
      setGuides(Array.isArray(data.guides) ? data.guides : []);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Ошибка при загрузке данных. Показаны демо-данные');
      // демо-данные, чтобы UI не был пустым
      setGuides([
        {
          title: 'Новые технологии в искусственном интеллекте',
          summary: 'Исследователи представили революционный подход к обучению нейронных сетей.',
          sources: [
            { name: 'TechCrunch', url: 'https://techcrunch.com' },
            { name: 'MIT Technology Review', url: 'https://technologyreview.com' }
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUserData({ user_id: '', username: '', password: '', themes: [], sources: [] });
    setGuides([]);
    setCurrentStep(1);
    setError(null);
    setUsernameAvailable(null);
  };

  const NewspaperMascot = ({ expression = 'happy', message }) => (
    <div className="flex flex-col items-center mb-8">
      <div className="relative">
        <svg width="120" height="120" viewBox="0 0 120 120" className="animate-bounce-slow">
          <rect x="20" y="30" width="80" height="70" fill="#ffffff" stroke="#333" strokeWidth="2" rx="4" />
          <rect x="25" y="35" width="70" height="12" fill="#4f46e5" rx="2" />
          <line x1="30" y1="52" x2="90" y2="52" stroke="#333" strokeWidth="1.5" />
          <line x1="30" y1="58" x2="85" y2="58" stroke="#999" strokeWidth="1" />
          <line x1="30" y1="63" x2="88" y2="63" stroke="#999" strokeWidth="1" />
          <line x1="30" y1="68" x2="82" y2="68" stroke="#999" strokeWidth="1" />
          <line x1="30" y1="75" x2="55" y2="75" stroke="#ccc" strokeWidth="1" />
          <line x1="30" y1="80" x2="55" y2="80" stroke="#ccc" strokeWidth="1" />
          <line x1="30" y1="85" x2="55" y2="85" stroke="#ccc" strokeWidth="1" />
          <line x1="65" y1="75" x2="90" y2="75" stroke="#ccc" strokeWidth="1" />
          <line x1="65" y1="80" x2="90" y2="80" stroke="#ccc" strokeWidth="1" />
          <line x1="65" y1="85" x2="90" y2="85" stroke="#ccc" strokeWidth="1" />

          <circle cx="45" cy="45" r="5" fill="#333" />
          <circle cx="75" cy="45" r="5" fill="#333" />

          {expression === 'happy' && (
            <>
              <circle cx="46" cy="44" r="2" fill="#fff" />
              <circle cx="76" cy="44" r="2" fill="#fff" />
              <path d="M 45 55 Q 60 65 75 55" stroke="#333" strokeWidth="2" fill="none" strokeLinecap="round" />
            </>
          )}

          {expression === 'excited' && (
            <>
              <circle cx="46" cy="44" r="2" fill="#fff" />
              <circle cx="76" cy="44" r="2" fill="#fff" />
              <ellipse cx="60" cy="58" rx="8" ry="6" fill="#ff6b6b" />
            </>
          )}

          {expression === 'thinking' && (
            <>
              <line x1="42" y1="42" x2="48" y2="46" stroke="#333" strokeWidth="2" />
              <line x1="72" y1="42" x2="78" y2="46" stroke="#333" strokeWidth="2" />
              <line x1="50" y1="58" x2="70" y2="58" stroke="#333" strokeWidth="2" />
            </>
          )}

          <circle cx="30" cy="55" r="4" fill="#ffb3ba" opacity="0.6" />
          <circle cx="90" cy="55" r="4" fill="#ffb3ba" opacity="0.6" />
        </svg>

        <div className="absolute -top-2 -right-2 text-2xl animate-pulse">✨</div>
      </div>

      {message && (
        <div className="mt-4 px-6 py-3 bg-white rounded-2xl shadow-lg border-2 border-indigo-200 relative max-w-md">
          <div
            className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-0 h-0 
                        border-l-8 border-r-8 border-b-8 border-transparent border-b-white"
          />
          <p className="text-gray-700 font-medium text-center">{message}</p>
        </div>
      )}
    </div>
  );

  // UI — неаутентифицированный пользователь (регистрация/логин)
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6 flex items-center justify-center">
        <div className="max-w-4xl w-full">
          {currentStep === 1 && (
            <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12">
              <NewspaperMascot expression="happy" message="Привет! Я помогу тебе быть в курсе всех новостей!" />

              <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">Добро пожаловать!</h1>
              <p className="text-center text-gray-600 mb-8">Войди или создай аккаунт, чтобы начать</p>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500 rounded text-red-700 flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-4 max-w-md mx-auto">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Никнейм (должен быть уникальным)</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={userData.username}
                      onChange={(e) => setUserData(prev => ({ ...prev, username: e.target.value }))}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:outline-none transition-colors"
                      placeholder="Введите никнейм"
                    />
                    {usernameCheckLoading && userData.username.length >= 3 && (
                      <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                        <div className="w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                      </div>
                    )}
                    {!usernameCheckLoading && usernameAvailable !== null && userData.username.length >= 3 && (
                      <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                        {usernameAvailable ? <Check className="w-5 h-5 text-green-500" /> : <AlertCircle className="w-5 h-5 text-red-500" />}
                      </div>
                    )}
                  </div>
                  {!usernameCheckLoading && usernameAvailable !== null && userData.username.length >= 3 && (
                    <p className={`text-sm mt-1 ${usernameAvailable ? 'text-green-600' : 'text-red-600'}`}>
                      {usernameAvailable ? 'Никнейм свободен ✓' : 'Никнейм уже занят ✗'}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Пароль</label>
                  <input
                    type="password"
                    value={userData.password}
                    onChange={(e) => setUserData(prev => ({ ...prev, password: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:outline-none transition-colors"
                    placeholder="Введите пароль (минимум 6 символов)"
                  />
                </div>

                <button
                  onClick={handleLogin}
                  disabled={usernameAvailable === false}
                  className="w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  Продолжить
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12">
              <NewspaperMascot expression="thinking" message="Какие темы тебе интересны? Можешь выбрать несколько или пропустить!" />

              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Шаг 1 из 2: Выбери направления</h2>
                <button onClick={() => setCurrentStep(3)} className="text-indigo-600 hover:text-indigo-700 font-medium">
                  Пропустить →
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                {availableThemes.map(theme => (
                  <button
                    key={theme.id}
                    onClick={() => toggleTheme(theme.id)}
                    type="button"
                    className={`p-4 rounded-xl border-2 transition-all duration-300 text-left ${userData.themes.includes(theme.id) ? 'border-indigo-500 bg-indigo-50 shadow-md' : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-lg">{theme.name}</span>
                      {userData.themes.includes(theme.id) && <Check className="w-5 h-5 text-indigo-600" />}
                    </div>
                    <p className="text-sm text-gray-600">{theme.description}</p>
                  </button>
                ))}
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="px-6 py-3 border-2 border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition-all flex items-center gap-2"
                >
                  <ChevronLeft className="w-5 h-5" />
                  Назад
                </button>
                <button
                  onClick={() => setCurrentStep(3)}
                  className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center justify-center gap-2"
                >
                  Далее
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12">
              <NewspaperMascot expression="excited" message="Отлично! Теперь выбери источники новостей или пропусти этот шаг!" />

              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Шаг 2 из 2: Выбери источники</h2>
                <button onClick={handleRegister} disabled={loading} className="text-indigo-600 hover:text-indigo-700 font-medium disabled:opacity-50">
                  Пропустить →
                </button>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500 rounded text-red-700 flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
                {availableSources.map(source => (
                  <button
                    key={source.id}
                    onClick={() => toggleSource(source.id)}
                    type="button"
                    className={`p-4 rounded-xl border-2 transition-all duration-300 ${userData.sources.includes(source.id) ? 'border-indigo-500 bg-indigo-50 shadow-md' : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'}`}
                  >
                    <div className="font-semibold text-center">{source.name}</div>
                    {userData.sources.includes(source.id) && <Check className="w-4 h-4 text-indigo-600 mx-auto mt-2" />}
                  </button>
                ))}
              </div>

              <div className="flex gap-4">
                <button onClick={() => setCurrentStep(2)} disabled={loading} className="px-6 py-3 border-2 border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition-all flex items-center gap-2 disabled:opacity-50">
                  <ChevronLeft className="w-5 h-5" />
                  Назад
                </button>
                <button
                  onClick={handleRegister}
                  disabled={loading}
                  className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Регистрация...
                    </>
                  ) : (
                    <>Начать! 🎉</>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // UI — аутентифицированный пользователь
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16">
              <svg width="64" height="64" viewBox="0 0 120 120">
                <rect x="20" y="30" width="80" height="70" fill="#ffffff" stroke="#333" strokeWidth="2" rx="4" />
                <rect x="25" y="35" width="70" height="12" fill="#4f46e5" rx="2" />
                <line x1="30" y1="52" x2="90" y2="52" stroke="#333" strokeWidth="1.5" />
                <circle cx="45" cy="45" r="5" fill="#333" />
                <circle cx="75" cy="45" r="5" fill="#333" />
                <circle cx="46" cy="44" r="2" fill="#fff" />
                <circle cx="76" cy="44" r="2" fill="#fff" />
                <path d="M 45 55 Q 60 65 75 55" stroke="#333" strokeWidth="2" fill="none" />
              </svg>
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-800">Привет, {userData.username}! 👋</h1>
              <p className="text-gray-600">Твоя персональная лента новостей</p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={fetchGuides}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Загрузка...' : 'Обновить'}
            </button>

            <button onClick={handleLogout} className="flex items-center gap-2 px-6 py-3 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-all">
              <LogOut className="w-5 h-5" />
              Выйти
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-700 mt-0.5" />
            <div>
              <p className="text-red-700 font-semibold">Ошибка: {error}</p>
              <p className="text-red-600 text-sm mt-1">Показаны демо-данные для примера</p>
            </div>
          </div>
        )}

        <div className="space-y-6">
          {guides.length === 0 && !loading && (
            <div className="text-center py-16 bg-white rounded-2xl shadow-lg">
              <Newspaper className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg mb-2">Нажми "Обновить", чтобы загрузить новости</p>
              <p className="text-gray-400 text-sm">
                {userData.themes.length > 0 && `Темы: ${userData.themes.length} выбрано`}
                {userData.sources.length > 0 && ` • Источники: ${userData.sources.length} выбрано`}
                {userData.themes.length === 0 && userData.sources.length === 0 && 'Без фильтров - будут показаны все новости'}
              </p>
            </div>
          )}

          {guides.map((guide, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 overflow-hidden transform hover:-translate-y-1 border border-gray-100"
              style={{ animation: `slideIn 0.5s ease-out ${index * 0.1}s both` }}
            >
              <div className="p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-3 flex items-start gap-2">
                  <span className="flex-shrink-0 w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-bold mt-1">
                    {index + 1}
                  </span>
                  <span>{guide.title}</span>
                </h2>

                <p className="text-gray-600 leading-relaxed mb-4 ml-10">{guide.summary}</p>

                {guide.sources && guide.sources.length > 0 && (
                  <div className="ml-10 pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-2 mb-3">
                      <ExternalLink className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-semibold text-gray-700">Источники:</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {guide.sources.map((source, srcIndex) => (
                        <a
                          key={srcIndex}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 text-indigo-700 rounded-lg text-sm font-medium transition-all duration-300 hover:shadow-md transform hover:scale-105 border border-indigo-200"
                        >
                          <span>{source.name}</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
            </div>
          ))}
        </div>

        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="flex gap-2">
              <div className="w-3 h-3 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
              <div className="w-3 h-3 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <div className="w-3 h-3 bg-pink-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .animate-bounce-slow {
          animation: bounce 2s infinite;
        }

        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
};

export default InfoGuidesApp;
