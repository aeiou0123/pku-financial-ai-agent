"""Opt-in download of four public PDFs, hash-checked; no model or database call."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import urllib.request
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
SOURCES = [
    ('green_2024_annual', '2025-04-30', 'https://static.cninfo.com.cn/finalpage/2025-04-30/1223423684.PDF',
     '403637cba865c5aa1f39965d9e8b5a2df503314f6a6ce189009ed8748717fb48'),
    ('green_2024_preliminary', '2025-02-28', 'https://big5.sse.com.cn/site/cht/www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2025-02-28/688017_20250228_H5HD.pdf',
     '63afd9de638111217906302512c96e892d03bd3c6ab90258953031b2bfd1d3dc'),
    ('green_project_delay', '2026-07-10', 'https://static.cninfo.com.cn/finalpage/2026-07-10/1225418045.PDF',
     '4a2e10d794c5fa4fbee824e90f936dcd86e30958b973d95b1118d495a083414d'),
    ('green_2025_correction', '2026-07-10', 'https://static.cninfo.com.cn/finalpage/2026-07-10/1225418035.PDF',
     'fc4bc12996b625fb7ebf5a9f9094a04b5453ab086f0ad0533d4b895d76fb6260'),
]


def main():
    destination = ROOT / 'work' / 'public_case_originals_20261011'
    destination.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name, day, url, expected in SOURCES:
        path = destination / (name + '.pdf')
        existing = path.exists()
        status = None
        if existing:
            raw = path.read_bytes()
        else:
            request = urllib.request.Request(url, headers={'User-Agent': 'Claim2Value-Source-Verification/0.1'})
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                raw = response.read(20 * 1024 * 1024 + 1)
        if len(raw) > 20 * 1024 * 1024 or not raw.startswith(b'%PDF-'):
            raise ValueError(name + ': response is not a supported PDF; nothing overwritten')
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(name + ': bytes differ from verified original; nothing overwritten')
        reader = PdfReader(io.BytesIO(raw))
        if '688017' not in ''.join(page.extract_text() or '' for page in reader.pages):
            raise ValueError(name + ': company code missing')
        if not existing:
            path.write_bytes(raw)
        receipts.append({'name': path.name, 'url': url, 'published_at': day, 'sha256': actual,
                         'bytes': len(raw), 'pages': len(reader.pages), 'http_status': status,
                         'reused_existing_checked_file': existing,
                         'checked_at': datetime.now(timezone.utc).isoformat()})
    receipt_path = destination / ('receipt_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
    receipt_path.write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(destination))
    print(str(receipt_path))


if __name__ == '__main__':
    main()
