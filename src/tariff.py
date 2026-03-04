import pandas as pd


def create_time_of_use_tariff() -> pd.DataFrame:
    """
    Create a simple 24-hour time-of-use tariff table.
    Prices are in EUR/kWh.
    """
    prices = []
    for hour in range(24):
        if 0 <= hour <= 6:
            price = 0.20   # off-peak
        elif 7 <= hour <= 15:
            price = 0.30   # shoulder
        elif 16 <= hour <= 20:
            price = 0.45   # peak
        else:  # 21-23
            price = 0.30   # shoulder

        prices.append({"hour": hour, "price_eur_per_kwh": price})

    return pd.DataFrame(prices)


def calculate_total_charging_cost(
    fleet_load_df: pd.DataFrame,
    tariff_df: pd.DataFrame,
) -> float:
    """
    Calculate total charging cost for a fleet load profile.
    Assumes 1-hour timestep, so:
    energy (kWh) per hour = average load (kW) over that hour
    """
    merged = fleet_load_df.merge(tariff_df, on="hour", how="left")
    merged["hourly_cost_eur"] = merged["fleet_load_kw"] * merged["price_eur_per_kwh"]
    return float(merged["hourly_cost_eur"].sum())