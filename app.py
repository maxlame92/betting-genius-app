import streamlit as st
import google.generativeai as genai
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import os
import time

# ==========================================
# 1. CONFIGURATION INITIALE
# ==========================================
st.set_page_config(
    page_title="BettingGenius Ultimate V8",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DESIGN CSS (STABLE & PREMIUM)
# ==========================================
st.markdown("""
<style>
    /* FOND ET COULEURS GLOBALES */
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    
    /* TYPOGRAPHIE */
    h1, h2, h3 { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    h1 { color: #F8FAFC; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; }
    
    /* STYLE DES TICKETS (COUPONS) */
    .coupon-container {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
    }
    
    /* BORDURES LATÉRALES SELON CATÉGORIE */
    .border-safe { border-left: 6px solid #22C55E; }   /* VERT */
    .border-psycho { border-left: 6px solid #A855F7; } /* VIOLET */
    .border-fun { border-left: 6px solid #F59E0B; }    /* ORANGE */

    /* EN-TÊTE DU TICKET */
    .ticket-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15px;
        border-bottom: 1px solid #334155;
        padding-bottom: 10px;
    }
    .match-name { font-size: 1.2rem; font-weight: 700; color: #fff; }
    
    /* BADGES */
    .badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 800;
        padding: 4px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        margin-top: 5px;
    }
    .badge-psy { background-color: #581C87; color: #D8B4FE; border: 1px solid #A855F7; }
    
    /* JAUGE DE CONFIANCE */
    .conf-box { text-align: right; min-width: 80px; }
    .conf-label { font-size: 0.7rem; color: #94A3B8; }
    .conf-val { font-weight: bold; color: #fff; font-size: 1.1rem; }
    .progress-track { background: #334155; height: 6px; border-radius: 3px; margin-top: 4px; width: 100%; }
    .progress-bar { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #22C55E, #4ADE80); }

    /* PARI PRINCIPAL */
    .main-bet-box {
        font-size: 1.4rem;
        font-weight: 800;
        color: #22C55E;
        margin: 15px 0;
        text-align: center;
        background: #0F172A;
        padding: 12px;
        border-radius: 8px;
        border: 1px dashed #374151;
    }

    /* GRILLE DE STATS */
    .stats-container {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
    }
    .stat-card {
        flex: 1;
        background: #0F172A;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #334155;
    }
    .stat-title { font-size: 0.7em; color: #94A3B8; letter-spacing: 0.5px; text-transform: uppercase; }
    .stat-data { font-size: 1.1em; font-weight: bold; color: #F8FAFC; margin-top: 2px; }

    /* TEXTE ANALYSE */
    .analysis-footer {
        font-style: italic;
        color: #CBD5E1;
        font-size: 0.95em;
        line-height: 1.5;
        border-top: 1px solid #334155;
        padding-top: 10px;
    }

    /* BOUTON GLOBAL */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        border: none;
        padding: 16px;
        font-weight: bold;
        color: white;
        border-radius: 8px;
        font-size: 1.1rem;
        transition: all 0.2s;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
    }
    .stButton>button:hover { transform: scale(1.01); background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); }
    
    /* ANALYSE DÉTAILLÉE */
    .full-details {
        background-color: #1E293B;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #3B82F6;
        color: #E2E8F0;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR (CONFIGURATIONS)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2586/2586885.png", width=70)
    st.title("BettingGenius")
    st.markdown("**Version Ultimate (V8)**")
    st.markdown("---")
    
    # 3.1 Gestion de la Clé API (Render vs Local)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Clé API Google Gemini", type="password")

    # 3.2 Sélection du Modèle
    st.markdown("### 🧬 Cerveau IA")
    model_choice = st.selectbox(
        "Version du modèle :", 
        [
            "gemini-1.5-flash",        # Recommandé (Stable)
            "gemini-2.0-flash-exp",    # Rapide mais quotas stricts
            "gemini-1.5-pro",          # Très intelligent
            "gemini-2.5-flash",        # Nouvelle gen
            "Autre (Manuel)"
        ],
        index=0
    )
    
    if model_choice == "Autre (Manuel)":
        model_version = st.text_input("Nom technique", "gemini-1.5-flash")
    else:
        model_version = model_choice
    
    st.success(f"Actif : **{model_version}**")
    st.info("""
    **Modules actifs :**
    ✅ CloudScraper (Anti-Bot)
    ✅ PsychoEngine™ (Mental)
    ✅ Smart Coupons
    ✅ Anti-Crash (Retry)
    """)

# ==========================================
# 4. FONCTIONS CŒUR
# ==========================================

def get_besoccer_data(url):
    """
    Scrape BeSoccer en contournant les protections 403.
    """
    # Normalisation pour éviter les erreurs de langue
    url = url.replace("www.besoccer.com", "fr.besoccer.com")
    url = url.replace("/preview", "/avant-match")
    url = url.replace("/analysis", "/analyse")
    
    try:
        # Simulation d'un navigateur Chrome sur Windows
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Nettoyage brutal du code HTML inutile
            for tag in soup(["script", "style", "nav", "footer", "iframe", "svg", "header", "form", "aside"]):
                tag.extract()
            
            text = ' '.join(soup.get_text(separator=' ').split())
            title = soup.find('title').text if soup.find('title') else "Match Inconnu"
            
            if len(text) < 500: return None # Page vide ou bloquée
            return {"title": title, "content": text[:45000]} # Max context
        return None
    except:
        return None

def build_ultimate_prompt(match_data):
    """
    Le Prompt Complet intégrant les 9 points, la psycho et le JSON.
    """
    return f"""
    Tu es "BettingGenius", l'IA experte en paris sportifs.
    
    ANALYSE LE MATCH : {match_data['title']}
    DONNÉES : "{match_data['content']}"

    --- PHASE 1 : ANALYSE DÉTAILLÉE (TEXTE) ---
    Rédige une analyse structurée. Si info manquante, écris "❌ Non dispo".
    1. **🏆 Prédiction** : Forme + Dynamique Mentale.
    2. **🚩 Corners** : Stratégie & Stats.
    3. **🔢 Score exact**.
    4. **⚽ Total Buts**.
    5. **⏱️ Périodes**.
    6. **🏥 Absences**.
    7. **🏟️ Conditions**.
    8. **⚠️ Facteurs X**.
    9. **🎲 Monte Carlo**.

    --- PHASE 2 : CLASSIFICATION (JSON STRICT) ---
    Génère ce JSON pour créer le ticket.
    Catégories: "SAFE" (Confiance >80%), "PSYCHO" (Enjeu fort), "FUN".

    ```json
    {{
        "match": "{match_data['title']}",
        "pari_principal": "Ex: Victoire Real Madrid",
        "score_exact": "Ex: 3-1",
        "corners": "Ex: +9.5",
        "total_buts": "Ex: +3.5",
        "confiance": 85,
        "categorie": "SAFE", 
        "facteur_psycho": "Ex: COURSE AU TITRE / MAINTIEN / DERBY",
        "analyse_courte": "Résumé d'une phrase."
    }}
    ```
    """

# ==========================================
# 5. INTERFACE PRINCIPALE
# ==========================================
st.title("🧠 BettingGenius Ultimate")
st.markdown("#### L'outil d'analyse le plus complet. Collez vos liens ci-dessous.")

urls_input = st.text_area("🔗 Liens BeSoccer (Un par ligne)", height=120, placeholder="https://fr.besoccer.com/match/...")

if "results" not in st.session_state: st.session_state.results = []

# --- BOUTON DE LANCEMENT ---
if st.button("LANCER L'ANALYSE COMPLÈTE 🚀"):
    if not api_key or not urls_input:
        st.warning("⛔ Clé API ou Liens manquants.")
    else:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        st.session_state.results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Init IA
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel(model_version)
        except:
            st.error(f"❌ Modèle '{model_version}' invalide. Changez-le dans la barre latérale.")
            st.stop()
        
        # BOUCLE D'ANALYSE
        for i, url in enumerate(urls):
            status_text.markdown(f"**⏳ Match {i+1}/{len(urls)} : Analyse en cours...**")
            
            # Pause respectueuse
            time.sleep(2)
            
            data = get_besoccer_data(url)
            
            if data:
                # Retry Logic (3 essais)
                for attempt in range(3):
                    try:
                        res = model.generate_content(build_ultimate_prompt(data))
                        txt = res.text
                        
                        # Parsing JSON
                        j_match = re.search(r'\{.*\}', txt, re.DOTALL)
                        j_data = {}
                        if j_match:
                            clean = re.sub(r'//.*', '', j_match.group(0))
                            try: j_data = json.loads(clean)
                            except: j_data = {"match": data['title'], "pari_principal": "Erreur", "categorie": "FUN"}
                            if "match" not in j_data: j_data["match"] = data["title"]
                        
                        clean_txt = re.sub(r'```json.*```', '', txt, flags=re.DOTALL)
                        
                        st.session_state.results.append({
                            "json": j_data,
                            "text": clean_txt,
                            "title": data['title']
                        })
                        break # Succès
                    except Exception as e:
                        err = str(e)
                        if "429" in err: # Quota
                            status_text.warning("⚠️ Quota atteint. Pause de 20s...")
                            time.sleep(20)
                        elif "404" in err: # Modèle pas trouvé
                            st.error("❌ Modèle indisponible. Passez sur 'gemini-1.5-flash'.")
                            break
                        else:
                            break # Autre erreur
            else:
                st.error(f"Lien bloqué : {url}")
            
            progress_bar.progress((i + 1) / len(urls))
        
        status_text.empty()
        st.success("✅ Analyse terminée !")

# ==========================================
# 6. AFFICHAGE DES RÉSULTATS (TICKETS)
# ==========================================

def render_ticket(item, border_class, badge_class):
    """
    Génère le HTML du ticket proprement pour éviter les erreurs JS.
    """
    j = item['json']
    conf = j.get('confiance', 50)
    
    html = f"""
    <div class="coupon-container {border_class}">
        <!-- EN-TETE -->
        <div class="ticket-head">
            <div>
                <div class="match-name">{j.get('match')}</div>
                <span class="badge {badge_class}">{j.get('facteur_psycho', 'ANALYSE')}</span>
            </div>
            <div class="conf-box">
                <div class="conf-label">CONFIANCE</div>
                <div class="conf-val">{conf}%</div>
                <div class="progress-track">
                    <div class="progress-bar" style="width: {conf}%;"></div>
                </div>
            </div>
        </div>

        <!-- PRONOSTIC -->
        <div class="main-bet-box">
            🏆 {j.get('pari_principal')}
        </div>

        <!-- STATS -->
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-title">SCORE</div>
                <div class="stat-data">{j.get('score_exact', '-')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">BUTS</div>
                <div class="stat-data">{j.get('total_buts', '-')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">CORNERS</div>
                <div class="stat-data">{j.get('corners', '-')}</div>
            </div>
        </div>

        <!-- FOOTER -->
        <div class="analysis-footer">
            "{j.get('analyse_courte')}"
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

if st.session_state.results:
    st.markdown("---")
    
    # Filtrage
    safes = [r for r in st.session_state.results if r['json'].get('categorie') == 'SAFE']
    psychos = [r for r in st.session_state.results if r['json'].get('categorie') == 'PSYCHO']
    funs = [r for r in st.session_state.results if r['json'].get('categorie') == 'FUN']

    t1, t2, t3 = st.tabs(["🛡️ BLINDÉ", "🧠 TACTIQUE", "💣 FUN"])

    with t1:
        if safes:
            for item in safes: render_ticket(item, "border-safe", "bg-green")
        else: st.info("Aucun match 100% sûr détecté.")

    with t2:
        if psychos:
            for item in psychos: render_ticket(item, "border-psycho", "badge-psy")
        else: st.info("Aucun enjeu critique détecté.")

    with t3:
        if funs:
            for item in funs: render_ticket(item, "border-fun", "badge-psy")
        else: st.write("Aucun match Fun.")

    st.markdown("---")
    st.subheader("📝 DÉTAILS COMPLETS (9 POINTS)")
    for item in st.session_state.results:
        with st.expander(f"🔎 {item['title']}"):
            st.markdown(f'<div class="full-details">{item["text"]}</div>', unsafe_allow_html=True)