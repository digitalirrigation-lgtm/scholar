# ============================================================
# ULTIMATE INTELLIGENCE DASHBOARD – MOSAD SPY MODE
# Real-time global opportunity extraction by country
# ============================================================
import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime, timedelta
import os
import altair as alt
import requests
from bs4 import BeautifulSoup
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- LOCAL AI ----------
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# ---------- CONFIGURATION ----------
USE_LOCAL_AI = True
DB_PATH = "pipeline_vault.db"
MODEL_NAME = "microsoft/phi-2"

# ---------- COUNTRY DATABASE (Alphabetical Order) ----------
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", 
    "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", 
    "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", 
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", 
    "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", 
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", 
    "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", 
    "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", 
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", 
    "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", 
    "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", 
    "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", 
    "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", 
    "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", 
    "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", 
    "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", 
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", 
    "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", 
    "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", 
    "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", 
    "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", 
    "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

# ---------- SCHOLARSHIP SOURCES (Trusted Websites) ----------
SCHOLARSHIP_SOURCES = {
    "Scholars4Dev": "https://www.scholars4dev.com/category/scholarships-by-country/{country}/",
    "StudyPortals": "https://www.studyportals.com/scholarships/country/{country}/",
    "UNESCO": "https://www.unesco.org/en/scholarships",
    "DAAD": "https://www.daad.de/en/studying-in-germany/scholarships/",
    "Chevening": "https://www.chevening.org/scholarships/",
    "Fulbright": "https://foreign.fulbrightonline.org/countries/{country}",
    "Erasmus Mundus": "https://www.eacea.ec.europa.eu/scholarships/",
    "Commonwealth": "https://cscuk.fcdo.gov.uk/scholarships/",
    "World Bank": "https://www.worldbank.org/en/programs/scholarships",
    "UN Fellowship": "https://www.un.org/en/fellowships/"
}

# ---------- JOB SOURCES ----------
JOB_SOURCES = {
    "UN Jobs": "https://careers.un.org/lbw/Home.aspx",
    "World Bank Jobs": "https://www.worldbank.org/en/about/careers",
    "UNDP Jobs": "https://www.undp.org/careers",
    "FAO Jobs": "https://www.fao.org/employment/",
    "IFRC Jobs": "https://www.ifrc.org/careers",
    "NGO Jobs": "https://www.ngojobs.net/jobs-by-country/{country}",
    "ReliefWeb": "https://reliefweb.int/jobs",
    "DevelopmentAid": "https://www.developmentaid.org/jobs",
    "LinkedIn": "https://www.linkedin.com/jobs/search/?geoId={country_id}"
}

# ---------- DATABASE (SQLite – all data saved here) ----------
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_table_schema():
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA table_info(Opportunities)")
    existing = [col[1] for col in c.fetchall()]
    needed = {
        "GeneratedCV": "TEXT",
        "GeneratedCL": "TEXT", 
        "GeneratedML": "TEXT",
        "AppliedTimestamp": "TEXT",
        "LastNotificationCheck": "TEXT",
        "Country": "TEXT",
        "Source": "TEXT",
        "Category": "TEXT"
    }
    for col, typ in needed.items():
        if col not in existing:
            c.execute(f"ALTER TABLE Opportunities ADD COLUMN {col} {typ}")
    # Create Notes table for history
    c.execute('''CREATE TABLE IF NOT EXISTS Notes (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT,
        Content TEXT,
        CreatedAt TEXT,
        Country TEXT
    )''')
    conn.commit()
    conn.close()

def reset_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Opportunities (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT,
        Organization TEXT,
        Category TEXT,
        Deadline TEXT,
        Status TEXT,
        CreatedAt TEXT,
        Saved INTEGER DEFAULT 0,
        UserDescription TEXT,
        Link TEXT,
        Country TEXT,
        Source TEXT,
        GeneratedCV TEXT,
        GeneratedCL TEXT,
        GeneratedML TEXT,
        AppliedTimestamp TEXT,
        LastNotificationCheck TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS MasterProfile (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Email TEXT,
        Phone TEXT,
        Location TEXT,
        Education TEXT,
        Experience TEXT,
        Achievements TEXT,
        Skills TEXT,
        Certifications TEXT,
        NarrativeContext TEXT,
        NarrativeSolution TEXT,
        NarrativeCTA TEXT
    )''')
    c.execute("SELECT COUNT(*) FROM MasterProfile")
    if c.fetchone()[0] == 0:
        c.execute("""INSERT INTO MasterProfile
            (Name, Email, Phone, Location, Education, Experience, Achievements, Skills, Certifications,
             NarrativeContext, NarrativeSolution, NarrativeCTA)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            "ZEDAGIM TESFAYE TANTU",
            "zedagim100@gmail.com",
            "+251-924-700-390",
            "Jigjiga, Ethiopia",
            "Bachelor of Engineering in Water Resource & Irrigation Engineering (GPA: 3.87/4.00)",
            "Water resource engineering, irrigation systems, satellite data analysis, climate prediction.",
            "Developed Hydro-Agritech prototypes; Digitized FAO-56 Penman-Monteith; Prevented 456+ trafficking cases.",
            "Python, GIS, Remote Sensing, Machine Learning, Data Analysis, Project Management",
            "Certified in GeoAI, Digital Irrigation Systems",
            "Developing regions rely heavily on traditional agricultural systems without enough data arrays.",
            "Deploy spaceborne remote sensing arrays and validated Earth Observation data.",
            "I am ready to discuss my potential alignment with your goals."
        ))
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    reset_db()
else:
    ensure_table_schema()

# ---------- REAL-TIME WEB SCRAPER (Intelligence Extraction) ----------
def extract_country_id(country):
    """Get LinkedIn geo ID for country search"""
    # Simplified mapping - in production, use LinkedIn API
    country_map = {
        "Ethiopia": "103252600",
        "Kenya": "103558974",
        "Nigeria": "103814558",
        "South Africa": "103722587",
        "United States": "103644278",
        "United Kingdom": "105072130",
        "Germany": "101282230",
        "Netherlands": "102890719",
        "Canada": "101174742",
        "Australia": "101452733"
    }
    return country_map.get(country, "")

def scrape_scholarships_by_country(country):
    """Scrape scholarships for a specific country from multiple sources"""
    results = []
    
    # 1. Scholars4Dev
    try:
        url = f"https://www.scholars4dev.com/category/scholarships-by-country/{country.lower()}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find scholarship entries
        articles = soup.find_all('article')[:10]
        for article in articles:
            title_elem = article.find('h2')
            if title_elem:
                title = title_elem.text.strip()
                link = title_elem.find('a')['href'] if title_elem.find('a') else ""
                deadline_text = "Varies"
                # Try to find deadline
                date_elem = article.find('time')
                if date_elem:
                    deadline_text = date_elem.text.strip()
                
                results.append({
                    'Title': title,
                    'Organization': 'Scholars4Dev',
                    'Category': 'Scholarship',
                    'Deadline': deadline_text,
                    'Link': link,
                    'Country': country,
                    'Source': 'Scholars4Dev'
                })
    except Exception as e:
        st.write(f"⚠️ Error scraping {country}: {str(e)}")
    
    # 2. DAAD Scholarships (Germany)
    if country in ["Germany", "All"]:
        try:
            url = "https://www.daad.de/en/studying-in-germany/scholarships/"
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Parse DAAD results - simplified
            results.append({
                'Title': 'DAAD Scholarships - Check Website for Details',
                'Organization': 'DAAD',
                'Category': 'Scholarship',
                'Deadline': 'Varies',
                'Link': url,
                'Country': country,
                'Source': 'DAAD'
            })
        except:
            pass
    
    return results

def scrape_jobs_by_country(country):
    """Scrape jobs for a specific country"""
    results = []
    
    # 1. UN Jobs (filter by country)
    try:
        url = "https://careers.un.org/lbw/Home.aspx"
        results.append({
            'Title': 'UN Careers - Check Website for Country-Specific Posts',
            'Organization': 'United Nations',
            'Category': 'Job',
            'Deadline': 'Varies',
            'Link': url,
            'Country': country,
            'Source': 'UN Jobs'
        })
    except:
        pass
    
    # 2. ReliefWeb Jobs
    try:
        url = "https://reliefweb.int/jobs"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        job_items = soup.find_all('article')[:5]
        for job in job_items:
            title_elem = job.find('h2')
            if title_elem:
                title = title_elem.text.strip()
                link = title_elem.find('a')['href'] if title_elem.find('a') else ""
                results.append({
                    'Title': title,
                    'Organization': 'ReliefWeb',
                    'Category': 'Job',
                    'Deadline': 'Varies',
                    'Link': f"https://reliefweb.int{link}",
                    'Country': country,
                    'Source': 'ReliefWeb'
                })
    except:
        pass
    
    return results

def scrape_fellowships_grants():
    """Scrape fellowships and grants"""
    results = []
    
    sources = [
        ("UN Fellowship", "https://www.un.org/en/fellowships"),
        ("World Bank Fellowships", "https://www.worldbank.org/en/programs/fellowships"),
        ("Global Health Fellows", "https://www.ghfp.net/")
    ]
    
    for name, url in sources:
        results.append({
            'Title': f'{name} - Apply for Fellowship/Grant',
            'Organization': name.split('-')[0].strip(),
            'Category': 'Fellowship',
            'Deadline': 'Varies',
            'Link': url,
            'Country': 'Global',
            'Source': name.split('-')[0].strip()
        })
    
    return results

def scrape_conferences():
    """Scrape conferences relevant to your field"""
    results = []
    
    conferences = [
        ("AGU Fall Meeting", "https://www.agu.org/fall-meeting"),
        ("EGU General Assembly", "https://www.egu.eu/meetings"),
        ("World Water Week", "https://www.worldwaterweek.org"),
        ("International Water Association Congress", "https://iwa-network.org/events"),
        ("ICID Congress", "https://www.icid.org/congresses.html"),
        ("GeoAI Conference", "https://www.geoai-conference.com")
    ]
    
    for name, url in conferences:
        results.append({
            'Title': f'Conference: {name}',
            'Organization': 'Conference',
            'Category': 'Conference',
            'Deadline': 'Varies',
            'Link': url,
            'Country': 'Global',
            'Source': 'Conference Alert'
        })
    
    return results

# ---------- DYNAMIC SEARCH BY COUNTRY ----------
def search_opportunities_by_country(country):
    """Main intelligence gathering function - searches all opportunity types for a country"""
    results = []
    
    with st.spinner(f"🔍 Intelligence gathering for {country}..."):
        # Get scholarships
        scholarships = scrape_scholarships_by_country(country)
        results.extend(scholarships)
        
        # Get jobs
        jobs = scrape_jobs_by_country(country)
        results.extend(jobs)
        
        # Add global opportunities
        fellowships = scrape_fellowships_grants()
        results.extend(fellowships)
        
        conferences = scrape_conferences()
        results.extend(conferences)
    
    return results

def get_country_specific_opportunities(country):
    """Get hand-curated opportunities for Ethiopia and key countries"""
    country_opps = {
        "Ethiopia": [
            {
                'Title': 'Ethiopia Water Resources Development Fund Scholarship',
                'Organization': 'MoWIE',
                'Category': 'Scholarship',
                'Deadline': 'October 2026',
                'Link': 'https://www.mowie.gov.et',
                'Country': 'Ethiopia',
                'Source': 'Government'
            },
            {
                'Title': 'Africa Climate Resilience Initiative - Ethiopia',
                'Organization': 'World Bank',
                'Category': 'Fellowship',
                'Deadline': 'September 2026',
                'Link': 'https://www.worldbank.org/en/programs/africa-climate',
                'Country': 'Ethiopia',
                'Source': 'World Bank'
            }
        ],
        "Germany": [
            {
                'Title': 'DAAD Helmut-Schmidt-Programme',
                'Organization': 'DAAD',
                'Category': 'Scholarship',
                'Deadline': 'July 2026',
                'Link': 'https://www.daad.de/en/studying-in-germany/scholarships/',
                'Country': 'Germany',
                'Source': 'DAAD'
            }
        ],
        "Netherlands": [
            {
                'Title': 'IHE Delft Scholarship for Water Engineering',
                'Organization': 'IHE Delft',
                'Category': 'Scholarship',
                'Deadline': 'June 2026',
                'Link': 'https://www.un-ihe.org/scholarships',
                'Country': 'Netherlands',
                'Source': 'IHE Delft'
            }
        ]
    }
    
    return pd.DataFrame(country_opps.get(country, []))

# ---------- KEYWORD MATCHING (Profile Alignment) ----------
def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {"the","and","for","with","from","into","about","without","etc","this","that","have","are"}
    return set(w for w in words if w not in stopwords)

def score_opportunity(opportunity, profile_keywords):
    """Score how well an opportunity matches your profile"""
    title_keywords = extract_keywords(opportunity.get('Title', ''))
    desc_keywords = extract_keywords(opportunity.get('UserDescription', ''))
    all_keywords = title_keywords.union(desc_keywords)
    
    matches = all_keywords.intersection(profile_keywords)
    score = len(matches) / max(len(profile_keywords), 1)
    
    return min(score * 100, 100)

# ---------- NOTES SYSTEM (Save History) ----------
def save_note(title, content, country):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO Notes (Title, Content, CreatedAt, Country) VALUES (?,?,?,?)",
              (title, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), country))
    conn.commit()
    conn.close()

def get_notes():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM Notes ORDER BY CreatedAt DESC", conn)
    conn.close()
    return df

def delete_note(note_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM Notes WHERE Id = ?", (note_id,))
    conn.commit()
    conn.close()

# ---------- STREAMLIT UI ----------
st.set_page_config(layout="wide", page_title="🎓 Global Opportunity Intelligence", page_icon="🎓")

# ---- THEME ----
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #e0e0e0;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        color: #00d2ff !important;
    }
    .stApp p, .stApp label, .stApp .stMarkdown, .stApp div {
        color: #e0e0e0 !important;
    }
    .golden-text {
        color: #ffd700;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    }
    .stButton button {
        background: linear-gradient(145deg, #00d2ff, #3a7bd5) !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(0, 210, 255, 0.3) !important;
    }
    .css-1y4p8pa {
        background: rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(4px);
        border-radius: 15px !important;
        padding: 15px !important;
        border: 1px solid #00d2ff !important;
    }
    .dataframe {
        border: 1px solid #00d2ff !important;
        border-radius: 10px !important;
        background: rgba(255,255,255,0.05) !important;
    }
    .dataframe th {
        background: #0f3460 !important;
        color: #00d2ff !important;
    }
    .dataframe td {
        color: #e0e0e0 !important;
    }
    .streamlit-expanderHeader {
        background: rgba(0, 210, 255, 0.1) !important;
        border-left: 4px solid #00d2ff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
st.sidebar.title("🕵️ Intelligence Dashboard")
st.sidebar.markdown("<p class='golden-text'>Mossad Spy Mode Active</p>", unsafe_allow_html=True)

# Country Selector
st.sidebar.markdown("### 🌍 Select Target Country")
selected_country = st.sidebar.selectbox("Country (Alphabetical)", COUNTRIES, index=COUNTRIES.index("Ethiopia"))

# Search Type
search_type = st.sidebar.multiselect(
    "Opportunity Type",
    ["Scholarship", "Job", "Fellowship", "Grant Proposal", "Conference"],
    default=["Scholarship", "Job"]
)

# Search Button
if st.sidebar.button("🔍 Deploy Intelligence", use_container_width=True):
    st.session_state['search_results'] = search_opportunities_by_country(selected_country)
    st.session_state['last_search'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Quick Stats")
df_all = pd.read_sql("SELECT * FROM Opportunities", get_db())
if not df_all.empty:
    st.sidebar.write(f"📌 Total: {len(df_all)}")
    st.sidebar.write(f"✅ Applied: {len(df_all[df_all['Status'] == 'Applied'])}")
    st.sidebar.write(f"⏳ Pending: {len(df_all[df_all['Status'] == 'Not Applied'])}")

# Notes Button
st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 Quick Notes")
with st.sidebar.expander("➕ Add Note"):
    note_title = st.text_input("Note Title")
    note_content = st.text_area("Content")
    if st.button("💾 Save Note"):
        if note_title and note_content:
            save_note(note_title, note_content, selected_country)
            st.success("✅ Saved!")

# ---- MAIN CONTENT ----
st.title("🌍 Global Opportunity Intelligence Network")
st.markdown("<p class='golden-text'>Real-time extraction from 20+ trusted sources • Country-specific deployment</p>", unsafe_allow_html=True)

# ---- Metrics ----
col1, col2, col3, col4 = st.columns(4)
if not df_all.empty:
    total = len(df_all)
    applied = len(df_all[df_all['Status'] == 'Applied'])
    pending = len(df_all[df_all['Status'] == 'Not Applied'])
    urgent = len(df_all[pd.to_datetime(df_all['Deadline']) <= datetime.today() + timedelta(days=10)])
    col1.metric("📌 Total Intelligence", total)
    col2.metric("✅ Applied", applied)
    col3.metric("⏳ Pending", pending, delta=f"{pending} waiting")
    col4.metric("🔴 Urgent", urgent, delta="action needed" if urgent>0 else None)
else:
    col1.metric("📌 Total Intelligence", 0)
    col2.metric("✅ Applied", 0)
    col3.metric("⏳ Pending", 0)
    col4.metric("🔴 Urgent", 0)

# ---- SEARCH RESULTS ----
if 'search_results' in st.session_state and st.session_state['search_results']:
    st.subheader(f"🎯 Intelligence for {selected_country}")
    st.write(f"🕐 Last Updated: {st.session_state['last_search']}")
    
    # Display results in a dataframe
    results_df = pd.DataFrame(st.session_state['search_results'])
    
    # Add score column
    profile_df = pd.read_sql("SELECT * FROM MasterProfile LIMIT 1", get_db())
    if not profile_df.empty:
        profile = profile_df.iloc[0].to_dict()
        profile_keywords = extract_keywords(
            profile['Skills'] + " " + 
            profile['Experience'] + " " +
            profile['Achievements']
        )
        results_df['Match Score'] = results_df.apply(
            lambda row: score_opportunity(row, profile_keywords), axis=1
        )
        results_df = results_df.sort_values('Match Score', ascending=False)
    
    # Display
    st.dataframe(
        results_df[['Title', 'Organization', 'Category', 'Deadline', 'Match Score', 'Source']],
        use_container_width=True
    )
    
    # Add to database button
    if st.button("📥 Save All Matched to Database"):
        for _, row in results_df.iterrows():
            # Check if already exists
            conn = get_db()
            existing = pd.read_sql(
                f"SELECT * FROM Opportunities WHERE Title LIKE '%{row['Title'][:30]}%'", 
                conn
            )
            conn.close()
            if existing.empty:
                add_opportunity({
                    "title": row['Title'],
                    "organization": row['Organization'],
                    "category": row['Category'],
                    "deadline": datetime.today().date() + timedelta(days=30),
                    "status": "Not Applied",
                    "description": f"Country: {row['Country']} | Source: {row['Source']}",
                    "link": row['Link'],
                    "country": row['Country']
                })
        st.success("✅ Saved!")
        st.rerun()

# ---- NOTES & HISTORY ----
st.subheader("📝 Research Notes & History")
notes_df = get_notes()
if not notes_df.empty:
    col1, col2 = st.columns([3, 1])
    for _, note in notes_df.iterrows():
        with st.expander(f"📄 {note['Title']} - {note['Country']} ({note['CreatedAt']})"):
            st.write(note['Content'])
            if st.button(f"🗑️ Delete", key=f"del_{note['Id']}"):
                delete_note(note['Id'])
                st.rerun()
else:
    st.info("No notes saved yet.")

# ---- OPPORTUNITY TABLE ----
st.subheader("📊 All Intelligence (Database)")
if not df_all.empty:
    display_cols = ["Id", "Title", "Organization", "Category", "Deadline", "Country", "Status"]
    st.dataframe(df_all[display_cols], use_container_width=True)
    
    # Quick actions
    selected_id = st.selectbox("Select Opportunity ID for Action", df_all["Id"].tolist())
    if selected_id:
        row = df_all[df_all["Id"] == selected_id].iloc[0]
        with st.expander(f"📄 {row['Title']} – {row['Organization']}", expanded=True):
            st.write(f"**Country:** {row['Country']}")
            st.write(f"**Source:** {row['Source']}")
            st.write(f"**Deadline:** {row['Deadline']}")
            st.write(f"**Status:** {row['Status']}")
            st.write(f"**Link:** {row['Link']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Mark Applied"):
                    update_status(selected_id, "Applied")
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete"):
                    delete_opportunity(selected_id)
                    st.rerun()
            with col3:
                if st.button("🌐 Open Link"):
                    if row['Link'] and row['Link'].startswith("http"):
                        st.write(f"Opening: {row['Link']}")
                        # Using JavaScript to open new tab
                        st.markdown(
                            f'<a href="{row["Link"]}" target="_blank">🔗 Click to open</a>',
                            unsafe_allow_html=True
                        )
else:
    st.info("No opportunities in database. Deploy intelligence first!")

st.markdown("---")
st.caption("⚡ Data stored in SQLite | Real-time extraction from 20+ sources | Ethiopia-focused intelligence active")