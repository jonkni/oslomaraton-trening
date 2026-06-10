"""
Strava OAuth2 Authentication Module
Håndterer autentisering og token-refresh for Strava API
"""

import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from stravalib.client import Client
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = ".strava_token"


class StravaAuthHandler(BaseHTTPRequestHandler):
    """Handler for OAuth2 callback"""

    def do_GET(self):
        """Handle the OAuth2 callback"""
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
                <html>
                <body>
                    <h1>Autentisering vellykket!</h1>
                    <p>Du kan lukke dette vinduet og gå tilbake til terminalen.</p>
                </body>
                </html>
            """.encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("<html><body><h1>Feil ved autentisering</h1></body></html>".encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


def get_strava_client():
    """
    Hent en autentisert Strava-klient.
    Håndterer både første gangs autentisering og token refresh.
    """
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError(
            "STRAVA_CLIENT_ID og STRAVA_CLIENT_SECRET må være satt i .env filen.\n"
            "Se STRAVA_SETUP.md for instruksjoner."
        )

    client = Client()

    # Sjekk om vi har et lagret token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)

        # Forsøk å refresh token
        try:
            token_response = client.refresh_access_token(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=token_data['refresh_token']
            )

            # Lagre det nye tokenet
            save_token(token_response)
            client.access_token = token_response['access_token']

            print("✓ Strava-token refreshed")
            return client
        except Exception as e:
            print(f"⚠ Token refresh feilet: {e}")
            print("Starter ny autentisering...")

    # Første gangs autentisering
    print("\n=== Strava Autentisering ===")
    print("En nettleser vil åpnes for å autorisere appen.")
    print("Logg inn på Strava og godkjenn tilgang.\n")

    # Generer autoriserings-URL
    authorize_url = client.authorization_url(
        client_id=client_id,
        redirect_uri='http://localhost:8000',
        scope=['read_all', 'activity:read_all']
    )

    # Åpne nettleser
    webbrowser.open(authorize_url)

    # Start lokal server for å motta callback
    server = HTTPServer(('localhost', 8000), StravaAuthHandler)
    server.auth_code = None

    print("Venter på autorisering...")
    server.handle_request()

    if not server.auth_code:
        raise Exception("Autentisering feilet - ingen kode mottatt")

    # Bytt autoriserings-kode mot access token
    token_response = client.exchange_code_for_token(
        client_id=client_id,
        client_secret=client_secret,
        code=server.auth_code
    )

    # Lagre token for fremtidig bruk
    save_token(token_response)
    client.access_token = token_response['access_token']

    print("✓ Autentisering vellykket!\n")
    return client


def save_token(token_response):
    """Lagre token til fil"""
    token_data = {
        'access_token': token_response['access_token'],
        'refresh_token': token_response['refresh_token'],
        'expires_at': token_response['expires_at']
    }

    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)


if __name__ == "__main__":
    # Test autentisering
    try:
        client = get_strava_client()
        athlete = client.get_athlete()
        print(f"Logget inn som: {athlete.firstname} {athlete.lastname}")
    except Exception as e:
        print(f"Feil: {e}")
