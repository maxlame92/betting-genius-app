import streamlit as st
import google.generativeai as genai
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import os
import time

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="BettingGenius Ultimate - AI & PsychoEngine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DESIGN CSS "PREMIUM SAAS" ---
st.markdown("""
<style>
    /* FOND GLOBAL */
    .stApp { background-color: #0b0f19; color: #e0e6ed; }
    
    /* TYPOGRAPHIE */
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    h1 { color: #ffffff; font-weight: 800; }
    h3 { color: #10B981; } 

    /* STYLE DES CARTES "COUPONS" */
    .coupon-card {
        background: linear-gradient(145deg, #161b26, #11151e);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d3748;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s ease-in-out;
    }
    .coupon-card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.5); }

    /* BORDURES CATÉGORIES */
    .border-safe { border-left: 6px solid #10B981; }   /* Vert */
    .border-psycho { border-left: 6px solid #8B5CF6; } /* Violet */
    .border-fun { border-left: 6px solid #F59E0B; }    /* Orange */

    /* BADGES */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-right: 5px;
    }
    .badge-conf { background-color: #064e3b; color: #6ee7b7; border: 1px solid #10B981; }
    .badge-psy { background-color: #4c1d95; color: #c4b5fd; border: 1px solid #8B5CF6; }
    
    /* STATS GRID (Le design "Ticket") */
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 15px 0;
    }
    .stat-box {
        background: #111827;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #374151;
    }
    .stat-label { color: #9CA3AF; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { color: #fff; font-weight: bold; font-size: 1.1em; }

    /* BOUTON D'ACTION */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%);
        color: white; border: none; padding: 16px; font-size: 18px; font-weight: bold; border-radius: 10px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        transition: 0.3s;
    }
    .stButton>button:hover { background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%); }
    
    /* ZONE ANALYSE TEXTE COMPLETE */
    .full-analysis-box {
        background-color: #1f2937;
        padding: 25px;
        border-radius: 10px;
        border-left: 4px solid #3B82F6;
        color: #d1d5db;
        line-height: 1.6;
        font-size: 0.95em;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BARRE LATÉRALE (PARAMÈTRES) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2586/2586885.png", width=70)
    st.title("BettingGenius")
    st.markdown("**Ultimate Edition (V6)**")
    st.markdown("---")
    
    # Gestion Clé API (Auto Render ou Manuelle)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Clé API Google Gemini", type="password")

    st.markdown("### 🧬 Cerveau IA")
    # Liste complète des modèles
    model_choice = st.selectbox(
        "Version du modèle :", 
        [
            "gemini-1.5-flash",        # Le plus stable
            "gemini-2.0-flash-exp",    # Rapide
            "gemini-2.5-flash",        # Nouvelle génération
            "gemini-2.5-pro",          # Haute intelligence
            "gemini-1.5-pro-latest",   # Pro stable
            "Autre (Manuel)"
        ],
        index=0
    )
    
    if model_choice == "Autre (Manuel)":
        model_version = st.text_input("Nom technique", "gemini-1.5-flash")
    else:
        model_version = model_choice
    
    st.success(f"Modèle actif : **{model_version}**")
    st.info("✅ Anti-Bot BeSoccer Actif\n✅ PsychoEngine™ Actif\n✅ Design Ticket Actif")

# --- 4. FONCTION SCRAPING (ANTI-BLOCAGE) ---
def get_besoccer_data(url):
    """
    Récupère les données en contournant les erreurs 403.
    Force l'URL en français pour une meilleure analyse.
    """
    url = url.replace("www.besoccer.com", "fr.besoccer.com")
    url = url.replace("/preview", "/avant-match")
    url = url.replace("/analysis", "/analyse")
    
    try:
        # Configuration du CloudScraper (Imite Chrome sur Windows)
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Nettoyage agressif du HTML inutile
            for tag in soup(["script", "style", "nav", "footer", "iframe", "svg", "header", "aside", "form"]):
                tag.extract()
            
            text = ' '.join(soup.get_text(separator=' ').split())
            title = soup.find('title').text if soup.find('title') else "Match sans titre"
            
            # Vérification anti-page vide
            if len(text) < 500: return None
            
            return {"title": title, "content": text[:45000]} # Max context
        else:
            return None
    except:
        return None

def build_ultimate_prompt(match_data):
    """
    Le Prompt Maître : 9 Points + Psycho + JSON Ticket.
    """
    return f"""
    Tu es "BettingGenius", l'IA experte mondiale en paris sportifs.
    
    ANALYSE LE MATCH : {match_data['title']}
    DONNÉES : "{match_data['content']}"

    --- PARTIE 1 : ANALYSE TECHNIQUE & PSYCHOLOGIQUE (TEXTE) ---
    Rédige une analyse détaillée. Si info manquante, dis "❌ Non dispo".
    1. **🏆 Prédiction** : Forme + Dynamique Mentale (Confiance/Crise).
    2. **🚩 Corners** : Stratégie (Ailes/Axe).
    3. **🔢 Score exact**.
    4. **⚽ Total Buts** (xG, Momentum).
    5. **⏱️ Périodes** (Buts tardifs ?).
    6. **🏥 Absences** (Impact réel).
    7. **🏟️ Conditions** (Météo/Terrain).
    8. **⚠️ Facteurs X** (Arbitrage/Pression).
    9. **🎲 Monte Carlo** (Probabilités).

    --- PARTIE 2 : CLASSIFICATION ET COUPON (JSON STRICT) ---
    Génère ce JSON à la fin pour créer le ticket de pari.
    
    Catégories : 
    - "SAFE" (Confiance > 80%, Favori solide).
    - "PSYCHO" (Enjeu vital : Maintien, Titre, Derby).
    - "FUN" (Risqué ou Indécis).

    ```json
    {{
        "match": "{match_data['title']}",
        "pari_principal": "Ex: Victoire Real Madrid",
        "score_exact": "Ex: 3-1",
        "corners": "Ex: +9.5",
        "total_buts": "Ex: +3.5",
        "confiance": 85,
        "categorie": "SAFE", 
        "facteur_psycho": "Ex: COURSE AU TITRE / MAINTIEN / FORME OLYMPIQUE",
        "analyse_courte": "Une phrase d'expert pour résumer."
    }}
    ```
    """

# --- 5. INTERFACE PRINCIPALE ---

st.title("🧠 BettingGenius Ultimate")
st.markdown("Collez vos liens **BeSoccer** ci-dessous (Anglais ou Français acceptés).")

urls_input = st.text_area("🔗 Liens des matchs", height=120)

if "results" not in st.session_state: st.session_state.results = []

# --- LOGIQUE D'EXÉCUTION ---
if st.button("LANCER L'ANALYSE COMPLÈTE 🚀"):
    if not api_key or not urls_input:
        st.warning("⛔ Clé API ou liens manquants.")
    else:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        st.session_state.results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        genai.configure(api_key=api_key)
        
        # Test Modèle
        try:
            model = genai.GenerativeModel(model_version)
        except:
            st.error("❌ Modèle incorrect. Changez-le dans la barre latérale.")
            st.stop()
        
        for i, url in enumerate(urls):
            status_text.markdown(f"**⏳ Match {i+1}/{len(urls)} : Analyse en cours...**")
            
            # 1. Pause Anti-Ban BeSoccer
            time.sleep(2)
            
            # 2. Scraping
            data = get_besoccer_data(url)
            
            if data:
                # 3. Boucle de Réessai (Retry Logic) pour l'IA
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        response = model.generate_content(build_ultimate_prompt(data))
                        full_text = response.text
                        
                        # Extraction JSON
                        json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                        json_data = {}
                        if json_match:
                            clean_json = re.sub(r'//.*', '', json_match.group(0))
                            try: json_data = json.loads(clean_json)
                            except: json_data = {"match": data['title'], "pari_principal": "Erreur", "categorie": "FUN"}
                            if "match" not in json_data: json_data["match"] = data["title"]
                        
                        # Extraction Texte
                        clean_analysis = re.sub(r'```json.*```', '', full_text, flags=re.DOTALL)
                        
                        st.session_state.results.append({
                            "json": json_data,
                            "analysis_text": clean_analysis,
                            "title": data['title']
                        })
                        break # Succès, on sort du retry
                        
                    except Exception as e:
                        err = str(e)
                        if "429" in err: # Quota
                            status_text.warning(f"⚠️ Quota atteint. Pause de 20s...")
                            time.sleep(20)
                        elif "404" in err: # Modèle pas trouvé
                            st.error(f"❌ Le modèle {model_version} n'est pas disponible. Utilisez 'gemini-1.5-flash'.")
                            break
                        else:
                            st.error(f"Erreur IA : {err}")
                            break
                
                # Pause post-traitement
                time.sleep(1)
            else:
                st.error(f"Lien bloqué ou vide : {url}")
            
            progress_bar.progress((i + 1) / len(urls))
        
        status_text.empty()
        st.success("✅ Analyse terminée !")

# --- 6. AFFICHAGE DES RÉSULTATS (TICKETS & DÉTAILS) ---

if st.session_state.results:
    st.markdown("---")
    
    # Tri
    safes = [r for r in st.session_state.results if r['json'].get('categorie') == 'SAFE']
    psychos = [r for r in st.session_state.results if r['json'].get('categorie') == 'PSYCHO']
    funs = [r for r in st.session_state.results if r['json'].get('categorie') == 'FUN']

    st.subheader("🎟️ VOS COUPONS")
    
    # Onglets
    tab_safe, tab_psycho, tab_fun = st.tabs(["🛡️ BLINDÉ", "🧠 TACTIQUE", "💣 FUN"])

    # FONCTION D'AFFICHAGE DU TICKET
    def display_ticket(item, border_class, badge_class):
        j = item['json']
        st.markdown(f"""
        <div class="coupon-card {border_class}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div class="match-title" style="margin:0;">{j.get('match')}</div>
                <span class="badge badge-conf">{j.get('confiance')}%</span>
            </div>
            
            <div>
                <span class="badge {badge_class}">{j.get('facteur_psycho', 'ANALYSE')}</span>
            </div>

            <div class="prediction-main" style="margin: 15px 0; font-size:1.3em;">
                🏆 {j.get('pari_principal')}
            </div>

            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">SCORE EXACT</div>
                    <div class="stat-value">{j.get('score_exact', '-')}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">TOTAL BUTS</div>
                    <div class="stat-value">{j.get('total_buts', '-')}</div>
                </div>
            </div>
            
            <div style="margin-top:5px; font-size:0.9em; color:#9CA3AF;">
                🚩 Corners: <span style="color:#fff;">{j.get('corners', '-')}</span>
            </div>

            <div class="analysis-short">"{j.get('analyse_courte')}"</div>
        </div>
        """, unsafe_allow_html=True)

    with tab_safe:
        if safes:
            for item in safes: display_ticket(item, "border-safe", "badge-conf")
        else: st.info("Aucun match 100% sûr détecté.")

    with tab_psycho:
        if psychos:
            for item in psychos: display_ticket(item, "border-psycho", "badge-psy")
        else: st.info("Pas d'enjeu critique détecté.")

    with tab_fun:
        if funs:
            for item in funs: display_ticket(item, "border-fun", "badge-psy")
        else: st.write("Rien ici.")

    st.markdown("---")
    st.subheader("📝 ANALYSES DÉTAILLÉES (9 POINTS)")
    for item in st.session_state.results:
        with st.expander(f"🔎 {item['title']}", expanded=False):
            st.markdown(f"""<div class="full-analysis-box">{item['analysis_text']}</div>""", unsafe_allow_html=True)