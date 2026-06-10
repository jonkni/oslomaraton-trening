"""
Visualiserer treningsprogresjon og plan
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from fetch_strava_data import get_strava_client, fetch_activities, analyze_running_data


def plot_training_progression(df):
    """Visualiser treningsprogresjon over tid"""

    runs = df[df['type'] == 'Run'].copy()

    if len(runs) == 0:
        print("Ingen løpedata å visualisere")
        return

    # Sorter etter dato
    runs = runs.sort_values('start_date')

    # Beregn rullende gjennomsnitt (4 uker)
    runs['week'] = runs['start_date'].dt.to_period('W')
    weekly = runs.groupby('week').agg({
        'distance_km': 'sum',
        'pace_min_per_km': 'mean',
        'total_elevation_gain': 'sum'
    }).reset_index()

    weekly['week'] = weekly['week'].dt.to_timestamp()

    # Lag figur med subplots
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('Treningsprogresjon - Oslo Halvmaraton', fontsize=16, fontweight='bold')

    # Plot 1: Ukentlig distanse
    axes[0].bar(weekly['week'], weekly['distance_km'], width=5, alpha=0.7, color='#2E86AB')
    axes[0].axhline(y=weekly['distance_km'].mean(), color='red', linestyle='--',
                    label=f'Gjennomsnitt: {weekly["distance_km"].mean():.1f} km')
    axes[0].set_ylabel('Distanse (km)', fontsize=12)
    axes[0].set_title('Ukentlig Løpsdistanse', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Gjennomsnittlig pace
    axes[1].plot(weekly['week'], weekly['pace_min_per_km'], marker='o',
                 linewidth=2, markersize=6, color='#F24236')
    axes[1].axhline(y=weekly['pace_min_per_km'].mean(), color='green', linestyle='--',
                    label=f'Gjennomsnitt: {int(weekly["pace_min_per_km"].mean())}:{int((weekly["pace_min_per_km"].mean() % 1) * 60):02d} min/km')
    axes[1].set_ylabel('Pace (min/km)', fontsize=12)
    axes[1].set_title('Gjennomsnittlig Pace per Uke', fontsize=14)
    axes[1].invert_yaxis()  # Lavere pace = bedre
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Ukentlig høydemeter
    axes[2].bar(weekly['week'], weekly['total_elevation_gain'], width=5, alpha=0.7, color='#A23B72')
    axes[2].axhline(y=weekly['total_elevation_gain'].mean(), color='orange', linestyle='--',
                    label=f'Gjennomsnitt: {weekly["total_elevation_gain"].mean():.0f} m')
    axes[2].set_ylabel('Stigning (m)', fontsize=12)
    axes[2].set_title('Ukentlig Total Stigning', fontsize=14)
    axes[2].set_xlabel('Dato', fontsize=12)
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('treningsprogresjon.png', dpi=300, bbox_inches='tight')
    print("✓ Progresjonsgraf lagret til treningsprogresjon.png")
    plt.show()


def plot_future_plan():
    """Visualiser fremtidig treningsplan"""

    try:
        plan_df = pd.read_csv('treningsplan_oslo_halvmaraton.csv')
    except FileNotFoundError:
        print("⚠ Kjør først 'python training_plan.py' for å generere planen")
        return

    # Aggreger per uke
    weekly_plan = plan_df.groupby(['Uke', 'Fase']).size().reset_index()
    weekly_plan = weekly_plan.drop_duplicates('Uke')

    # Fargekoding per fase
    phase_colors = {
        'Oppbygging': '#4ECDC4',
        'Base/Volum': '#44AF69',
        'Grenada (varmt/kupert)': '#F95738',
        'Peak': '#FF6B35',
        'Nedtrapping': '#C7EFCF'
    }

    fig, ax = plt.subplots(1, 1, figsize=(14, 6))

    for i, row in weekly_plan.iterrows():
        color = phase_colors.get(row['Fase'], '#95A3B3')
        ax.bar(row['Uke'], 1, color=color, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax.text(row['Uke'], 0.5, row['Fase'], ha='center', va='center',
                fontsize=9, fontweight='bold', rotation=0)

    ax.set_xlabel('Uke', fontsize=12, fontweight='bold')
    ax.set_ylabel('')
    ax.set_title('Treningsplan - Periodisering mot Oslo Halvmaraton (12. sept 2026)',
                 fontsize=14, fontweight='bold')
    ax.set_yticks([])
    ax.set_xlim(0.5, weekly_plan['Uke'].max() + 0.5)
    ax.grid(axis='x', alpha=0.3)

    # Legg til race-markør
    race_week = weekly_plan['Uke'].max()
    ax.axvline(x=race_week + 0.5, color='red', linestyle='--', linewidth=3, label='🏁 Oslo Halvmaraton')
    ax.legend(loc='upper right', fontsize=12)

    plt.tight_layout()
    plt.savefig('treningsplan_periodisering.png', dpi=300, bbox_inches='tight')
    print("✓ Periodiseringsgraf lagret til treningsplan_periodisering.png")
    plt.show()


def main():
    """Hovedfunksjon"""
    print("\n" + "="*60)
    print("VISUALISERING - TRENINGSPROGRESJON")
    print("="*60)

    # Hent data
    print("\n[1/3] Henter Strava-data...")
    client = get_strava_client()
    after_date = datetime.now() - timedelta(days=180)
    df = fetch_activities(client, after_date=after_date)
    print(f"✓ Hentet {len(df)} aktiviteter")

    # Visualiser historisk data
    print("\n[2/3] Lager progresjonsgraf...")
    plot_training_progression(df)

    # Visualiser fremtidig plan
    print("\n[3/3] Lager periodiseringsgraf...")
    plot_future_plan()

    print("\n" + "="*60)
    print("FERDIG!")
    print("="*60)
    print("\nGrafene er lagret:")
    print("  • treningsprogresjon.png - Historisk progresjon")
    print("  • treningsplan_periodisering.png - Fremtidig plan")
    print("\n")


if __name__ == "__main__":
    main()
