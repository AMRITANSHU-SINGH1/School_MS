# School MS: Comprehensive School Management & Social Platform

Welcome to the repository for **EduConnect** (School Management System + Social Connect). This project is a robust, full-stack Flask application designed to bridge the gap between traditional academic administration and modern, interactive student-alumni networking.

Unlike standard school portals, this application merges a complete **School Management System (SMS)** with a rich **Social Networking** environment, allowing students, teachers, and alumni to connect, share achievements, and build professional networks natively within their institution's ecosystem.

---

## 🌟 Key Features

The application is heavily role-based, ensuring secure and tailored experiences for four distinct user types: Admins, Teachers, Students, and Alumni.

### 🏛️ 1. Academic Management (Core SMS)

**Admin Dashboard:**

* **Entity Management:** Full CRUD capabilities for Grades, Subjects, Classes, Teachers, and Students.
* **Academic Allocation:** Assign specific subjects and teachers to designated classes.
* **Alumni Management:** Direct oversight and onboarding of graduated students.

**Teacher Portal:**

* **Class & Student Management:** View assigned classes and student rosters.
* **Attendance Tracking:** Mark and review daily attendance with dynamic reporting.
* **Academic Grading:** Input marks, calculate percentages, and track student performance.
* **Assignment Hub:** Create assignments, upload attachments, track deadlines, and grade student submissions with feedback.
* **Class Diary & Communication:** Maintain a daily class diary (notes, homework) and broadcast urgent notifications to classes.

**Student Portal:**

* **Academic Tracking:** View personal attendance statistics, subject-wise performance, and monthly trends.
* **Assignment Submission:** Upload files or provide links for pending assignments, and review teacher feedback on graded work.
* **Daily Updates:** Access the class diary and receive real-time notifications from teachers.

### 🤝 2. Social Connect (The Integrated Network)

A LinkedIn-style networking layer accessible to Students, Teachers, and Alumni.

* **Extended Profiles:** Users can add profile pictures, headlines, bios, locations, and social links (GitHub, LinkedIn).
* **Professional Portfolios:** Add and showcase Skills, Work Experience/Internships, Achievements, and Hobbies.
* **Skill Endorsements:** Network members can endorse each other's skills to build credibility.
* **Connections & Networking:** Send, accept, or reject connection requests. Features an intelligent "Discovery" algorithm suggesting connections based on matching skills.
* **Interactive Feed:** Create posts with text and image uploads. Engage with the network via likes and comments.
* **Alumni Directory:** A searchable database of graduates, filterable by graduation year and current company.

---

## 🛠️ Tech Stack

* **Backend Framework:** Python 3.x, Flask
* **Database:** SQLite (via Flask-SQLAlchemy)
* **Authentication & Security:** Werkzeug Security (Password Hashing), Session-based Auth, Custom Role-based Decorators
* **Frontend Rendering:** Jinja2 Templating
* **File Handling:** Native OS/Werkzeug secure file uploads (Assignments, Submissions, Profile Pictures, Post Images)

---

## 🚀 Installation & Setup

Follow these steps to get the project running on your local machine.

### Prerequisites

* Python 3.8+
* `pip` (Python package installer)

### 1. Clone the repository

```bash
git clone https://github.com/AMRITANSHU-SINGH1/School_MS.git

```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

```

### 3. Install Dependencies

Create a `requirements.txt` file if you haven't already, or install the core dependencies directly:

```bash
pip install Flask Flask-SQLAlchemy Werkzeug

```

### 4. Initialize and Run the Application

The application is configured to automatically create the SQLite database (`SMS.db`) and necessary upload directories on its first run.

```bash
python app.py

```

*The server will start on `http://127.0.0.1:5000`.*

### 5. Default Credentials

Upon the first initialization, a default system administrator account is generated automatically:

* **Username:** `admin`
* **Password:** `admin123`

*Note: Please change these credentials or the secret key in `app.config['SECRET_KEY']` before deploying to a production environment.*

---

## 📂 Project Structure Note

The application heavily relies on dynamic file uploads. Ensure your server has the correct read/write permissions for the generated `static/uploads/` directory, which houses:

* `/assignments` - Teacher assignment attachments
* `/submissions` - Student homework files
* `/profiles` - User profile pictures
* `/posts` - Social feed images

---

## 👨‍💻 Author

Developed and maintained by 
**Amritanshu Singh**\n
**Shudhanshu Ranjan**\n
**Tanish Sharma**\n
**Ananya Raj**\n
**B Hasini**\n
.

If you are contributing to this project, please ensure any new database models are accurately mapped in the `app.py` context and frontend templates are updated accordingly.
