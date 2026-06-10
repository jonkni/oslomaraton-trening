"""
Genererer treningsprogram for Oslo halvmaraton basert på norsk modell
(Marius Bakken / threshold-basert trening)
"""

import pandas as pd
from datetime import datetime, timedelta
from fetch_strava_data import fetch_activities, analyze_running_data, get_strava_client


class TrainingPlanGenerator:
    """Genererer treningsprogram basert på norsk modell"""

    def __init__(self, race_date, current_fitness, injury_history=None):
        """
        Args:
            race_date: Dato for løpet (datetime)
            current_fitness: Dict med nøkkeldata fra Strava
            injury_history: Info om skader
        """
        self.race_date = race_date
        self.today = datetime.now()
        self.weeks_to_race = (race_date - self.today).days // 7
        self.current_fitness = current_fitness
        self.injury_history = injury_history or {}

        # Grenada-periode (begrenset treningmulighet)
        self.grenada_start = datetime(2026, 6, 22)
        self.grenada_end = datetime(2026, 7, 19)

        # Norsk modell prinsipper
        self.threshold_paces = self._calculate_threshold_paces()

    def _calculate_threshold_paces(self):
        """
        Beregn treningssoner basert på nåværende form og mål

        Norsk modell fokuserer på:
        - Anaerob terskel (AT) / "laktatterskel"
        - Double threshold (2x terskel per uke)
        - Lange rolige løp
        - Litt hurtigere arbeid (kortintervaller)

        Bruker race-paces fra Sentrumsløpet 10km (4:58/km) som baseline
        """
        # Sentrumsløpet 10km: 50:00 (4:58/km) - beste indikator på nåværende form
        race_10k_pace = 4.97  # 4:58 min/km

        # Beregn halvmaraton race pace fra 10k (Riegel formel + Oslo profil)
        # 10k @ 4:58 -> HM @ ca 5:12-5:15 (flatt)
        # Oslo HM (+145m) -> +10-12 sek/km -> 5:22-5:27
        # Comeback-justering (konservativ) -> 5:12/km målpace (realistisk)

        race_pace_hm = 5.20  # 5:12/km - realistisk mål med god trening

        paces = {
            'easy': race_pace_hm + 1.0,  # Rolig grunntrening (60 sek/km langsommere)
            'long_run': race_pace_hm + 0.7,  # Lang rolig (ca 6:00/km)
            'threshold': race_pace_hm + 0.15,  # Terskel (5:27/km - halvmaraton pace + 15 sek)
            'tempo': race_pace_hm,  # Tempo = race pace (5:12/km)
            'interval': race_10k_pace,  # 10k race pace for intervaller (4:58/km)
            'race_pace_hm': race_pace_hm,  # Målpace halvmaraton (5:12/km)
        }

        return paces

    def estimate_race_time(self):
        """
        Estimer halvmaraton-tid basert på:
        - 10k race: 50:00 (Sentrumsløpet april 2026)
        - Riegel formel for halvmaraton-prediksjon
        - Løypeprofil (145m stigning)
        - Tidligere beste (1:38)
        - Kneskade i mai 2025 (13 måneder siden)
        """
        # Baseline: 10k på 50:00 predikerer HM på flat løype
        # Riegel: T2 = T1 * (D2/D1)^1.06
        # HM fra 10k @ 50min: ~1:50 (5:12/km) optimalt

        race_pace_hm = self.threshold_paces['race_pace_hm']  # 5:12/km
        distance_km = 21.0975

        # Scenarioer basert på treningsprogresjon
        # Optimistisk: Perfekt trening, god dag -> nær 10k-prediksjon
        optimistic_pace = 5.03  # 1:46 (nær flatt HM prediksjon)
        optimistic_time = (optimistic_pace * distance_km) + 2  # +2 min for høyde

        # Realistisk: God trening, normal dag -> race pace mål
        realistic_pace = race_pace_hm  # 5:12/km
        realistic_time = (realistic_pace * distance_km) + 2.5  # +2.5 min for høyde

        # Konservativt: Trygt comeback-mål
        conservative_pace = 5.43  # 1:55/km
        conservative_time = conservative_pace * distance_km

        scenarios = {
            'optimistic': optimistic_time,
            'realistic': realistic_time,
            'conservative': conservative_time,
        }

        return scenarios, race_pace_hm

    def generate_plan(self):
        """Generer ukentlig treningsplan"""

        plan = []
        current_week_start = self.today

        for week_num in range(1, self.weeks_to_race + 1):
            week_end = current_week_start + timedelta(days=7)

            # Sjekk om uken overlapper med Grenada
            in_grenada = (
                (current_week_start <= self.grenada_end) and
                (week_end >= self.grenada_start)
            )

            week_plan = self._generate_week(
                week_num=week_num,
                week_start=current_week_start,
                in_grenada=in_grenada
            )

            plan.append(week_plan)
            current_week_start = week_end

        return plan

    def _generate_week(self, week_num, week_start, in_grenada):
        """
        Generer plan for én uke

        Norsk modell ukesstruktur:
        - Mandag: Rolig / restitusjon
        - Tirsdag: Terskelintervaller (første double threshold)
        - Onsdag: Rolig
        - Torsdag: Terskel/tempo (andre double threshold)
        - Fredag: Hviledag eller lett jogg
        - Lørdag: Langtur
        - Søndag: Rolig eller hviledag
        """

        # Base ukevolum
        base_weekly_km = self.current_fitness['last_4_weeks']['avg_km_per_week']

        # Periodisering
        weeks_to_race = self.weeks_to_race - week_num + 1

        if weeks_to_race <= 2:
            # Nedtrapping
            phase = "Nedtrapping"
            weekly_km = base_weekly_km * 0.6
            intensity_level = "Lav"
        elif weeks_to_race <= 4:
            # Peak/kvalitet
            phase = "Peak"
            weekly_km = base_weekly_km * 1.1
            intensity_level = "Høy"
        elif in_grenada:
            # Grenada - redusert volum, fokus på kvalitet
            phase = "Grenada (varmt/kupert)"
            weekly_km = base_weekly_km * 0.7
            intensity_level = "Moderat"
        elif week_num <= 4:
            # Oppbygging
            phase = "Oppbygging"
            weekly_km = base_weekly_km * 0.95
            intensity_level = "Moderat"
        else:
            # Base/volum
            phase = "Base/Volum"
            weekly_km = base_weekly_km * 1.05
            intensity_level = "Moderat-Høy"

        # Spesifikk ukesplan
        sessions = self._create_sessions(weekly_km, phase, in_grenada)

        return {
            'week': week_num,
            'date_range': f"{week_start.strftime('%d.%m')} - {(week_start + timedelta(days=6)).strftime('%d.%m.%Y')}",
            'phase': phase,
            'total_km': weekly_km,
            'intensity': intensity_level,
            'sessions': sessions,
            'notes': self._get_week_notes(week_num, phase, in_grenada)
        }

    def _create_sessions(self, weekly_km, phase, in_grenada):
        """Lag øktplan for uken"""

        sessions = []
        threshold_pace = self.threshold_paces['threshold']
        easy_pace = self.threshold_paces['easy']
        interval_pace = self.threshold_paces['interval']

        def pace_str(pace):
            return f"{int(pace)}:{int((pace % 1) * 60):02d}"

        if phase == "Nedtrapping":
            # Nedtrapping - reduser volum og intensitet
            sessions = [
                {"day": "Mandag", "type": "Hvile", "details": "Hviledag", "warmup": "", "bike_alt": "Hviledag"},
                {"day": "Tirsdag", "type": "Rolig", "details": f"40 min rolig @ {pace_str(easy_pace)}", "warmup": "10 min lett jogg", "bike_alt": "45 min rolig sykkel (zone 2)"},
                {"day": "Onsdag", "type": "Tempo", "details": f"30 min inkl. 3x5 min @ {pace_str(threshold_pace)}", "warmup": "15 min rolig + 3x100m strides", "bike_alt": "40 min sykkel: 10 min oppvarming, 3x5 min @ terskel, 10 min nedjogg"},
                {"day": "Torsdag", "type": "Rolig", "details": f"30 min rolig", "warmup": "5 min lett jogg", "bike_alt": "35 min rolig sykkel (zone 2)"},
                {"day": "Fredag", "type": "Hvile", "details": "Hviledag", "warmup": "", "bike_alt": "Hviledag"},
                {"day": "Lørdag", "type": "Lang", "details": f"60-70 min @ {pace_str(easy_pace + 0.1)} (race preview)", "warmup": "10 min lett jogg", "bike_alt": "90 min rolig sykkel (zone 2)"},
                {"day": "Søndag", "type": "Hvile/lett", "details": "Hviledag eller 20-30 min lett", "warmup": "", "bike_alt": "30 min lett sykkel eller hvile"},
            ]

        elif in_grenada:
            # Grenada - tilpass til varme, kupert terreng
            sessions = [
                {"day": "Mandag", "type": "Hvile", "details": "Hviledag - akklimatisering", "warmup": "", "bike_alt": "Hviledag"},
                {"day": "Tirsdag", "type": "Fartlek", "details": f"40 min fartlek (korte stigninger) - TIDLIG MORGEN", "warmup": "10 min lett jogg", "bike_alt": "50 min sykkel: inkl. 8-10x1 min hard i bakke"},
                {"day": "Onsdag", "type": "Rolig", "details": f"30 min rolig @ {pace_str(easy_pace + 0.2)} - tilpass til varme", "warmup": "5 min lett jogg", "bike_alt": "35 min rolig sykkel"},
                {"day": "Torsdag", "type": "Bakkeintervaller", "details": "30 min inkl. 6-8x1 min bakke", "warmup": "15 min rolig + 3x100m strides", "bike_alt": "40 min sykkel: 6-8x1 min hard i bakke"},
                {"day": "Fredag", "type": "Hvile", "details": "Hviledag", "warmup": "", "bike_alt": "Hviledag"},
                {"day": "Lørdag", "type": "Lang", "details": f"60-80 min rolig i kupert terreng - TIDLIG MORGEN", "warmup": "10 min lett jogg", "bike_alt": "90-110 min rolig sykkel (kupert rute)"},
                {"day": "Søndag", "type": "Rolig/svømming", "details": "30 min lett jogg eller svømming for restitusjon", "warmup": "", "bike_alt": "30 min lett sykkel eller svømming"},
            ]

        else:
            # Normal treningsuke (norsk modell)
            long_run_km = weekly_km * 0.35  # 35% av ukevolum
            threshold_1 = "2x10 min" if phase == "Oppbygging" else "3x10 min"
            threshold_2 = "30 min" if phase != "Peak" else "40 min"

            sessions = [
                {"day": "Mandag", "type": "Rolig", "details": f"40-50 min rolig @ {pace_str(easy_pace)}",
                 "warmup": "10 min lett jogg", "bike_alt": "50-60 min rolig sykkel (zone 2)"},
                {"day": "Tirsdag", "type": "Terskel", "details": f"{threshold_1} @ {pace_str(threshold_pace)} (2-3 min pause)",
                 "warmup": "15 min rolig + 4x100m strides + 5 min pause", "bike_alt": f"60 min sykkel: 15 min oppvarming, {threshold_1} @ terskel (2-3 min lett mellom), 10 min nedjogg"},
                {"day": "Onsdag", "type": "Rolig", "details": f"40-50 min rolig @ {pace_str(easy_pace)}",
                 "warmup": "10 min lett jogg", "bike_alt": "50-60 min rolig sykkel (zone 2)"},
                {"day": "Torsdag", "type": "Tempo/Terskel", "details": f"{threshold_2} @ {pace_str(threshold_pace - 0.05)}",
                 "warmup": "15 min rolig + 4x100m strides", "bike_alt": f"50 min sykkel: 15 min oppvarming, {threshold_2} @ terskel, 10 min nedjogg"},
                {"day": "Fredag", "type": "Hvile/lett", "details": "Hviledag eller 30 min lett",
                 "warmup": "", "bike_alt": "30 min lett sykkel eller hvile"},
                {"day": "Lørdag", "type": "Langtur", "details": f"{long_run_km:.0f}-{long_run_km+2:.0f} km @ {pace_str(easy_pace)}",
                 "warmup": "10 min lett jogg", "bike_alt": f"{int(long_run_km * 7)}-{int((long_run_km+2) * 7)} min rolig sykkel (zone 2)"},
                {"day": "Søndag", "type": "Rolig", "details": f"50-60 min rolig @ {pace_str(easy_pace + 0.1)}",
                 "warmup": "10 min lett jogg", "bike_alt": "60-70 min rolig sykkel (zone 2)"},
            ]

            # Legg til intervalluke hver 3. uke
            if (phase == "Base/Volum" or phase == "Peak") and (weekly_km > 50):
                if int(weekly_km) % 3 == 0:  # Enkel heuristikk
                    sessions[3] = {
                        "day": "Torsdag",
                        "type": "Intervaller",
                        "details": f"8-10x800m @ {pace_str(interval_pace)} (400m jogg pause)"
                    }

        return sessions

    def _get_week_notes(self, week_num, phase, in_grenada):
        """Ekstra notater for uken"""
        notes = []

        if week_num == 1:
            notes.append("⚠ Post-2TL Jeløya: Fokus på restitusjon første del av uken")

        if in_grenada:
            notes.append("🌴 Grenada: Tren tidlig morgen pga. varme. Tilpass intensitet til forhold.")
            notes.append("💧 VIKTIG: Ekstra hydrasjon og elektrolytter")

        if phase == "Peak":
            notes.append("🎯 Peak-fase: Høy kvalitet, moderat volum")

        if phase == "Nedtrapping":
            notes.append("🔽 Nedtrapping: Bevar intensitet, reduser volum")

        if self.weeks_to_race - week_num + 1 == 3:
            notes.append("📅 3 uker til løp: Siste harde uke, fokuser på restitujon etter økter")

        return notes

    def print_plan(self, plan):
        """Print treningsplan"""
        print("\n" + "="*80)
        print("TRENINGSPLAN - OSLO HALVMARATON 12. SEPTEMBER 2026")
        print("Basert på norsk modell (threshold-fokusert)")
        print("="*80)

        # Tidsmål
        scenarios, pace = self.estimate_race_time()
        print(f"\n🎯 ESTIMERTE TIDSMÅL:")
        print(f"   Optimistisk:  {int(scenarios['optimistic']//60)}:{int(scenarios['optimistic']%60):02d} (5:02/km)")
        print(f"   Realistisk:   {int(scenarios['realistic']//60)}:{int(scenarios['realistic']%60):02d} ⭐ (5:12/km)")
        print(f"   Konservativt: {int(scenarios['conservative']//60)}:{int(scenarios['conservative']%60):02d} (5:26/km)")
        print(f"\n   Målpace: {int(pace)}:{int((pace % 1) * 60):02d} min/km")
        print(f"   (Basert på 10k @ 50:00 i Sentrumsløpet, justert for Oslo-profil)")
        print(f"   (Tidligere beste: 1:38 - du er på god vei tilbake!)")

        print(f"\n📊 NØKKELPRINSIPPER (Norsk modell):")
        print("   • 2x terskeltrening per uke (Tuesday + Thursday)")
        print("   • Lang rolig løp på lørdag (30-35% av ukevolum)")
        print("   • Rolig grunntrening mellom")
        print("   • Periodiske intervaller (800m-1000m)")
        print("   • Nedtrapping 2 uker før løp")

        print(f"\n⚠ VIKTIGE HENSYN:")
        print("   • Comeback etter kneskade (mai 2025) - lytt til kroppen!")
        print("   • 🚴 Kne betendt/hovent? Bruk sykkelalternativet for økten")
        print("   • Grenada 22. juni - 19. juli: Redusert volum, tilpass til varme")
        print("   • Positiv split på 2TL: Fokus på jevn innsats i terreng/varme")

        print("\n" + "="*80)
        print("UKESPLAN")
        print("="*80)

        for week in plan:
            print(f"\n{'─'*80}")
            print(f"UKE {week['week']}: {week['date_range']}")
            print(f"Fase: {week['phase']} | Mål: {week['total_km']:.0f} km | Intensitet: {week['intensity']}")
            print(f"{'─'*80}")

            for session in week['sessions']:
                print(f"  {session['day']:10s} | {session['type']:15s} | {session['details']}")
                if session.get('warmup'):
                    print(f"              {'':15s}   🔥 Oppvarming: {session['warmup']}")
                if session.get('bike_alt'):
                    print(f"              {'':15s}   🚴 Sykkel alt: {session['bike_alt']}")

            if week['notes']:
                print(f"\n  📝 Notater:")
                for note in week['notes']:
                    print(f"     {note}")

        print("\n" + "="*80)
        print("LYKKE TIL MED TRENINGEN! 🏃‍♂️")
        print("="*80 + "\n")


def main():
    """Hovedfunksjon"""
    print("="*60)
    print("TRENINGSPLANLEGGER - OSLO HALVMARATON")
    print("="*60)

    # Hent Strava-data
    print("\n[1/3] Henter data fra Strava...")
    client = get_strava_client()
    after_date = datetime.now() - timedelta(days=180)  # Siste 6 måneder
    df = fetch_activities(client, after_date=after_date)
    print(f"✓ Hentet {len(df)} aktiviteter fra siste 6 måneder")

    # Analyser
    print("\n[2/3] Analyserer treningsdata...")
    analysis = analyze_running_data(df)

    if 'error' in analysis:
        print(f"⚠ Feil: {analysis['error']}")
        return

    # Generer plan
    print("\n[3/3] Genererer treningsplan...")
    race_date = datetime(2026, 9, 12)

    injury_info = {
        'type': 'Kneskade (korsbånd, menisk, brusk)',
        'surgery_date': datetime(2025, 5, 1),
        'notes': 'Ta hensyn til redusert terrengtoleanse'
    }

    planner = TrainingPlanGenerator(
        race_date=race_date,
        current_fitness=analysis,
        injury_history=injury_info
    )

    plan = planner.generate_plan()
    planner.print_plan(plan)

    # Lagre til CSV
    rows = []
    for week in plan:
        for session in week['sessions']:
            rows.append({
                'Uke': week['week'],
                'Datoperiode': week['date_range'],
                'Fase': week['phase'],
                'Dag': session['day'],
                'Økttype': session['type'],
                'Detaljer': session['details'],
                'Oppvarming': session.get('warmup', ''),
                'Sykkel-alternativ': session.get('bike_alt', ''),
            })

    df_plan = pd.DataFrame(rows)
    df_plan.to_csv('treningsplan_oslo_halvmaraton.csv', index=False)
    print("✓ Plan lagret til treningsplan_oslo_halvmaraton.csv")


if __name__ == "__main__":
    main()
