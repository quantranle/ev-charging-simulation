import pandas as pd


def calculate_fleet_metrics(
    fleet_load_df: pd.DataFrame,
    ev_results_df: pd.DataFrame,
) -> dict:
    """
    Calculate core metrics for the charging simulation.
    """
    peak_load_kw = float(fleet_load_df["fleet_load_kw"].max())
    total_energy_delivered_kwh = float(ev_results_df["energy_delivered_kwh"].sum())
    total_energy_needed_kwh = float(ev_results_df["energy_needed_kwh"].sum())

    completion_rate = float(ev_results_df["completed"].mean()) if len(ev_results_df) > 0 else 0.0

    return {
        "peak_load_kw": round(peak_load_kw, 3),
        "total_energy_delivered_kwh": round(total_energy_delivered_kwh, 3),
        "total_energy_needed_kwh": round(total_energy_needed_kwh, 3),
        "completion_rate_pct": round(completion_rate * 100, 2),
    }