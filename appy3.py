# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import re
import os
import requests  # <-- Libreria per Telegram aggiunta

app = Flask(__name__)

# ---------------- CONFIGURAZIONE TELEGRAM (SICURA) ----------------
# Il token viene letto dalle impostazioni segrete del server (Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "635753889"  # L'ID della chat non è un segreto, può stare qui

def invia_backup_telegram(testo_conto):
    # Se stiamo testando il programma e non abbiamo messo il token, non va in crash
    if not TELEGRAM_TOKEN:
        print("Nessun token Telegram trovato. Salto l'invio del messaggio.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": testo_conto}, timeout=5)
    except Exception as e:
        print(f"Errore durante l'invio a Telegram: {e}")
# ------------------------------------------------------------------

# ---------------- MENU COMPLETO ----------------
MENU = {
    "Aperitivo & Snack": ["Tagliere Aperitivo (10.00€)", "Frittura Mista di Pesce (15.00€)", "Bustina di Patatine (2.00€)", "Nuggets di Pollo (6.00€)", "Frittura di Verdura (6.00€)", "Patatine Fritte (5.00€)"],
    
    "Pizze": ["Faccia di vecchia (6.00€)", "4 gusti (7.00€)", "Sfincionello (6.00€)", "Parmigiana (8.00€)", "Margherita (6.00€)", "Rustica (8.00€)"],
    
    "Cocktails (10.00€)": ["Mojito","Mojito Cubano","Rossini","Negroni Sbagliato","Americano","Boulevardier","Old Fashioned","Gin Tonic","Gin Lemon","Negroni","London Mule","Gin Sour","Long Island Ice Tea","Rum Cooler","Pina Colada","Bellini","Negrosky","Vodka Tonic","Vodka Lemon","Vodka Sour","Sex on the beach","Mexican Mule","Paloma","Margarita","Moscow Mule","Cosmopolitan"],
    
    "Spritz (8.00€)": ["Aperol Spritz", "Campari Spritz", "Agave Spritz"],
    "Spritz Premium (10.00€)": ["Hugo Spritz"],
    
    "I Nostri Gin (10.00€)": ["Gin Mare", "Gin del Professore", "Hendrick's", "Monkey 47", "Etna Gin", "Ionico", "Roku", "Malfy Pompelmo", "Amuerte", "Portofino", "Nordes", "J. Rose", "Tanqueray n. ten"],
    "I Nostri Rum (10.00€)": ["Kraken", "Zacapa 23", "Matusalem 23", "Havana 7", "Legendario"],
    "Le Nostre Vodka (10.00€)": ["Belvedere", "GreyGoose", "Beluga"],
    "Le Nostre Tequila (10.00€)": ["Patron Silver", "Patron Anejo", "Espolon Blanco", "Don Julio Silver", "Mezcal"],
    "I Nostri Whiskey (10.00€)": ["Oban 14 (12.00€)", "Jack Daniel's (6.00€)", "Four Roses (6.00€)", "Jack Daniel's Honey (6.00€)", "Jameson (6.00€)"],
    "Liquori & Amari (6.00€)": ["Fireball", "Pastis 51", "Limoncello", "Cointreau", "Sambuca", "Baileys", "Frangelico", "Drambuie", "Italicus", "Jägermeister", "Montenegro", "Amaro del Capo", "Amaro Amara", "Jefferson"],
    
    "Analcolici (8.00€)": ["Virgin Colada", "Virgin Mojito", "Tropicana"],
    "Analcolici Premium (8.00€)": ["Tanqueray 0.0"],
    
    "Birre (5.00€)": ["Corona", "Corona zero", "Birra dello Stretto", "Ceres Bionda", "Tennent's", "Menabrea rossa", "Daura (gluten free)"],
    
    "Vini al Calice": {
        "Kikè (Calice)": 7.00,
        "Kebrilla (Calice)": 7.00,
        "Babbio Frizzante (Calice)": 7.00,
        "Taurus Frizzante (Calice)": 7.00,
        "Victora Rosato (Calice)": 7.00,
        "Etna Bianco DOC Tornatore (Calice)": 8.00,
        "Prosecco (Calice)": 7.00
    },
    
    "Vini in Bottiglia": {
        "Kikè Cantina Fina (Bottiglia)": 30.00,
        "Kebrilla Cantina Fina (Bottiglia)": 30.00,
        "Babbio Gorghi Tondi (Bottiglia)": 30.00,
        "Taurus Cantina Brugnano (Bottiglia)": 30.00,
        "Victora Rosato Brugnano (Bottiglia)": 30.00,
        "Etna Bianco DOC Tornatore (Bottiglia)": 35.00,
        "Bottiglia di Prosecco": 30.00
    },
    
    "Soft Drink": {"Acqua Naturale 0,5 lt": 2.0, "Acqua Frizzante 0,5 lt": 2.0, "Coca Cola": 3.0, "Coca Cola Zero": 3.0, "Fanta": 3.0, "Succo Pera/Pesca/Ace/Ananas": 3.0, "Schweppes Lemon": 3.0, "Acqua Tonica Schweppes": 3.0, "Acqua Tonica Mediterranean fever tree": 4.0, "Acqua Tonica Indian fever tree": 4.0, "Pinkgrapefruit Tonic fever tree": 4.0, "Ginger beer fever tree": 4.0}
}

# Aperitivo e Pizze in Cucina, il resto al Bar
REPARTI_PRODOTTI = {cat: "cucina" if cat in ["Aperitivo & Snack", "Pizze"] else "bar" for cat in MENU.keys()}

CODA_STAMPE = []
ULTIMA_STAMPA_BAR = ""
ULTIMA_STAMPA_CUCINA = ""
ULTIMA_STAMPA_CASSA = ""
STORICO_CONTI = []
INCASSO_CONTANTI_GIORNO = 0.0
INCASSO_CARTA_GIORNO = 0.0

tavoli_stato = {i: {"ordine": [], "info": "", "coperti": 1, "gia_incassato_contanti": 0.0, "gia_incassato_carta": 0.0, "aperto_il": datetime.now().strftime("%H:%M")} for i in range(1, 101)}

def determina_prezzo_base(prodotto):
    match = re.search(r'\((\d+\.\d+)€\)', prodotto)
    if match: return float(match.group(1))
    for categoria, contenuto in MENU.items():
        if isinstance(contenuto, dict) and prodotto in contenuto: return contenuto[prodotto]
        elif isinstance(contenuto, list) and prodotto in contenuto:
            if "12.00€" in prodotto: return 12.0
            if "10.00€" in categoria: return 10.0
            if "8.00€" in categoria: return 8.0
            if "7.00€" in categoria: return 7.0
            if "6.00€" in categoria: return 6.0
            if "5.00€" in categoria: return 5.0
    return 10.0

def totale_tavolo(numero_tavolo):
    return round(sum(voce["prezzo"] for voce in tavoli_stato[numero_tavolo]["ordine"]), 2)

def residuo_tavolo(numero_tavolo):
    return round(totale_tavolo(numero_tavolo) - (tavoli_stato[numero_tavolo]["gia_incassato_contanti"] + tavoli_stato[numero_tavolo]["gia_incassato_carta"]), 2)

@app.route('/')
def home(): return render_template('prova.html', menu=MENU)

@app.route('/get_tavolo/<int:num>', methods=['GET'])
def get_tavolo(num):
    dati = tavoli_stato[num]
    return jsonify({"ordine": dati["ordine"], "info": dati["info"], "coperti": dati["coperti"], "gia_incassato_contanti": dati["gia_incassato_contanti"], "gia_incassato_carta": dati["gia_incassato_carta"], "totale": totale_tavolo(num), "residuo": residuo_tavolo(num)})

@app.route('/add', methods=['POST'])
def add():
    data = request.json
    tavolo_num = int(data["tavolo"])
    prodotto = data["prodotto"]
    quantita = int(data.get("quantita", 1))
    nota = data.get("nota", "")
    calici = int(data.get("calici", 0))

    if calici > 0:
        nota = (nota + f" | {calici} CALICI") if nota else f"{calici} CALICI"

    prezzo_personalizzato = data.get("prezzo_personalizzato")
    if prezzo_personalizzato and str(prezzo_personalizzato).strip() not in ["", "null", "undefined"]:
        prezzo_unitario = float(str(prezzo_personalizzato).replace(",", "."))
    else:
        prezzo_unitario = determina_prezzo_base(prodotto)

    categoria = "bar"
    for cat, contenuto in MENU.items():
        if prodotto in contenuto: categoria = REPARTI_PRODOTTI[cat]

    trovato = False
    for voce in tavoli_stato[tavolo_num]["ordine"]:
        if voce["prodotto"] == prodotto and voce["note"] == nota and voce["stampato"] == False:
            voce["qta"] += quantita
            voce["prezzo"] += prezzo_unitario * quantita
            trovato = True
            break

    if not trovato:
        tavoli_stato[tavolo_num]["ordine"].append({
            "prodotto": prodotto, "qta": quantita, "note": nota, "prezzo_unitario": prezzo_unitario, 
            "prezzo": prezzo_unitario * quantita, "reparto": categoria, "stampato": False
        })
    return jsonify({"success": True})

@app.route('/paga/<int:num>', methods=['POST'])
def paga(num):
    data = request.json
    tipo = data["tipo"]
    importo = float(str(data["importo"]).replace(",", "."))
    global INCASSO_CONTANTI_GIORNO, INCASSO_CARTA_GIORNO

    if tipo == "CONTANTI":
        tavoli_stato[num]["gia_incassato_contanti"] += importo
        INCASSO_CONTANTI_GIORNO += importo
    elif tipo == "CARTA":
        tavoli_stato[num]["gia_incassato_carta"] += importo
        INCASSO_CARTA_GIORNO += importo
    return jsonify({"success": True})

@app.route('/coperti/<int:num>', methods=['POST'])
def aggiorna_coperti(num):
    tavoli_stato[num]["coperti"] = int(request.json.get("coperti", 1))
    return jsonify({"success": True})

@app.route('/elimina_voce/<int:num>/<int:indice>', methods=['POST'])
def elimina_voce(num, indice):
    ordine = tavoli_stato[num]["ordine"]
    if 0 <= indice < len(ordine): ordine.pop(indice)
    return jsonify({"success": True})

@app.route('/messaggio_stampante', methods=['POST'])
def messaggio_stampante():
    data = request.json
    CODA_STAMPE.append({"reparto": data["reparto"], "corpo": f"\n\n--- NOTA DA SALA ---\n{data['testo']}\n\n\n"})
    return jsonify({"success": True})

@app.route('/stampa/<int:num>', methods=['POST'])
def stampa(num):
    global ULTIMA_STAMPA_BAR, ULTIMA_STAMPA_CUCINA, ULTIMA_STAMPA_CASSA
    dest = request.args.get("dest", "bar")
    ordine = tavoli_stato[num]["ordine"]

    if dest != "cassa":
        nuove_voci = [v for v in ordine if v["reparto"] == dest and not v["stampato"]]
        if not nuove_voci: return jsonify({"status": "Nessun nuovo ordine da stampare"})
        testo = f"TAVOLO {num}\n---------------------\n"
        for v in nuove_voci:
            testo += f"{v['qta']}x {v['prodotto']}\n"
            if v["note"]: testo += f" NOTE: {v['note']}\n"
            v["stampato"] = True
        testo += "\n\n\n"
        CODA_STAMPE.append({"reparto": dest, "corpo": testo})
        if dest == "bar": ULTIMA_STAMPA_BAR = testo
        else: ULTIMA_STAMPA_CUCINA = testo
        return jsonify({"status": f"Comanda inviata a {dest.upper()}"})

    # --- CHIUSURA TAVOLO ---
    totale = totale_tavolo(num)
    contanti = tavoli_stato[num]["gia_incassato_contanti"]
    carta = tavoli_stato[num]["gia_incassato_carta"]
    residuo = residuo_tavolo(num)
    
    testo = f"CONTO TAVOLO {num}\n---------------------\n"
    for v in ordine: testo += f"{v['qta']}x {v['prodotto']} {v['prezzo']:.2f}€\n"
    testo += f"---------------------\nTOTALE CONTO: {totale:.2f}€\nPAGATO CASH : {contanti:.2f}€\nPAGATO POS  : {carta:.2f}€\nRESIDUO     : {residuo:.2f}€\n---------------------\n\n\n"
    
    CODA_STAMPE.append({"reparto": "cassa", "corpo": testo})
    
    # --- INVIO A TELEGRAM AGGIUNTO QUI ---
    invia_backup_telegram(testo)
    
    tavoli_stato[num] = {"ordine": [], "info": "", "coperti": 1, "gia_incassato_contanti": 0, "gia_incassato_carta": 0, "aperto_il": datetime.now().strftime("%H:%M")}
    return jsonify({"status": "Conto finale stampato e tavolo liberato"})

@app.route('/prendi_stampa', methods=['GET'])
def prendi_stampa():
    if CODA_STAMPE: return jsonify(CODA_STAMPE.pop(0))
    return jsonify({}), 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=True)
