"""Observe the four lab findings against the fixed loopback target only."""

import argparse
import http.client
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo

TARGET = "http://127.0.0.1:8080"
ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    """Read stable page markers, form tokens, and local script references."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.csrf = None
        self.markers = {}
        self.item_ids = []
        self.scripts = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "meta" and attrs.get("name") == "csrf-token":
            self.csrf = attrs.get("content")
        if tag == "input" and attrs.get("name") == "csrf_token":
            self.csrf = attrs.get("value")
        if tag == "input" and attrs.get("name") == "item_id":
            self.item_ids.append(attrs.get("value"))
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])
        for name, value in attributes:
            if name.startswith("data-"):
                self.markers.setdefault(name, []).append(value)

    def marker(self, name):
        values = self.markers.get(name, [])
        return values[0] if values else None


@dataclass
class Response:
    status: int
    body: str
    headers: dict

    def page(self):
        return Page(self.body)


class LocalClient:
    """No environment proxies; every connection and redirect stays on loopback:8080."""

    def __init__(self, target=TARGET):
        if target != TARGET:
            raise ValueError(f"Only {TARGET} is permitted.")
        self.cookies = {}

    @staticmethod
    def local_path(value):
        parts = urlsplit(value)
        if parts.scheme or parts.netloc:
            if parts.scheme != "http" or parts.netloc != "127.0.0.1:8080":
                raise ValueError("Refused an off-origin URL or redirect.")
        if not parts.path.startswith("/"):
            raise ValueError("Only absolute local paths are permitted.")
        return parts.path + ("?" + parts.query if parts.query else "")

    def request(self, method, path, data=None):
        for _ in range(6):
            path = self.local_path(path)
            body = urlencode(data).encode("ascii") if data is not None else None
            headers = {
                "Cookie": "; ".join(f"{name}={value}" for name, value in self.cookies.items())
            }
            if body is not None:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            connection = http.client.HTTPConnection("127.0.0.1", 8080, timeout=10)
            try:
                connection.request(method, path, body=body, headers=headers)
                response = connection.getresponse()
                result = Response(
                    response.status,
                    response.read().decode("utf-8"),
                    {name.lower(): value for name, value in response.getheaders()},
                )
                for header in response.headers.get_all("Set-Cookie", []):
                    for name, cookie in SimpleCookie(header).items():
                        if cookie["max-age"] == "0":
                            self.cookies.pop(name, None)
                        else:
                            self.cookies[name] = cookie.coded_value
            finally:
                connection.close()
            if result.status not in (301, 302, 303, 307, 308):
                return result
            path = self.local_path(result.headers.get("location", ""))
            if result.status == 303 or (result.status in (301, 302) and method == "POST"):
                method, data = "GET", None
        raise RuntimeError("Too many local redirects.")

    def get(self, path):
        return self.request("GET", path)

    def form_post(self, path, data, form_path):
        form = self.get(form_path)
        token = form.page().csrf
        if form.status != 200 or not token:
            raise RuntimeError(f"Could not obtain a valid form at {form_path}.")
        return self.request("POST", path, {**data, "csrf_token": token})

    def login(self, username, password, admin=False):
        path = "/admin/login" if admin else "/login"
        result = self.form_post(path, {"username": username, "password": password}, path)
        if result.status != 200 or result.page().marker("data-authenticated") != "true":
            raise RuntimeError("Demo login did not complete.")
        return result


def save_evidence(name, lines):
    directory = ROOT / "evidence" / "baseline"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = directory / f"{name}-{stamp}.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_with_log(name, operation, target=TARGET):
    lines = []

    def emit(line):
        lines.append(line)
        print(line)

    stamp = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")
    emit(f"SecureShop {name} | {TARGET} | {stamp} Asia/Kolkata")
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        emit(f"Source commit={revision}; working_tree={'modified' if dirty else 'clean'}")
    except (OSError, subprocess.CalledProcessError):
        emit("Source commit unavailable (not a Git checkout).")
    status = 0
    try:
        operation(LocalClient(target), emit)
    except (OSError, ValueError, RuntimeError, AssertionError) as error:
        emit(f"FAIL: {error}")
        status = 1
    path = save_evidence(name, lines)
    print(f"Saved {path.relative_to(ROOT)}")
    return status


def replay(client, emit):
    client.login("customer_a", "CustomerA!2026")
    foreign = client.get("/orders/4")
    returned = foreign.page().marker("data-order-owner") == "customer_b"
    emit(
        f"A01 /orders/4: HTTP {foreign.status}; foreign_order_data_returned={str(returned).lower()}"
    )
    queries = (
        ("normal", "notebook"),
        ("true", "notebook%' OR '1'='1' -- "),
        ("false", "notebook%' AND '1'='2' -- "),
    )
    counts = {}
    for label, query in queries:
        result = client.get("/search?" + urlencode({"q": query}))
        marker = result.page().marker("data-result-count")
        counts[label] = int(marker) if marker is not None else None
        emit(f"A03 {label} comparison: HTTP {result.status}; result_count={counts[label]}")
    emit(f"A03 boolean_pair_counts_differ={str(counts['true'] != counts['false']).lower()}")
    for path in ("/", "/products"):
        result = client.get(path)
        emit(
            f"A05 {path}: HTTP {result.status}; X-Frame-Options={result.headers.get('x-frame-options', '(absent)')}; "
            f"Content-Security-Policy={result.headers.get('content-security-policy', '(absent)')}"
        )
    catalogue = client.get("/products")
    jquery = [
        path
        for path in catalogue.page().scripts
        if path.startswith("/static/vendor/jquery/jquery-")
    ]
    emit(f"A06 catalogue jQuery reference: {', '.join(jquery) if jquery else '(not found)'}")
    emit(
        "A06 observation records the loaded library; browser exploitation was not tested or claimed."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target", default=TARGET, help="Must equal http://127.0.0.1:8080 exactly."
    )
    args = parser.parse_args()
    if args.target != TARGET:
        parser.error(f"Only {TARGET} is permitted.")
    sys.exit(run_with_log("replay", replay, args.target))
