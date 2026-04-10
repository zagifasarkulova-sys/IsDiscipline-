# IsDiscipline

Социальная сеть для тех, кто добивается — плюс Telegram бот для продуктивности.

---

## Что внутри

### Сайт (`webapp/`)
Полноценное социальное приложение лучше Telegram:

- **Лента** — посты, лайки, комментарии, XP за активность
- **Чаты** — real-time сообщения, голосовые, видеокружки
- **Профиль** — streak, XP, статистика
- **Админ-панель** — полный контроль: пользователи, посты, роли
- **Тёмный дизайн** — фиолетово-циановая тема, анимации, glassmorphism

### Telegram бот
- Deep Work таймер (25/50/90 мин)
- Утренний фокус и вечерний аудит
- Streak и XP система
- Еженедельный обзор
- При старте отправляет ссылку на сайт

---

## Деплой сайта на Render

### 1. PostgreSQL база данных
- Render Dashboard → New → PostgreSQL
- Скопируй `Internal Database URL`

### 2. Web Service для сайта
- New → Web Service → из GitHub репо
- **Root Directory:** `webapp`
- **Runtime:** Docker
- **Branch:** `main`

### 3. Переменные окружения сайта
```
DATABASE_URL=internal_database_url_из_render
NEXTAUTH_SECRET=любая_случайная_строка
NEXTAUTH_URL=https://твой-сайт.onrender.com
PORT=3000
```

### 4. После деплоя
Первый зарегистрированный пользователь — обычный юзер.
Чтобы сделать себя админом, выполни в базе:
```sql
UPDATE "User" SET role = 'ADMIN' WHERE username = 'твой_username';
```

---

## Деплой бота на Render

### Web Service для бота
- Root Directory: `/` (корень репо)
- Runtime: Docker
- Health Check Path: `/health`

### Переменные окружения бота
```
BOT_TOKEN=токен_от_BotFather
DATABASE_URL=internal_database_url_из_render
RENDER_EXTERNAL_URL=https://твой-бот.onrender.com
PORT=8080
```

### Поддержание активности (cron-job.org)
| Поле | Значение |
|------|----------|
| URL | `https://твой-бот.onrender.com/health` |
| Расписание | Каждые 5 минут |
| Метод | GET |

---

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация, главное меню + ссылка на сайт |
| `/admin` | Настройки уведомлений |

## Расписание уведомлений (Asia/Almaty)

| Время | Событие |
|-------|---------|
| 08:00 | Утренний фокус |
| 21:00 | Вечерний аудит |
| Воскресенье 20:00 | Еженедельный обзор |
