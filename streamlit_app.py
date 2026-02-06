def save_cloud():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        inv_list = []
        deck_list = []
        for u, data in st.session_state.users.items():
            # Usiamo "Dati" come nome colonna per coerenza col codice
            inv_list.append({"Utente": u, "Dati": json.dumps(data["inv"])})
            deck_list.append({"Utente": u, "Dati": json.dumps(data["decks"])})
        
        # Riferimento dinamico all'URL dai secrets
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        conn.update(spreadsheet=sheet_url, worksheet="inventario", data=pd.DataFrame(inv_list))
        conn.update(spreadsheet=sheet_url, worksheet="decks", data=pd.DataFrame(deck_list))
    except Exception as e:
        st.sidebar.error(f"Errore tecnico: {e}") # Questo ti dirà l'errore esatto ora

def load_cloud():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Leggiamo i dati
        df_inv = conn.read(spreadsheet=sheet_url, worksheet="inventario", ttl=0)
        df_deck = conn.read(spreadsheet=sheet_url, worksheet="decks", ttl=0)
        
        new_users = {}
        for u in ["Antonio", "Andrea", "Fabio"]:
            # Cerchiamo l'utente e prendiamo il valore della colonna "Dati"
            u_inv = df_inv[df_inv["Utente"] == u]["Dati"].values
            u_deck = df_deck[df_deck["Utente"] == u]["Dati"].values
            
            new_users[u] = {
                "inv": json.loads(u_inv[0]) if len(u_inv) > 0 else {k: {} for k in ["lock_bit", "blade", "main_blade", "assist_blade", "ratchet", "bit", "ratchet_integrated_bit"]},
                "decks": json.loads(u_deck[0]) if len(u_deck) > 0 else [{"name": "DECK 1", "slots": {str(i): {} for i in range(3)}}]
            }
        return new_users
    except Exception as e:
        return None