# 👥 Team Mate

**Team Mate** is a web platform designed for developers and project teams.  
It facilitates finding teammates, managing projects, tracking tasks, and monitoring participant ratings.  
Built on **Django**, the project combines simplicity, flexibility, and team spirit 💡.

---

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
- Track task statuses (`To Do`, `In Progress`, `Done`)  
- Support for tags and deadlines  
- Personalized task lists for each user  

---

## 🛠️ Technologies

| Component | Technology |
|-----------|------------|
| Backend | Django 5+ |
| Frontend | Bootstrap 5 + Flowbite |
| ORM | Django ORM |
| Database | SQLite |
| Authentication | Django Auth (custom user model `Developer`) |
| Templates | Django Templates + Bootstrap |
| Project Logic | Custom managers and M2M relationships |

---

## 🗄️ Initial Data Setup

To explore the platform with pre-populated data, load the `initial_data.json` fixture. This includes sample users, projects, tasks, ratings, and more to help you get started.

python manage.py loaddata initial_data.json


## 🔑 Superuser Access
To experience the platform as an admin (who participates in projects and owns some), use the following credentials to log in to the Django admin panel (e.g., http://localhost:8000/admin/):

Username: admin
Password: admin

The admin user is fully integrated into the platform, participating in projects (e.g., as a Team Lead in "SaaS Analytics" and "Admin Project 2") and owning projects ("Admin Project 1" and "Admin Project 2"). This allows you to explore the platform from an admin's perspective.
