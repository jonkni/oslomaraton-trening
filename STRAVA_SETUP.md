# Strava API Setup Guide

## Steg 1: Opprett Strava API App

1. Gå til [https://www.strava.com/settings/api](https://www.strava.com/settings/api)
2. Klikk på "Create & Manage Your App" eller "My API Application"
3. Fyll ut følgende felter:
   - **Application Name:** Oslo Marathon Training Analyzer
   - **Category:** Training
   - **Club:** (valgfritt, kan la stå tomt)
   - **Website:** http://localhost
   - **Authorization Callback Domain:** localhost
   - **Application Description:** Treningsanalyse for Oslo halvmaraton

4. Godta vilkårene og klikk "Create"

## Steg 2: Hent API-nøklene

Etter opprettelse vil du se:
- **Client ID** (et tall)
- **Client Secret** (en lang streng - HOLD DENNE HEMMELIG!)

## Steg 3: Opprett .env fil

Kopier `Client ID` og `Client Secret` og kjør følgende kommando:

```bash
cat > .env << 'EOF'
STRAVA_CLIENT_ID=DIN_CLIENT_ID
STRAVA_CLIENT_SECRET=DIN_CLIENT_SECRET
EOF
```

Erstatt `DIN_CLIENT_ID` og `DIN_CLIENT_SECRET` med de faktiske verdiene.

## Steg 4: Første gangs autentisering

Når du kjører Python-scriptet første gang, vil det:
1. Åpne en nettleser
2. Be deg logge inn på Strava
3. Be om tillatelse til å lese dine aktiviteter
4. Lagre en token som brukes for fremtidige forespørsler

Dette trenger bare gjøres én gang!
