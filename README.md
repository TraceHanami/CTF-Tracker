# 🚩 CTF & Hackathon Tracker

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready, full-stack event aggregation platform for **Cybersecurity CTFs** and **Hackathons**. Automatically discovers, scrapes, normalizes, filters, tracks, and exports events from global platforms with automated pricing caps, regional filtering, team roster management, and email export capabilities.

---

## ⚡ Features

- **🌐 Multi-Source Event Scraping**: Automatically aggregates events from:
  - **CTFtime** (Official REST API)
  - **Devpost** (Hackathon Listings API)
  - **Devfolio** (Public API)
  - **Unstop / Dare2Compete** (Public API)
  - **MLH (Major League Hacking)** (Official Schedule)
  - **India Offline Fests** (IIT Madras, NIT Trichy, VIT, SRM, Amrita, etc.)
  - **DuckDuckGo Web Search** (Fallback Event Discovery)

- **🎯 Smart Rule-Based Filtering**:
  - **Price Gate**: Free ($\text{₹}0$) or affordable ($\le \text{₹}500$).
  - **Location & Mode Gate**: Accepts all **Online** events globally, or **Offline** events in **Tamil Nadu**, **Kerala**, or **Bengaluru**.
  - **Strict Date Boundary**: Filters out past events; includes today's events ($\text{date} = \text{today}$) and upcoming events ($\text{date} > \text{today}$).

- **🛠️ Full CRUD for Events & Teams**:
  - **Events**: Create custom events, alter event details, and delete events with backend disk persistence.
  - **Teams**: Create teams, alter team names/leads, select members from candidate pool, toggle participation, and delete teams.

- **📊 Professional Report Export Engine**:
  - **Excel Workbook (`.xlsx`)**: Styled multi-tab report with clickable registration links, active event highlights, and team rosters.
  - **PDF Report (`.pdf`)**: Formatted event summary document.
  - **Automated SMTP Dispatch**: Send reports directly to any email address.

- **🖥️ Dark-Mode Dashboard**:
  - Modern, responsive TailwindCSS interface with instant search, filter chips, stat cards, and interactive modal dialogs.

---

## 📁 Repository Structure

```
CTF-Tracker/
├── app.py                  # Main Flask application & REST API routes
├── exporter.py             # OpenPyXL & ReportLab report generator (Excel + PDF)
├── event_scrapers.py       # Mock catalogue & fallback provider
├── run_once.py             # CLI runner for quick terminal testing
├── team_dashboard.html     # Dedicated team management interface
├── requirements.txt        # Production dependency specifications
├── Dockerfile              # Containerization specification
├── docker-compose.yml      # Multi-container orchestration config
├── LICENSE                 # MIT License
├── README.md               # Documentation (you are here)
├── core/                   # Core business logic
│   ├── aggregator.py       # Pipeline orchestrator & deduplication
│   ├── filters.py          # Regional, pricing, and date filter rules
│   ├── seen_tracker.py     # Fingerprint tracking for dedup
│   └── utils.py            # HTTP request helpers & date parsers
├── scrapers/               # Data scrapers
│   ├── ctftime.py          # CTFtime API scraper
│   ├── devpost.py          # Devpost scraper
│   ├── devfolio.py         # Devfolio API scraper
│   ├── hackerearth.py      # HackerEarth scraper
│   ├── unstop.py           # Unstop API scraper
│   ├── dare2compete.py     # Dare2Compete scraper
│   ├── mlh.py              # Major League Hacking scraper
│   ├── india_offline.py    # South India offline college fest scraper
│   └── search_engine.py    # DuckDuckGo fallback search engine scraper
├── templates/
│   └── index.html          # Main web app dashboard template
├── static/
│   ├── css/style.css       # Custom design system styles
│   └── js/app.js           # Dynamic frontend UI script
└── tests/                  # Automated test suite
    ├── test_api.py         # REST API integration tests
    ├── test_filters.py     # Date & location filter tests
    └── test_scrapers.py    # Scraper unit tests
```

---

## 🚀 Quickstart Guide

### Option 1: Local Python Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/TraceHanami/CTF-Tracker.git
   cd CTF-Tracker
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables** (Optional, for email exports):
   Create a `.env` file in the project root:
   ```env
   FLASK_ENV=development
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://localhost:5000`.

---

### Option 2: Docker Container

Deploy using Docker and Docker Compose:

```bash
docker-compose up --build -d
```
The service will be live on `http://localhost:5000`.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `GET /api/events` | `GET` | Retrieve filtered active events (`?refresh=true`, `?search=...`) |
| `POST /api/events` | `POST` | Create a new custom event |
| `PUT /api/events/<id>` | `PUT` | Edit / alter an existing event |
| `DELETE /api/events/<id>` | `DELETE` | Delete an event permanently |
| `GET /api/stats` | `GET` | Retrieve event stats and category breakdown |
| `GET /api/teams` | `GET` | Retrieve active team rosters |
| `POST /api/teams` | `POST` | Create a new team |
| `PUT /api/teams/<id>` | `PUT` | Edit / alter team details or participation |
| `DELETE /api/teams/<id>` | `DELETE` | Delete a team |
| `POST /api/export/email` | `POST` | Generate & email Excel + PDF reports |

---

## 🧪 Running Tests

Run the test suite using `pytest`:

```bash
pytest tests/
```

Or run a CLI pipeline check:

```bash
python run_once.py --source ctftime
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for details.
