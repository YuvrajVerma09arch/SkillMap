# SkillMap AI 🚀

SkillMap is an AI-powered career accelerator that connects job seekers with recruiters using semantic matching, not just keyword search.

## 🌟 Key Features
* **Smart Resume Analyst:** Uses Groq/Llama 3 to score resumes against JDs.
* **AI Mock Interviewer:** Voice-interactive technical interviews with real-time feedback.
* **Career Roadmaps:** Generates personalized learning paths to bridge skill gaps.
* **One-Click Apply:** Seamless application tracking for Recruiters.
* **Monetized:** Integrated Razorpay payment gateway for premium features.

## 🛠️ Tech Stack
* **Backend:** Python, Flask, SQLAlchemy
* **Database:** PostgreSQL (Neon DB)
* **AI Engine:** Groq API (Llama 3.3 70B)
* **Payments:** Razorpay
* **Deployment:** Render / Gunicorn

## 📦 Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/yourusername/skillmap.git](https://github.com/yourusername/skillmap.git)
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up environment variables in `.env`:
    ```
    SECRET_KEY=your_secret
    SQLALCHEMY_DATABASE_URI=your_db_url
    GROQ_API_KEY=your_key
    RAZORPAY_KEY_ID=your_key
    RAZORPAY_KEY_SECRET=your_secret
    ```
4.  Run the application:
    ```bash
    flask run
    ```

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
<<<<<<< HEAD
Built with by Team SkillMap
=======
Built with ❤️ by Team SkillMap
>>>>>>> origin/payment-Integration
