from pathlib import Path

import matplotlib.pyplot as plt

from src.charging_simulator import simulate_uncontrolled_charging
from src.metrics import calculate_fleet_metrics
from src.profile_generator import generate_ev_profiles, validate_profiles


def save_day1_profile_plots(df, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Arrival hour histogram
    plt.figure(figsize=(8, 4))
    plt.hist(df["arrival_hour"], bins=range(0, 25), edgecolor="black", align="left")
    plt.xticks(range(0, 24))
    plt.xlabel("Arrival Hour")
    plt.ylabel("Number of EVs")
    plt.title("EV Arrival Hour Distribution (Synthetic Profiles)")
    plt.tight_layout()
    plt.savefig(figures_dir / "arrival_hour_histogram.png", dpi=150)
    plt.close()

    # Energy needed histogram
    plt.figure(figsize=(8, 4))
    plt.hist(df["energy_needed_kwh"], bins=10, edgecolor="black")
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


def main() -> None:
    output_dir = Path("results")
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Day 1 profiles
    profiles_df = generate_ev_profiles(n_evs=50, seed=42)
    validate_profiles(profiles_df)

    profiles_path = output_dir / "ev_profiles_day1.csv"
    profiles_df.to_csv(profiles_path, index=False)

    # Save Day 1 distributions
    save_day1_profile_plots(profiles_df, figures_dir)

    # Day 2 simulation: uncontrolled charging
    fleet_load_df, ev_results_df = simulate_uncontrolled_charging(
        profiles_df=profiles_df,
        charging_power_kw=7.0,
    )

    # Save outputs
    fleet_load_path = output_dir / "fleet_load_uncontrolled.csv"
    ev_results_path = output_dir / "ev_results_uncontrolled.csv"
    fleet_load_df.to_csv(fleet_load_path, index=False)
    ev_results_df.to_csv(ev_results_path, index=False)

    # Save plot
    save_uncontrolled_load_plot(fleet_load_df, figures_dir)

    # Metrics
    metrics = calculate_fleet_metrics(fleet_load_df, ev_results_df)

    print("=== Day 2: Uncontrolled Charging Simulation ===")
    print(f"Profiles saved: {profiles_path}")
    print(f"Fleet load saved: {fleet_load_path}")
    print(f"EV results saved: {ev_results_path}")
    print(f"Figures saved in: {figures_dir}")
    print()

    print("Fleet load (first 10 rows):")
    print(fleet_load_df.head(10).to_string(index=False))
    print()

    print("Per-EV results (first 10 rows):")
    print(ev_results_df.head(10).to_string(index=False))
    print()

    print("Metrics:")
    for k, v in metrics.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    main()