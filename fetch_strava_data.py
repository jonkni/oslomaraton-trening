"""
Henter og analyserer treningsdata fra Strava
"""

import pandas as pd
from datetime import datetime, timedelta
from strava_auth import get_strava_client


def fetch_activities(client, after_date=None, before_date=None):
    """
    Hent aktiviteter fra Strava

    Args:
        client: Autentisert Strava-klient
        after_date: Hent aktiviteter etter denne datoen (datetime)
        before_date: Hent aktiviteter før denne datoen (datetime)

    Returns:
        DataFrame med aktiviteter
    """
    activities = []

    for activity in client.get_activities(after=after_date, before=before_date):
        activities.append({
            'id': activity.id,
            'name': activity.name,
            'type': activity.type,
            'start_date': activity.start_date_local,
            'distance_km': float(activity.distance) / 1000 if activity.distance else 0,
            'moving_time_minutes': activity.moving_time.total_seconds() / 60 if activity.moving_time else 0,
            'elapsed_time_minutes': activity.elapsed_time.total_seconds() / 60 if activity.elapsed_time else 0,
            'total_elevation_gain': float(activity.total_elevation_gain) if activity.total_elevation_gain else 0,
            'average_speed_kmh': float(activity.average_speed) * 3.6 if activity.average_speed else 0,
            'max_speed_kmh': float(activity.max_speed) * 3.6 if activity.max_speed else 0,
            'average_heartrate': float(activity.average_heartrate) if activity.average_heartrate else None,
            'max_heartrate': float(activity.max_heartrate) if activity.max_heartrate else None,
            'suffer_score': activity.suffer_score if hasattr(activity, 'suffer_score') else None,
            'has_heartrate': activity.has_heartrate,
            'average_cadence': float(activity.average_cadence) if activity.average_cadence else None,
        })

    df = pd.DataFrame(activities)

    if len(df) > 0:
        # Beregn pace (min/km)
        df['pace_min_per_km'] = df.apply(
            lambda row: row['moving_time_minutes'] / row['distance_km']
            if row['distance_km'] > 0 else None,
            axis=1
        )

        # Format pace som "MM:SS"
        df['pace_formatted'] = df['pace_min_per_km'].apply(
            lambda x: f"{int(x)}:{int((x % 1) * 60):02d}" if pd.notna(x) else None
        )

        # Sorter etter dato
        df = df.sort_values('start_date', ascending=False)

    return df


def analyze_running_data(df):
    """
    Analyser løpsdata og gi oppsummering

    Args:
        df: DataFrame med aktiviteter

    Returns:
        Dictionary med analyse-resultater
    """
    # Filtrer kun løping
    runs = df[df['type'] == 'Run'].copy()

    if len(runs) == 0:
        return {"error": "Ingen løpeaktiviteter funnet"}

    # Timeframes
    now = datetime.now()
    last_4_weeks = runs[runs['start_date'] >= (now - timedelta(weeks=4))]
    last_12_weeks = runs[runs['start_date'] >= (now - timedelta(weeks=12))]

    analysis = {
        'total_runs': len(runs),
        'total_distance_km': runs['distance_km'].sum(),
        'total_elevation_m': runs['total_elevation_gain'].sum(),

        # Siste 4 uker
        'last_4_weeks': {
            'runs': len(last_4_weeks),
            'total_km': last_4_weeks['distance_km'].sum(),
            'avg_km_per_week': last_4_weeks['distance_km'].sum() / 4,
            'avg_pace': last_4_weeks['pace_min_per_km'].mean(),
            'avg_elevation_per_run': last_4_weeks['total_elevation_gain'].mean(),
        },

        # Siste 12 uker
        'last_12_weeks': {
            'runs': len(last_12_weeks),
            'total_km': last_12_weeks['distance_km'].sum(),
            'avg_km_per_week': last_12_weeks['distance_km'].sum() / 12,
            'avg_pace': last_12_weeks['pace_min_per_km'].mean(),
        },

        # Lengste løp
        'longest_run': {
            'distance_km': runs['distance_km'].max(),
            'date': runs.loc[runs['distance_km'].idxmax(), 'start_date'],
            'pace': runs.loc[runs['distance_km'].idxmax(), 'pace_formatted'],
        },

        # Raskeste pace (filtrert på >3km for å unngå oppvarming)
        'fastest_pace': None,
    }

    long_runs = runs[runs['distance_km'] >= 3]
    if len(long_runs) > 0:
        fastest_idx = long_runs['pace_min_per_km'].idxmin()
        analysis['fastest_pace'] = {
            'pace': long_runs.loc[fastest_idx, 'pace_formatted'],
            'distance_km': long_runs.loc[fastest_idx, 'distance_km'],
            'date': long_runs.loc[fastest_idx, 'start_date'],
        }

    # Finn 2TL på Jeløya
    jeloya = runs[runs['name'].str.contains('2TL|Jeløya|jeloya', case=False, na=False)]
    if len(jeloya) > 0:
        latest_jeloya = jeloya.iloc[0]
        analysis['jeloya_2tl'] = {
            'date': latest_jeloya['start_date'],
            'distance_km': latest_jeloya['distance_km'],
            'time_minutes': latest_jeloya['moving_time_minutes'],
            'pace': latest_jeloya['pace_formatted'],
            'elevation_gain': latest_jeloya['total_elevation_gain'],
        }

    return analysis


def print_analysis(analysis):
    """Print analyse-resultater på en pen måte"""
    print("\n" + "="*60)
    print("TRENINGSANALYSE - STRAVA DATA")
    print("="*60)

    if 'error' in analysis:
        print(f"\n⚠ {analysis['error']}")
        return

    print(f"\n📊 TOTALT:")
    print(f"   Antall løp: {analysis['total_runs']}")
    print(f"   Total distanse: {analysis['total_distance_km']:.1f} km")
    print(f"   Total stigning: {analysis['total_elevation_m']:.0f} m")

    print(f"\n📅 SISTE 4 UKER:")
    w4 = analysis['last_4_weeks']
    print(f"   Antall løp: {w4['runs']}")
    print(f"   Total: {w4['total_km']:.1f} km")
    print(f"   Gjennomsnitt per uke: {w4['avg_km_per_week']:.1f} km")
    print(f"   Gjennomsnittlig pace: {int(w4['avg_pace'])}:{int((w4['avg_pace'] % 1) * 60):02d} min/km")
    print(f"   Gjennomsnittlig stigning per løp: {w4['avg_elevation_per_run']:.0f} m")

    print(f"\n📅 SISTE 12 UKER:")
    w12 = analysis['last_12_weeks']
    print(f"   Antall løp: {w12['runs']}")
    print(f"   Total: {w12['total_km']:.1f} km")
    print(f"   Gjennomsnitt per uke: {w12['avg_km_per_week']:.1f} km")
    print(f"   Gjennomsnittlig pace: {int(w12['avg_pace'])}:{int((w12['avg_pace'] % 1) * 60):02d} min/km")

    print(f"\n🏃 LENGSTE LØP:")
    longest = analysis['longest_run']
    print(f"   {longest['distance_km']:.1f} km @ {longest['pace']} min/km")
    print(f"   Dato: {longest['date'].strftime('%d.%m.%Y')}")

    if analysis['fastest_pace']:
        print(f"\n⚡ RASKESTE PACE (>3km):")
        fastest = analysis['fastest_pace']
        print(f"   {fastest['pace']} min/km over {fastest['distance_km']:.1f} km")
        print(f"   Dato: {fastest['date'].strftime('%d.%m.%Y')}")

    if 'jeloya_2tl' in analysis:
        print(f"\n🏔️ 2TL JELØYA:")
        jtl = analysis['jeloya_2tl']
        print(f"   Dato: {jtl['date'].strftime('%d.%m.%Y')}")
        print(f"   Distanse: {jtl['distance_km']:.2f} km")
        print(f"   Tid: {int(jtl['time_minutes']//60)}:{int(jtl['time_minutes']%60):02d}")
        print(f"   Pace: {jtl['pace']} min/km")
        print(f"   Stigning: {jtl['elevation_gain']:.0f} m")

    print("\n" + "="*60 + "\n")


def main():
    """Hovedfunksjon"""
    print("Henter data fra Strava...")

    # Autentiser
    client = get_strava_client()

    # Hent aktiviteter fra siste år
    after_date = datetime.now() - timedelta(days=365)
    df = fetch_activities(client, after_date=after_date)

    print(f"✓ Hentet {len(df)} aktiviteter")

    # Lagre rå data
    df.to_csv('strava_activities.csv', index=False)
    print("✓ Data lagret til strava_activities.csv")

    # Analyser
    analysis = analyze_running_data(df)
    print_analysis(analysis)

    return df, analysis


if __name__ == "__main__":
    df, analysis = main()
