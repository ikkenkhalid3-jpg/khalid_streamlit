from pathlib import Path
import io
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Santé — Rendez-vous",
    page_icon="🏥",
    layout="wide",
)

DEFAULT_FILE = Path(__file__).with_name("06_Sante.xlsm")

st.title("🏥 Tableau de bord — Rendez-vous de santé")
st.caption("Analyse des rendez-vous de janvier à août 2026 • Données fictives")

with st.sidebar:
    st.header("Paramètres")
    uploaded_file = st.file_uploader(
        "Importer le fichier Excel (.xlsm ou .xlsx)",
        type=["xlsm", "xlsx"],
        help="Vous pouvez aussi placer 06_Sante.xlsm dans le même dossier que ce fichier Python.",
    )

@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes | None, file_path: str | None) -> pd.DataFrame:
    """Load and prepare the appointment dataset."""
    if file_bytes is not None:
        source = io.BytesIO(file_bytes)
    elif file_path and Path(file_path).exists():
        source = file_path
    else:
        raise FileNotFoundError(
            "Fichier Excel introuvable. Importez 06_Sante.xlsm dans la barre latérale "
            "ou placez-le dans le même dossier que output.py."
        )

    # In the provided workbook, the third row contains the headers.
    data = pd.read_excel(source, sheet_name="Données", header=2, engine="openpyxl")
    data = data.dropna(how="all").copy()
    data.columns = [str(column).strip() for column in data.columns]

    required = [
        "ID rendez-vous", "Date rendez-vous", "Ville", "Service",
        "Canal réservation", "Type visite", "Délai RDV (jours)", "Statut",
        "Attente sur place (min)", "Consultation (min)", "Satisfaction /5",
    ]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(
            "Certaines colonnes attendues sont absentes : "
            + ", ".join(missing)
            + ". Vérifiez que la feuille « Données » et la ligne d'en-tête sont correctes."
        )

    data["Date rendez-vous"] = pd.to_datetime(data["Date rendez-vous"], errors="coerce")
    for column in [
        "Délai RDV (jours)", "Attente sur place (min)",
        "Consultation (min)", "Satisfaction /5",
    ]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    for column in ["Statut", "Service", "Ville", "Canal réservation", "Type visite"]:
        data[column] = data[column].astype("string").str.strip()

    data["Mois"] = data["Date rendez-vous"].dt.to_period("M")
    return data


try:
    if uploaded_file is not None:
        df = load_data(uploaded_file.getvalue(), None)
        st.sidebar.success("Fichier importé.")
    elif DEFAULT_FILE.exists():
        df = load_data(None, str(DEFAULT_FILE))
        st.sidebar.info(f"Source locale : {DEFAULT_FILE.name}")
    else:
        st.info(
            "Pour commencer, importez le fichier **06_Sante.xlsm** dans la barre latérale. "
            "Vous pouvez également le placer à côté de `output.py`."
        )
        st.stop()
except Exception as exc:
    st.error(f"Impossible de charger les données : {exc}")
    st.stop()

if df.empty:
    st.warning("Le fichier ne contient aucune ligne exploitable.")
    st.stop()

# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.subheader("Filtres")
    services = sorted(df["Service"].dropna().astype(str).unique().tolist())
    cities = sorted(df["Ville"].dropna().astype(str).unique().tolist())
    statuses = sorted(df["Statut"].dropna().astype(str).unique().tolist())
    channels = sorted(df["Canal réservation"].dropna().astype(str).unique().tolist())

    selected_services = st.multiselect("Service", services, default=services)
    selected_cities = st.multiselect("Ville", cities, default=cities)
    selected_statuses = st.multiselect("Statut", statuses, default=statuses)
    selected_channels = st.multiselect("Canal de réservation", channels, default=channels)

    min_date = df["Date rendez-vous"].min()
    max_date = df["Date rendez-vous"].max()
    if pd.notna(min_date) and pd.notna(max_date):
        date_range = st.date_input(
            "Période",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
        )
    else:
        date_range = None

filtered = df.copy()
filtered = filtered[
    filtered["Service"].astype(str).isin(selected_services)
    & filtered["Ville"].astype(str).isin(selected_cities)
    & filtered["Statut"].astype(str).isin(selected_statuses)
    & filtered["Canal réservation"].astype(str).isin(selected_channels)
]
if date_range and isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[
        filtered["Date rendez-vous"].between(start_date, end_date, inclusive="both")
    ]

if filtered.empty:
    st.warning("Aucun rendez-vous ne correspond aux filtres sélectionnés.")
    st.stop()

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def pct(numerator: float, denominator: float) -> float:
    return (numerator / denominator * 100) if denominator else 0.0

def show_bar_chart(series: pd.Series, title: str, xlabel: str, ylabel: str = "") -> None:
    if series.empty:
        st.info("Pas assez de données pour afficher ce graphique.")
        return
    fig, ax = plt.subplots(figsize=(8, 4.4))
    series.sort_values().plot(kind="barh", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)

# ---------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------
st.subheader("Vue d'ensemble")
total = len(filtered)
status_counts = filtered["Statut"].value_counts()
honored = int(status_counts.get("Honoré", 0))
absent = int(status_counts.get("Absent", 0))
cancelled = int(status_counts.get("Annulé", 0))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Rendez-vous prévus", f"{total:,}".replace(",", " "))
k2.metric("Taux honorés", f"{pct(honored, total):.1f} %", f"{honored} rendez-vous")
k3.metric("Taux d'absence", f"{pct(absent, total):.1f} %", f"{absent} rendez-vous")
k4.metric("Taux d'annulation", f"{pct(cancelled, total):.1f} %", f"{cancelled} rendez-vous")

honored_df = filtered.loc[filtered["Statut"].eq("Honoré")]
wait_mean = honored_df["Attente sur place (min)"].mean()
consult_mean = honored_df["Consultation (min)"].mean()
satisfaction_mean = honored_df["Satisfaction /5"].mean()
delay_mean = filtered["Délai RDV (jours)"].mean()

k5, k6, k7, k8 = st.columns(4)
k5.metric("Délai moyen", f"{delay_mean:.1f} jours" if pd.notna(delay_mean) else "N/D")
k6.metric("Attente moyenne", f"{wait_mean:.1f} min" if pd.notna(wait_mean) else "N/D")
k7.metric("Consultation moyenne", f"{consult_mean:.1f} min" if pd.notna(consult_mean) else "N/D")
k8.metric("Satisfaction moyenne", f"{satisfaction_mean:.2f} / 5" if pd.notna(satisfaction_mean) else "N/D")

st.caption(
    "Les taux de statut utilisent les rendez-vous filtrés comme dénominateur. "
    "L'attente, la durée de consultation et la satisfaction sont calculées uniquement "
    "sur les visites honorées et les valeurs renseignées."
)

# ---------------------------------------------------------------------
# Question 1: volume by service
# ---------------------------------------------------------------------
st.divider()
st.header("1. Quel service reçoit le plus de rendez-vous ?")
volume_service = filtered.groupby("Service").size().sort_values(ascending=False)
left, right = st.columns([1.15, 1])
with left:
    show_bar_chart(volume_service, "Rendez-vous planifiés par service", "Nombre de rendez-vous", "Service")
with right:
    display_volume = volume_service.rename("Rendez-vous").to_frame()
    st.dataframe(display_volume, use_container_width=True)
    if not volume_service.empty:
        st.success(
            f"Service le plus sollicité : **{volume_service.index[0]}** "
            f"({int(volume_service.iloc[0])} rendez-vous, "
            f"{pct(volume_service.iloc[0], total):.1f} % du total filtré)."
        )

# ---------------------------------------------------------------------
# Question 2: statuses by service
# ---------------------------------------------------------------------
st.divider()
st.header("2. Quels sont les taux honorés, absents et annulés par service ?")
status_table = pd.crosstab(filtered["Service"], filtered["Statut"])
status_table = status_table.reindex(columns=["Honoré", "Absent", "Annulé"], fill_value=0)
status_rates = status_table.div(status_table.sum(axis=1).replace(0, pd.NA), axis=0).fillna(0) * 100
left, right = st.columns([1.2, 1])
with left:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    status_rates.plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("Répartition des statuts par service")
    ax.set_xlabel("Service")
    ax.set_ylabel("Part des rendez-vous (%)")
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=25)
    ax.legend(title="Statut", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)
with right:
    st.dataframe(status_table, use_container_width=True)
    st.markdown("**Taux par service (%)**")
    st.dataframe(status_rates.round(1), use_container_width=True)
    absence_rates = status_rates["Absent"].sort_values(ascending=False)
    if not absence_rates.empty:
        st.info(
            f"Taux d'absence le plus élevé : **{absence_rates.index[0]}** "
            f"({absence_rates.iloc[0]:.1f} %)."
        )

# ---------------------------------------------------------------------
# Question 3: booking lead time
# ---------------------------------------------------------------------
st.divider()
st.header("3. Quels services ont les délais de rendez-vous les plus longs ?")
lead_time = (
    filtered.groupby("Service")["Délai RDV (jours)"]
    .agg(N="count", Moyenne="mean", Médiane="median")
    .sort_values("Moyenne", ascending=False)
)
left, right = st.columns([1.15, 1])
with left:
    show_bar_chart(lead_time["Moyenne"].dropna(), "Délai moyen par service", "Jours", "Service")
with right:
    st.dataframe(lead_time.round(1), use_container_width=True)
    if not lead_time["Moyenne"].dropna().empty:
        service_long = lead_time["Moyenne"].dropna().idxmax()
        st.warning(
            f"Délai moyen le plus long : **{service_long}** "
            f"({lead_time.loc[service_long, 'Moyenne']:.1f} jours)."
        )

# ---------------------------------------------------------------------
# Question 4: waiting time by city for honored visits
# ---------------------------------------------------------------------
st.divider()
st.header("4. Comment l'attente varie-t-elle selon la ville ?")
wait_by_city = (
    honored_df.groupby("Ville")["Attente sur place (min)"]
    .agg(N="count", Moyenne="mean", Médiane="median")
    .sort_values("Moyenne", ascending=False)
)
left, right = st.columns([1.15, 1])
with left:
    show_bar_chart(wait_by_city["Moyenne"].dropna(), "Attente moyenne par ville — visites honorées", "Minutes", "Ville")
with right:
    st.dataframe(wait_by_city.round(1), use_container_width=True)
    wait_valid = wait_by_city["Moyenne"].dropna()
    if not wait_valid.empty:
        city_high = wait_valid.idxmax()
        city_low = wait_valid.idxmin()
        st.info(
            f"Attente la plus élevée : **{city_high}** "
            f"({wait_valid.max():.1f} min). "
            f"Attente la plus faible : **{city_low}** "
            f"({wait_valid.min():.1f} min)."
        )

# ---------------------------------------------------------------------
# Question 5: monthly activity and absences
# ---------------------------------------------------------------------
st.divider()
st.header("5. Comment évoluent le volume et les absences par mois ?")
monthly_source = filtered.dropna(subset=["Date rendez-vous"]).copy()
monthly_source["Mois"] = monthly_source["Date rendez-vous"].dt.to_period("M").dt.to_timestamp()
monthly = monthly_source.groupby("Mois").agg(
    Rendez_vous=("ID rendez-vous", "size"),
    Absents=("Statut", lambda values: values.eq("Absent").sum()),
    Annules=("Statut", lambda values: values.eq("Annulé").sum()),
    Honores=("Statut", lambda values: values.eq("Honoré").sum()),
)
monthly["Taux absence (%)"] = monthly["Absents"].div(monthly["Rendez_vous"]).mul(100)
left, right = st.columns(2)
with left:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(monthly.index, monthly["Rendez_vous"], marker="o", label="Rendez-vous planifiés")
    ax.plot(monthly.index, monthly["Absents"], marker="s", linestyle="--", label="Absents")
    ax.set_title("Volume et absences par mois")
    ax.set_xlabel("Mois")
    ax.set_ylabel("Nombre")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)
with right:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(monthly.index, monthly["Taux absence (%)"], marker="o")
    ax.set_title("Taux d'absence par mois")
    ax.set_xlabel("Mois")
    ax.set_ylabel("Absents / rendez-vous planifiés (%)")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)
st.dataframe(monthly.round(1), use_container_width=True)
if not monthly.empty:
    peak = monthly["Rendez_vous"].idxmax()
    absence_peak = monthly["Absents"].idxmax()
    st.caption(
        f"Plus grand volume : {peak:%B %Y} ({int(monthly.loc[peak, 'Rendez_vous'])} rendez-vous). "
        f"Plus grand nombre d'absences : {absence_peak:%B %Y} "
        f"({int(monthly.loc[absence_peak, 'Absents'])}). "
        "Comparer également le taux d'absence, car le volume mensuel varie."
    )

# ---------------------------------------------------------------------
# Question 6: recommendation
# ---------------------------------------------------------------------
st.divider()
st.header("6. Quelles améliorations proposer ?")
st.markdown(
    "Les suggestions ci-dessous sont des pistes à tester. Les données décrivent des tendances "
    "et ne prouvent pas, à elles seules, les causes des absences ou des temps d'attente."
)

recommendations = []
absence_rates = status_rates["Absent"].dropna()
if not absence_rates.empty:
    recommendations.append(
        f"**Réduire les absences :** tester des rappels SMS/WhatsApp et simplifier le report ou "
        f"l'annulation. Priorité d'investigation : {absence_rates.idxmax()} "
        f"(taux d'absence observé {absence_rates.max():.1f} %)."
    )
lead_valid = lead_time["Moyenne"].dropna()
if not lead_valid.empty:
    recommendations.append(
        f"**Réduire les délais :** examiner les créneaux et la capacité de {lead_valid.idxmax()}, "
        f"où le délai moyen est de {lead_valid.max():.1f} jours."
    )
wait_valid = wait_by_city["Moyenne"].dropna()
if not wait_valid.empty:
    recommendations.append(
        f"**Améliorer l'attente :** analyser les horaires, effectifs et flux de patients à "
        f"{wait_valid.idxmax()}, où l'attente moyenne est de {wait_valid.max():.1f} minutes."
    )
recommendations.append(
    "**Mesurer l'impact :** suivre mensuellement le taux d'absence, le délai moyen, l'attente "
    "et la satisfaction après chaque changement."
)
for item in recommendations:
    st.markdown(f"- {item}")

# ---------------------------------------------------------------------
# Data preview and download
# ---------------------------------------------------------------------
with st.expander("Voir les données filtrées"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Télécharger les données filtrées (CSV)",
        data=csv_bytes,
        file_name="rendez_vous_filtres.csv",
        mime="text/csv",
    )

with st.expander("Méthodologie et limites"):
    st.markdown(
        "- Les taux de statut utilisent tous les rendez-vous filtrés comme dénominateur.\n"
        "- Les analyses d'attente, de durée de consultation et de satisfaction ne portent que "
        "sur les visites honorées et les valeurs disponibles.\n"
        "- Les valeurs manquantes ne sont pas converties en zéros.\n"
        "- Les résultats sont descriptifs ; les différences entre villes/services ne démontrent "
        "pas de causalité.\n"
        "- Les données du classeur sont décrites comme fictives."
    )
