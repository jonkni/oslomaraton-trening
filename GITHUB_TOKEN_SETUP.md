# GitHub Token Setup

Din GitHub Personal Access Token har utløpt. Her er hvordan du setter opp en ny fine-grained token.

## Hvorfor fine-grained token?

✅ **Bedre sikkerhet** - begrenset til kun dette repoet
✅ **Mindre risiko** - hvis token lekker, påvirker kun ett repo
✅ **Mer kontroll** - spesifikke tillatelser

## Steg 1: Opprett fine-grained token

1. Gå til [GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens](https://github.com/settings/tokens?type=beta)

2. Klikk **Generate new token**

3. Fyll ut:
   - **Token name:** `oslomaraton-trening-mac`
   - **Expiration:** `90 days` (eller lengre)
   - **Repository access:** `Only select repositories`
     - Velg: `jonkni/oslomaraton-trening`

4. **Repository permissions:**
   - Contents: `Read and write`
   - Metadata: `Read-only` (settes automatisk)

5. Klikk **Generate token**

6. **VIKTIG:** Kopier tokenet NÅ - du får ikke se det igjen!

## Steg 2: Oppdater git credentials

### Alternativ A: Bruk git credential helper (anbefalt)

```bash
# Oppdater remote URL til å bruke token
git remote set-url origin https://<DITT_TOKEN>@github.com/jonkni/oslomaraton-trening.git

# Test at det fungerer
git push
```

Erstatt `<DITT_TOKEN>` med tokenet du kopierte.

### Alternativ B: Bruk macOS Keychain

```bash
# Fjern gammel credential fra keychain
git credential-osxkeychain erase << EOF
host=github.com
protocol=https
EOF

# Neste gang du pusher vil du bli bedt om passord - bruk tokenet
git push

# Username: jonkni
# Password: <paste token here>
```

macOS Keychain vil huske tokenet for fremtiden.

### Alternativ C: Bruk GitHub CLI (enklest!)

Hvis du har `gh` installert:

```bash
# Autentiser med gh
gh auth login

# Velg:
# - GitHub.com
# - HTTPS
# - Yes (authenticate Git)
# - Paste an authentication token
# - <paste your token>

# Test
git push
```

## Steg 3: Test

```bash
git push
```

Hvis det fungerer, er du ferdig! 🎉

## Feilsøking

### "Authentication failed"
- Sjekk at tokenet har `Contents: Read and write` tillatelse
- Sjekk at tokenet ikke er utløpt
- Sjekk at du valgte riktig repository

### "Token not found"
- Tokenet er kun synlig én gang ved opprettelse
- Generer et nytt token hvis du mistet det

### "Permission denied"
- Sjekk at tokenet har tilgang til `jonkni/oslomaraton-trening`

## Sikkerhetstips

- ❌ **ALDRI** commit token til git
- ❌ **ALDRI** del token med andre
- ✅ Sett expiration date (90 dager anbefalt)
- ✅ Bruk separate tokens for ulike maskiner
- ✅ Revoke gamle tokens når de ikke brukes

---

**Når tokenet er satt opp kan du pushe alle tidligere commits:**

```bash
git push
```
