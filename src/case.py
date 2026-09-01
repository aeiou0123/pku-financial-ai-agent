"""
Claim2Value 通用案例抽象层

设计原则：
- 公司/案例不硬编码在 Agent 里
- 每个案例包含统一的 claim、证据、参数、财务模型入口
- 支持机器人关节产业链中不同类型 claim 的验证
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import date


class ClaimType(str, Enum):
    """Claim 类型"""
    TECHNICAL_PERFORMANCE = "technical_performance"  # 技术性能：扭矩密度提升 30%
    CAPACITY_DEMAND = "capacity_demand"              # 产能/需求：出货增长 247%
    CUSTOMER_ORDER = "customer_order"                # 客户/订单：获特斯拉 4000 套订单
    MARKET_OUTLOOK = "market_outlook"                # 市场展望：人形机器人带来 10 倍空间
    FINANCIAL_FORECAST = "financial_forecast"        # 财务预测：2027 毛利率提升至 45%


class EvidenceLevel(str, Enum):
    """证据强度等级"""
    OFFICIAL_FILING = "official_filing"      # 年报/公告/招股书
    DATASHEET = "datasheet"                  # 官方产品手册
    PATENT = "patent"                        # 专利
    ANALYST_REPORT = "analyst_report"        # 券商研报
    INDUSTRY_REPORT = "industry_report"      # 行业报告
    NEWS_MEDIA = "news_media"                # 新闻报道
    RUMOR = "rumor"                          # 市场传闻


@dataclass
class Claim:
    """一个待验证的 claim"""
    id: str
    text: str
    company: str
    product: str
    claim_type: ClaimType
    metric: str                          # 被衡量的指标，如"扭矩密度"
    value: str                           # 指标数值或变化，如"+30%"
    baseline: Optional[str] = None       # 比较基准，如"上一代产品"
    source_text: Optional[str] = None    # 原始出处文字
    source_url: Optional[str] = None
    evidence_level: Optional[EvidenceLevel] = None
    confidence: Optional[float] = None   # 0-1
    verification_status: str = "pending" # pending / supported / partially_supported / refuted
    definition_issues: List[str] = field(default_factory=list)
    evidence_list: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class ProductSpec:
    """产品技术参数"""
    company: str
    product_series: str
    model: str
    rated_torque_nm: Optional[float] = None
    peak_torque_nm: Optional[float] = None
    continuous_torque_nm: Optional[float] = None
    weight_kg: Optional[float] = None
    torque_density_nm_kg: Optional[float] = None
    power_density_w_kg: Optional[float] = None
    efficiency_pct: Optional[float] = None
    backlash_arcsec: Optional[float] = None
    lifetime_h: Optional[float] = None
    max_input_speed_rpm: Optional[float] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class FinancialSnapshot:
    """财务快照"""
    company: str
    report_date: date
    revenue_bn: Optional[float] = None           # 营业收入（亿元）
    gross_margin_pct: Optional[float] = None     # 毛利率
    net_profit_bn: Optional[float] = None        # 净利润（亿元）
    rd_expense_pct: Optional[float] = None       # 研发费用率
    robot_revenue_pct: Optional[float] = None    # 机器人业务收入占比
    capacity_utilization: Optional[float] = None # 产能利用率
    source_url: Optional[str] = None


@dataclass
class CompanyCase:
    """一个完整的验证案例"""
    company_name: str
    stock_code: str
    sector: str                      # 所属细分：谐波减速器 / 无框力矩电机 / RV 减速器
    primary_claim: Claim
    claims: List[Claim] = field(default_factory=list)
    product_specs: List[ProductSpec] = field(default_factory=list)
    competitor_specs: List[ProductSpec] = field(default_factory=list)
    financials: List[FinancialSnapshot] = field(default_factory=list)
    raw_documents: List[Dict[str, Any]] = field(default_factory=list)

    def add_claim(self, claim: Claim):
        self.claims.append(claim)

    def add_product_spec(self, spec: ProductSpec):
        self.product_specs.append(spec)

    def add_competitor_spec(self, spec: ProductSpec):
        self.competitor_specs.append(spec)

    def add_financial(self, fin: FinancialSnapshot):
        self.financials.append(fin)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典，便于存入 JSON"""
        from dataclasses import asdict
        return asdict(self)


# 预定义三个案例的工厂函数

def green_harmonic_case() -> CompanyCase:
    """主案例：绿的谐波"""
    return CompanyCase(
        company_name="绿的谐波",
        stock_code="688017.SH",
        sector="谐波减速器",
        primary_claim=Claim(
            id="GH_001",
            text="绿的谐波2025年发布的新一代谐波减速器关节模组扭矩密度较上一代提升30%",
            company="绿的谐波",
            product="新一代谐波减速器关节模组",
            claim_type=ClaimType.TECHNICAL_PERFORMANCE,
            metric="扭矩密度",
            value="+30%",
            baseline="上一代产品",
            source_text="公司2025世界机器人大会发布资料",
            verification_status="pending",
            notes="需确认：额定vs峰值、质量定义、测试条件"
        )
    )


def buke_case() -> CompanyCase:
    """辅助案例 1：步科股份"""
    return CompanyCase(
        company_name="步科股份",
        stock_code="688160.SH",
        sector="无框力矩电机",
        primary_claim=Claim(
            id="BK_001",
            text="步科股份第四代FMK无框力矩电机功率密度提升20%，2025年无框力矩电机出货8.3万台，同比增长247%",
            company="步科股份",
            product="第四代FMK无框力矩电机",
            claim_type=ClaimType.CAPACITY_DEMAND,
            metric="功率密度/出货量",
            value="+20% / 8.3万台(+247%)",
            baseline="上一代产品 / 2024年同期",
            source_text="2025年半年报/调研纪要",
            verification_status="pending",
            notes="需拆分验证：技术性能claim和产能/需求claim"
        )
    )


def shuanghuan_case() -> CompanyCase:
    """辅助案例 2：双环传动"""
    return CompanyCase(
        company_name="双环传动",
        stock_code="002472.SZ",
        sector="RV减速器",
        primary_claim=Claim(
            id="SH_001",
            text="双环传动RV减速器扭矩密度达180N·m/kg，2025年获特斯拉Optimus 4000套订单",
            company="双环传动",
            product="RV减速器",
            claim_type=ClaimType.CUSTOMER_ORDER,
            metric="扭矩密度/订单量",
            value="180N·m/kg / 4000套",
            baseline="行业平均/前期订单",
            source_text="券商研报/市场报道",
            verification_status="pending",
            notes="需确认：180 N·m/kg口径（电机/模组/额定/峰值）；4000套订单证据来源"
        )
    )


# 案例注册表
CASE_REGISTRY = {
    "green_harmonic": green_harmonic_case,
    "buke": buke_case,
    "shuanghuan": shuanghuan_case,
}


def load_case(case_name: str) -> CompanyCase:
    """按名称加载案例"""
    if case_name not in CASE_REGISTRY:
        raise ValueError(f"Unknown case: {case_name}. Available: {list(CASE_REGISTRY.keys())}")
    return CASE_REGISTRY[case_name]()


def list_cases() -> List[str]:
    """列出所有可用案例"""
    return list(CASE_REGISTRY.keys())


if __name__ == "__main__":
    # 简单测试
    for name in list_cases():
        case = load_case(name)
        print(f"\n[{case.stock_code}] {case.company_name} | {case.sector}")
        print(f"Primary Claim: {case.primary_claim.text}")
        print(f"Type: {case.primary_claim.claim_type.value}")
