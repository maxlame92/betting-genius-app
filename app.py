import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
import json
import re
import os
import time
from datetime import date

# ==========================================
# 1. CONFIGURATION INITIALE
# ==========================================
st.set_page_config(
    page_title="BettingGenius API - Ultimate",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DESIGN CSS "PREMIUM SAAS"
# ==========================================
st.markdown("""
<style>
    /* FOND ET COULEURS */
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    
    /* TYPOGRAPHIE */
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; }
    h1 { color: #F8FAFC; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; }
    
    /* STYLE DES TICKETS (RÉSULTATS) */
    .coupon-container {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
    }
    
    /* STYLE LISTE DES MATCHS */
    .match-row {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #3B82F6;
        transition: transform 0.2s;
    }
    .match-row:hover { transform: translateX(5px); background-color: #2D3748; }

    /* BORDURES CATÉGORIES */
    .border-safe { border-left: 6px solid #22C55E; }   /* VERT */
    .border-psycho { border-left: 6px solid #A855F7; } /* VIOLET */
    .border-fun { border-left: 6px solid #F59E0B; }    /* ORANGE */

    /* BADGES */
    .badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 800;
        padding: 4px 8px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .badge-psy { background-color: #581C87; color: #D8B4FE; border: 1px solid #A855F7; }
    
    /* JAUGE CONFIANCE */
    .progress-track { background: #334155; height: 6px; border-radius: 3px; margin-top: 5px; width: 100%; }
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

    /* BOUTON ANALYSE */
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white; border: none; font-weight: bold; border-radius: 8px;
        width: 100%;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); }
    
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
# 3. SIDEBAR (CLÉS API)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2586/2586885.png", width=70)
    st.title("BettingGenius")
    st.markdown("**Version API (Automatique)**")
    st.markdown("---")
    
    # 1. Clé Gemini
    gemini_key = os.environ.get("GOOGLE_API_KEY")
    if not gemini_key:
        gemini_key = st.text_input("🔑 Clé Gemini AI", type="password")
    
    st.markdown("---")
    
    # 2. Clé RapidAPI
    rapid_key = st.text_input("🔑 Clé API-Football (RapidAPI)", type="password", help="Gratuit sur rapidapi.com (100 req/jour)")
    
    st.markdown("---")
    
    # 3. Modèle IA
    model_version = st.selectbox("Modèle IA :", ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"])
    
    st.info("✅ Connexion API Directe\n✅ PsychoEngine™ Actif\n✅ Design Ticket Actif")

# ==========================================
# 4. FONCTIONS API (MOTEUR DE DONNÉES)
# ==========================================

def get_headers(api_key):
    return {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

def get_fixtures(api_key, league_id, date_str):
    """Récupère la liste des matchs"""
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    # Saison 2024 (Changez en 2025 si besoin selon la période)
    querystring = {"league": str(league_id), "season": "2024", "date": str(date_str)}
    
    try:
        response = requests.get(url, headers=get_headers(api_key), params=querystring)
        return response.json().get('response', [])
    except:
        return []

def get_match_predictions(api_key, fixture_id):
    """
    Récupère les PREDICTIONS calculées par l'API Football.
    C'est une mine d'or pour l'IA (Forme, H2H, Probas, Comparaison).
    """
    url = "https://api-football-v1.p.rapidapi.com/v3/predictions"
    querystring = {"fixture": str(fixture_id)}
    
    try:
        response = requests.get(url, headers=get_headers(api_key), params=querystring)
        data = response.json().get('response', [])
        if data:
            return json.dumps(data[0], indent=2) # On retourne tout le JSON brut
        return None
    except:
        return None

def build_api_prompt(match_title, json_data):
    """
    Le Prompt Ultimate adapté pour lire le JSON de l'API au lieu du texte.
    """
    return f"""
    Tu es "BettingGenius". Analyse ce match : {match_title}
    
    DONNÉES TECHNIQUES (JSON API) :
    {json_data}
    
    --- MISSION 1 : ANALYSE (9 POINTS & PSYCHO) ---
    Utilise les données fournies (Forme, H2H, Attaque/Défense, Comparaison) pour rédiger l'analyse.
    1. **🏆 Prédiction** (Logique vs Surprise).
    2. **🧠 Facteur Psycho** (Enjeu, Série de victoires/défaites, Domicile/Extérieur).
    3. **🚩 Corners & Buts** (Stats off/def).
    4. **🔢 Score Exact**.
    5. **⚠️ Facteurs Risques**.
    
    --- MISSION 2 : TICKET JSON ---
    Génère le JSON final pour l'affichage.
    Catégories: "SAFE" (>75% proba API), "PSYCHO" (Enjeu fort), "FUN".

    ```json
    {{
        "match": "{match_title}",
        "pari_principal": "Ex: Victoire Manchester",
        "score_exact": "Ex: 2-1",
        "corners": "Ex: +9.5",
        "total_buts": "Ex: +2.5",
        "confiance": 80,
        "categorie": "SAFE",
        "facteur_psycho": "Ex: FORME DOMICILE / CHOC AU SOMMET",
        "analyse_courte": "Résumé court."
    }}
    ```
    """

# ==========================================
# 5. INTERFACE PRINCIPALE
# ==========================================

st.title("⚡ BettingGenius API")
st.markdown("Sélectionnez une ligue et une date. Plus besoin de liens !")

# Initialisation Session State
if 'selected_match_id' not in st.session_state: st.session_state.selected_match_id = None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None

if not rapid_key or not gemini_key:
    st.warning("⚠️ Veuillez entrer vos Clés API dans la barre latérale.")
else:
    # --- FILTRES ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        # ID des Ligues Majeures (API-Football IDs)
        leagues = {
            "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": 39,
            "La Liga 🇪🇸": 140,
            "Bundesliga 🇩🇪": 78,
            "Serie A 🇮🇹": 135,
            "Ligue 1 🇫🇷": 61,
            "Champions League 🇪🇺": 2,
            "Europa League 🇪🇺": 3
        }
        league_choice = st.selectbox("Championnat", list(leagues.keys()))
        league_id = leagues[league_choice]
    
    with col2:
        date_choice = st.date_input("Date", date.today())
        
    with col3:
        st.write("")
        st.write("")
        if st.button("🔍 CHERCHER"):
            with st.spinner("Récupération des matchs..."):
                st.session_state.matches = get_fixtures(rapid_key, league_id, date_choice)
                st.session_state.analysis_result = None # Reset analyse précédente

    # --- LISTE DES MATCHS ---
    if 'matches' in st.session_state and st.session_state.matches:
        st.markdown(f"### {len(st.session_state.matches)} Matchs trouvés")
        
        for m in st.session_state.matches:
            home = m['teams']['home']['name']
            away = m['teams']['away']['name']
            fid = m['fixture']['id']
            status = m['fixture']['status']['short']
            time_match = m['fixture']['date'][11:16]
            
            # Affichage en ligne propre
            col_a, col_b, col_c = st.columns([0.2, 0.6, 0.2])
            with col_a:
                st.markdown(f"**{time_match}**")
            with col_b:
                st.markdown(f"⚽ **{home}** vs **{away}**")
            with col_c:
                # BOUTON D'ANALYSE PAR MATCH
                if st.button("Analyser 🧠", key=fid):
                    st.session_state.selected_match_id = fid
                    
                    with st.spinner(f"Analyse approfondie de {home} vs {away}..."):
                        # 1. Appel API-Football (Détails)
                        stats_json = get_match_predictions(rapid_key, fid)
                        
                        if stats_json:
                            # 2. Appel Gemini
                            genai.configure(api_key=gemini_key)
                            model = genai.GenerativeModel(model_version)
                            
                            try:
                                prompt = build_api_prompt(f"{home} vs {away}", stats_json)
                                response = model.generate_content(prompt)
                                full_text = response.text
                                
                                # Parsing
                                j_data = {}
                                j_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                                if j_match:
                                    clean = re.sub(r'//.*', '', j_match.group(0))
                                    try: j_data = json.loads(clean)
                                    except: j_data = {"match": f"{home}-{away}", "pari_principal": "Erreur", "categorie": "FUN"}
                                
                                clean_text = re.sub(r'```json.*```', '', full_text, flags=re.DOTALL)
                                
                                # Stockage résultat
                                st.session_state.analysis_result = {
                                    "json": j_data,
                                    "text": clean_text
                                }
                            except Exception as e:
                                st.error(f"Erreur IA : {e}")
                        else:
                            st.error("Pas de données détaillées disponibles pour ce match (Trop tôt ou Ligue mineure).")

    # --- AFFICHAGE DU RÉSULTAT (TICKET) ---
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        j = res['json']
        
        st.markdown("---")
        st.subheader("🎟️ RÉSULTAT DE L'ANALYSE")
        
        # Détermination couleur
        cat = j.get('categorie', 'FUN')
        border_cls = "border-safe" if cat == "SAFE" else "border-psycho" if cat == "PSYCHO" else "border-fun"
        
        # HTML TICKET (Stable)
        html = f"""
        <div class="coupon-container {border_cls}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px; border-bottom:1px solid #334155; padding-bottom:10px;">
                <div>
                    <div style="font-size:1.2rem; font-weight:700; color:#fff;">{j.get('match')}</div>
                    <span class="badge badge-psy" style="margin-top:5px;">{j.get('facteur_psycho', 'ANALYSE')}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.7rem; color:#94A3B8;">CONFIANCE</div>
                    <div style="font-weight:bold; color:#fff; font-size:1.1rem;">{j.get('confiance')}%</div>
                    <div class="progress-track">
                        <div class="progress-bar" style="width: {j.get('confiance')}%;"></div>
                    </div>
                </div>
            </div>

            <div class="main-bet-box">
                🏆 {j.get('pari_principal')}
            </div>

            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <div style="flex:1; background:#0F172A; padding:10px; border-radius:8px; text-align:center; border:1px solid #334155;">
                    <div style="font-size:0.7em; color:#94A3B8;">SCORE</div>
                    <div style="font-size:1.1em; font-weight:bold; color:#F8FAFC;">{j.get('score_exact', '-')}</div>
                </div>
                <div style="flex:1; background:#0F172A; padding:10px; border-radius:8px; text-align:center; border:1px solid #334155;">
                    <div style="font-size:0.7em; color:#94A3B8;">BUTS</div>
                    <div style="font-size:1.1em; font-weight:bold; color:#F8FAFC;">{j.get('total_buts', '-')}</div>
                </div>
                <div style="flex:1; background:#0F172A; padding:10px; border-radius:8px; text-align:center; border:1px solid #334155;">
                    <div style="font-size:0.7em; color:#94A3B8;">CORNERS</div>
                    <div style="font-size:1.1em; font-weight:bold; color:#F8FAFC;">{j.get('corners', '-')}</div>
                </div>
            </div>

            <div style="font-style:italic; color:#CBD5E1; font-size:0.95em; border-top:1px solid #334155; padding-top:10px;">
                "{j.get('analyse_courte')}"
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        
        # Détails Texte
        with st.expander("📝 Lire l'analyse complète (9 Points)"):
            st.markdown(f'<div class="full-details">{res["text"]}</div>', unsafe_allow_html=True)