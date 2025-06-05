# The Perspective Shift ✨

*Timeless wisdom for this moment*

A web application that helps you gain new perspectives by matching your current feelings and thoughts with curated wisdom from throughout history. Share what's on your mind and discover insights from philosophers, writers, scientists, and thinkers who've faced similar moments.

## 🌟 What It Does

- **Share Your Thoughts** - Tell us how you're feeling or what's on your mind
- **Get Wisdom Quotes** - Receive 2-3 carefully selected quotes that speak to your situation  
- **Understand the Context** - Each quote comes with perspective explanations and historical background
- **Share Inspiration** - Create beautiful images of quotes to share with others
- **Stay Anonymous** - No accounts, no tracking of who you are

## 🚀 Try It Out

Visit the live application or run it locally to experience personalized wisdom curation.

### Running Locally

**Prerequisites:** Python 3.11+ and an OpenAI API key

1. **Clone and Install**
   ```bash
   git clone https://github.com/yourusername/PerspectiveShifter.git
   cd PerspectiveShifter
   pip install -r requirements.txt
   ```

2. **Set Up Environment**
   Create a `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=sqlite:///perspective_shift.db
   SESSION_SECRET=your_secret_key_here
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```
   
   Visit `http://localhost:5001`

## 💡 How It Works

1. **Input Your Feelings** - Share what you're experiencing right now
2. **AI-Powered Matching** - Our system finds relevant wisdom from diverse sources
3. **Contextual Quotes** - Get quotes with explanations of how they apply to your situation
4. **Share & Reflect** - Save favorite quotes or share them as beautiful images

### Example

**Input:** "I'm feeling overwhelmed with work deadlines"

**Output:** Curated quotes about managing pressure, finding clarity in chaos, and reframing challenges - each with historical context and perspective explanations.

## 🔒 Privacy & Data

We believe in transparency about data practices:

- **What we save:** Your messages (no names or personal info) to provide faster responses and enable sharing features
- **What we protect:** All data is stored securely with encryption that would take thousands of years to break
- **What we never collect:** Names, emails, locations, device info, or any way to identify you personally

See our [Privacy Page](./templates/privacy.html) for complete details in plain language.

## 🛠️ Technical Overview

- **Backend:** Python Flask application
- **AI:** OpenAI GPT-4o-mini for wisdom curation
- **Database:** SQLite (development) / PostgreSQL (production)
- **Frontend:** Modern responsive design with accessibility focus
- **Images:** Python PIL/Pillow for quote image generation
- **Deployment:** Serverless-ready architecture

## 📖 Features

- **Smart Caching** - Faster responses for similar inputs
- **Graceful Fallbacks** - Backup quotes when AI service is unavailable  
- **Anonymous Analytics** - Daily usage stats without personal identification
- **Responsive Design** - Works beautifully on all devices
- **Share Functionality** - Generate shareable quote images
- **Privacy First** - Built with user privacy as the foundation

## 🤝 Contributing

We welcome contributions! Whether it's:

- Adding new wisdom sources
- Improving the user interface
- Enhancing privacy features
- Fixing bugs or performance issues

Please read our contributing guidelines and feel free to open issues or pull requests.

## 📄 License

MIT License - feel free to use this project as inspiration for your own wisdom-sharing applications.

## 🙏 Acknowledgments

- OpenAI for enabling intelligent quote curation
- The countless wisdom traditions and thinkers whose insights help people gain new perspectives
- The open source community for the tools that make this possible

---

**Made with care for those seeking wisdom and new perspectives** 🌅