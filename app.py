import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro Cashflow & Partner Split", page_icon="🏠", layout="wide")
st.title("🏠 Pro Cashflow: Partner-Split & Kredit-Rechner")
st.markdown("""
Dieses Tool trennt strikt zwischen **Gesamtkosten (Haushalt)** und **Deinem Anteil**.
Zudem bietet es eine professionelle Finanzierungsrechnung für Immobilien (Laufzeit vs. Rate).
""")

# ==========================================
# 1. SZENARIO & PARTNER SPLIT
# ==========================================
with st.sidebar.expander("1. Szenario & Partner Split", expanded=True):
    # Split Logik
    st.subheader("Kostenaufteilung")
    split_pct = st.slider("Mein Kostenanteil (Miete/Essen/Haus) %", 0, 100, 65, help="Wieviel % der gemeinsamen Kosten trägst DU?") / 100.0
    
    st.markdown("---")
    # Markt
    szenario = st.selectbox("Marktphase", ["Neutral (5% / 2%)", "Bullish (8% / 1.5%)", "Bearish (3% / 4%)"])
    if szenario == "Neutral (5% / 2%)":
        rendite = 5.0; inflation = 2.0
    elif szenario.startswith("Bullish"):
        rendite = 8.0; inflation = 1.5
    else:
        rendite = 3.0; inflation = 4.0
        
    rendite_input = st.number_input("Rendite p.a. (%)", value=rendite, step=0.1)/100
    inflation_input = st.number_input("Inflation p.a. (%)", value=inflation, step=0.1)/100
    
    alter_jetzt = st.number_input("Dein Alter", value=31)
    alter_ziel = st.number_input("Ziel Alter", value=67)
    startkapital = st.number_input("Dein Startkapital €", value=50000)

# ==========================================
# 2. EINKOMMEN (NUR DU)
# ==========================================
with st.sidebar.expander("2. Dein Einkommen (Karriere)", expanded=False):
    st.info("Hier kommen nur DEINE Einnahmen rein.")
    # Stufe 1
    brutto_start = st.number_input("Brutto Aktuell €", value=100000)
    var_anteil = st.slider("Variabler Anteil %", 0, 100, 20) / 100
    steigerung = st.number_input("Steigerung p.a. %", value=3.0) / 100
    
    # Beförderung
    has_promo = st.checkbox("Beförderung geplant?")
    promo_alter = 0; promo_brutto = 0
    if has_promo:
        c1, c2 = st.columns(2)
        promo_alter = c1.number_input("Alter Beförderung", value=38)
        promo_brutto = c2.number_input("Neues Brutto €", value=140000)
        
    # Steuer-Funktion (Vereinfacht)
    def net_calc(brutto):
        # Ganz grobe Annäherung Steuerklasse 1
        sozial = min(brutto * 0.2, 16000)
        taxable = brutto - sozial - 1200
        if taxable < 11000: tax = 0
        elif taxable < 62000: tax = (taxable - 11000) * 0.35 # Mittelwert
        else: tax = 15000 + (taxable - 62000) * 0.42
        return brutto - sozial - tax

# ==========================================
# 3. WOHNEN (HAUSHALT TOTAL)
# ==========================================
with st.sidebar.expander("3. Wohnen (Haushalt Total)", expanded=True):
    wohn_modus = st.radio("Modus", ["Miete", "Kauf"])
    
    miete_total = 0; nk_total = 0
    rate_total = 0; haus_wert = 0; restschuld_start = 0; zins = 0; tilgung_calc = 0
    
    # Nebenkosten immer
    nk_total = st.number_input("Nebenkosten Total (Warm/Strom/Internet) €", value=450, help="Gesamte NK für alle Personen")
    
    if wohn_modus == "Miete":
        miete_total = st.number_input("Kaltmiete Total €", value=1600)
        miet_steigerung = st.number_input("Mietsteigerung %", value=2.0)/100
    
    else: # KAUF
        st.write("---")
        st.subheader("Finanzierung (Gesamtobjekt)")
        kauf_alter = st.number_input("Kaufalter", value=35)
        kaufpreis = st.number_input("Kaufpreis (inkl. NK) €", value=600000)
        ek_total = st.number_input("Eigenkapital Total €", value=100000)
        kredit_betrag = kaufpreis - ek_total
        
        st.info(f"Zu finanzieren: {kredit_betrag:,.0f} €")
        
        zins = st.number_input("Sollzins %", value=3.4) / 100
        
        # DER KNACKPUNKT: Rate oder Laufzeit
        calc_method = st.radio("Berechnungsziel", ["Rate vorgeben (Wann fertig?)", "Laufzeit vorgeben (Welche Rate?)"])
        
        if calc_method == "Rate vorgeben (Wann fertig?)":
            rate_wunsch = st.number_input("Wunschrate (Zins+Tilgung) €", value=2300)
            rate_total = rate_wunsch
            # Plausi Check Zins
            min_zins_cost = kredit_betrag * (zins / 12)
            if rate_total <= min_zins_cost:
                st.error(f"Rate zu niedrig! Zinsen sind schon {min_zins_cost:.0f}€. Kredit wächst!")
        else:
            laufzeit_jahre = st.number_input("Laufzeit (Jahre)", value=25)
            # Annuitätenformel
            # R = K * (q^n * (q-1)) / (q^n - 1)  mit q = 1 + zins/12
            q = 1 + (zins / 12)
            n_monate = laufzeit_jahre * 12
            rate_total = kredit_betrag * (q**n_monate * (q-1)) / (q**n_monate - 1)
            st.success(f"Notwendige Rate: {rate_total:,.2f} €")
            
        instandhaltung = st.number_input("Instandhaltung Total €", value=400)
        haus_wert = kaufpreis
        restschuld_start = kredit_betrag

# ==========================================
# 4. LEBEN & AUTO (DETAIL & SPLIT)
# ==========================================
with st.sidebar.expander("4. Ausgaben (Detail & Split)", expanded=False):
    st.caption("Standardwerte sind vorausgefüllt. 'Geteilt' wird mit deinem %-Satz verrechnet.")
    
    # GETEILTE KOSTEN
    st.markdown("**Geteilte Kosten (Haushalt)**")
    c1, c2 = st.columns(2)
    var_supermarkt = c1.number_input("Supermarkt/Drogerie (Total) €", value=600)
    var_essen = c2.number_input("Restaurant/Bestellen (Total) €", value=200)
    var_urlaub = c1.number_input("Urlaub Budget (Jahr Total) €", value=4000)
    var_sonst = c2.number_input("Sonstiges Gemeinsam €", value=200)
    
    summe_geteilt = var_supermarkt + var_essen + (var_urlaub/12) + var_sonst
    
    # PERSÖNLICHE KOSTEN
    st.markdown("---")
    st.markdown("**Nur Deine Kosten (100%)**")
    pers_handy = st.number_input("Dein Handy/Abos €", value=60)
    pers_fun = st.number_input("Dein Spaß/Hobby/Rauchen €", value=300)
    pers_geschenke = st.number_input("Geschenke €", value=100)
    
    # AUTO (KOMPLEX)
    st.markdown("---")
    st.markdown("**Dein Auto**")
    auto_typ = st.selectbox("Auto Finanzierung", ["Leasing", "Kauf (Bar)", "Kein Auto"])
    auto_kosten = 0; auto_kauf_preis = 0; auto_intervall = 0; auto_steuer = 0
    
    if auto_typ == "Leasing":
        auto_kosten = st.number_input("Leasingrate €", value=450)
        auto_steuer = st.number_input("Vers./Steuer (Jahr) €", value=800)
    elif auto_typ == "Kauf (Bar)":
        auto_kauf_preis = st.number_input("Kaufpreis €", value=35000)
        auto_intervall = st.number_input("Neukauf alle X Jahre", value=8)
        auto_kosten = st.number_input("Rücklage Reparatur €", value=150)
        auto_steuer = st.number_input("Vers./Steuer (Jahr) €", value=800)

# ==========================================
# SIMULATION ENGINE
# ==========================================
def simulate():
    months = (alter_ziel - alter_jetzt) * 12
    data = []
    
    wealth = startkapital
    equity_house = 0
    loan_balance = 0
    has_house = False
    
    # Current Values (Total)
    curr_brutto = brutto_start
    curr_miete_total = miete_total
    curr_nk_total = nk_total
    curr_instand = 0 if wohn_modus == "Miete" else instandhaltung
    
    curr_geteilt_monthly = var_supermarkt + var_essen + var_sonst
    curr_urlaub_yr = var_urlaub
    
    curr_pers_fix = pers_handy + pers_fun + pers_geschenke
    
    curr_auto_monthly = auto_kosten
    curr_auto_tax = auto_steuer
    
    # KAUF SIM VARS
    sim_rate = 0
    
    for m in range(months + 1):
        year_idx = m // 12
        month_idx = m % 12
        age = alter_jetzt + year_idx
        
        # --- 1. JÄHRLICHE UPDATES (Januar) ---
        if m > 0 and month_idx == 0:
            inf = (1 + inflation_input)
            # Kosten wachsen
            curr_nk_total *= inf
            curr_instand *= inf
            curr_geteilt_monthly *= inf
            curr_urlaub_yr *= inf
            curr_pers_fix *= inf
            curr_auto_monthly *= inf
            curr_auto_tax *= inf
            
            # Gehalt wächst
            curr_brutto *= (1 + steigerung)
            
            # Miete wächst
            if not has_house and wohn_modus == "Miete":
                curr_miete_total *= (1 + miet_steigerung)
            
            # Auto Kauf (Cash Event)
            if auto_typ == "Kauf (Bar)" and year_idx > 0 and year_idx % auto_intervall == 0:
                price_now = auto_kauf_preis * (inf**year_idx)
                wealth -= price_now

        # --- 2. EVENTS ---
        # Beförderung
        if has_promo and age == promo_alter and month_idx == 0:
            curr_brutto = promo_brutto
            
        # Hauskauf
        if wohn_modus == "Kauf" and age == kauf_alter and month_idx == 0 and not has_house:
            # Wir ziehen nur DEINEN Anteil am Eigenkapital ab? 
            # Annahme: Du zahlst deinen Split-Anteil am EK oder alles?
            # Hier: Wir nehmen Split-Anteil vom EK
            my_ek_invest = ek_total * split_pct
            wealth -= my_ek_invest
            
            loan_balance = kredit_betrag
            sim_rate = rate_total
            has_house = True
            curr_miete_total = 0
            
        # --- 3. INCOME ---
        # Netto Rechner
        netto_total = net_calc(curr_brutto)
        
        # Aufteilung Fix/Var
        income_month = (netto_total * (1 - var_anteil)) / 12
        
        # Bonus im Dezember
        if month_idx == 11:
            income_month += (netto_total * var_anteil)
            
        # --- 4. EXPENSES (THE SPLIT) ---
        
        # A. Wohnen
        cost_housing_total = curr_miete_total + curr_nk_total
        if has_house:
            cost_housing_total = sim_rate + curr_nk_total + curr_instand
            # Kredit Tilgung im Hintergrund (Gesamtbetrachtung Bank)
            interest = loan_balance * (zins / 12)
            principal = sim_rate - interest
            loan_balance -= principal
            if loan_balance < 0: loan_balance = 0
            
        # DEIN ANTEIL WOHNEN
        my_housing_cost = cost_housing_total * split_pct
        
        # B. Leben Geteilt
        # Urlaub monatlich glätten oder im Sommer? 
        # User wollte Glättung im Standard, aber wir buchen es hier im Monat
        cost_shared_items = curr_geteilt_monthly
        if month_idx == 6: # Sommerurlaub
            cost_shared_items += curr_urlaub_yr
            
        # DEIN ANTEIL LEBEN
        my_living_shared = cost_shared_items * split_pct
        
        # C. Persönlich (100% Du)
        my_personal = curr_pers_fix + curr_auto_monthly
        if month_idx == 0:
            my_personal += curr_auto_tax
            
        # TOTAL OUT
        total_out = my_housing_cost + my_living_shared + my_personal
        
        # --- 5. CASHFLOW ---
        cashflow = income_month - total_out
        
        # Zinsen Depot
        wealth *= (1 + rendite_input)**(1/12)
        wealth += cashflow
        
        # Hauswert (für Networth)
        house_value_curr = 0
        if has_house:
            # Haus wächst mit Inflation
            house_value_curr = haus_wert * ((1 + inflation_input)**(m/12))
        
        # Dein Net Worth Anteil am Haus
        # (Hauswert - Schulden) * Split_Pct
        equity_net = max(0, house_value_curr - loan_balance) * split_pct
        
        data.append({
            "Alter": age,
            "Jahr": 2026 + year_idx,
            "Monat": month_idx + 1,
            "Netto_Income": round(income_month),
            "Ausgabe_Wohnen_Anteil": round(my_housing_cost),
            "Ausgabe_Leben_Anteil": round(my_living_shared),
            "Ausgabe_Privat": round(my_personal),
            "Total_Ausgaben": round(total_out),
            "Sparbetrag": round(cashflow),
            "Depot_Wert": round(wealth),
            "Immo_Equity_Mein": round(equity_net),
            "Gesamt_Networth": round(wealth + equity_net),
            "Restschuld_Gesamt": round(loan_balance)
        })
        
    return pd.DataFrame(data)

df = simulate()

# ==========================================
# DASHBOARD
# ==========================================

# KPI
final_nw = df.iloc[-1]["Gesamt_Networth"]
final_depot = df.iloc[-1]["Depot_Wert"]
final_debt = df.iloc[-1]["Restschuld_Gesamt"]

c1, c2, c3 = st.columns(3)
c1.metric("Dein Endvermögen (Split bereinigt)", f"{final_nw:,.0f} €")
c2.metric("Dein Depotstand", f"{final_depot:,.0f} €")
if final_debt > 0:
    c3.metric("Restschuld Haus (Gesamt)", f"{final_debt:,.0f} €", "Noch nicht abbezahlt!", delta_color="inverse")
else:
    c3.metric("Haus", "Abbezahlt ✅")

# TABS
tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Daten", "ℹ️ Berechnung"])

with tab1:
    st.subheader("Vermögensentwicklung (Nur Dein Anteil)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Alter"], y=df["Depot_Wert"], name="Dein Depot", stackgroup='one'))
    fig.add_trace(go.Scatter(x=df["Alter"], y=df["Immo_Equity_Mein"], name="Dein Haus-Equity", stackgroup='one'))
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("Einnahmen vs. Ausgaben (Dein Cashflow)")
    # Aggregation auf Jahre
    df_yr = df.groupby("Alter").sum(numeric_only=True).reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df_yr["Alter"], y=df_yr["Netto_Income"], name="Dein Netto", marker_color="#2ecc71"))
    fig2.add_trace(go.Bar(x=df_yr["Alter"], y=df_yr["Total_Ausgaben"], name="Deine Ausgaben", marker_color="#e74c3c"))
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.dataframe(df)
    st.download_button("CSV Export", df.to_csv().encode("utf-8"), "pro_cashflow.csv")

with tab3:
    st.markdown("""
    ### So rechnet das Tool
    
    1.  **Split-Logik**:
        * Alle Kosten unter "Wohnen" und "Geteilte Kosten" werden addiert.
        * Dann wird mit deinem Faktor **{:.0f}%** multipliziert.
        * Beispiel: Miete 2.000€ * 0.65 = Du zahlst 1.300€.
    
    2.  **Immobilien-Kredit (Annuität)**:
        * Wir nutzen die bankübliche Formel.
        * *Laufzeit-Modus:* Berechnet die Rate, damit die Restschuld nach X Jahren exakt 0 ist.
        * *Raten-Modus:* Prüft monatlich, wie viel getilgt wird. Wenn Rate < Zinsen, wachsen die Schulden (Warnung!).
        
    3.  **Auto**:
        * Kauf-Option zieht alle X Jahre einen großen Batzen Cash vom Depot ab (simuliert Neuanschaffung + Inflation).
    """.format(split_pct*100))

