from __future__ import annotations

import numpy as np
import pandas as pd


def generate_ev_profiles(
    n_evs: int = 50,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic EV charging profiles for a single day.

    Fields:
    - ev_id
    - arrival_hour (0-20)
    - departure_hour (arrival+1 to 23)
    - battery_kwh
    - initial_soc
    - target_soc

    Notes:
    - This is a simple synthetic generator for Day 1.
    - We keep departure on the same day to avoid midnight complexity for now.
    """
    rng = np.random.default_rng(seed)

    ev_ids = np.arange(1, n_evs + 1)

    # Arrival between 0 and 20 so we can guarantee at least 1 hour before midnight
    arrival_hours = rng.integers(low=0, high=21, size=n_evs)

    departure_hours = []
    for arrival in arrival_hours:
        # At least 1 hour after arrival, at most 23
        dep = rng.integers(low=arrival + 1, high=24)
        departure_hours.append(dep)
    departure_hours = np.array(departure_hours)

    # Typical EV battery sizes (kWh), simple uniform distribution
    battery_kwh = rng.uniform(low=40.0, high=80.0, size=n_evs).round(1)

    # Initial SOC between 15% and 70%
    initial_soc = rng.uniform(low=0.15, high=0.70, size=n_evs).round(2)

    # Target SOC between 80% and 95%, must be > initial_soc
    raw_target_soc = rng.uniform(low=0.80, high=0.95, size=n_evs)
    target_soc = np.maximum(raw_target_soc, initial_soc + 0.10)
    target_soc = np.clip(target_soc, 0.80, 0.95).round(2)

    # If clipping caused target <= initial for any edge case, fix it
    for i in range(n_evs):
        if target_soc[i] <= initial_soc[i]:
            target_soc[i] = min(0.95, round(initial_soc[i] + 0.10, 2))

    df = pd.DataFrame(
        {
            "ev_id": ev_ids,
            "arrival_hour": arrival_hours,
            "departure_hour": departure_hours,
            "battery_kwh": battery_kwh,
            "initial_soc": initial_soc,
            "target_soc": target_soc,
        }
    )

    # Derived fields for convenience
    df["energy_needed_kwh"] = (
        df["battery_kwh"] * (df["target_soc"] - df["initial_soc"])
    ).round(2)
    df["available_hours"] = df["departure_hour"] - df["arrival_hour"]

    return df


def validate_profiles(df: pd.DataFrame) -> None:
    """
    Basic validation checks for generated profiles.
    Raises ValueError if any check fails.
    """
    required_cols = {
        "ev_id",
        "arrival_hour",
        "departure_hour",
        "battery_kwh",
        "initial_soc",
        "target_soc",
        "energy_needed_kwh",
        "available_hours",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if (df["arrival_hour"] < 0).any() or (df["arrival_hour"] > 23).any():
        raise ValueError("arrival_hour out of range")

    if (df["departure_hour"] < 1).any() or (df["departure_hour"] > 23).any():
        raise ValueError("departure_hour out of range")

    if (df["departure_hour"] <= df["arrival_hour"]).any():
        raise ValueError("departure_hour must be greater than arrival_hour")

    if (df["battery_kwh"] <= 0).any():
        raise ValueError("battery_kwh must be positive")

    if ((df["initial_soc"] < 0) | (df["initial_soc"] > 1)).any():
        raise ValueError("initial_soc must be between 0 and 1")

    if ((df["target_soc"] < 0) | (df["target_soc"] > 1)).any():
        raise ValueError("target_soc must be between 0 and 1")

    if (df["target_soc"] <= df["initial_soc"]).any():
        raise ValueError("target_soc must be greater than initial_soc")

    if (df["energy_needed_kwh"] <= 0).any():
        raise ValueError("energy_needed_kwh must be positive")


if __name__ == "__main__":
    profiles = generate_ev_profiles(n_evs=10, seed=42)
    validate_profiles(profiles)
    print(profiles.head(10).to_string(index=False))