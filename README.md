# Real-Time Chat Application

A scalable **real-time chat web application** built with **Django, Django Channels, Redis, and WebSockets**, supporting **private and group messaging** with low-latency communication.

🚀 **Live Demo:**  
https://chat-app-mvol.onrender.com  
*(Initial load may take time due to Render free tier)*

📦 **GitHub Repository:**  
https://github.com/siddesh-thotam/chat-app

---

## ✨ Features

- 🔴 Real-time messaging using WebSockets
- 👥 Private and group chat support
- 🟢 Online user presence tracking
- 🔐 OAuth2 authentication (Google & GitHub)
- 🖼️ Media upload support via Cloudinary
- ⚡ Low-latency messaging (<200ms)
- 🌐 Production deployment on Render

---

## 🛠 Tech Stack

### Backend
- **Framework:** Django
- **Real-Time Layer:** Django Channels
- **Message Broker:** Redis
- **Authentication:** Django Allauth (Google & GitHub OAuth2)
- **Database:** PostgreSQL (Production), SQLite (Development)

### Frontend
- HTML, CSS
- Vanilla JavaScript
- WebSockets API

### Deployment & Infrastructure
- **Hosting:** Render.com
- **Media Storage:** Cloudinary
- **WSGI/ASGI:** Daphne / Gunicorn
- **Static Files:** WhiteNoise

---

## 🧠 How It Works

1. Users authenticate using Google or GitHub OAuth
2. WebSocket connections are established using Django Channels
3. Redis acts as the channel layer for real-time message broadcasting
4. Messages are delivered instantly to connected users
5. User presence is tracked based on active WebSocket connections
6. Media files are uploaded and served via Cloudinary

---

## 📂 Project Structure

chat-app/
├── core/ # Django project settings
├── chat/ # Chat application
│ ├── consumers.py # WebSocket consumers
│ ├── routing.py # WebSocket routing
│ ├── models.py # Chat models
│ ├── views.py
│ └── templates/
├── static/
├── requirements.txt
├── render.yaml
└── README.md


---

## ⚙️ Installation (Local Development)

### Prerequisites
- Python 3.11+
- Redis
- pip
- Virtual environment

---

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/siddesh-thotam/chat-app.git
cd chat-app

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Redis server
redis-server

# Run development server
python manage.py runserver

Visit 👉 http://127.0.0.1:8000

🔐 Environment Variables

Create a .env file and configure:

SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=your-database-url
REDIS_URL=redis://localhost:6379
CLOUDINARY_URL=your-cloudinary-url

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

🚀 Deployment

This project is deployed on Render.com using render.yaml.

Deployment Steps

Connect GitHub repository to Render

Add required environment variables

Deploy the service

Run migrations on production

🧪 Testing
python manage.py test

📈 Performance Notes

Redis-backed channel layer for fast message delivery

Optimized WebSocket consumers

Efficient database queries

Scales horizontally with Redis

🔮 Future Enhancements

Read receipts & typing indicators

Message reactions & emojis

File sharing improvements

Push notifications

End-to-end encryption

Mobile-friendly UI

👨‍💻 Author

Siddesh

📄 License

This project is licensed under the MIT License.