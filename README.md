# ⚡ NovaMind — Weekly Content Engine

NovaMind is an AI-powered content repurposing platform built with Streamlit. It turns one blog topic into a complete, personalized campaign for every audience segment — automatically.

Write once. Reach everyone. In minutes.

---

## What It Does

NovaMind solves the **content repurposing gap**: you create great content, but it only gets used once. The platform takes a single topic or blog post and generates:

- **A full blog post** (400–1500 words, configurable tone and length)
- **3 personalized newsletters** — one per audience persona (Agency Owners, Startup Marketers, Solo Creators)
- **9 A/B-ready subject lines** (3 per persona, each using a different psychological hook)
- **A repurposing guide** with LinkedIn posts, Twitter threads, video scripts, and email drip sequences
- **Performance predictions** based on historical persona benchmarks

Everything is saved to a local SQLite database and available for download in Markdown, CSV, or JSON.

---

## Prerequisites

- Python 3.10 or higher
- An Anthropic API key (optional — the app works in Mock Mode without one)
- An OpenAI API key (optional, alternative to Anthropic)

---

## Installation

### 1. Clone or navigate to the project

```bash
cd /Users/seohyunkang/novamind-content-automation
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables (optional)

Copy the example file and add your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLM_PROVIDER=anthropic
```

If you leave the file empty or skip this step, NovaMind runs in **Mock Mode** with realistic pre-written demo content.

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Mock Mode

**Mock Mode** is the default when no API key is configured. It produces high-quality, realistic demo content — the same structure and formatting as live AI output, but using pre-written templates. This means:

- The app is fully functional without an API key
- All features work: generation, saving, exporting, analytics
- The content is professional and suitable for demos

A yellow **🟡 Mock Mode** badge appears in the header and sidebar when active.

When a valid API key is present, a green **🟢 Live API** badge appears and all generation uses the real LLM.

---

## Page-by-Page Feature Tour

### ⚡ Dashboard (Home)
The main landing page shows:
- Summary metrics: total campaigns, active personas, average open rate, last generated date
- Quick action buttons to jump to generation or analytics
- Recent campaigns table with status and View links
- How It Works explainer for new users

### ✨ Content Generator
The core generation UI:
- Configure topic, angle, tone, CTA type, length, and personas
- Click **Generate Campaign** — the app calls the LLM (or mock), builds the full campaign, and saves it to the database
- Results appear in 5 tabs: Blog Post, Newsletters, Subject Lines, Repurposing, Predictions
- Each newsletter expander shows subject line, preview text, email body, and a styled CTA button

### 🎯 Persona Library
Detailed cards for all three audience personas:
- **Creative Agency Owner** — ROI-focused, peer-to-peer tone
- **Marketing Manager (Startup)** — Data-driven, performance-focused
- **Freelancer / Solo Creator** — Casual, efficiency-first

Each card shows demographics, goals, pain points, messaging angle, CTA style, preferred tone, and content hooks.

### 🗓️ Weekly Automation
Configure a recurring generation schedule:
- Toggle automation on/off
- Set day of week and time
- Configure default personas, tone, CTA, and topic category
- View next scheduled run and job history table
- **Run Now** button for on-demand generation with confirmation dialog

### 👥 CRM Contacts
Contact management across 63 mock contacts (21 per persona):
- Filter by persona, lifecycle stage, lead status, and search text
- Segment overview cards with lifecycle breakdown bars
- Newsletter assignment preview — see who receives each variant
- Export as CSV (all contacts or per-persona)

### 📊 Analytics
Performance visualization:
- KPI row: open rate, CTR, total campaigns, best performing persona
- Line chart: open rate trends over 8 weeks by persona
- Bar chart: CTR comparison across segments
- Horizontal bar: conversion rate comparison
- Best subject lines per persona with visual open rate bars
- AI Insights section with 3 analytically-derived optimization recommendations

### 📥 Export
Download all campaign deliverables:
- Blog post (Markdown)
- Campaign summary (Markdown)
- Newsletters bundle — all personas in one file (Markdown)
- CRM contacts (CSV)
- Full campaign data (JSON)
- Individual newsletter files per persona

---

## Project Structure

```
novamind-content-automation/
├── app.py                          # Dashboard (main page)
├── pages/
│   ├── 1_Content_Generator.py      # Campaign generation UI
│   ├── 2_Personas.py               # Persona library
│   ├── 3_Weekly_Automation.py      # Scheduler + job history
│   ├── 4_CRM_Contacts.py           # Contact management + exports
│   ├── 5_Analytics.py              # Charts + AI insights
│   └── 6_Export.py                 # File downloads
├── services/
│   ├── llm_service.py              # LLM abstraction (Anthropic / OpenAI / Mock)
│   ├── content_service.py          # Blog, newsletter, subject line generation
│   ├── crm_service.py              # Contact filtering and export
│   ├── analytics_service.py        # Benchmarks, trends, AI insights
│   └── scheduler_service.py        # Automation settings and job execution
├── db/
│   └── database.py                 # SQLite CRUD (campaigns, settings, jobs)
├── utils/
│   ├── config.py                   # Environment variables + app constants
│   └── helpers.py                  # Formatting and utility functions
├── data/
│   ├── personas.json               # 3 persona definitions
│   ├── sample_topics.json          # Topic categories and examples
│   └── mock_contacts.csv           # 63 demo contacts
├── exports/                        # Download staging (gitignored)
├── .env.example                    # Environment template
├── requirements.txt
└── README.md
```

---

## Key Design Decisions

**Streamlit multi-page app structure**
Each major feature lives in its own page file under `pages/`. Streamlit's built-in multi-page routing handles navigation automatically.

**LLM abstraction with mock fallback**
`LLMService` detects the available provider at startup. If no API key is found, it routes all generation through `mock_generate()` — which returns structured, realistic content — so the app is always demo-ready.

**SQLite for persistence**
Campaign data, scheduler settings, and job logs are stored in a local `novamind.db` SQLite database. No external database setup required. The schema is created automatically on first run via `init_db()`.

**Service-layer architecture**
Business logic is cleanly separated from the UI. Each service class has a single responsibility:
- `ContentService` orchestrates LLM calls for content generation
- `CRMService` reads and filters the contacts CSV
- `AnalyticsService` provides benchmarks and insight data
- `SchedulerService` manages automation state and job execution

**Persona-driven personalization**
The three personas (Agency Owner, Startup Marketer, Solo Creator) are data-driven — defined in `personas.json` with goals, pain points, tone preferences, and content hooks. All content prompts inject the relevant persona context to produce genuinely differentiated output.

**`@st.cache_resource` for service instances**
Service classes are expensive to initialize (they import API clients). Caching them as resources ensures they are created once per app session, not on every re-render.

---

## Screenshots

Suggested screenshots to capture for documentation or demos:

1. **Dashboard** — with a few campaigns in the Recent Campaigns table
2. **Content Generator** — Blog Post tab showing a generated article
3. **Content Generator** — Newsletters tab with persona expanders open
4. **Persona Library** — all three cards side by side
5. **Analytics** — line chart + AI insights section
6. **CRM Contacts** — segment overview cards + contacts table
7. **Export** — download card grid

---

## License

MIT — use freely for commercial and personal projects.
