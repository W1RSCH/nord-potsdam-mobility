#!/usr/bin/env python3
"""Download and extract Potsdam traffic count plan ZIPs linked in the local CSV register.

No API key is required for the public, direct ZIP URLs contained in the register.
The script keeps the original ZIP/PDF files and writes normalized CSV + GeoJSON outputs.
Only the first page is OCRed when the PDF contains no extractable text; this page
contains the junction diagram and the summary counts in the examples supplied.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_REGISTER = DATA / "verkehrszahlungen_register.csv"
DEFAULT_ARCHIVES = DATA / "traffic_archives"
DEFAULT_PDFS = DATA / "traffic_pdfs"
DEFAULT_TEXT = DATA / "traffic_text"
USER_AGENT = "NordPotsdamTrafficCountResearch/1.0 (local academic project; public dataset downloads)"
ALLOWED_HOSTS = {"de.ftp.opendatasoft.com", "ftp.opendatasoft.com"}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_register(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Registerdatei nicht gefunden: {path}")
    # The Potsdam export is semicolon-separated. Sniffing also handles comma CSVs.
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(raw[:8192], delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";"
    rows = list(csv.DictReader(raw.splitlines(), dialect=dialect))
    if not rows or "Zählpläne" not in rows[0]:
        raise ValueError("CSV-Schema nicht erkannt. Erwartet wird mindestens die Spalte 'Zählpläne'.")
    return rows


def kpnr_key(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return "unknown"
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    return re.sub(r"[^0-9A-Za-z_-]", "_", s)


def download_one(row: dict[str, str], archive_dir: Path, force: bool = False) -> dict[str, Any]:
    url = (row.get("Zählpläne") or "").strip()
    kpnr = kpnr_key(row.get("KPNR"))
    name = (row.get("Name") or "").strip()
    result = {"kpnr": kpnr, "name": name, "url": url, "status": "no_archive_link", "archive": "", "bytes": 0, "error": ""}
    if not url:
        return result
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS or not parsed.path.lower().endswith(".zip"):
        result.update(status="rejected_url", error="URL liegt nicht auf dem freigegebenen öffentlichen Potsdam-FTP-Host.")
        return result

    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / f"{kpnr}.zip"
    if dest.exists() and dest.stat().st_size > 0 and not force:
        try:
            with zipfile.ZipFile(dest) as zf:
                bad = zf.testzip()
            if bad is None:
                result.update(status="cached", archive=str(dest), bytes=dest.stat().st_size)
                return result
        except (zipfile.BadZipFile, OSError):
            pass

    last_error = ""
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/zip,*/*"})
            with urllib.request.urlopen(req, timeout=90) as response:
                payload = response.read()
            from io import BytesIO
            with zipfile.ZipFile(BytesIO(payload)) as zf:
                bad = zf.testzip()
                if bad:
                    raise zipfile.BadZipFile(f"Defekte ZIP-Komponente: {bad}")
            tmp = dest.with_suffix(".zip.part")
            tmp.write_bytes(payload)
            tmp.replace(dest)
            result.update(status="downloaded", archive=str(dest), bytes=len(payload))
            return result
        except Exception as exc:  # retries for transient FTP/HTTP errors
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < 3:
                time.sleep(1.5 * attempt)
    result.update(status="failed", error=last_error)
    return result


def safe_extract_pdfs(archive: Path, kpnr: str, pdf_root: Path) -> list[Path]:
    extracted: list[Path] = []
    out_dir = pdf_root / kpnr
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            if member.is_dir() or not member.filename.lower().endswith(".pdf"):
                continue
            # Extract only the basename; never trust paths inside remote ZIPs.
            basename = Path(member.filename.replace("\\", "/")).name
            if not basename:
                continue
            target = out_dir / basename
            data = zf.read(member)
            if not target.exists() or target.stat().st_size != len(data):
                target.write_bytes(data)
            extracted.append(target)
    return extracted


def run_command(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def pdf_text(pdf: Path, text_dir: Path, enable_ocr: bool = True) -> tuple[str, bool, str]:
    text_dir.mkdir(parents=True, exist_ok=True)
    text_path = text_dir / (pdf.stem + ".txt")
    result = run_command(["pdftotext", "-layout", str(pdf), "-"], timeout=120)
    text = result.stdout if result and result.returncode == 0 else ""
    if len(text.strip()) >= 100:
        text_path.write_text(text, encoding="utf-8")
        return text, False, "pdftotext"

    if not enable_ocr:
        text_path.write_text(text, encoding="utf-8")
        return text, False, "no_text_layer"

    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        text_path.write_text(text, encoding="utf-8")
        return text, False, "ocr_tools_missing"

    with tempfile.TemporaryDirectory(prefix="potsdam_ocr_") as td:
        prefix = Path(td) / "page"
        render = run_command(["pdftoppm", "-f", "1", "-l", "1", "-r", "280", "-png", "-singlefile", str(pdf), str(prefix)], timeout=120)
        image_path = Path(str(prefix) + ".png")
        if not image_path.exists():
            text_path.write_text(text, encoding="utf-8")
            return text, False, "ocr_render_failed"
        langs_result = run_command(["tesseract", "--list-langs"], timeout=20)
        langs_text = (langs_result.stdout + langs_result.stderr) if langs_result else ""
        lang = "deu+eng" if "deu" in langs_text and "eng" in langs_text else ("deu" if "deu" in langs_text else "eng")
        ocr = run_command(["tesseract", str(image_path), "stdout", "-l", lang, "--psm", "6"], timeout=120)
        ocr_text = ocr.stdout if ocr and ocr.returncode == 0 else ""
        if len(ocr_text.strip()) > len(text.strip()):
            text = ocr_text
            text_path.write_text(text, encoding="utf-8")
            return text, True, f"tesseract-{lang}"
    text_path.write_text(text, encoding="utf-8")
    return text, False, "no_text_extracted"


def parse_int_token(token: str) -> int | None:
    token = token.strip().replace("|", "")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", token):
        return int(token.replace(".", ""))
    if token.isdigit():
        return int(token)
    return None


def parse_vehicle_rows(text: str) -> tuple[list[str], list[dict[str, Any]]]:
    direction_headers: list[str] = []
    for line in text.splitlines():
        m = re.search(r"\b(NORD)\s+(OST)\s+(SÜD|SUED)\s+(WEST|WG)\s+SUMME", line, re.I)
        if m:
            direction_headers = [m.group(1).upper(), m.group(2).upper(), m.group(3).upper().replace("SUED", "SÜD"), m.group(4).upper()]
            break
    if not direction_headers:
        direction_headers = ["Richtung_1", "Richtung_2", "Richtung_3", "Richtung_4"]

    # On the right-hand table, the vehicle category (RAD/NFZ/SV/KFZ/FZ) is
    # usually printed only on the FSp row. NSp and 6h continue on the lines below.
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    current_category: str | None = None
    for line in text.splitlines():
        clean = line.replace("|", " ").replace("[", " ").replace("]", " ").strip()
        first = re.search(r"\b(RAD|NFZ|SV|KFZ|FZ)\s+FSp\b(.*)", clean, re.I)
        if first:
            current_category = first.group(1).upper()
            period, tail = "FSp", first.group(2)
        else:
            continuation = re.match(r"^(NSp|6h)\b(.*)", clean, re.I)
            if not continuation or not current_category:
                continue
            period, tail = continuation.group(1), continuation.group(2)
        values: list[int] = []
        for token in re.findall(r"(?<![A-Za-z])\d[\d.]*", tail):
            value = parse_int_token(token)
            if value is not None:
                values.append(value)
        if len(values) < 5:
            continue
        values = values[:5]  # four approach counts plus sum; percentage omitted
        key = (current_category, period, tuple(values))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "vehicle_class": current_category,
            "period": period,
            "approaches": dict(zip(direction_headers[:4], values[:4])),
            "total": values[4],
        })
    return direction_headers, rows


def parse_pdf(pdf: Path, kpnr: str, station: str, enable_ocr: bool, text_dir: Path) -> dict[str, Any]:
    text, ocr_used, method = pdf_text(pdf, text_dir / kpnr, enable_ocr)
    normalized = re.sub(r"\s+", " ", text)
    survey_date = None
    date_match = re.search(r"DATUM\s*:.*?(\d{2}\.\d{2}\.\d{4})", normalized, re.I)
    if date_match:
        try:
            survey_date = dt.datetime.strptime(date_match.group(1), "%d.%m.%Y").date().isoformat()
        except ValueError:
            pass

    morning = morning_time = afternoon = afternoon_time = six_hour = None
    start = re.search(r"SUMME\s+Zufahrten", normalized, re.I)
    if start:
        summary = normalized[start.start():start.start() + 750]
        nsp_match = re.search(r"\(?NSp\)?\s*:?.{0,220}?([\d.]{1,10})\s*K[FZ]{2}/h\s*(\d{1,2}:\d{2})", summary, re.I)
        if nsp_match:
            before_nsp = summary[:nsp_match.start()]
            fsp_match = re.search(r"([\d.]{1,10})\s*K[FZ]{2}/h\s*(\d{1,2}:\d{2})", before_nsp, re.I)
            if fsp_match:
                morning = parse_int_token(fsp_match.group(1))
                morning_time = fsp_match.group(2)
            afternoon = parse_int_token(nsp_match.group(1))
            afternoon_time = nsp_match.group(2)
        six_match = re.search(r"\b6h\s*:?\s*([\d.]{1,10})\s*K[FZ]{2}\b", summary, re.I)
        if six_match:
            six_hour = parse_int_token(six_match.group(1))

    # Keep table extraction separate from the headline totals; table rows can be OCR-noisy.
    directions, vehicle_rows = parse_vehicle_rows(text)
    if ocr_used:
        vehicle_rows = []  # OCR can misread individual table cells; headline totals are much more stable.
    report_dates = re.findall(r"\b\d{2}\.\d{2}\.\d{4}\b", normalized)
    return {
        "kpnr": kpnr,
        "station": station,
        "survey_date": survey_date,
        "morning_peak_kfz_h": morning,
        "morning_peak_time": morning_time,
        "afternoon_peak_kfz_h": afternoon,
        "afternoon_peak_time": afternoon_time,
        "six_hour_kfz": six_hour,
        "extraction_method": method,
        "ocr_used": ocr_used,
        "parse_status": "ok" if any(v is not None for v in (morning, afternoon, six_hour)) else "review_required",
        "pdf_file": pdf.name,
        "pdf_path": str(pdf.relative_to(ROOT)),
        "report_dates": report_dates[:4],
        "direction_headers": directions,
        "vehicle_rows": vehicle_rows,
        "text_preview": normalized[:700],
    }


def parse_geo_point(value: str) -> list[float] | None:
    if not value:
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?", value)
    if len(nums) < 2:
        return None
    lat, lon = float(nums[0]), float(nums[1])
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return [lon, lat]
    return None


def build_geojson(rows: list[dict[str, Any]], register: list[dict[str, str]]) -> dict[str, Any]:
    locations: dict[str, dict[str, Any]] = {}
    for row in register:
        key = kpnr_key(row.get("KPNR"))
        locations[key] = {"name": (row.get("Name") or "").strip(), "coordinates": parse_geo_point(row.get("Geo Point") or ""), "odp": row.get("ODP") or "", "zahlplan_url": row.get("Zählpläne") or ""}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        grouped.setdefault(r["kpnr"], []).append(r)

    features = []
    for kpnr, measurements in grouped.items():
        loc = locations.get(kpnr, {})
        coords = loc.get("coordinates")
        if not coords:
            continue
        measurements.sort(key=lambda x: x.get("survey_date") or "", reverse=True)
        latest = measurements[0]
        compact = []
        for m in measurements:
            compact.append({
                "survey_date": m.get("survey_date"),
                "morning_peak_kfz_h": m.get("morning_peak_kfz_h"),
                "morning_peak_time": m.get("morning_peak_time"),
                "afternoon_peak_kfz_h": m.get("afternoon_peak_kfz_h"),
                "afternoon_peak_time": m.get("afternoon_peak_time"),
                "six_hour_kfz": m.get("six_hour_kfz"),
                "extraction_method": m.get("extraction_method"),
                "ocr_used": m.get("ocr_used"),
                "parse_status": m.get("parse_status"),
                "pdf_file": m.get("pdf_file"),
                "pdf_path": m.get("pdf_path"),
                "vehicle_rows": m.get("vehicle_rows", []),
                "direction_headers": m.get("direction_headers", []),
            })
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": coords},
            "properties": {
                "kpnr": kpnr,
                "name": loc.get("name") or latest.get("station") or kpnr,
                "odp": loc.get("odp", ""),
                "zahlplan_url": loc.get("zahlplan_url", ""),
                "measurement_count": len(compact),
                "latest_survey_date": latest.get("survey_date"),
                "latest_morning_peak_kfz_h": latest.get("morning_peak_kfz_h"),
                "latest_afternoon_peak_kfz_h": latest.get("afternoon_peak_kfz_h"),
                "latest_six_hour_kfz": latest.get("six_hour_kfz"),
                "measurements": compact,
                "data_note": "Werte aus veröffentlichten Stromlinienplan-PDFs; OCR-Werte müssen bei ocr_used=true stichprobenartig geprüft werden.",
            },
        })
    return {"type": "FeatureCollection", "name": "Potsdam Verkehrszählungen - ausgewertete Zählpläne", "features": features}


def main() -> int:
    parser = argparse.ArgumentParser(description="Potsdamer Zählplan-ZIPs automatisch herunterladen und PDF-Zählwerte extrahieren.")
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER, help="Semikolon-CSV aus Open Data Potsdam")
    parser.add_argument("--archives", type=Path, default=DEFAULT_ARCHIVES, help="Ordner für ZIP-Archive")
    parser.add_argument("--pdfs", type=Path, default=DEFAULT_PDFS, help="Ordner für extrahierte PDF-Dateien")
    parser.add_argument("--text", type=Path, default=DEFAULT_TEXT, help="Ordner für extrahierte PDF-/OCR-Texte")
    parser.add_argument("--workers", type=int, default=3, help="Parallele Downloads, empfohlen 2-4")
    parser.add_argument("--force", action="store_true", help="Vorhandene ZIP-Dateien erneut herunterladen")
    parser.add_argument("--no-download", action="store_true", help="Nur bereits vorhandene ZIP-Dateien auswerten")
    parser.add_argument("--no-ocr", action="store_true", help="Keine OCR für gescannte PDF-Seiten ausführen")
    args = parser.parse_args()

    rows = read_register(args.register)
    linked = [r for r in rows if (r.get("Zählpläne") or "").strip()]
    print(f"Register: {len(rows)} Zählstellen · {len(linked)} direkte ZIP-Links · {len(rows)-len(linked)} ohne ZIP-Link")
    args.archives.mkdir(parents=True, exist_ok=True)

    download_log: list[dict[str, Any]] = []
    if args.no_download:
        for row in linked:
            kpnr = kpnr_key(row.get("KPNR"))
            p = args.archives / f"{kpnr}.zip"
            download_log.append({"kpnr": kpnr, "name": row.get("Name", ""), "url": row.get("Zählpläne", ""), "status": "cached" if p.exists() else "missing", "archive": str(p) if p.exists() else "", "bytes": p.stat().st_size if p.exists() else 0, "error": ""})
    else:
        print(f"Lade fehlende Archive mit {max(1,args.workers)} parallelen Verbindungen …")
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 6))) as pool:
            futures = [pool.submit(download_one, row, args.archives, args.force) for row in linked]
            for i, fut in enumerate(as_completed(futures), 1):
                res = fut.result()
                download_log.append(res)
                if i % 10 == 0 or i == len(futures):
                    print(f"  Downloadstatus: {i}/{len(futures)}")
    write_csv(ROOT / "data" / "traffic_download_log.csv", download_log, ["kpnr", "name", "url", "status", "archive", "bytes", "error"])

    all_measurements: list[dict[str, Any]] = []
    parse_log: list[dict[str, Any]] = []
    for row in rows:
        kpnr = kpnr_key(row.get("KPNR"))
        archive = args.archives / f"{kpnr}.zip"
        if not archive.exists():
            continue
        station = (row.get("Name") or "").strip()
        try:
            pdfs = safe_extract_pdfs(archive, kpnr, args.pdfs)
        except Exception as exc:
            parse_log.append({"kpnr": kpnr, "station": station, "pdf": "", "status": "archive_error", "detail": str(exc)})
            continue
        for pdf in pdfs:
            try:
                parsed = parse_pdf(pdf, kpnr, station, not args.no_ocr, args.text)
                all_measurements.append(parsed)
                parse_log.append({"kpnr": kpnr, "station": station, "pdf": pdf.name, "status": parsed["parse_status"], "detail": parsed["extraction_method"]})
            except Exception as exc:
                parse_log.append({"kpnr": kpnr, "station": station, "pdf": pdf.name, "status": "parse_error", "detail": str(exc)})

    csv_rows = []
    for r in all_measurements:
        csv_rows.append({**{k: r.get(k) for k in ["kpnr", "station", "survey_date", "morning_peak_kfz_h", "morning_peak_time", "afternoon_peak_kfz_h", "afternoon_peak_time", "six_hour_kfz", "extraction_method", "ocr_used", "parse_status", "pdf_file", "pdf_path"]}, "vehicle_rows_json": json.dumps(r.get("vehicle_rows", []), ensure_ascii=False)})
    write_csv(DATA / "traffic_measurements.csv", csv_rows, ["kpnr", "station", "survey_date", "morning_peak_kfz_h", "morning_peak_time", "afternoon_peak_kfz_h", "afternoon_peak_time", "six_hour_kfz", "extraction_method", "ocr_used", "parse_status", "pdf_file", "pdf_path", "vehicle_rows_json"])
    write_csv(DATA / "traffic_parse_log.csv", parse_log, ["kpnr", "station", "pdf", "status", "detail"])
    geojson = build_geojson(all_measurements, rows)
    (DATA / "verkehrszahlungen_messwerte.geojson").write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")

    good = sum(1 for x in all_measurements if x["parse_status"] == "ok")
    ocr = sum(1 for x in all_measurements if x["ocr_used"])
    downloaded = sum(1 for x in download_log if x["status"] == "downloaded")
    cached = sum(1 for x in download_log if x["status"] == "cached")
    failed = sum(1 for x in download_log if x["status"] in {"failed", "rejected_url"})
    print("\nFertig.")
    print(f"ZIPs neu geladen: {downloaded} · bereits vorhanden: {cached} · fehlgeschlagen: {failed}")
    print(f"PDF-Berichte: {len(all_measurements)} · davon mit extrahierbaren Kennwerten: {good} · OCR genutzt: {ocr}")
    print("Ergebnisse:")
    print(f"  {DATA / 'traffic_measurements.csv'}")
    print(f"  {DATA / 'verkehrszahlungen_messwerte.geojson'}")
    print(f"  {DATA / 'traffic_download_log.csv'}")
    print(f"  {DATA / 'traffic_parse_log.csv'}")
    print("Hinweis: OCR- und Parsergebnisse bitte anhand der verlinkten Original-PDFs stichprobenartig prüfen.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Abgebrochen.", file=sys.stderr)
        raise SystemExit(130)
