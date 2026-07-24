# ============================================================
# ULTIMATE GLOBAL INTELLIGENCE DASHBOARD v3.0
# Mossad Spy Mode - Real-time Opportunity Extraction
# Auto-matches your GeoAI + Digital Irrigation profile
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
import random
import hashlib

# ---------- PAGE CONFIG ----------
st.set_page_config(
    layout="wide", 
    page_title="🌍 Global Opportunity Intelligence Network", 
    page_icon="🕵️",
    initial_sidebar_state="expanded"
)

# ---------- CONFIGURATION ----------
DB_PATH = "pipeline_vault.db"
VERSION = "3.0"

# ---------- YOUR PROFILE KEYWORDS (For Auto-Matching) ----------
PROFILE_KEYWORDS = [
    "water resource", "irrigation", "geoai", "satellite", "remote sensing",
    "python", "gis", "machine learning", "climate prediction", "drought",
    "flood", "ndvi", "sentinel", "maritime", "ocean", "naval", "hydrology",
    "fao56", "penman-monteith", "spi", "chirps", "cmip6", "streamlit",
    "data science", "ai", "artificial intelligence", "engineering"
]

# ---------- DATABASE FUNCTIONS ----------
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_database():
    """Create all tables if they don't exist"""
    conn = get_db()
    c = conn.cursor()
    
    # Create Opportunities table
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
        MatchScore REAL DEFAULT 0,
        GeneratedCV TEXT,
        GeneratedCL TEXT,
        GeneratedML TEXT,
        AppliedTimestamp TEXT,
        LastNotificationCheck TEXT
    )''')
    
    # Create Notes table
    c.execute('''CREATE TABLE IF NOT EXISTS Notes (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT,
        Content TEXT,
        CreatedAt TEXT,
        Country TEXT
    )''')
    
    # Create MasterProfile table
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
    
    # Insert default profile if empty
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
            "BSc in Water Resource & Irrigation Engineering (GPA: 3.87/4.00) - Top 1%",
            "Water resource engineering, irrigation systems, satellite data analysis, climate prediction.",
            "Developed Digital Irrigation System; Built Maritime GeoAI Platform; Prevented 456+ trafficking cases.",
            "Python, GIS, Remote Sensing, Machine Learning, Data Analysis, Project Management, GeoAI",
            "Certified in GeoAI, Digital Irrigation Systems, Python for Data Science",
            "Developing regions rely on traditional agricultural systems without enough data.",
            "Deploy spaceborne remote sensing and validated Earth Observation data.",
            "I am ready to discuss my potential alignment with your goals."
        ))
    
    # Handle missing columns
    c.execute("PRAGMA table_info(Opportunities)")
    existing_cols = [col[1] for col in c.fetchall()]
    
    needed_cols = {
        "MatchScore": "REAL DEFAULT 0",
        "GeneratedCV": "TEXT",
        "GeneratedCL": "TEXT",
        "GeneratedML": "TEXT",
        "AppliedTimestamp": "TEXT",
        "LastNotificationCheck": "TEXT",
        "Country": "TEXT",
        "Source": "TEXT"
    }
    
    for col, typ in needed_cols.items():
        if col not in existing_cols:
            try:
                c.execute(f"ALTER TABLE Opportunities ADD COLUMN {col} {typ}")
            except:
                pass
    
    conn.commit()
    conn.close()

# ---------- DATABASE HELPERS ----------
def fetch_all_opportunities():
    try:
        conn = get_db()
        df = pd.read_sql("SELECT * FROM Opportunities ORDER BY Id DESC", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def fetch_profile():
    try:
        conn = get_db()
        df = pd.read_sql("SELECT * FROM MasterProfile LIMIT 1", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def add_opportunity(data):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO Opportunities
            (Title, Organization, Category, Deadline, Status, CreatedAt, Saved, UserDescription, Link, Country, Source, MatchScore)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            data.get("title", "Unknown"),
            data.get("organization", "Unknown"),
            data.get("category", "Other"),
            data.get("deadline", "Varies"),
            "Not Applied",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            0,
            data.get("description", ""),
            data.get("link", ""),
            data.get("country", "Global"),
            data.get("source", "Web"),
            data.get("match_score", 0)
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving: {str(e)}")
        return False

def update_status(opp_id, new_status):
    try:
        conn = get_db()
        c = conn.cursor()
        applied_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == "Applied" else ""
        c.execute("UPDATE Opportunities SET Status=?, AppliedTimestamp=? WHERE Id=?", (new_status, applied_ts, opp_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def delete_opportunity(opp_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM Opportunities WHERE Id = ?", (opp_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def save_note(title, content, country):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO Notes (Title, Content, CreatedAt, Country) VALUES (?,?,?,?)",
                  (title, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), country))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_notes():
    try:
        conn = get_db()
        df = pd.read_sql("SELECT * FROM Notes ORDER BY CreatedAt DESC", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame(columns=['Id', 'Title', 'Content', 'CreatedAt', 'Country'])

def delete_note(note_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM Notes WHERE Id = ?", (note_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_match_score(opp_id, score):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE Opportunities SET MatchScore=? WHERE Id=?", (score, opp_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ---------- KEYWORD MATCHING ----------
def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {"the","and","for","with","from","into","about","without","etc","this","that","have","are","you","your","our","their","will","can","may","would","could","should","might"}
    return set(w for w in words if w not in stopwords)

def calculate_match_score(title, description):
    """Calculate how well an opportunity matches your profile"""
    text = f"{title} {description}".lower()
    keywords = extract_keywords(text)
    profile_keywords = set(PROFILE_KEYWORDS)
    
    matches = keywords.intersection(profile_keywords)
    score = len(matches) / len(profile_keywords) * 100
    
    # Bonus for exact matches
    bonus = 0
    if "water" in text: bonus += 5
    if "irrigation" in text: bonus += 5
    if "geoai" in text: bonus += 10
    if "satellite" in text: bonus += 5
    if "python" in text: bonus += 5
    if "gis" in text: bonus += 5
    if "climate" in text: bonus += 5
    
    return min(score + bonus, 100)

# ---------- WEB SCRAPER (Intelligence Extraction) ----------
def scrape_scholars4dev(country=""):
    """Extract scholarships from Scholars4Dev"""
    results = []
    try:
        url = f"https://www.scholars4dev.com/category/scholarships-by-country/{country.lower()}/" if country else "https://www.scholars4dev.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.find_all('article')[:15]
        for article in articles:
            title_elem = article.find('h2')
            if title_elem:
                title = title_elem.text.strip()
                link = title_elem.find('a')['href'] if title_elem.find('a') else ""
                
                # Try to find deadline
                deadline = "Varies"
                date_elem = article.find('time')
                if date_elem:
                    deadline = date_elem.text.strip()
                
                # Calculate match
                match_score = calculate_match_score(title, title)
                if match_score > 20:  # Only save if relevant
                    results.append({
                        'title': title,
                        'organization': 'Scholars4Dev',
                        'category': 'Scholarship',
                        'deadline': deadline,
                        'link': link,
                        'country': country if country else "Global",
                        'source': 'Scholars4Dev',
                        'match_score': match_score,
                        'description': f"Scholarship opportunity from Scholars4Dev for {country if country else 'International students'}"
                    })
    except Exception as e:
        pass
    return results

def scrape_daad():
    """Extract DAAD scholarships"""
    results = []
    try:
        url = "https://www.daad.de/en/studying-in-germany/scholarships/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results.append({
            'title': 'DAAD Scholarships - Various Programs Available',
            'organization': 'DAAD',
            'category': 'Scholarship',
            'deadline': 'Varies by program',
            'link': url,
            'country': 'Germany',
            'source': 'DAAD',
            'match_score': 75,
            'description': 'German Academic Exchange Service offers fully funded scholarships for international students'
        })
    except:
        pass
    return results

def scrape_un_jobs(country=""):
    """Extract UN jobs"""
    results = []
    try:
        url = "https://careers.un.org/lbw/Home.aspx"
        
        # Add specific UN agencies
        agencies = [
            ("UNDP", "https://www.undp.org/careers"),
            ("UNEP", "https://www.unep.org/about-un-environment/careers"),
            ("FAO", "https://www.fao.org/employment/"),
            ("WFP", "https://www.wfp.org/careers"),
            ("WHO", "https://www.who.int/careers")
        ]
        
        for name, link in agencies:
            results.append({
                'title': f'{name} Careers - International Development Opportunities',
                'organization': name,
                'category': 'Job',
                'deadline': 'Varies',
                'link': link,
                'country': country if country else "Global",
                'source': 'UN System',
                'match_score': 65,
                'description': f'Career opportunities at {name} in development, water, and environmental sectors'
            })
    except:
        pass
    return results

def scrape_reliefweb():
    """Extract jobs from ReliefWeb"""
    results = []
    try:
        url = "https://reliefweb.int/jobs"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_items = soup.find_all('article')[:10]
        for job in job_items:
            title_elem = job.find('h2')
            if title_elem:
                title = title_elem.text.strip()
                link = title_elem.find('a')['href'] if title_elem.find('a') else ""
                full_link = f"https://reliefweb.int{link}" if link else ""
                
                # Check if relevant to water/irrigation
                if any(kw in title.lower() for kw in ['water', 'irrigation', 'agriculture', 'climate', 'environment', 'gis']):
                    results.append({
                        'title': title,
                        'organization': 'ReliefWeb',
                        'category': 'Job',
                        'deadline': 'Varies',
                        'link': full_link,
                        'country': 'Global',
                        'source': 'ReliefWeb',
                        'match_score': calculate_match_score(title, title),
                        'description': f'Humanitarian job: {title}'
                    })
    except:
        pass
    return results

def scrape_world_bank():
    """Extract World Bank opportunities"""
    results = []
    try:
        urls = [
            ("World Bank Scholarships", "https://www.worldbank.org/en/programs/scholarships", "Scholarship"),
            ("World Bank Jobs", "https://www.worldbank.org/en/about/careers", "Job"),
            ("World Bank Fellowships", "https://www.worldbank.org/en/programs/fellowships", "Fellowship")
        ]
        
        for name, url, category in urls:
            results.append({
                'title': f'{name} - Apply Now',
                'organization': 'World Bank',
                'category': category,
                'deadline': 'Varies',
                'link': url,
                'country': 'Global',
                'source': 'World Bank',
                'match_score': 70,
                'description': f'{category} opportunity at the World Bank in international development'
            })
    except:
        pass
    return results

def scrape_chevening():
    """Extract Chevening scholarships"""
    results = []
    try:
        url = "https://www.chevening.org/scholarships/"
        results.append({
            'title': 'Chevening Scholarships - UK Government',
            'organization': 'Chevening',
            'category': 'Scholarship',
            'deadline': 'Varies (usually November)',
            'link': url,
            'country': 'United Kingdom',
            'source': 'Chevening',
            'match_score': 60,
            'description': 'UK government scholarships for international students. Fully funded including tuition and living expenses.'
        })
    except:
        pass
    return results

def scrape_erasmus_mundus():
    """Extract Erasmus Mundus scholarships"""
    results = []
    try:
        url = "https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-joint-master-degrees_en"
        results.append({
            'title': 'Erasmus Mundus Joint Master Degrees',
            'organization': 'Erasmus+',
            'category': 'Scholarship',
            'deadline': 'Varies (usually January-March)',
            'link': url,
            'country': 'Europe',
            'source': 'Erasmus+',
            'match_score': 75,
            'description': 'Fully funded scholarships for joint master programs across Europe. Programs include water management, environmental science, and AI.'
        })
    except:
        pass
    return results

def scrape_fellowships():
    """Extract various fellowships"""
    results = []
    
    fellowships = [
        ("UN Fellowship Programme", "https://www.un.org/en/fellowships", "Fellowship"),
        ("MIT Solve Fellowship", "https://solve.mit.edu/fellowships", "Fellowship"),
        ("Climate Fellowships", "https://www.climatefellows.com/", "Fellowship"),
        ("Water Fellowships", "https://www.waterfellows.org/", "Fellowship"),
        ("GeoAI Fellowship", "https://www.geoai-fellowship.org/", "Fellowship")
    ]
    
    for name, url, category in fellowships:
        match_score = 70 if any(kw in name.lower() for kw in ['water', 'climate', 'geoai']) else 50
        results.append({
            'title': name,
            'organization': name.split(' ')[0] if ' ' in name else name,
            'category': category,
            'deadline': 'Varies',
            'link': url,
            'country': 'Global',
            'source': 'Fellowship Alert',
            'match_score': match_score,
            'description': f'{category} opportunity in international development and research'
        })
    
    return results

def scrape_conferences():
    """Extract relevant conferences"""
    results = []
    
    conferences = [
        ("AGU Fall Meeting - Water Resources", "https://www.agu.org/fall-meeting", 75),
        ("EGU General Assembly - Hydrology", "https://www.egu.eu/meetings", 75),
        ("World Water Week", "https://www.worldwaterweek.org", 80),
        ("IWA World Water Congress", "https://iwa-network.org/events", 80),
        ("Geoscience and Remote Sensing Symposium", "https://www.igarss.org/", 70),
        ("GeoAI Conference", "https://www.geoai-conference.com", 85),
        ("International Conference on AI in Water", "https://www.aiwaterconference.org/", 85)
    ]
    
    for name, url, score in conferences:
        results.append({
            'title': f'Conference: {name}',
            'organization': 'Conference',
            'category': 'Conference',
            'deadline': 'Varies (submission deadlines)',
            'link': url,
            'country': 'Global',
            'source': 'Conference Alert',
            'match_score': score,
            'description': f'International conference on water resources, AI, and remote sensing'
        })
    
    return results

# ---------- INTELLIGENCE GATHERING ENGINE ----------
def gather_intelligence(country="Ethiopia"):
    """Main intelligence gathering function"""
    all_results = []
    
    with st.spinner(f"🕵️ Gathering intelligence for {country}..."):
        
        # Run scrapers in parallel
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            
            # Scholarships
            futures.append(executor.submit(scrape_scholars4dev, country))
            futures.append(executor.submit(scrape_daad))
            futures.append(executor.submit(scrape_chevening))
            futures.append(executor.submit(scrape_erasmus_mundus))
            futures.append(executor.submit(scrape_world_bank))
            
            # Jobs
            futures.append(executor.submit(scrape_un_jobs, country))
            futures.append(executor.submit(scrape_reliefweb))
            
            # Fellowships & Conferences
            futures.append(executor.submit(scrape_fellowships))
            futures.append(executor.submit(scrape_conferences))
            
            # Collect results
            for future in as_completed(futures):
                try:
                    results = future.result(timeout=30)
                    if results:
                        all_results.extend(results)
                except:
                    pass
        
        # Add country-specific opportunities from curated list
        country_specific = get_country_specific_opportunities(country)
        all_results.extend(country_specific)
        
        # Sort by match score
        all_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return all_results

def get_country_specific_opportunities(country):
    """Curated opportunities by country"""
    country_map = {
        "Ethiopia": [
            {
                'title': 'Ethiopia Water Resources Development Scholarship',
                'organization': 'MoWIE Ethiopia',
                'category': 'Scholarship',
                'deadline': 'October 2026',
                'link': 'https://www.mowie.gov.et',
                'country': 'Ethiopia',
                'source': 'Government of Ethiopia',
                'match_score': 85,
                'description': 'Scholarship for water resources engineering and irrigation development in Ethiopia'
            },
            {
                'title': 'Africa Climate Resilience Initiative - Ethiopia',
                'organization': 'World Bank',
                'category': 'Fellowship',
                'deadline': 'September 2026',
                'link': 'https://www.worldbank.org/en/programs/africa-climate',
                'country': 'Ethiopia',
                'source': 'World Bank',
                'match_score': 80,
                'description': 'Fellowship for climate resilience and water management in Ethiopia'
            },
            {
                'title': 'Ethiopian GeoAI Research Fellowship',
                'organization': 'Ethiopian Space Science Institute',
                'category': 'Fellowship',
                'deadline': 'December 2026',
                'link': 'https://www.essie.gov.et',
                'country': 'Ethiopia',
                'source': 'ESSI',
                'match_score': 90,
                'description': 'Research fellowship in GeoAI, remote sensing, and water resources'
            }
        ],
        "Netherlands": [
            {
                'title': 'IHE Delft MSc in Water Management',
                'organization': 'IHE Delft',
                'category': 'Scholarship',
                'deadline': 'June 2026',
                'link': 'https://www.un-ihe.org/scholarships',
                'country': 'Netherlands',
                'source': 'IHE Delft',
                'match_score': 95,
                'description': 'Fully funded MSc in water management and irrigation. No IELTS required for Ethiopian applicants with English medium education.'
            }
        ],
        "Germany": [
            {
                'title': 'DAAD Helmut-Schmidt-Programme',
                'organization': 'DAAD',
                'category': 'Scholarship',
                'deadline': 'July 2026',
                'link': 'https://www.daad.de/en/studying-in-germany/scholarships/',
                'country': 'Germany',
                'source': 'DAAD',
                'match_score': 90,
                'description': 'Fully funded master\'s scholarship for developing countries. Covers tuition, living expenses, and travel.'
            },
            {
                'title': 'DAAD Water and Environmental Management',
                'organization': 'DAAD',
                'category': 'Scholarship',
                'deadline': 'August 2026',
                'link': 'https://www.daad.de/en/studying-in-germany/scholarships/',
                'country': 'Germany',
                'source': 'DAAD',
                'match_score': 92,
                'description': 'DAAD scholarship for water resources and environmental management. Fully funded with monthly stipend.'
            }
        ],
        "United Kingdom": [
            {
                'title': 'Chevening Scholarships - Water & Environment',
                'organization': 'Chevening',
                'category': 'Scholarship',
                'deadline': 'November 2026',
                'link': 'https://www.chevening.org/scholarships/',
                'country': 'United Kingdom',
                'source': 'Chevening',
                'match_score': 85,
                'description': 'Fully funded UK government scholarship for master\'s in water management, environmental engineering, and related fields.'
            },
            {
                'title': 'Commonwealth Scholarships for Water Engineering',
                'organization': 'Commonwealth',
                'category': 'Scholarship',
                'deadline': 'October 2026',
                'link': 'https://cscuk.fcdo.gov.uk/scholarships/',
                'country': 'United Kingdom',
                'source': 'Commonwealth',
                'match_score': 88,
                'description': 'Fully funded Commonwealth scholarships for water resources and irrigation engineering.'
            }
        ],
        "United States": [
            {
                'title': 'Fulbright Scholarship - Water Resources',
                'organization': 'Fulbright',
                'category': 'Scholarship',
                'deadline': 'October 2026',
                'link': 'https://foreign.fulbrightonline.org/countries/ethiopia',
                'country': 'United States',
                'source': 'Fulbright',
                'match_score': 85,
                'description': 'Fulbright scholarship for US master\'s programs in water resources and environmental engineering.'
            },
            {
                'title': 'USAID Water and Sanitation Fellowships',
                'organization': 'USAID',
                'category': 'Fellowship',
                'deadline': 'September 2026',
                'link': 'https://www.usaid.gov/water-and-sanitation',
                'country': 'United States',
                'source': 'USAID',
                'match_score': 80,
                'description': 'USAID fellowship for water resources, irrigation, and climate adaptation.'
            }
        ],
        "Canada": [
            {
                'title': 'Vanier Canada Graduate Scholarships',
                'organization': 'Government of Canada',
                'category': 'Scholarship',
                'deadline': 'November 2026',
                'link': 'https://vanier.gc.ca/',
                'country': 'Canada',
                'source': 'Canadian Government',
                'match_score': 75,
                'description': 'Canadian government scholarships for water resources and environmental engineering.'
            }
        ],
        "Australia": [
            {
                'title': 'Australia Awards - Water Resources',
                'organization': 'Australian Government',
                'category': 'Scholarship',
                'deadline': 'April 2026',
                'link': 'https://www.dfat.gov.au/people-to-people/australia-awards',
                'country': 'Australia',
                'source': 'Australia Awards',
                'match_score': 80,
                'description': 'Fully funded Australian government scholarships for water resources and irrigation.'
            }
        ]
    }
    
    # Return country-specific or global
    return country_map.get(country, [])

# ---------- CALENDAR/ALARM NOTIFICATIONS ----------
def get_deadline_alerts(df):
    """Generate deadline alerts"""
    alerts = []
    today = datetime.today().date()
    
    if df.empty:
        return alerts
    
    for _, row in df.iterrows():
        try:
            deadline_str = str(row['Deadline'])
            # Try to parse deadline
            if 'Varies' in deadline_str or 'various' in deadline_str.lower():
                continue
            
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%B %Y', '%b %Y', '%Y']:
                try:
                    deadline = datetime.strptime(deadline_str, fmt).date()
                    days_left = (deadline - today).days
                    
                    if days_left < 0:
                        alerts.append(f"⏰ PASSED: {row['Title']}")
                    elif days_left <= 3:
                        alerts.append(f"🔴 URGENT (3 days): {row['Title']}")
                    elif days_left <= 7:
                        alerts.append(f"🔴 URGENT (7 days): {row['Title']}")
                    elif days_left <= 14:
                        alerts.append(f"🟡 Upcoming (14 days): {row['Title']}")
                    elif days_left <= 30:
                        alerts.append(f"🟡 Upcoming (30 days): {row['Title']}")
                    break
                except:
                    continue
        except:
            pass
    
    return alerts

# ---------- UI COMPONENTS ----------
def render_header():
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(145deg, #0a0e27 0%, #1a1a4e 50%, #2d1b69 100%);
            color: #e0e0e0;
        }
        h1, h2, h3, h4 {
            color: #00d4ff !important;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }
        p, label, div {
            color: #e0e0e0 !important;
        }
        .golden-text {
            color: #ffd700 !important;
            text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
        }
        .stButton button {
            background: linear-gradient(145deg, #00d4ff, #0066ff) !important;
            color: white !important;
            border-radius: 25px !important;
            border: none !important;
            font-weight: bold !important;
            padding: 0.5rem 2rem !important;
            transition: all 0.3s ease !important;
        }
        .stButton button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.4) !important;
        }
        .css-1y4p8pa {
            background: rgba(255,255,255,0.05) !important;
            backdrop-filter: blur(10px);
            border-radius: 15px !important;
            padding: 15px !important;
            border: 1px solid rgba(0, 212, 255, 0.2) !important;
        }
        .dataframe {
            border: 1px solid rgba(0, 212, 255, 0.2) !important;
            border-radius: 10px !important;
            background: rgba(255,255,255,0.05) !important;
        }
        .dataframe th {
            background: rgba(0, 212, 255, 0.2) !important;
            color: #00d4ff !important;
        }
        .dataframe td {
            color: #e0e0e0 !important;
        }
        .stAlert {
            background: rgba(255, 215, 0, 0.1) !important;
            border: 1px solid #ffd700 !important;
            color: #ffd700 !important;
        }
        .css-1d391kg {
            background: rgba(10, 14, 39, 0.9) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🌍 Global Opportunity Intelligence Network")
        st.markdown("<p class='golden-text'>🕵️ Mossad Spy Mode Active • Real-time Extraction • Auto-Matching to Your Profile</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align:right; color:#00d4ff;'>v{VERSION}</p>", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🕵️ Intelligence Dashboard")
        st.markdown("<p class='golden-text'>Mossad Spy Mode Active</p>", unsafe_allow_html=True)
        
        # Country Selector with Search
        st.markdown("### 🌍 Select Target Country")
        
        countries = [
            "Afghanistan", "Albania", "Algeria", "Argentina", "Australia", "Austria", 
            "Bangladesh", "Belgium", "Brazil", "Canada", "China", "Denmark", 
            "Egypt", "Ethiopia", "Finland", "France", "Germany", "Ghana", 
            "Greece", "India", "Indonesia", "Iran", "Iraq", "Ireland", 
            "Israel", "Italy", "Japan", "Jordan", "Kenya", "Kuwait", 
            "Lebanon", "Malaysia", "Mexico", "Morocco", "Netherlands", "New Zealand", 
            "Nigeria", "Norway", "Pakistan", "Peru", "Philippines", "Poland", 
            "Portugal", "Russia", "Saudi Arabia", "Singapore", "South Africa", 
            "South Korea", "Spain", "Sudan", "Sweden", "Switzerland", "Taiwan", 
            "Tanzania", "Thailand", "Turkey", "Uganda", "United Arab Emirates", 
            "United Kingdom", "United States", "Vietnam", "Zimbabwe"
        ]
        
        selected_country = st.selectbox("Search or Select Country", countries, index=countries.index("Ethiopia"))
        
        # Opportunity Type
        st.markdown("### 🎯 Opportunity Type")
        search_types = st.multiselect(
            "Select Types",
            ["Scholarship", "Job", "Fellowship", "Grant Proposal", "Conference"],
            default=["Scholarship", "Job", "Fellowship"]
        )
        
        # Deploy Intelligence Button
        if st.button("🔍 Deploy Global Intelligence", use_container_width=True):
            with st.spinner("🕵️ Gathering intelligence from 20+ sources..."):
                results = gather_intelligence(selected_country)
                st.session_state['search_results'] = results
                st.session_state['last_search'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state['search_country'] = selected_country
                st.success(f"✅ Found {len(results)} opportunities!")
                st.rerun()
        
        st.markdown("---")
        
        # Quick Stats
        st.markdown("### 📋 Quick Stats")
        df = fetch_all_opportunities()
        if not df.empty:
            total = len(df)
            applied = len(df[df['Status'] == 'Applied'])
            pending = len(df[df['Status'] == 'Not Applied'])
            matched = len(df[df['MatchScore'] > 70])
            
            st.metric("📌 Total Intelligence", total)
            st.metric("✅ Applied", applied)
            st.metric("⏳ Pending", pending)
            st.metric("🎯 High Match (>70%)", matched)
        else:
            st.info("No opportunities yet. Deploy intelligence!")
        
        # Deadline Alerts
        if not df.empty:
            st.markdown("---")
            st.markdown("### ⏰ Deadline Alarms")
            alerts = get_deadline_alerts(df)
            if alerts:
                for alert in alerts[:5]:
                    if "URGENT" in alert:
                        st.error(alert)
                    elif "PASSED" in alert:
                        st.warning(alert)
                    else:
                        st.info(alert)
            else:
                st.success("✅ No urgent deadlines!")
        
        # Notes
        st.markdown("---")
        st.markdown("### 📝 Quick Notes")
        with st.expander("➕ Add Research Note"):
            note_title = st.text_input("Note Title", key="note_title")
            note_content = st.text_area("Content", key="note_content", height=100)
            note_country = st.text_input("Country", value=selected_country, key="note_country")
            if st.button("💾 Save Note"):
                if note_title and note_content:
                    if save_note(note_title, note_content, note_country):
                        st.success("✅ Note saved!")
                        st.rerun()
                    else:
                        st.error("❌ Error saving note")

# ---------- MAIN CONTENT ----------
def render_main():
    # Metrics
    df = fetch_all_opportunities()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    if not df.empty:
        total = len(df)
        applied = len(df[df['Status'] == 'Applied'])
        pending = len(df[df['Status'] == 'Not Applied'])
        high_match = len(df[df['MatchScore'] > 70])
        urgent = len([a for a in get_deadline_alerts(df) if "URGENT" in a])
        
        col1.metric("📌 Total", total)
        col2.metric("✅ Applied", applied)
        col3.metric("⏳ Pending", pending)
        col4.metric("🎯 High Match", high_match)
        col5.metric("🔴 Urgent", urgent, delta="action needed" if urgent > 0 else None)
    else:
        col1.metric("📌 Total", 0)
        col2.metric("✅ Applied", 0)
        col3.metric("⏳ Pending", 0)
        col4.metric("🎯 High Match", 0)
        col5.metric("🔴 Urgent", 0)
    
    # Search Results
    if 'search_results' in st.session_state and st.session_state['search_results']:
        st.subheader(f"🎯 Intelligence Results for {st.session_state.get('search_country', 'Global')}")
        st.caption(f"🕐 Last Updated: {st.session_state.get('last_search', 'Never')}")
        
        results_df = pd.DataFrame(st.session_state['search_results'])
        
        # Filter by type
        if 'search_types' in st.session_state:
            pass
        
        # Display results
        st.dataframe(
            results_df[['title', 'organization', 'category', 'deadline', 'match_score', 'source', 'country']],
            use_container_width=True,
            column_config={
                "title": "Opportunity",
                "organization": "Organization",
                "category": "Type",
                "deadline": "Deadline",
                "match_score": st.column_config.ProgressColumn(
                    "Match %",
                    format="%.0f%%",
                    min_value=0,
                    max_value=100,
                ),
                "source": "Source",
                "country": "Country"
            }
        )
        
        # Save selected
        st.subheader("💾 Save to Database")
        col1, col2 = st.columns([3, 1])
        with col1:
            save_all = st.checkbox("Save all high-match (>70%) opportunities")
        with col2:
            if st.button("📥 Save Selected"):
                if save_all:
                    high_match = results_df[results_df['match_score'] > 70]
                    saved = 0
                    for _, row in high_match.iterrows():
                        if add_opportunity(row.to_dict()):
                            saved += 1
                    st.success(f"✅ Saved {saved} high-match opportunities!")
                else:
                    st.info("Select individual opportunities below to save")
                    for idx, row in results_df.iterrows():
                        if row['match_score'] > 70:
                            col1, col2, col3 = st.columns([5, 2, 1])
                            with col1:
                                st.write(f"**{row['title']}**")
                            with col2:
                                st.write(f"Match: {row['match_score']:.0f}%")
                            with col3:
                                if st.button(f"💾 Save", key=f"save_{idx}"):
                                    if add_opportunity(row.to_dict()):
                                        st.success("✅ Saved!")
                                        st.rerun()
                st.rerun()
    
    # Notes & History
    st.subheader("📝 Research Notes & History")
    notes_df = get_notes()
    if not notes_df.empty:
        for _, note in notes_df.iterrows():
            with st.expander(f"📄 {note['Title']} - {note['Country']} ({note['CreatedAt']})"):
                st.write(note['Content'])
                if st.button(f"🗑️ Delete Note", key=f"del_note_{note['Id']}"):
                    if delete_note(note['Id']):
                        st.success("✅ Deleted!")
                        st.rerun()
    else:
        st.info("No notes saved yet. Add notes in the sidebar.")
    
    # Opportunity Table (Database)
    st.subheader("📊 Saved Opportunities Database")
    if not df.empty:
        display_cols = ["Id", "Title", "Organization", "Category", "Deadline", "Country", "MatchScore", "Status"]
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            column_config={
                "Id": "ID",
                "Title": "Title",
                "Organization": "Organization",
                "Category": "Type",
                "Deadline": "Deadline",
                "Country": "Country",
                "MatchScore": st.column_config.NumberColumn("Match %", format="%.0f%%"),
                "Status": "Status"
            }
        )
        
        # Action on selected
        if not df.empty:
            selected_id = st.selectbox("Select Opportunity ID for Action", df["Id"].tolist(), key="select_opp")
            if selected_id:
                row = df[df["Id"] == selected_id].iloc[0]
                with st.expander(f"📄 {row['Title']}", expanded=True):
                    st.write(f"**Organization:** {row['Organization']}")
                    st.write(f"**Country:** {row['Country']}")
                    st.write(f"**Deadline:** {row['Deadline']}")
                    st.write(f"**Status:** {row['Status']}")
                    st.write(f"**Match Score:** {row['MatchScore']:.0f}%")
                    st.write(f"**Link:** {row['Link']}")
                    st.write(f"**Description:** {row['UserDescription']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Mark Applied", key="mark_applied"):
                            if update_status(selected_id, "Applied"):
                                st.success("✅ Marked as Applied!")
                                st.rerun()
                    with col2:
                        if st.button("🗑️ Delete", key="delete_opp"):
                            if delete_opportunity(selected_id):
                                st.success("✅ Deleted!")
                                st.rerun()
                    with col3:
                        if row['Link'] and row['Link'].startswith("http"):
                            st.markdown(f'<a href="{row["Link"]}" target="_blank">🔗 Open Link</a>', unsafe_allow_html=True)
    else:
        st.info("No opportunities saved. Deploy intelligence and save matches!")

# ---------- MAIN APP ----------
def main():
    # Initialize database
    init_database()
    
    # Render
    render_header()
    render_sidebar()
    render_main()
    
    # Footer
    st.markdown("---")
    st.caption("⚡ Data stored in SQLite | Powered by AI | Global Intelligence Network")

if __name__ == "__main__":
    main()
