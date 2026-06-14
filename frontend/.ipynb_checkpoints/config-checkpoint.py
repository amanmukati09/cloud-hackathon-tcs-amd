# frontend/config.py

import os
from css import custom_css, saas_theme

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

APP_TITLE = "AegisAI - SRE Incident Management"
APP_FAVICON = "🛡️"

PWA_HEAD = """
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="AegisAI">
<meta name="theme-color" content="#0f172a">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="manifest" href="data:application/json;base64,ewogICAgIm5hbWUiOiAiQWVnaXNBSSAtIFNSRSBQbGF0Zm9ybSIsCiAgICAic2hvcnRfbmFtZSI6ICJBZWdpc0FJIiwKICAgICJkZXNjcmlwdGlvbiI6ICJBSS1Qb3dlcmVkIEluY2lkZW50IE1hbmFnZW1lbnQgUGxhdGZvcm0iLAogICAgInN0YXJ0X3VybCI6ICIvIiwKICAgICJkaXNwbGF5IjogInN0YW5kYWxvbmUiLAogICAgImJhY2tncm91bmRfY29sb3IiOiAiIzBmMTcyYSIsCiAgICAidGhlbWVfY29sb3IiOiAiIzM4YmRmOCIsCiAgICAiaWNvbnMiOiBbCiAgICAgICAgewogICAgICAgICAgICAic3JjIjogImRhdGE6aW1hZ2Uvc3ZnK3htbDtiYXNlNjQsUEhOMlp5QjRiV3h1Y3owaWFIUjBjRG92TDNkM2R5NTNNeTV2Y21jdk1qQXZNUzloWkdkc2VYTXZabkFpSUhodGJHNXpQU0phWldOdmJTSWdkRzhnYzJoaGJtNWxiRDBpYVhOdmJpSWdaVzU0UFNJalAzc3ZMMjV6SWlCbWFXeHNQU0owY25WemRDMWphR0Z1YjJVaVB6NEtQR1JwYldVZ2JHOWpZV3hQYm1GMGFXOXVQVHd2WkdsdFpUNDhMM04wYVhScFpEND0iLAogICAgICAgICAgICAic2l6ZXMiOiAiMTkyeDE5MiIsCiAgICAgICAgICAgICJ0eXBlIjogImltYWdlL3N2Zyt4bWwiCiAgICAgICAgfQogICAgXQp9">
"""

SEVERITY_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH": "#ef4444", 
    "MEDIUM": "#f59e0b",
    "LOW": "#10b981",
    "UNKNOWN": "#6b7280"
}

THEME = saas_theme
CSS = custom_css