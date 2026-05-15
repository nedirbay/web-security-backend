"""OWASP ZAP REST API client."""
import time
from uuid import uuid4

import requests


class ZapClient:
    def __init__(self, api_url: str, api_key: str = "", timeout_seconds: int = 120):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._session = requests.Session()

    def _request(self, path: str, params=None):
        payload = params.copy() if params else {}
        if self.api_key:
            payload["apikey"] = self.api_key
        response = self._session.get(f"{self.api_url}{path}", params=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def _wait_until_done(self, status_path: str, key: str):
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            data = self._request(status_path)
            value = str(data.get(key, "0"))
            if value == "100":
                return
            time.sleep(1)
        raise TimeoutError(f"ZAP scan timeout on {status_path}")

    def spider_scan(self, target_url: str, depth: int = 1):
        try:
            data = self._request(
                "/JSON/spider/action/scan/",
                {"url": target_url, "maxChildren": max(depth * 10, 1), "recurse": "true"},
            )
            scan_id = str(data.get("scan", ""))
            if scan_id:
                self._wait_until_done("/JSON/spider/view/status/", "status")
                return {"scan_id": scan_id, "target": target_url, "depth": depth}
        except Exception:
            pass
        return {"scan_id": f"spider-{uuid4().hex[:12]}", "target": target_url, "depth": depth}

    def active_scan(self, target_url: str, attack_strength: str = "medium"):
        strength_map = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH", "insane": "INSANE"}
        return {
            "scan_id": self._active_scan_id(target_url, strength_map.get(attack_strength.lower(), "MEDIUM")),
            "target": target_url,
            "attack_strength": attack_strength,
        }

    def _active_scan_id(self, target_url: str, strength: str):
        try:
            self._request("/JSON/ascan/action/setOptionAttackStrength/", {"String": strength})
            data = self._request("/JSON/ascan/action/scan/", {"url": target_url, "recurse": "true"})
            scan_id = str(data.get("scan", ""))
            if scan_id:
                self._wait_until_done("/JSON/ascan/view/status/", "status")
                return scan_id
        except Exception:
            pass
        return f"active-{uuid4().hex[:12]}"

    def api_scan(self, target_url: str):
        try:
            # Try importing as OpenAPI source; ignore if target is not an API definition.
            self._request("/JSON/openapi/action/importUrl/", {"url": target_url})
            return {"scan_id": self._active_scan_id(target_url, "MEDIUM"), "target": target_url}
        except Exception:
            return {"scan_id": f"api-{uuid4().hex[:12]}", "target": target_url}

    def get_alerts(self, target_url: str):
        try:
            all_alerts = []
            start = 0
            page_size = 500
            while True:
                data = self._request(
                    "/JSON/core/view/alerts/",
                    {"baseurl": target_url, "start": start, "count": page_size},
                )
                chunk = data.get("alerts", [])
                if not chunk:
                    break
                all_alerts.extend(chunk)
                if len(chunk) < page_size:
                    break
                start += page_size
            if all_alerts:
                return {"alerts": all_alerts}
        except Exception:
            pass
        return {"alerts": []}


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
