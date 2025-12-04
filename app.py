import streamlit as st
import google.generativeai as genai
import cloudscraper # C'est l'arme secrète contre les blocages
from bs4 import BeautifulSoup
import json
import re
import os
import time

# --- 1. CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="BettingGenius Ultimate - Anti-Bot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE VISUEL PREMIUM (CSS) ---
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

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("BettingGenius")
    st.markdown("**Version Ultimate (Anti-Bot)**")
    st.markdown("---")
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Clé API Google Gemini", type="password")

    model_version = st.selectbox("Modèle :", ["gemini-1.5-flash", "gemini-2.0-flash-exp"])
    
    st.success("✅ Module CloudScraper actif\n✅ Anti-Blocage BeSoccer")

# --- 4. FONCTION DE SCRAPING PUISSANTE (CloudScraper) ---

def get_besoccer_data(url):
    """
    Utilise CloudScraper pour contourner les protections 403/Cloudflare.
    Convertit aussi les liens en Français pour faciliter l'analyse.
    """
    # 1. Conversion automatique en lien Français (plus facile à lire pour le bot)
    url = url.replace("www.besoccer.com", "fr.besoccer.com")
    url = url.replace("/preview", "/avant-match")
    url = url.replace("/analysis", "/analyse")
    
    try:
        # Création d'un scraper qui imite un vrai navigateur (Chrome)
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Tentative de connexion
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Suppression des éléments inutiles
            for tag in soup(["script", "style", "nav", "footer", "iframe", "svg", "header", "aside"]):
                tag.extract()
            
            text = ' '.join(soup.get_text(separator=' ').split())
            title = soup.find('title').text if soup.find('title') else "Match sans titre"
            
            # Vérification si on a vraiment récupéré du contenu
            if len(text) < 500:
                return None
                
            return {"title": title, "content": text[:40000]}
        else:
            # En cas d'échec silencieux
            return None
            
    except Exception as e:
        # En cas d'erreur technique
        return None

def build_ultimate_prompt(match_data):
    """ Prompt Maître avec structure JSON stricte """
    return f"""
    Tu es "BettingGenius", l'IA ultime d'aide aux paris sportifs.
    
    MATCH À ANALYSER : {match_data['title']}
    DONNÉES BRUTES : "{match_data['content']}"

    --- MISSION 1 : L'ANALYSE DÉTAILLÉE (TEXTE) ---
    Si une info manque, écris "❌ Info non disponible". Ne rien inventer.

    1. **🏆 Prédiction de victoire** : Analyse la forme et la DYNAMIQUE MENTALE.
    2. **🚩 Corners** : Stats et stratégies.
    3. **🔢 Score exact**.
    4. **⚽ Total Buts**.
    5. **⏱️ Performance par période**.
    6. **🏥 Absences/Retours** (Si mentionné).
    7. **🏟️ Conditions** (Si mentionné).
    8. **⚠️ Facteurs X** (Arbitre, cartons, enjeux).
    9. **🎲 Simulation Monte Carlo**.

    --- MISSION 2 : CLASSIFICATION ET COUPON (JSON) ---
    Catégories: "SAFE" (Sûr >80%), "PSYCHO" (Enjeu vital/Revanche), "FUN" (Risqué).

    Format JSON attendu (Ne rien mettre après ce bloc) :
    ```json
    {{
        "match": "{match_data['title']}",
        "pari_principal": "Ex: Victoire Marseille",
        "score_exact": "Ex: 2-1",
        "corners": "Ex: +8.5 Corners",
        "total_buts": "Ex: +2.5 Buts",
        "confiance": 85,
        "categorie": "SAFE", 
        "facteur_psycho": "Ex: COURSE AU TITRE / MAINTIEN / NEUTRE",
        "analyse_courte": "Phrase de résumé."
    }}
    ```
    """

# --- 5. INTERFACE PRINCIPALE ---

st.title("🧠 BettingGenius Ultimate")
st.markdown("### L'outil d'analyse qui contourne les blocages.")
st.markdown("Collez vos liens **BeSoccer** (même anglais, ils seront convertis).")

urls_input = st.text_area("🔗 Liens des matchs", height=150, placeholder="https://fr.besoccer.com/match/...")

if "results" not in st.session_state:
    st.session_state.results = []

if st.button("LANCER L'ANALYSE 🚀"):
    if not api_key or not urls_input:
        st.warning("⛔ Clé API ou liens manquants.")
    else:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        st.session_state.results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_version)
        
        for i, url in enumerate(urls):
            status_text.markdown(f"**🕵️‍♂️ Scraping intelligent du match {i+1}...**")
            
            # Pause de 1 seconde pour éviter d'être trop agressif
            time.sleep(1)
            
            data = get_besoccer_data(url)
            
            if data:
                try:
                    response = model.generate_content(build_ultimate_prompt(data))
                    full_text = response.text
                    
                    json_data = {}
                    json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                    if json_match:
                        clean_json = re.sub(r'//.*', '', json_match.group(0))
                        try:
                            json_data = json.loads(clean_json)
                        except:
                            json_data = {"match": data['title'], "pari_principal": "Erreur", "categorie": "FUN"}
                        
                        if "match" not in json_data: json_data["match"] = data["title"]
                    
                    clean_analysis_text = re.sub(r'```json.*```', '', full_text, flags=re.DOTALL)
                    
                    st.session_state.results.append({
                        "json": json_data,
                        "analysis_text": clean_analysis_text,
                        "title": data['title']
                    })
                    
                except Exception as e:
                    st.error(f"Erreur IA sur {i+1}: {e}")
            else:
                st.error(f"⚠️ Impossible de lire le lien : {url} (Site inaccessible ou protégé)")
            
            progress_bar.progress((i + 1) / len(urls))
        
        status_text.empty()
        st.success("✅ Analyse terminée !")

# --- 6. AFFICHAGE RÉSULTATS ---

if st.session_state.results:
    st.markdown("---")
    safes = [r for r in st.session_state.results if r['json'].get('categorie') == 'SAFE']
    psychos = [r for r in st.session_state.results if r['json'].get('categorie') == 'PSYCHO']
    funs = [r for r in st.session_state.results if r['json'].get('categorie') == 'FUN']

    st.subheader("🎟️ VOS COUPONS")
    
    tab_safe, tab_psycho, tab_fun = st.tabs(["🛡️ BLINDÉ", "🧠 TACTIQUE", "💣 FUN"])

    with tab_safe:
        if safes:
            for item in safes:
                j = item['json']
                st.markdown(f"""
                <div class="coupon-card border-safe">
                    <div class="match-title">{j.get('match')}</div>
                    <div><span class="badge badge-conf">{j.get('confiance')}%</span></div>
                    <div class="prediction-main">🏆 {j.get('pari_principal')}</div>
                    <div class="prediction-details">⚽ {j.get('total_buts')} | 🔢 {j.get('score_exact')}</div>
                    <div class="analysis-short">"{j.get('analyse_courte')}"</div>
                </div>""", unsafe_allow_html=True)
        else: st.info("Aucun match 100% sûr.")

    with tab_psycho:
        if psychos:
            for item in psychos:
                j = item['json']
                st.markdown(f"""
                <div class="coupon-card border-psycho">
                    <div class="match-title">{j.get('match')}</div>
                    <div><span class="badge badge-psy">🧠 {j.get('facteur_psycho')}</span></div>
                    <div class="prediction-main">👉 {j.get('pari_principal')}</div>
                    <div class="analysis-short">"{j.get('analyse_courte')}"</div>
                </div>""", unsafe_allow_html=True)
        else: st.info("Pas d'enjeu critique.")

    with tab_fun:
        if funs:
            for item in funs:
                j = item['json']
                st.markdown(f"""
                <div class="coupon-card border-fun">
                    <div class="match-title">{j.get('match')}</div>
                    <div class="prediction-main">🎲 {j.get('pari_principal')}</div>
                </div>""", unsafe_allow_html=True)
        else: st.write("Rien ici.")

    st.markdown("---")
    st.subheader("📝 ANALYSES DÉTAILLÉES")
    for item in st.session_state.results:
        with st.expander(f"🔎 {item['title']}", expanded=False):
            st.markdown(f"""<div class="full-analysis-box">{item['analysis_text']}</div>""", unsafe_allow_html=True)