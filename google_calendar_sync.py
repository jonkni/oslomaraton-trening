"""
Synkroniserer treningsplan til Google Calendar
"""

import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

# Scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Calendar event color (ID 9 = Blue for sports)
TRAINING_COLOR_ID = '9'


def get_calendar_service():
    """Autentiser og hent Google Calendar service"""
    creds = None

    # Token lagres i token.pickle etter første autentisering
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Hvis ingen gyldige credentials, autentiser
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("\n⚠️  Mangler credentials.json")
                print("Se GOOGLE_CALENDAR_SETUP.md for instruksjoner")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Lagre credentials for neste gang
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'En feil oppstod: {error}')
        return None


def create_training_event(service, date, session, week_phase):
    """Opprett en treningsøkt i Google Calendar"""

    # Sett start-tid basert på økttype
    if 'TIDLIG MORGEN' in session['details']:
        start_time = date.replace(hour=6, minute=30)
        end_time = start_time + timedelta(hours=1, minutes=30)
    elif session['type'] in ['Terskel', 'Tempo/Terskel', 'Intervaller']:
        start_time = date.replace(hour=17, minute=0)  # Ettermiddag
        end_time = start_time + timedelta(hours=1, minutes=30)
    elif session['type'] == 'Langtur' or session['type'] == 'Lang':
        start_time = date.replace(hour=9, minute=0)  # Lørdag morgen
        end_time = start_time + timedelta(hours=2)
    else:
        start_time = date.replace(hour=18, minute=0)  # Kveld
        end_time = start_time + timedelta(hours=1)

    # Bygg beskrivelse
    description_parts = [
        f"**{session['type']}**",
        f"\n{session['details']}",
    ]

    if session.get('warmup'):
        description_parts.append(f"\n\n🔥 **Oppvarming:** {session['warmup']}")

    if session.get('bike_alt'):
        description_parts.append(f"\n\n🚴 **Sykkel-alternativ (hvis kne betendt):**\n{session['bike_alt']}")

    description_parts.append(f"\n\n📅 **Fase:** {week_phase}")
    description_parts.append(f"\n🎯 **Oslo Halvmaraton** - 12. september 2026")

    description = '\n'.join(description_parts)

    # Tittel
    title = f"🏃 {session['type']}: {session['details'].split('@')[0].strip()[:30]}"

    event = {
        'summary': title,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Oslo',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Europe/Oslo',
        },
        'colorId': TRAINING_COLOR_ID,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 60},  # 1 time før
            ],
        },
        'extendedProperties': {
            'private': {
                'trainingPlan': 'OsloHalvmaraton2026',
                'sessionType': session['type'],
                'phase': week_phase,
            }
        }
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('id')
    except HttpError as error:
        print(f'Feil ved oppretting av event: {error}')
        return None


def delete_existing_training_events(service):
    """Slett eksisterende treningsøkter fra planen"""
    try:
        # Søk etter events med vår custom property
        now = datetime.now().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime',
            privateExtendedProperty='trainingPlan=OsloHalvmaraton2026'
        ).execute()

        events = events_result.get('items', [])

        deleted_count = 0
        for event in events:
            service.events().delete(
                calendarId='primary',
                eventId=event['id']
            ).execute()
            deleted_count += 1

        return deleted_count
    except HttpError as error:
        print(f'Feil ved sletting av events: {error}')
        return 0


def sync_training_plan_to_calendar():
    """Hovedfunksjon: Synkroniser treningsplan til Google Calendar"""

    print("\n" + "="*60)
    print("GOOGLE CALENDAR SYNKRONISERING")
    print("="*60)

    # Les treningsplan
    try:
        df = pd.read_csv('treningsplan_oslo_halvmaraton.csv')
    except FileNotFoundError:
        print("\n⚠️  Finner ikke treningsplan_oslo_halvmaraton.csv")
        print("Kjør først: python training_plan.py")
        return

    # Autentiser
    print("\n[1/3] Autentiserer med Google Calendar...")
    service = get_calendar_service()

    if not service:
        return

    print("✓ Autentisert!")

    # Slett eksisterende events
    print("\n[2/3] Sletter gamle treningsøkter fra kalenderen...")
    deleted = delete_existing_training_events(service)
    print(f"✓ Slettet {deleted} gamle økter")

    # Opprett nye events
    print("\n[3/3] Oppretter nye treningsøkter...")

    created_count = 0

    for _, row in df.iterrows():
        # Parse dato fra "10.06 - 16.06.2026" format
        date_str = row['Datoperiode'].split(' - ')[0]
        year = 2026

        # Map dag til offset
        day_offset = {
            'Mandag': 0, 'Tirsdag': 1, 'Onsdag': 2,
            'Torsdag': 3, 'Fredag': 4, 'Lørdag': 5, 'Søndag': 6
        }

        # Beregn faktisk dato
        week_start = datetime.strptime(f"{date_str}.{year}", "%d.%m.%Y")
        session_date = week_start + timedelta(days=day_offset[row['Dag']])

        # Bygg session dict
        session = {
            'type': row['Økttype'],
            'details': row['Detaljer'],
            'warmup': row['Oppvarming'] if 'Oppvarming' in row and pd.notna(row['Oppvarming']) else '',
            'bike_alt': row['Sykkel-alternativ'] if 'Sykkel-alternativ' in row and pd.notna(row['Sykkel-alternativ']) else '',
        }

        # Opprett event
        event_id = create_training_event(
            service,
            session_date,
            session,
            row['Fase']
        )

        if event_id:
            created_count += 1
            print(f"  ✓ {session_date.strftime('%d.%m')} - {row['Dag']}: {row['Økttype']}")

    print(f"\n✓ Opprettet {created_count} treningsøkter i Google Calendar!")
    print("\n" + "="*60)
    print("FERDIG!")
    print("="*60)
    print("\nØktene er nå synkronisert til din Google Calendar.")
    print("For å oppdatere planen senere, kjør dette scriptet på nytt.\n")


if __name__ == "__main__":
    sync_training_plan_to_calendar()
