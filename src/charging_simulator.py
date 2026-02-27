from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def simulate_uncontrolled_charging(
    profiles_df: pd.DataFrame,
    charging_power_kw: float = 7.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate uncontrolled charging for a fleet over a single day (24 hourly slots).

    Assumptions:
    - Charging starts immediately at arrival_hour
    - Constant charging power (kW)
    - Hourly resolution
    - Charging stops when energy_needed_kwh is met or at departure_hour
    - departure_hour is treated as the last available hour boundary (not inclusive)
      Example: arrival=10, departure=13 -> charging can occur in hours 10,11,12
    Returns:
    - fleet_load_df: hourly aggregate fleet load
    - ev_results_df: per-EV charging results
    """
    n_hours = 24
    hourly_load_kw = np.zeros(n_hours, dtype=float)

    ev_results = []

    for _, row in profiles_df.iterrows():
        ev_id = int(row["ev_id"])
        arrival = int(row["arrival_hour"])
        departure = int(row["departure_hour"])
        energy_needed = float(row["energy_needed_kwh"])

        remaining_energy = energy_needed
        energy_delivered = 0.0

        # For hourly resolution: each hour can deliver up to charging_power_kw * 1h = charging_power_kw kWh
        for hour in range(arrival, departure):
            if remaining_energy <= 1e-9:
                break

            energy_this_hour = min(charging_power_kw, remaining_energy)  # kWh in 1 hour
            power_this_hour = energy_this_hour  # because 1-hour timestep, kWh == average kW over that hour

            hourly_load_kw[hour] += power_this_hour
            remaining_energy -= energy_this_hour
            energy_delivered += energy_this_hour

        completed = energy_delivered >= energy_needed - 1e-6

        ev_results.append(
            {
                "ev_id": ev_id,
                "arrival_hour": arrival,
                "departure_hour": departure,
                "energy_needed_kwh": round(energy_needed, 3),
                "energy_delivered_kwh": round(energy_delivered, 3),
                "energy_shortfall_kwh": round(max(0.0, energy_needed - energy_delivered), 3),
                "completed": completed,
            }
        )

    fleet_load_df = pd.DataFrame(
        {
            "hour": np.arange(n_hours),
            "fleet_load_kw": hourly_load_kw.round(3),
        }
    )

    ev_results_df = pd.DataFrame(ev_results)

    return fleet_load_df, ev_results_df

def simulate_rule_based_smart_charging(
    profiles_df: pd.DataFrame,
    charging_power_kw: float = 7.0,
    peak_hours: list = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Rule-based smart charging:
    - Allocate charging to non-peak hours first (within arrival->departure window)
    - If still not enough, use peak hours
    - Constant power, hourly resolution

    peak_hours: list of hours to avoid (e.g., [16,17,18])
    """
    if peak_hours is None:
        peak_hours = [16, 17, 18]

    n_hours = 24
    hourly_load_kw = np.zeros(n_hours, dtype=float)
    ev_results = []

    for _, row in profiles_df.iterrows():
        ev_id = int(row["ev_id"])
        arrival = int(row["arrival_hour"])
        departure = int(row["departure_hour"])
        energy_needed = float(row["energy_needed_kwh"])

        remaining_energy = energy_needed
        energy_delivered = 0.0

        available_hours = list(range(arrival, departure))
        non_peak = [h for h in available_hours if h not in peak_hours]
        peak = [h for h in available_hours if h in peak_hours]

        # Prefer non-peak hours first
        preferred_schedule = non_peak + peak

        for hour in preferred_schedule:
            if remaining_energy <= 1e-9:
                break

            energy_this_hour = min(charging_power_kw, remaining_energy)  # kWh in 1 hour
            power_this_hour = energy_this_hour  # average kW over 1 hour step

            hourly_load_kw[hour] += power_this_hour
            remaining_energy -= energy_this_hour
            energy_delivered += energy_this_hour

        completed = energy_delivered >= energy_needed - 1e-6

        ev_results.append(
            {
                "ev_id": ev_id,
                "arrival_hour": arrival,
                "departure_hour": departure,
                "energy_needed_kwh": round(energy_needed, 3),
                "energy_delivered_kwh": round(energy_delivered, 3),
                "energy_shortfall_kwh": round(max(0.0, energy_needed - energy_delivered), 3),
                "completed": completed,
            }
        )

    fleet_load_df = pd.DataFrame(
        {"hour": np.arange(n_hours), "fleet_load_kw": hourly_load_kw.round(3)}
    )
    ev_results_df = pd.DataFrame(ev_results)

    return fleet_load_df, ev_results_df