st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* TITOLO UTENTE PICCOLO */
    .user-title { font-size: 28px !important; font-weight: bold; margin-bottom: 20px; color: #f1f5f9; text-align: left !important; }

    /* REGOLE TAB AGGIUNGI (INTOCCABILI - RIPRISTINATE) */
    /* Forza l'allineamento centrale per tutto il contenuto dei container nella Tab Aggiungi */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
        text-align: center !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .bey-name { 
        font-weight: bold; 
        font-size: 1.4rem; 
        color: #60a5fa; 
        text-transform: uppercase; 
        text-align: center !important; 
        width: 100%; 
        display: block;
    }

    .comp-name-centered { 
        font-size: 1.1rem; 
        color: #cbd5e1; 
        text-align: center !important; 
        width: 100%; 
        display: block; 
        margin-top: 5px;
    }

    hr { margin-top: 8px !important; margin-bottom: 8px !important; opacity: 0.3; }

    /* BOTTONI AGGIUNGI */
    div.stButton > button {
        width: auto !important; min-width: 150px !important;
        height: 30px !important; background-color: #334155 !important; color: white !important;
        border: 1px solid #475569 !important; border-radius: 4px !important;
    }

    /* STILE EXPANDER (DECK & INVENTARIO) */
    .stExpander { border: 1px solid #334155 !important; background-color: #1e293b !important; text-align: left !important; margin-bottom: 5px !important; }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)