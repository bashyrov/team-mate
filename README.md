# Team Mate
Team Mate is a web platform designed for developers and project teams.
It facilitates finding teammates, managing projects, tracking tasks, and monitoring participant ratings.
Built on Django, the project combines simplicity, flexibility, and team spirit 💡.

The project is available at: 🔗 https://team-mate.onrender.com/

[![Django](https://img.shields.io/badge/Django-5.2%2B-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)


## 🚀 Key Features

### 🔹 For Developers

- Create and edit profiles: specify position, tech stack, portfolio, and social media links
- View personal ratings and leaderboards
- Receive feedback and ratings from colleagues and managers
- Leaderboard showcasing top developers based on project ratings

### 🔹 For Projects

- Create and manage projects
- Add participants and assign roles
- Open roles for recruiting new team members
- Project evaluation by participants
- Automatic recalculation of average project and participant ratings
- Custom permissions for each project member
- Built-in task tracker

### 🔹 For Tasks

- Create and assign tasks
- Track task statuses (To Do, In Progress, Done)
- Support for tags and deadlines
- Personalized task lists for each user

### 🔹 User Registration

- Secure user registration system to create new accounts and start participating in projects immediately.

## Quick Start (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/bashyrov/team-mate.git
cd rick-and-morty-api
```

### 2. Copy example env file
```bash
cp .env.sample .env
```


### 3. Start docker-compose
```bash
docker-compose up --build
```

API will be available at: http://127.0.0.1:8000

### 🗄️ Initial Data Setup
```bash
docker-compose exec team-mate-web-1 sh
python manage.py loaddata initial_data.json
```

