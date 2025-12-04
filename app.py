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
    page_title="BettingGenius Ultimate - NextGen AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e0e6ed; }
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    h1 { color: #ffffff; font-weight: 800; }
    h3 { color: #10B981; } 
    .coupon-card {
        background: linear-gradient(145deg, #161b26, #11151e);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d3748;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s ease-in-out;
    }
    .coupon-card:hover { transform: translateY(-3px); }
    .border-safe { border-left: 6px solid #10B981; }
    .border-psycho { border-left: 6px solid #8B5CF6; }
    .border-fun { border-left: 6px solid #F59E0B; }
    .badge { padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; margin-right: 8px; }
    .badge-conf { background-color: #064e3b; color: #6ee7b7; border: 1px solid #10B981; }
    .badge-psy { background-color: #4c1d95; color: #c4b5fd; border: 1px solid #8B5CF6; }
    .match-title { font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 10px; }
    .prediction-main { color: #10B981; font-weight: 700; font-size: 1.1rem; margin-bottom: 5px; }
    .prediction-details { color: #94a3b8; font-size: 0.9rem; display: flex; gap: 15px; }
    .analysis-short { color: #cbd5e1; font-style: italic; margin-top: 10px; border-top: 1px solid #2d3748; padding-top: 8px; }
    .stButton>button { width: 100%; background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%); color: white; border: none; padding: 16px; font-size: 18px; font-weight: bold; border-radius: 10px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4); }
    .full-analysis-box { background-color: #1f2937; padding: 25px; border-radius: 10px; border-left: 4px solid #3B82F6; color: #d1d5db; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR (SÉLECTION DES NOUVEAUX MODÈLES) ---
with st.sidebar:
    st.title("BettingGenius")
    st.markdown("**Version Ultimate (NextGen)**")
    st.markdown("---")
    
    # Gestion Clé API
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Clé API Google Gemini", type="password")

    st.markdown("### 🧬 Choix du Cerveau IA")
    
    # LISTE MISE À JOUR AVEC TES INFOS
    model_choice = st.selectbox(
        "Modèle :", 
        [
            "gemini-1.5-flash",        # Valeur sûre (Stable)
            "gemini-2.0-flash-exp",    # Experimental actuel
            "gemini-2.5-flash",        # Nouveau (Selon tes infos)
            "gemini-2.5-pro",          # Nouveau (Selon tes infos)
            "gemini-3.0-pro-preview",  # Le futur (Selon tes infos)
            "Autre (Saisie Manuelle)"  # Au cas où le nom change
        ],
        index=0
    )
    
    # Si l'utilisateur veut entrer un nom spécifique manuellement
    if model_choice == "Autre (Saisie Manuelle)":
        model_version = st.text_input("Entrez le nom technique (ex: gemini-experimental)", "gemini-1.5-flash")
    else:
        model_version = model_choice
    
    st.info(f"Modèle actif : **{model_version}**")

# --- 4. SCRAPING (CLOUDSCRAPER - ANTI BLOCK) ---
def get_besoccer_data(url):
    url = url.replace("www.besoccer.com", "fr.besoccer.com")
    url = url.replace("/preview", "/avant-match")
    url = url.replace("/analysis", "/analyse")
    
    try:
        # Configuration Scraper Navigateur
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer", "iframe", "svg", "header", "aside"]):
                tag.extract()
            text = ' '.join(soup.get_text(separator=' ').split())
            title = soup.find('title').text if soup.find('title') else "Match sans titre"
            if len(text) < 500: return None
            return {"title": title, "content": text[:40000]} # On prend large pour la version Pro
        else:
            return None
    except:
        return None

def build_ultimate_prompt(match_data):
    return f"""
    Tu es "BettingGenius". Analyse ce match : {match_data['title']}
    Données : "{match_data['content']}"

    --- 1. ANALYSE TECHNIQUE & MENTALE ---
    (Si info manquante, dis '❌ Non dispo')
    1. **🏆 Prédiction** : Forme + Dynamique Mentale.
    2. **🚩 Corners** : Stats & tactique.
    3. **🔢 Score exact**.
    4. **⚽ Total Buts**.
    5. **⏱️ Périodes**.
    6. **🏥 Absences**.
    7. **🏟️ Conditions**.
    8. **⚠️ Facteurs X** (Arbitrage/Pression).
    9. **🎲 Monte Carlo**.

    --- 2. COUPON JSON STRICT ---
    Catégories: "SAFE" (Sûr), "PSYCHO" (Enjeu fort), "FUN" (Risqué).
    
    ```json
    {{
        "match": "{match_data['title']}",
        "pari_principal": "Ex: Victoire X",
        "score_exact": "Ex: 2-1",
        "corners": "Ex: +8.5",
        "total_buts": "Ex: +2.5",
        "confiance": 85,
        "categorie": "SAFE", 
        "facteur_psycho": "Ex: TITRE / MAINTIEN / DERBY",
        "analyse_courte": "Résumé court."
    }}
    ```
    """

# --- 5. INTERFACE ---

st.title("🧠 BettingGenius Ultimate")
st.markdown("Le bot s'adaptera automatiquement à la version de Gemini choisie.")
urls_input = st.text_area("🔗 Liens des matchs", height=150)

if "results" not in st.session_state: st.session_state.results = []

if st.button("LANCER L'ANALYSE 🚀"):
    if not api_key or not urls_input:
        st.warning("⛔ Clé API ou liens manquants.")
    else:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        st.session_state.results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        genai.configure(api_key=api_key)
        
        # VERIFICATION DU MODELE AVANT DE COMMENCER
        try:
            model = genai.GenerativeModel(model_version)
            # Petit test silencieux pour voir si le modèle existe pour la clé
            # (On ne fait pas de requête, juste l'init)
        except Exception as e:
            st.error(f"❌ Le modèle '{model_version}' n'est pas reconnu. Essayez 'gemini-1.5-flash' ou vérifiez le nom.")
            st.stop()
        
        for i, url in enumerate(urls):
            status_text.markdown(f"**⏳ Match {i+1}/{len(urls)} : Analyse en cours...**")
            
            # Pause Anti-Ban BeSoccer
            time.sleep(2) 
            
            data = get_besoccer_data(url)
            
            if data:
                # Retry Logic Anti-Quota
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        response = model.generate_content(build_ultimate_prompt(data))
                        full_text = response.text
                        
                        json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                        json_data = {}
                        if json_match:
                            clean_json = re.sub(r'//.*', '', json_match.group(0))
                            try: json_data = json.loads(clean_json)
                            except: json_data = {"match": data['title'], "pari_principal": "Erreur", "categorie": "FUN"}
                            if "match" not in json_data: json_data["match"] = data["title"]
                        
                        clean_analysis = re.sub(r'```json.*```', '', full_text, flags=re.DOTALL)
                        
                        st.session_state.results.append({
                            "json": json_data,
                            "analysis_text": clean_analysis,
                            "title": data['title']
                        })
                        break 
                        
                    except Exception as e:
                        err_msg = str(e)
                        if "429" in err_msg: # Quota
                            wait_time = 20
                            status_text.warning(f"⚠️ Quota atteint ({model_version}). Pause de {wait_time}s...")
                            time.sleep(wait_time)
                        elif "404" in err_msg or "not found" in err_msg.lower(): # Modèle introuvable
                            st.error(f"❌ Le modèle '{model_version}' n'existe pas ou n'est pas activé sur votre compte. Sélectionnez 'gemini-1.5-flash' pour que ça marche à coup sûr.")
                            break
                        else:
                            st.error(f"Erreur IA : {e}")
                            break
                
                time.sleep(2) 
                
            else:
                st.error(f"Lien illisible (Protection active) : {url}")
            
            progress_bar.progress((i + 1) / len(urls))
        
        status_text.empty()
        st.success("✅ Analyse terminée !")

# --- 6. RÉSULTATS ---
if st.session_state.results:
    safes = [r for r in st.session_state.results if r['json'].get('categorie') == 'SAFE']
    psychos = [r for r in st.session_state.results if r['json'].get('categorie') == 'PSYCHO']
    funs = [r for r in st.session_state.results if r['json'].get('categorie') == 'FUN']

    st.markdown("---")
    tab_safe, tab_psycho, tab_fun = st.tabs(["🛡️ BLINDÉ", "🧠 TACTIQUE", "💣 FUN"])

    with tab_safe:
        if safes:
            for item in safes:
                j = item['json']
                st.markdown(f"""<div class="coupon-card border-safe"><div class="match-title">{j.get('match')}</div><div><span class="badge badge-conf">{j.get('confiance')}%</span></div><div class="prediction-main">🏆 {j.get('pari_principal')}</div><div class="analysis-short">"{j.get('analyse_courte')}"</div></div>""", unsafe_allow_html=True)
        else: st.info("Aucun match Sûr.")

    with tab_psycho:
        if psychos:
            for item in psychos:
                j = item['json']
                st.markdown(f"""<div class="coupon-card border-psycho"><div class="match-title">{j.get('match')}</div><div><span class="badge badge-psy">🧠 {j.get('facteur_psycho')}</span></div><div class="prediction-main">👉 {j.get('pari_principal')}</div><div class="analysis-short">"{j.get('analyse_courte')}"</div></div>""", unsafe_allow_html=True)
        else: st.info("Aucun match Psycho.")

    with tab_fun:
        if funs:
            for item in funs:
                j = item['json']
                st.markdown(f"""<div class="coupon-card border-fun"><div class="match-title">{j.get('match')}</div><div class="prediction-main">🎲 {j.get('pari_principal')}</div></div>""", unsafe_allow_html=True)
        else: st.write("Rien ici.")

    st.markdown("---")
    for item in st.session_state.results:
        with st.expander(f"🔎 {item['title']}", expanded=False):
            st.markdown(f"""<div class="full-analysis-box">{item['analysis_text']}</div>""", unsafe_allow_html=True)