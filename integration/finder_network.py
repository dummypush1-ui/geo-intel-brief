"""Fixed original Finder fetch origins; explicit gated preview opt-in only.

This module contains no requests, proxy forwarding, credential handling or
polling. Direct-provider origins preserve the original optional personal-key
mode. Do not accept request-supplied hosts or wildcard origins.
"""
FINDER_CONNECT_ORIGINS=(
 'https://hsn-ai-proxy.onrender.com',
 'https://api.frankfurter.dev',
 'https://api.open-meteo.com',
 'https://marine-api.open-meteo.com',
 'https://generativelanguage.googleapis.com',
 'https://api.groq.com',
 'https://api.mistral.ai',
)

def connect_sources(enabled=False):
 if type(enabled) is not bool:raise ValueError('Explicit boolean network gate required')
 return "'self'"+(' '+' '.join(FINDER_CONNECT_ORIGINS) if enabled else '')

def from_env(environ):
 value=environ.get('FINDER_NETWORK_PREVIEW_ENABLED','false')
 if value not in ('true','false'):raise ValueError('Exact true/false Finder network flag required')
 return value=='true'

def manual_ships_shell(shell):
 """Port original ship UI, but suppress three retry/refresh timer sites in private preview.
 Original files remain preserved. No network permission implies polling permission.
 """
 retry="if (V.ships) shipsTimer = setTimeout(() => { shipsLoad(); }, 15000);"
 refresh="if (V.ships) shipsTimer = setTimeout(shipsLoad, 60000);"
 if shell.count(retry)!=2 or shell.count(refresh)!=2:raise ValueError('Finder ships timer seam changed')
 return shell.replace(retry,'/* Preview manual retry only: polling disabled. */').replace(refresh,'/* Preview manual refresh only: polling disabled. */').replace(' - auto-refreshes every 60 seconds',' - manual refresh only in private preview')
