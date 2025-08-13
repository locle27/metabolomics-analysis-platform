# Advanced Metabolomics Data Analysis Platform

A professional metabolomics data analysis platform for extracting, managing, and visualizing lipid chromatography data from the Baker Institute. Features interactive dual-chart visualizations with advanced filtering and scientific-grade analysis tools.

## 🧬 Features

- **Professional Interface**: Phenikaa University-inspired design
- **Interactive Charts**: Dual-chart system with Chart.js 4.4.0 and zoom controls
- **PostgreSQL Database**: 800+ lipids with complete XIC chromatogram data
- **Advanced Filtering**: Real-time lipid search and class-based filtering
- **Scientific Analysis**: Precision tooltips and integration area visualization

## 🚀 Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   git clone https://github.com/yourusername/metabolomics-project.git
   cd metabolomics-project
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Set your PostgreSQL connection in .env file
   echo "DATABASE_URL=postgresql://username:password@localhost/metabolomics_db" > .env
   
   # Import data
   python import_hybrid_database.py
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

### Railway Deployment

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. **Fork this repository**
2. **Connect to Railway**
3. **Add PostgreSQL service**
4. **Set environment variables**:
   - `DATABASE_URL` (Railway provides this automatically)
   - `SECRET_KEY` (generate a secure key)

## 🗂️ Project Structure

```
metabolomics-project/
├── app.py                     # Main Flask application
├── models.py                  # Database models and schemas
├── dual_chart_service.py      # Chart generation engine
├── requirements.txt           # Python dependencies
├── templates/                 # HTML templates with Phenikaa UI
├── static/                    # CSS, JS, and assets
├── selenium_api_hybrid_results/ # Scraped data (excluded from git)
└── complete_annotated_ions_results/ # Processed data
```

## 🧪 Supported Lipid Classes

- **AC** - Acyl Carnitines
- **TG** - Triacylglycerols  
- **PC** - Phosphatidylcholines
- **PE** - Phosphatidylethanolamines
- **SM** - Sphingomyelins
- **Cer** - Ceramides
- **LPC/LPE** - Lysophospholipids
- And 15+ additional classes

## 🔧 Technology Stack

- **Backend**: Flask 2.3.3, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5, Chart.js 4.4.0, Inter font
- **Database**: PostgreSQL with 800+ lipid records
- **Deployment**: Railway, Gunicorn

## 📊 Chart System

- **Chart 1**: Focused view (±0.6 minutes from main lipid)
- **Chart 2**: Overview (0-16 minutes complete range)
- **Interactions**: Click-to-zoom, pan controls
- **Tooltips**: Static tooltips on integration areas

## 🎨 Design System

Based on Phenikaa University design with exact color matching:
- Primary Blue: `#2E4C92`
- Secondary Blue: `#213671` 
- Orange Accent: `#E94B00`
- Inter font family

## 📝 License

This project is for educational and research purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Contact

For questions about the metabolomics platform, please open an issue.