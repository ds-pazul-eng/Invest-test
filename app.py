
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="SPXL Entry Calculator", layout="centered")

st.title("SPXL Entry- und Take-Profit Rechner")
st.markdown("""Gib das lokale Hoch von SPXL sowie deine Portfolio-Parameter ein. Die App berechnet die Kaufstufen, investierte Beträge, kumuliertes Investment, gewichteten Durchschnittspreis und das Take-Profit-Ziel (20%).""")

# Eingaben
local_high = st.number_input("Local High (SPXL)", value=190.34, format="%.4f")
portfolio_total = st.number_input("Gesamtes Portfolio (€)", value=1_000_000.0, format="%.2f")
allocated_pct = st.number_input("Anteil des Portfolios für diese Strategie (%)", value=70.0, min_value=0.0, max_value=100.0, format="%.2f")
allocated_value = portfolio_total * allocated_pct / 100.0

st.write(f"Verfügbarer Betrag für diese Strategie: €{allocated_value:,.2f}")

# Regeln (kann der Nutzer anpassen)
st.subheader("Strategie-Parameter (anpassbar)")
drop_sequence = st.text_input("Rückgänge je Stufe in % (kommagetrennt, relativ zur vorherigen Stufe)", value="-15,-10,-7,-10,-10")
alloc_sequence = st.text_input("Investierte Anteile je Stufe in % des allokierten Betrags (kommagetrennt)", value="20,15,20,20,15")

drops = [float(x.strip()) for x in drop_sequence.split(",") if x.strip()!='']
allocs = [float(x.strip()) for x in alloc_sequence.split(",") if x.strip()!='']

if len(drops) != len(allocs):
    st.error("Die Anzahl der Rückgänge und Investitions-Prozentwerte muss übereinstimmen.")
else:
    # Berechnungen
    levels = []
    prev_price = local_high
    for i, (d, a) in enumerate(zip(drops, allocs), start=1):
        price = prev_price * (1 + d/100.0)
        invest_amount = allocated_value * (a/100.0)
        levels.append({
            "Stufe": f"Buy {i}",
            "Rückgang (%)": d,
            "Preis (SPXL)": round(price,4),
            "Investiert (%)": a,
            "Investitionsbetrag (€)": round(invest_amount,2)
        })
        prev_price = price

    df = pd.DataFrame(levels)
    df["Kumuliertes Investment (€)"] = df["Investitionsbetrag (€)"].cumsum()
    # gewichteter Durchschnittspreis: sum(price * amount)/sum(amount)
    weighted = (df["Preis (SPXL)"] * df["Investitionsbetrag (€)"]).cumsum() / df["Kumuliertes Investment (€)"]
    df["Gewichteter Durchschnittspreis (SPXL)"] = weighted.round(4)
    df["Take-Profit (SPXL)"] = (df["Gewichteter Durchschnittspreis (SPXL)"] * 1.2).round(4)
    df["Kumulierte Investiert (%)"] = (df["Investitionsbetrag (€)"] / allocated_value *100).cumsum().round(2)

    st.subheader("Kaufstufen & Kennzahlen")
    st.dataframe(df.style.format({
        "Preis (SPXL)": "{:.4f}",
        "Investitionsbetrag (€)": "{:,.2f}",
        "Kumuliertes Investment (€)": "{:,.2f}",
        "Gewichteter Durchschnittspreis (SPXL)": "{:.4f}",
        "Take-Profit (SPXL)": "{:.4f}"
    }))

    # Gesamtposition nach allen Käufen
    total_invested = df["Kumuliertes Investment (€)"].iloc[-1]
    avg_price = df["Gewichteter Durchschnittspreis (SPXL)"].iloc[-1]
    total_pct_invested = df["Kumulierte Investiert (%)"].iloc[-1]

    st.markdown(f"**Gesamt investiert:** €{total_invested:,.2f} ({total_pct_invested:.1f}% des Allokations)")
    st.markdown(f"**Gewichteter Durchschnittspreis (Ende):** {avg_price:.4f} SPXL")
    st.markdown(f"**Take-Profit Ziel (20%):** {avg_price*1.2:.4f} SPXL")

    # Trim-Regel (Break-even trim)
    trim_pct = st.number_input("Trimmen bei Break-even: verkaufe x% des Portfolios (%)", value=10.0, min_value=0.0, max_value=100.0, format="%.2f")
    trim_amount_eur = portfolio_total * (trim_pct/100.0)
    st.write(f"Wenn der Preis wieder auf den gewichteten Durchschnitt ({avg_price:.4f}) steigt, würde ein Trim von {trim_pct}% dem Verkauf von ca. €{trim_amount_eur:,.2f} entsprechen.")

    # Visualisierung
    st.subheader("Visualisierung")
    fig, ax = plt.subplots()
    ax.plot(df["Preis (SPXL)"].values, marker='o')
    ax.axhline(avg_price, linestyle='--')
    ax.axhline(avg_price*1.2, linestyle=':')
    ax.set_xlabel("Stufe")
    ax.set_ylabel("Preis (SPXL)")
    ax.set_title("Einstiegs- und Zielpreise")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["Stufe"])
    st.pyplot(fig)

    # Download CSV
    csv = df.to_csv(index=False)
    st.download_button("CSV herunterladen", data=csv, file_name="spxl_entry_points.csv", mime="text/csv")
