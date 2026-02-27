import pandas as pd


def calculate_fleet_metrics(
    fleet_load_df: pd.DataFrame,
    ev_results_df: pd.DataFrame,
) -> dict:
    peak_load_kw = float(fleet_load_df["fleet_load_kw"].max())
    total_energy_delivered_kwh = float(ev_results_df["energy_delivered_kwh"].sum())
    total_energy_needed_kwh = float(ev_results_df["energy_needed_kwh"].sum())
    completion_rate = float(ev_results_df["completed"].mean()) if len(ev_results_df) else 0.0

    shortfalls = ev_results_df.loc[~ev_results_df["completed"], "energy_shortfall_kwh"]
    avg_shortfall = float(shortfalls.mean()) if len(shortfalls) else 0.0
    p95_shortfall = float(shortfalls.quantile(0.95)) if len(shortfalls) else 0.0
    n_incomplete = int((~ev_results_df["completed"]).sum())

    return {
        "peak_load_kw": round(peak_load_kw, 3),
        "total_energy_delivered_kwh": round(total_energy_delivered_kwh, 3),
        "total_energy_needed_kwh": round(total_energy_needed_kwh, 3),
        "completion_rate_pct": round(completion_rate * 100, 2),
        "n_incomplete": n_incomplete,
        "avg_shortfall_kwh_incomplete": round(avg_shortfall, 3),
        "p95_shortfall_kwh_incomplete": round(p95_shortfall, 3),
    }