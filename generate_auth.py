#!/usr/bin/env python3
import urllib.parse

code_verifier = "yG-X9jYJb-pz6FAePTVJE5fSXXDQ0lMaSFEMCXn-lHNf-1ir578y6O4rB99K5Ps6q4R6Wa10a_46JmkOG4B8wQ"
code_challenge = "YAyIUec7deSwz83a4KCpiDMj80mI-mWK3sfFSSj49P0"
client_id = "110758"
redirect_uri = "http://localhost:9123/callback"

params = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
    "scope": "auth",
}

auth_url = (
    "https://public-api.wordpress.com/oauth2-1/authorize?"
    + urllib.parse.urlencode(params)
)

print("AUTH_URL:")
print(auth_url)
print()
print("CODE_VERIFIER (save this):")
print(code_verifier)
