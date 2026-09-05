"""
evidence_ledger.py — Claim2Value 证据账本
==========================================

管理证据生命周期：来源等级分级、证据指纹、交叉验证状态。
为 claim_verifier 提供可信度打分基础。

设计原则：
  - 来源等级是客观的（年报 > 研报 > 新闻 > 传闻），不依赖 LLM 判断
  - 证据指纹用于去重和溯源
  - 交叉验证状态记录多条证据是否一致

用法：
  from src.evidence_ledger import EvidenceLedger, Evidence, EvidenceLevel

  ledger = EvidenceLedger()
  ledger.add(Evidence(
      source_text="国信证券研报：2024年谐波减速器销量24.65万台",
      source_type=EvidenceLevel.ANALYST_REPORT,
      source_url="https://...",
  ))
  score = ledger.trust_score()  # 0.0-1.0
"""

from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple


class EvidenceLevel(str, Enum):
    """证据来源等级（从高到低）"""
    OFFICIAL_FILING = "official_filing"      # 年报/公告/招股书
    DATASHEET = "datasheet"                  # 官方产品手册
    PATENT = "patent"                        # 专利
    ANALYST_REPORT = "analyst_report"        # 券商研报
    INDUSTRY_REPORT = "industry_report"      # 行业报告
    NEWS_MEDIA = "news_media"                # 新闻报道
    RUMOR = "rumor"                          # 市场传闻/网传消息
    UNKNOWN = "unknown"                      # 未分类


# 来源等级 → 基础可信度分
LEVEL_TRUST = {
    EvidenceLevel.OFFICIAL_FILING: 0.95,
    EvidenceLevel.DATASHEET: 0.90,
    EvidenceLevel.PATENT: 0.85,
    EvidenceLevel.ANALYST_REPORT: 0.75,
    EvidenceLevel.INDUSTRY_REPORT: 0.70,
    EvidenceLevel.NEWS_MEDIA: 0.50,
    EvidenceLevel.RUMOR: 0.20,
    EvidenceLevel.UNKNOWN: 0.30,
}

# 来源关键词 → 证据等级（用于自动分类）
SOURCE_KEYWORDS: List[Tuple[str, EvidenceLevel]] = [
    # 从高到低匹配，先命中先用
    ("年报", EvidenceLevel.OFFICIAL_FILING),
    ("招股书", EvidenceLevel.OFFICIAL_FILING),
    ("半年报", EvidenceLevel.OFFICIAL_FILING),
    ("公告", EvidenceLevel.OFFICIAL_FILING),
    ("季报", EvidenceLevel.OFFICIAL_FILING),
    ("datasheet", EvidenceLevel.DATASHEET),
    ("产品手册", EvidenceLevel.DATASHEET),
    ("技术规格书", EvidenceLevel.DATASHEET),
    ("专利", EvidenceLevel.PATENT),
    ("研报", EvidenceLevel.ANALYST_REPORT),
    ("证券", EvidenceLevel.ANALYST_REPORT),
    ("券商", EvidenceLevel.ANALYST_REPORT),
    ("行业报告", EvidenceLevel.INDUSTRY_REPORT),
    ("GGII", EvidenceLevel.INDUSTRY_REPORT),
    ("蓝皮书", EvidenceLevel.INDUSTRY_REPORT),
    ("新闻", EvidenceLevel.NEWS_MEDIA),
    ("报道", EvidenceLevel.NEWS_MEDIA),
    ("网传", EvidenceLevel.RUMOR),
    ("市场传闻", EvidenceLevel.RUMOR),
    ("股吧", EvidenceLevel.RUMOR),
    ("自媒体", EvidenceLevel.RUMOR),
    ("爆料", EvidenceLevel.RUMOR),
    ("未经证实", EvidenceLevel.RUMOR),
]


@dataclass
class Evidence:
    """单条证据"""
    source_text: str                                   # 证据原文
    source_type: EvidenceLevel = EvidenceLevel.UNKNOWN # 来源等级
    source_url: Optional[str] = None                   # 来源 URL
    extracted_values: Dict[str, str] = field(default_factory=dict)  # 从证据中提取的数值
    fingerprint: Optional[str] = None                  # 内容指纹（自动计算）

    def __post_init__(self):
        if self.fingerprint is None and self.source_text:
            self.fingerprint = hashlib.sha256(
                self.source_text.encode("utf-8")
            ).hexdigest()[:16]

    @property
    def trust(self) -> float:
        return LEVEL_TRUST.get(self.source_type, 0.3)

    @property
    def is_empty(self) -> bool:
        return not self.source_text or not self.source_text.strip()


@dataclass
class CrossValidationResult:
    """交叉验证结果"""
    consistent: bool              # 多条证据是否一致
    conflict_count: int           # 冲突数量
    supporting_count: int         # 支持数量
    note: str = ""


class EvidenceLedger:
    """证据账本：管理一个 claim 的所有证据"""

    def __init__(self):
        self._evidence: List[Evidence] = []

    def add(self, evidence: Evidence):
        """添加证据"""
        self._evidence.append(evidence)

    def add_from_text(self, source_text: str, source_url: str = None) -> Evidence:
        """从来源文本创建并添加证据（自动分类等级）"""
        ev = Evidence(
            source_text=source_text,
            source_type=self._classify_source(source_text),
            source_url=source_url,
        )
        self._evidence.append(ev)
        return ev

    @property
    def all_evidence(self) -> List[Evidence]:
        return list(self._evidence)

    @property
    def non_empty(self) -> List[Evidence]:
        return [e for e in self._evidence if not e.is_empty]

    @property
    def is_empty(self) -> bool:
        """所有证据都为空"""
        return len(self.non_empty) == 0

    def _classify_source(self, text: str) -> EvidenceLevel:
        """根据来源文本自动分类证据等级"""
        if not text:
            return EvidenceLevel.UNKNOWN
        text_lower = text.lower()
        for keyword, level in SOURCE_KEYWORDS:
            if keyword.lower() in text_lower:
                return level
        return EvidenceLevel.UNKNOWN

    def trust_score(self) -> float:
        """
        综合可信度评分（0.0-1.0）。

        逻辑：
        - 无证据 → 0.0（应触发 abstain）
        - 有证据 → 取最高等级来源的信任分，并按证据数量微调
        - 多条高等级来源一致 → 加分
        - 存在低等级来源 → 不加分但也不扣分（来源降级由 claim_verifier 处理）
        """
        ev_list = self.non_empty
        if not ev_list:
            return 0.0

        # 基础分 = 最高等级来源的信任分
        max_trust = max(e.trust for e in ev_list)

        # 多条独立来源加分（每条 +0.02，上限 +0.10）
        unique_fingerprints = {e.fingerprint for e in ev_list if e.fingerprint}
        bonus = min(0.02 * (len(unique_fingerprints) - 1), 0.10) if len(unique_fingerprints) > 1 else 0.0

        return min(max_trust + bonus, 1.0)

    def highest_level(self) -> Optional[EvidenceLevel]:
        """返回当前最高证据等级"""
        ev_list = self.non_empty
        if not ev_list:
            return None
        # LEVEL_TRUST 的 key 顺序就是从高到低
        level_order = list(LEVEL_TRUST.keys())
        return min(
            (e.source_type for e in ev_list),
            key=lambda lv: level_order.index(lv) if lv in level_order else len(level_order),
        )

    def has_low_credibility_source(self) -> bool:
        """是否存在低可信度来源（传闻级别）"""
        return any(e.source_type == EvidenceLevel.RUMOR for e in self.non_empty)

    def cross_validate(self, claim_values: Dict[str, str]) -> CrossValidationResult:
        """
        交叉验证：检查证据中的数值与 claim 中的数值是否一致。

        Args:
            claim_values: 从 claim 中提取的 {指标名: 数值} 字典

        Returns:
            CrossValidationResult
        """
        ev_list = self.non_empty
        if not ev_list:
            return CrossValidationResult(
                consistent=False, conflict_count=0,
                supporting_count=0, note="无证据可交叉验证"
            )

        supporting = 0
        conflicting = 0

        for metric, claimed_value in claim_values.items():
            for ev in ev_list:
                # 在证据文本中查找该数值
                if claimed_value and str(claimed_value) in ev.source_text:
                    supporting += 1
                elif ev.extracted_values:
                    ev_val = ev.extracted_values.get(metric)
                    if ev_val and str(ev_val) == str(claimed_value):
                        supporting += 1
                    elif ev_val and str(ev_val) != str(claimed_value):
                        conflicting += 1

        return CrossValidationResult(
            consistent=conflicting == 0 and supporting > 0,
            conflict_count=conflicting,
            supporting_count=supporting,
            note=f"{supporting} 条证据支持，{conflicting} 条冲突"
        )

    def summary(self) -> Dict:
        """返回账本摘要（用于报告输出）"""
        ev_list = self.non_empty
        return {
            "evidence_count": len(ev_list),
            "trust_score": round(self.trust_score(), 3),
            "highest_level": self.highest_level().value if self.highest_level() else None,
            "has_low_credibility": self.has_low_credibility_source(),
            "sources": [
                {
                    "level": e.source_type.value,
                    "trust": round(e.trust, 2),
                    "text_preview": e.source_text[:100] + "..." if len(e.source_text) > 100 else e.source_text,
                }
                for e in ev_list
            ],
        }


def extract_numbers(text: str) -> Dict[str, str]:
    """从文本中提取所有数值（带上下文），返回 {上下文: 数值}"""
    if not text:
        return {}
    results = {}
    # 匹配数值（整数、小数、百分比）
    for match in re.finditer(r'([\d.]+)\s*(%|亿|万|台|Nm|kg|rpm|arcmin|h)?', text):
        value = match.group(1)
        # 取数值前 10 个字符作为上下文
        start = max(0, match.start() - 10)
        context = text[start:match.start()].strip()
        if context:
            results[context] = value
    return results
