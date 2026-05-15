"""Lightweight OWASP ZAP client abstraction.

This implementation is intentionally deterministic for local development/tests.
"""
from uuid import uuid4


class ZapClient:
    def __init__(self, api_url: str, api_key: str = "", timeout_seconds: int = 120):
        self.api_url = api_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def spider_scan(self, target_url: str, depth: int = 1):
        return {"scan_id": f"spider-{uuid4().hex[:12]}", "target": target_url, "depth": depth}

    def active_scan(self, target_url: str, attack_strength: str = "medium"):
        return {
            "scan_id": f"active-{uuid4().hex[:12]}",
            "target": target_url,
            "attack_strength": attack_strength,
        }

    def api_scan(self, target_url: str):
        return {"scan_id": f"api-{uuid4().hex[:12]}", "target": target_url}

    def get_alerts(self, target_url: str):
        return {
            "alerts": [
                {
                    "name": "X-Frame-Options Header Not Set",
                    "risk": "Medium",
                    "url": target_url,
                    "owasp": "A05:2021-Security Misconfiguration",
                },
                {
                    "name": "Content Security Policy (CSP) Header Not Set",
                    "risk": "Low",
                    "url": target_url,
                    "owasp": "A05:2021-Security Misconfiguration",
                },
            ]
        }


def parse_alerts(raw_results: dict):
    alerts = raw_results.get("alerts", [])
    parsed = []
    for alert in alerts:
        parsed.append(
            {
                "name": alert.get("name", ""),
                "risk": alert.get("risk", "Info"),
                "url": alert.get("url", ""),
                "owasp": alert.get("owasp", "Unknown"),
            }
        )
    return parsed
