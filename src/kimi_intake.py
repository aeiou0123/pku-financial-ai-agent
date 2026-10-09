"""Prepare supplied Kimi candidates for offline review, without certifying them."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

CLAIMS = {
    'GH_007': '绿的谐波LHS-32谐波减速器额定扭矩51-130 Nm，重量2.5 kg',
    'BK_003': '步科股份第四代FMK无框力矩电机同尺寸扭矩输出提升约22%',
    'SH_002': '双环传动SHPR-20E RV减速器额定扭矩110-231 Nm，重量4.7 kg',
    'BK_001': '步科股份无框电机累计出货超5万台，在协作机器人行业位居国产TOP2',
}
STATUSES = {'not_started', 'candidate_link', 'read_original', 'not_found', 'conflict'}
MANIFEST_FIELDS = ['file_name', 'stock_code', 'company', 'document_type',
                   'source_database', 'source_url', 'published_at', 'downloaded_at',
                   'period', 'unit', 'currency', 'license_notes', 'intended_use', 'sha256']


def _string(row, key):
    value = row.get(key, '')
    if not isinstance(value, str):
        raise ValueError(f'{key}须为字符串，未知值留空')
    return value.strip()


def prepare_candidates(input_path, source_root, output_dir):
    """Check local file provenance and emit candidates; no network or bank writes."""
    raw = Path(input_path).read_bytes()
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError('候选文件最多5MB')
    data = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('须使用schema_version=1的回传模板')
    rows = data.get('candidates')
    if not isinstance(rows, list) or len(rows) != len(CLAIMS):
        raise ValueError('第一轮须包含四条声明，每条一条主要证据；其他证据放补充文件')
    root = Path(source_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('source_root须为原件目录')
    seen, batch, manifests, statuses = set(), [], {}, []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('每条候选须为对象')
        cid = _string(row, 'claim_id')
        if cid not in CLAIMS or cid in seen:
            raise ValueError('claim_id未知或重复')
        seen.add(cid)
        if _string(row, 'claim_text') != CLAIMS[cid]:
            raise ValueError(f'{cid}不得改写原始待核声明')
        status = _string(row, 'status')
        if status not in STATUSES:
            raise ValueError(f'{cid}的status不在允许值中')
        url = _string(row, 'source_url')
        if any(ord(c) < 32 or ord(c) == 127 for c in url):
            raise ValueError(f'{cid}来源链接不能含换行或控制字符')
        parsed = urlsplit(url)
        if url and (parsed.scheme not in {'http', 'https'} or not parsed.netloc
                    or parsed.username or parsed.password):
            raise ValueError(f'{cid}须提供不含凭据的HTTP(S)来源链接')
        if status == 'candidate_link' and not url:
            raise ValueError(f'{cid}仅找到链接时须填写链接')
        if status == 'not_found' and not _string(row, 'search_scope'):
            raise ValueError(f'{cid}未找到时须说明实际检索范围')
        included = False
        if status == 'read_original':
            name = _string(row, 'file_name')
            relative = Path(name)
            if not name or relative.is_absolute() or '..' in relative.parts:
                raise ValueError(f'{cid}原件须为source_root下的相对路径')
            file = (root / relative).resolve(strict=True)
            if not file.is_relative_to(root) or not file.is_file():
                raise ValueError(f'{cid}原件不得越出source_root')
            content = file.read_bytes()
            if file.suffix.lower() != '.pdf' or not content.startswith(b'%PDF-'):
                raise ValueError(f'{cid}本接入器只接受本地PDF；网页原件另交待人工核对')
            digest = hashlib.sha256(content).hexdigest()
            if _string(row, 'sha256').lower() != digest:
                raise ValueError(f'{cid}原件SHA-256缺失或不一致；由有文件工具的一方计算')
            page = row.get('pdf_page')
            if isinstance(page, bool) or not isinstance(page, int) or page < 1:
                raise ValueError(f'{cid}pdf_page须为从1开始的整数')
            excerpt = _string(row, 'excerpt')
            if not url or not _string(row, 'title') or not excerpt:
                raise ValueError(f'{cid}已读取原文须包含标题、来源链接和逐字摘录')
            if len(excerpt) > 25000:
                raise ValueError(f'{cid}请只提供相关原文，不超过25000字符')
            locator = f'{name} | PDF文件页{page} | 印刷页{_string(row, "printed_page")} | SHA256 {digest}'
            batch.append({'case_id': cid, 'claim': CLAIMS[cid], 'source': excerpt,
                          'source_url': url, 'source_locator': locator})
            m = {key: _string(row, key) for key in MANIFEST_FIELDS}
            m.update(file_name=name, sha256=digest, intended_use='候选证据核查；未认证原文或结论')
            manifests[(name, digest)] = m
            included = True
        statuses.append({'claim_id': cid, 'supplied_status': status,
                         'eligible_for_text_review': included,
                         'human_review': 'pending'})
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'candidate_snapshot.json').write_bytes(raw)
    for name, fields, records in [
        ('evidence_batch.csv', ['case_id', 'claim', 'source', 'source_url', 'source_locator'], batch),
        ('source_manifest.csv', MANIFEST_FIELDS, list(manifests.values())),
        ('manual_review.csv', ['claim_id', 'supplied_status', 'eligible_for_text_review', 'human_review'], statuses),
    ]:
        with (out / name).open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    receipt = {'scope': 'LOCAL_PDF_BYTES_AND_CANDIDATE_FORMAT_ONLY_NOT_SOURCE_AUTHENTICATION',
               'candidate_sha256': hashlib.sha256(raw).hexdigest(),
               'candidate_count': len(rows), 'text_review_count': len(batch),
               'external_api_calls': 0, 'claim_bank_modified': False,
               'requires_human_review': True,
               'unchecked': ['PDF是否可打开、页数和页码是否正确', '摘录是否确为原文及表格列',
                             '文档发布主体、版本、日期和引用真实性', '性能可比性、排名和财务因果关系'],
               'records': statuses}
    (out / 'intake_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt
