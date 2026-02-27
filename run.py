from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from src.charging_simulator import simulate_uncontrolled_charging, simulate_rule_based_smart_charging
from src.metrics import calculate_fleet_metrics
from src.profile_generator import generate_ev_profiles, validate_profiles

def save_profile_plots(profiles_df, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Arrival hour histogram
    plt.figure(figsize=(8, 4))
    plt.hist(profiles_df["arrival_hour"], bins=range(0, 25), edgecolor="black", align="left")
    plt.xticks(range(0, 24))
    plt.xlabel("Arrival Hour")
    plt.ylabel("Number of EVs")
    plt.title("EV Arrival Hour Distribution (Synthetic Profiles)")
    plt.tight_layout()
    plt.savefig(figures_dir / "arrival_hour_histogram.png", dpi=150)
    plt.close()

    # Energy needed histogram
    plt.figure(figsize=(8, 4))
    plt.hist(profiles_df["energy_needed_kwh"], bins=10, edgecolor="black")
    plt.xlabel("Energy Needed (kWh)")
    plt.ylabel("Number of EVs")
    plt.title("Energy Needed Distribution (Synthetic Profiles)")
    plt.tight_layout()
    plt.savefig(figures_dir / "energy_needed_histogram.png", dpi=150)
    plt.close()


def save_uncontrolled_load_plot(fleet_load_df, figures_dir: Path) -> None:
    plt.figure(figsize=(9, 4.5))
    plt.plot(fleet_load_df["hour"], fleet_load_df["fleet_load_kw"], marker="o")
    plt.xticks(range(0, 24))
    plt.xlabel("Hour of Day")
    plt.ylabel("Fleet Charging Load (kW)")
    plt.title("Uncontrolled EV Charging - Aggregate Fleet Load")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figures_dir / "aggregate_load_uncontrolled.png", dpi=150)
    plt.close()

def save_comparison_plot(load_a, load_b, labels, figures_dir: Path, filename: str) -> None:
    plt.figure(figsize=(9, 4.5))
    plt.plot(load_a["hour"], load_a["fleet_load_kw"], marker="o", label=labels[0])
    plt.plot(load_b["hour"], load_b["fleet_load_kw"], marker="o", label=labels[1])
    plt.xticks(range(0, 24))
    plt.xlabel("Hour of Day")
    plt.ylabel("Fleet Charging Load (kW)")
    plt.title("Fleet Load Comparison")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / filename, dpi=150)
    plt.close()

def main() -> None:
    output_dir = Path("results")
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Generate profiles (Day 1)
    # -------------------------
    profiles_df = generate_ev_profiles(n_evs=50, seed=42)
    validate_profiles(profiles_df)

    profiles_path = output_dir / "ev_profiles_day1.csv"
    profiles_df.to_csv(profiles_path, index=False)

    # Save Day 1 distributions
    save_profile_plots(profiles_df, figures_dir)

    # -------------------------
    # Simulations (Day 3)
    # -------------------------
    charging_power_kw = 7.0
    peak_hours = [16, 17, 18]  # avoid these hours

    # Uncontrolled (baseline)
    fleet_unctrl, ev_unctrl = simulate_uncontrolled_charging(
        profiles_df=profiles_df,
        charging_power_kw=charging_power_kw,
    )
    metrics_unctrl = calculate_fleet_metrics(fleet_unctrl, ev_unctrl)

    # Smart (rule-based peak avoidance)
    fleet_smart, ev_smart = simulate_rule_based_smart_charging(
        profiles_df=profiles_df,
        charging_power_kw=charging_power_kw,
        peak_hours=peak_hours,
    )
    metrics_smart = calculate_fleet_metrics(fleet_smart, ev_smart)

    # -------------------------
    # Save outputs
    # -------------------------
    fleet_unctrl.to_csv(output_dir / "fleet_load_uncontrolled.csv", index=False)
    ev_unctrl.to_csv(output_dir / "ev_results_uncontrolled.csv", index=False)

    fleet_smart.to_csv(output_dir / "fleet_load_smart_rule_based.csv", index=False)
    ev_smart.to_csv(output_dir / "ev_results_smart_rule_based.csv", index=False)

    # -------------------------
    # Save plots
    # -------------------------
    save_uncontrolled_load_plot(fleet_unctrl, figures_dir)
    save_comparison_plot(
        fleet_unctrl,
        fleet_smart,
        labels=["Uncontrolled", "Smart (Rule-based)"],
        figures_dir=figures_dir,
        filename="fleet_load_comparison_uncontrolled_vs_smart.png",
    )

    # -------------------------
    # Root-cause analysis: feasibility check (uncontrolled)
    # -------------------------
    merged = profiles_df.merge(
        ev_unctrl, on=["ev_id", "arrival_hour", "departure_hour", "energy_needed_kwh"]
    )
    merged["max_possible_energy_kwh"] = merged["available_hours"] * charging_power_kw
    merged["feasible"] = merged["energy_needed_kwh"] <= merged["max_possible_energy_kwh"] + 1e-9

    not_completed = merged[merged["completed"] == False].copy()

    # -------------------------
    # Print report
    # -------------------------
    print("=== Day 3: Comparison ===")
    print(f"Profiles saved: {profiles_path}")
    print("Peak avoidance hours:", peak_hours)
    print()

    print("Uncontrolled metrics:")
    for k, v in metrics_unctrl.items():
        print(f" - {k}: {v}")
    print()

    print("Smart (rule-based) metrics:")
    for k, v in metrics_smart.items():
        print(f" - {k}: {v}")
    print()

    print("=== Root-cause: Incomplete EVs (Uncontrolled) ===")
    print("Not completed EVs:", len(not_completed))
    print("Not completed but feasible (should be near 0):", int(not_completed["feasible"].sum()))
    print()

    if len(not_completed) > 0:
        print("Top 10 shortfalls:")
        cols = [
            "ev_id",
            "arrival_hour",
            "departure_hour",
            "available_hours",
            "energy_needed_kwh",
            "max_possible_energy_kwh",
            "energy_delivered_kwh",
            "energy_shortfall_kwh",
            "feasible",
        ]
        print(
            not_completed.sort_values("energy_shortfall_kwh", ascending=False)[cols]
            .head(10)
            .to_string(index=False)
        )

    print("seed=42, n_evs=", len(profiles_df))
    print("arrival min/max:", profiles_df["arrival_hour"].min(), profiles_df["arrival_hour"].max())
    print("available_hours min/max:", profiles_df["available_hours"].min(), profiles_df["available_hours"].max())
    print("energy_needed mean:", profiles_df["energy_needed_kwh"].mean())
    print("charging_power_kw:", charging_power_kw)

    pd.DataFrame([{"scenario":"uncontrolled", **metrics_unctrl},
                  {"scenario":"smart_rule_based", **metrics_smart}]
    ).to_csv(output_dir / "metrics_comparison_day3.csv", index=False)


if __name__ == "__main__":
    main()