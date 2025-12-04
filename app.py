import streamlit as st
import google.generativeai as genai
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import os
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="BettingGenius Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS STABILISÉ (Fix pour le bug d'affichage) ---
st.markdown("""
<style>
    /* Fond */
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    
    /* Typographie */
    h1, h2, h3 { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    h1 { color: #F8FAFC; text-transform: uppercase; letter-spacing: 1px; }
    
    /* CARTES COUPONS (Design Ticket 1xBet style) */
    .coupon-card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #334155;
        position: relative;
        overflow: hidden;
    }
    
    /* Bordures colorées */
    .safe-border { border-left: 5px solid #22C55E; }
    .psycho-border { border-left: 5px solid #A855F7; }
    .fun-border { border-left: 5px solid #F59E0B; }

    /* En-tête du ticket */
    .ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15px;
        border-bottom: 1px solid #334155;
        padding-bottom: 10px;
    }
    .ticket-match { font-size: 1.1rem; font-weight: 700; color: #fff; }
    
    /* Badges */
    .ticket-badge {
        font-size: 0.75rem;
        font-weight: 800;
        padding: 4px 8px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .bg-green { background-color: #064E3B; color: #4ADE80; border: 1px solid #22C55E; }
    .bg-purple { background-color: #581C87; color: #D8B4FE; border: 1px solid #A855F7; }
    
    /* Prédiction Principale */
    .main-bet {
        font-size: 1.4rem;
        font-weight: 800;
        color: #22C55E;
        margin: 10px 0;
        text-align: center;
        background: #111827;
        padding: 10px;
        border-radius: 8px;
        border: 1px dashed #374151;
    }

    /* Grille Stats */
    .stats-row {
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }
    .stat-item {
        flex: 1;
        background: #0F172A;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
        border: 1px solid #334155;
    }
    .stat-label { font-size: 0.7em; color: #94A3B8; letter-spacing: 0.5px; }
    .stat-val { font-size: 1.1em; font-weight: bold; color: #F8FAFC; }

    /* Jauge de Confiance (Barre visuelle) */
    .progress-bg {
        background: #334155;
        height: 6px;
        border-radius: 3px;
        margin-top: 5px;
        width: 100%;
    }
    .progress-fill {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #22C55E, #4ADE80);
    }

    /* Analyse texte */
    .analysis-text {
        margin-top: 15px;
        font-style: italic;
        color: #CBD5E1;
        font-size: 0.9em;
        line-height: 1.5;
        background: #1e293b; 
        padding-top: 10px;
    }

    /* Bouton */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        border: none;
        padding: 15px;
        font-weight: bold;
        color: white;
        border-radius: 8px;
        font-size: 1.1rem;
        transition: transform 0.1s;
    }
    .stButton>button:hover { transform: scale(1.01); }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2586/2586885.png", width=60)
    st.title("BettingGenius")
    st.markdown("**V7 - Stable Edition**")
    
    # Clé API
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Clé API Gemini", type="password")

    # Choix Modèle
    model_choice = st.selectbox("Modèle IA :", ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-2.5-flash", "Autre"])
    if model_choice == "Autre":
        model_version = st.text_input("Nom technique", "gemini-1.5-pro")
    else:
        model_version = model_choice
        
    st.success("Système prêt.")

# --- 4. SCRAPING ---
def get_besoccer_data(url):
    url = url.replace("www.besoccer.com", "fr.besoccer.com").replace("/preview", "/avant-match").replace("/analysis", "/analyse")
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
        response = scraper.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer", "iframe", "svg", "header", "form"]): tag.extract()
            text = ' '.join(soup.get_text(separator=' ').split())
            title = soup.find('title').text if soup.find('title') else "Match"
            if len(text) < 500: return None
            return {"title": title, "content": text[:40000]}
        return None
    except: return None

def build_prompt(match_data):
    return f"""
    Tu es "BettingGenius". Analyse : {match_data['title']}
    Données : "{match_data['content']}"

    --- 1. ANALYSE (9 POINTS) ---
    Si info absente, écris "❌ Non dispo".
    1. **🏆 Prédiction** (Forme/Mental).
    2. **🚩 Corners**.
    3. **🔢 Score exact**.
    4. **⚽ Buts**.
    5. **⏱️ Périodes**.
    6. **🏥 Absences**.
    7. **🏟️ Conditions**.
    8. **⚠️ Facteurs X**.
    9. **🎲 Monte Carlo**.

    --- 2. COUPON JSON ---
    Catégories: "SAFE" (>80%), "PSYCHO" (Enjeu), "FUN".
    ```json
    {{
        "match": "{match_data['title']}",
        "pari_principal": "Ex: Victoire Real",
        "score_exact": "Ex: 2-1",
        "corners": "Ex: +9.5",
        "total_buts": "Ex: +2.5",
        "confiance": 85,
        "categorie": "SAFE", 
        "facteur_psycho": "Ex: TITRE / MAINTIEN",
        "analyse_courte": "Résumé court."
    }}
    ```
    """

# --- 5. INTERFACE ---
st.title("🧠 BettingGenius Pro")
st.markdown("Analyseur IA de paris sportifs. Collez vos liens ci-dessous.")

urls_input = st.text_area("🔗 Liens BeSoccer", height=100)

if "results" not in st.session_state: st.session_state.results = []

if st.button("LANCER L'ANALYSE 🚀"):
    if not api_key or not urls_input:
        st.warning("⛔ Manque Clé API ou Liens")
    else:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        st.session_state.results = []
        progress = st.progress(0)
        status = st.empty()
        
        genai.configure(api_key=api_key)
        try: model = genai.GenerativeModel(model_version)
        except: st.error("Modèle invalide"); st.stop()
        
        for i, url in enumerate(urls):
            status.text(f"Analyse {i+1}/{len(urls)}...")
            time.sleep(1.5) # Pause anti-ban
            data = get_besoccer_data(url)
            
            if data:
                # Retry logic
                for attempt in range(2):
                    try:
                        res = model.generate_content(build_prompt(data))
                        txt = res.text
                        
                        # JSON Parse
                        j_match = re.search(r'\{.*\}', txt, re.DOTALL)
                        j_data = {}
                        if j_match:
                            clean = re.sub(r'//.*', '', j_match.group(0))
                            try: j_data = json.loads(clean)
                            except: j_data = {"match": data['title'], "pari_principal": "Erreur", "categorie": "FUN"}
                            if "match" not in j_data: j_data["match"] = data["title"]
                        
                        clean_txt = re.sub(r'```json.*```', '', txt, flags=re.DOTALL)
                        st.session_state.results.append({"json": j_data, "text": clean_txt, "title": data['title']})
                        break
                    except Exception as e:
                        if "429" in str(e): time.sleep(20)
                        else: break
            
            progress.progress((i+1)/len(urls))
        
        status.empty()
        st.success("✅ Terminé !")

# --- 6. AFFICHAGE (NOUVEAU DESIGN SANS ERREUR) ---

# Fonction pour afficher une carte proprement sans casser le DOM
def render_ticket(item, border_class, badge_class):
    j = item['json']
    confiance = j.get('confiance', 50)
    
    # Construction du HTML propre
    html_content = f"""
    <div class="coupon-card {border_class}">
        <!-- EN-TÊTE -->
        <div class="ticket-header">
            <div style="flex-grow:1;">
                <div class="ticket-match">{j.get('match')}</div>
                <div style="margin-top:5px;">
                    <span class="ticket-badge {badge_class}">{j.get('facteur_psycho', 'ANALYSE')}</span>
                </div>
            </div>
            <div style="text-align:right; min-width:60px;">
                <div style="font-size:0.8em; color:#94A3B8;">CONFIANCE</div>
                <div style="font-weight:bold; color:#fff;">{confiance}%</div>
                <div class="progress-bg">
                    <div class="progress-fill" style="width: {confiance}%;"></div>
                </div>
            </div>
        </div>

        <!-- PARI PRINCIPAL -->
        <div class="main-bet">
            🏆 {j.get('pari_principal')}
        </div>

        <!-- STATS -->
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-label">SCORE</div>
                <div class="stat-val">{j.get('score_exact', '-')}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">BUTS</div>
                <div class="stat-val">{j.get('total_buts', '-')}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">CORNERS</div>
                <div class="stat-val">{j.get('corners', '-')}</div>
            </div>
        </div>

        <!-- TEXTE -->
        <div class="analysis-text">
            "{j.get('analyse_courte')}"
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

if st.session_state.results:
    st.markdown("---")
    
    safes = [r for r in st.session_state.results if r['json'].get('categorie') == 'SAFE']
    psychos = [r for r in st.session_state.results if r['json'].get('categorie') == 'PSYCHO']
    funs = [r for r in st.session_state.results if r['json'].get('categorie') == 'FUN']

    t1, t2, t3 = st.tabs(["🛡️ BLINDÉ", "🧠 TACTIQUE", "💣 FUN"])

    with t1:
        if safes:
            for item in safes: render_ticket(item, "safe-border", "bg-green")
        else: st.info("Aucun match 100% sûr.")

    with t2:
        if psychos:
            for item in psychos: render_ticket(item, "psycho-border", "bg-purple")
        else: st.info("Aucun match à enjeu critique.")

    with t3:
        if funs:
            for item in funs: render_ticket(item, "fun-border", "bg-purple")
        else: st.write("Rien ici.")

    st.markdown("---")
    st.subheader("📝 DÉTAILS COMPLETS")
    for item in st.session_state.results:
        with st.expander(f"🔎 {item['title']}"):
            st.markdown(item['text'])