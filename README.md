# 🇮🇹 Civic Bridge

**Italian Civic Engagement Platform** - Find and contact your elected representatives

An intuitive web platform that helps Italian citizens easily identify and contact their representatives in the Camera dei Deputati, Senato della Repubblica, and European Parliament based on their location.

## ✨ Features

- **🔍 Smart City Search**: Autocomplete search for Italian comuni
- **🏛️ Multi-Institution Coverage**: Camera, Senato, and EU Parliament representatives
- **📧 Contact Integration**: 
  - Direct email client integration (mailto)
  - OAuth integration for Gmail/Outlook (in development)
- **📝 Professional Templates**: Pre-written formal Italian correspondence templates
- **🎯 Accurate Mapping**: Location-based representative matching
- **📱 Responsive Design**: Works on desktop and mobile

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Virtual environment (included in repo)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/civic-bridge.git
cd civic-bridge

# Activate virtual environment (Windows)
venv\Scripts\activate

# Start the server
python api_server.py
```

Visit `http://localhost:5000` to use the application.

## 🗂️ Data Sources

The platform uses official Italian government data:
- **Camera dei Deputati**: Deputy contact information and electoral districts
- **Senato della Repubblica**: Senator details and regional assignments  
- **Parlamento Europeo**: Italian MEP information and constituencies
- **Administrative Data**: Italian comuni, provinces, and regions

## 🎯 How It Works

1. **Search**: Type your city name (autocomplete helps)
2. **Discover**: See all your elected representatives across institutions
3. **Contact**: Click to open pre-filled emails or use direct sending
4. **Track**: Monitor your civic engagement (coming soon)

## 🛠️ Technical Stack

- **Backend**: Python, Flask, Pandas
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Processing**: CSV-based government data parsing
- **APIs**: Custom REST endpoints for lookup and autocomplete

## 📋 Roadmap

- [x] **Phase 0**: Basic representative lookup and contact
- [ ] **Phase 1**: Electoral district mapping enhancement
- [ ] **Phase 2**: UI improvements (categories, filters, photos)
- [ ] **Phase 3**: Pre-defined email themes and templates
- [ ] **Phase 4**: User authentication and history
- [ ] **Phase 5**: Contact tracking and analytics
- [ ] **Phase 6**: Complete OAuth implementation

## 🤝 Contributing

This is an open-source civic engagement tool. Contributions welcome for:
- Data accuracy improvements
- UI/UX enhancements  
- Additional features
- Documentation

## 📄 License

Open source - built to strengthen Italian democracy through digital civic engagement.

## 🙏 Acknowledgments

Built with [Claude Code](https://claude.ai/code) - AI-powered development assistant.

---

**Made with ❤️ for Italian civic participation**