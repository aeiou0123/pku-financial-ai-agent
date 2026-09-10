// Claim2Value 路演 PPT 生成脚本（12 页，16:9）
// 数据源：docs/proposal/11_pitch_outline.md（2026-09-09 新口径）
const pptxgen = require("pptxgenjs");

const NAVY = "1E2761";   // 主色（深海军蓝）
const ICE = "CADCFC";    // 冰蓝
const WHITE = "FFFFFF";
const GOLD = "F0B429";   // 关键数字强调
const INK = "212121";    // 正文深色
const MUTE = "5A6372";   // 弱化灰
const LIGHT = "F4F7FE";  // 浅底

const F_HEAD = "微软雅黑";
const F_BODY = "微软雅黑";

const p = new pptxgen();
p.defineLayout({ name: "W16x9", width: 13.333, height: 7.5 });
p.layout = "W16x9";

// ---------- 工具 ----------
function footer(slide, pageNo, chapter) {
  slide.addText(
    [
      { text: chapter, options: { color: MUTE } },
      { text: `   ${String(pageNo).padStart(2, "0")} / 12`, options: { color: MUTE } },
    ],
    { x: 9.2, y: 7.05, w: 3.9, h: 0.35, fontFace: F_BODY, fontSize: 10, align: "right" }
  );
}
function leftRail(slide) {
  slide.addShape("rect", { x: 0, y: 0, w: 0.16, h: 7.5, fill: { color: NAVY } });
}
function chip(slide, x, y, d, txt, bg, fg) {
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: bg } });
  slide.addText(txt, { x, y: y - 0.02, w: d, h: d, align: "center", valign: "middle", fontFace: F_HEAD, fontSize: 15, bold: true, color: fg });
}
function statCard(slide, x, y, w, h, big, label, note) {
  slide.addShape("roundRect", { x, y, w, h, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
  slide.addText(big, { x: x + 0.1, y: y + 0.12, w: w - 0.2, h: 0.85, fontFace: F_HEAD, fontSize: 36, bold: true, color: NAVY, align: "center" });
  slide.addText(label, { x: x + 0.1, y: y + 0.98, w: w - 0.2, h: 0.4, fontFace: F_BODY, fontSize: 13, bold: true, color: INK, align: "center" });
  if (note) slide.addText(note, { x: x + 0.1, y: y + 1.38, w: w - 0.2, h: 0.5, fontFace: F_BODY, fontSize: 10, color: MUTE, align: "center" });
}
function titleBlock(slide, kicker, title) {
  slide.addText(kicker, { x: 0.75, y: 0.42, w: 9, h: 0.4, fontFace: F_BODY, fontSize: 13, bold: true, color: GOLD, charSpacing: 2 });
  slide.addText(title, { x: 0.72, y: 0.82, w: 11.8, h: 0.85, fontFace: F_HEAD, fontSize: 30, bold: true, color: NAVY });
}

// ---------- P1 封面（深色） ----------
{
  const s = p.addSlide();
  s.background = { color: NAVY };
  // 链条装饰：三个圆 + 连线
  const cy = 2.55;
  [4.6, 6.4, 8.2].forEach((cx, i) => {
    s.addShape("ellipse", { x: cx, y: cy, w: 0.55, h: 0.55, fill: { color: i === 1 ? GOLD : ICE } });
    if (i < 2) s.addShape("rect", { x: cx + 0.55, y: cy + 0.24, w: 1.25, h: 0.07, fill: { color: ICE } });
  });
  s.addText("CLAIM  →  证据  →  价值", { x: 4.35, y: 3.2, w: 5.6, h: 0.4, fontFace: F_BODY, fontSize: 12, color: ICE, align: "center", charSpacing: 3 });
  s.addText("Claim2Value", { x: 0.8, y: 3.75, w: 11.7, h: 1.15, fontFace: F_HEAD, fontSize: 54, bold: true, color: WHITE, align: "center" });
  s.addText("工业技术 Claim 到金融价值的可信映射 Agent", { x: 0.8, y: 4.95, w: 11.7, h: 0.6, fontFace: F_HEAD, fontSize: 21, color: ICE, align: "center" });
  s.addText("把「公司说自己技术多牛」变成「证据支持的财务影响」", { x: 0.8, y: 5.65, w: 11.7, h: 0.5, fontFace: F_BODY, fontSize: 15, color: GOLD, align: "center" });
  s.addText("北大金融 AI 智能体创新大赛  ·  机器人关节模组产业链", { x: 0.8, y: 6.65, w: 11.7, h: 0.4, fontFace: F_BODY, fontSize: 12, color: ICE, align: "center" });
}

// ---------- P2 痛点：信息断层 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "PROBLEM", "痛点：工程信号与金融决策之间的信息断层");
  // 左：技术信号
  s.addShape("roundRect", { x: 0.75, y: 1.95, w: 4.1, h: 2.5, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
  s.addText("产业链技术信号", { x: 0.95, y: 2.1, w: 3.7, h: 0.4, fontFace: F_HEAD, fontSize: 15, bold: true, color: NAVY });
  s.addText([
    { text: "· 减速器扭矩密度提升公告\n", options: {} },
    { text: "· 丝杠量产与订单落地\n", options: {} },
    { text: "· 募投扩产 / 产能爬坡\n", options: {} },
    { text: "· 新品发布与参数宣称", options: {} },
  ], { x: 0.95, y: 2.55, w: 3.7, h: 1.8, fontFace: F_BODY, fontSize: 12.5, color: INK, lineSpacing: 20 });
  // 右：金融决策
  s.addShape("roundRect", { x: 8.45, y: 1.95, w: 4.1, h: 2.5, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
  s.addText("金融决策", { x: 8.65, y: 2.1, w: 3.7, h: 0.4, fontFace: F_HEAD, fontSize: 15, bold: true, color: NAVY });
  s.addText([
    { text: "· 这条技术宣称值多少钱？\n", options: {} },
    { text: "· 证据强度够不够写进报告？\n", options: {} },
    { text: "· 买 / 卖 / 持有的赔率判断", options: {} },
  ], { x: 8.65, y: 2.55, w: 3.7, h: 1.8, fontFace: F_BODY, fontSize: 12.5, color: INK, lineSpacing: 20 });
  // 中间断层
  s.addShape("rightArrow", { x: 4.95, y: 2.75, w: 3.4, h: 0.9, fill: { color: GOLD } });
  s.addText("断层", { x: 4.95, y: 2.82, w: 3.4, h: 0.75, align: "center", fontFace: F_HEAD, fontSize: 16, bold: true, color: NAVY });
  // 三个具体表现
  const gaps = [
    ["人肉翻译", "工程宣称到财务影响靠人工转译，慢、不可复算"],
    ["口径打架", "卖方研报各说各话——降价假设已被现实击穿（ASP 1,500 假设 vs 实际 1,293 元）"],
    ["真假难辨", "买方无法区分「已验证证据」与「公司话术」"],
  ];
  gaps.forEach((g, i) => {
    const x = 0.75 + i * 4.25;
    chip(s, x, 4.85, 0.5, String(i + 1), NAVY, WHITE);
    s.addText(g[0], { x: x + 0.62, y: 4.85, w: 3.5, h: 0.5, fontFace: F_HEAD, fontSize: 16, bold: true, color: NAVY, valign: "middle" });
    s.addText(g[1], { x, y: 5.5, w: 4.0, h: 1.3, fontFace: F_BODY, fontSize: 12, color: INK, lineSpacing: 17 });
  });
  footer(s, 2, "02_problem");
}

// ---------- P3 产品：四层流水线 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "PRODUCT", "产品：从 Claim 到估值的可信流水线");
  const steps = ["Claim", "验证", "门控", "工程归一化", "经济映射", "因果批判", "财务三情景"];
  steps.forEach((t, i) => {
    const x = 0.7 + i * 1.82;
    const isKey = (i === 1 || i === 5);
    s.addShape("roundRect", { x, y: 2.0, w: 1.62, h: 0.85, rectRadius: 0.09, fill: { color: isKey ? GOLD : NAVY } });
    s.addText(t, { x, y: 2.0, w: 1.62, h: 0.85, align: "center", valign: "middle", fontFace: F_HEAD, fontSize: 13, bold: true, color: isKey ? NAVY : WHITE });
    if (i < 6) s.addShape("rightArrow", { x: x + 1.6, y: 2.33, w: 0.24, h: 0.2, fill: { color: MUTE } });
  });
  s.addText("验证层与批判层是别家没有的两道闸", { x: 0.75, y: 3.0, w: 11.8, h: 0.4, fontFace: F_BODY, fontSize: 12, color: MUTE, align: "center", italic: true });
  // 四个卖点 2x2
  const sells = [
    ["传导而非并存", "验证结论直接传导进估值假设，不是「验证归验证、财务照算」的两套数字"],
    ["逐条溯源", "每条假设带证据等级 + 置信度 + provenance 链，可一键回溯公告原文页码"],
    ["透明打折", "因果批判层区分行业 β 与公司 α，置信度从 0.5 打到 0.32，折扣写在输出里"],
    ["三栏输入", "每个输入分历史锚点 / 人工假设 / 计算结果三栏，评审知道每个数字从哪来"],
  ];
  sells.forEach((g, i) => {
    const x = 0.75 + (i % 2) * 6.15, y = 3.6 + Math.floor(i / 2) * 1.62;
    s.addShape("roundRect", { x, y, w: 5.9, h: 1.42, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
    s.addText(g[0], { x: x + 0.25, y: y + 0.12, w: 5.4, h: 0.42, fontFace: F_HEAD, fontSize: 15, bold: true, color: NAVY });
    s.addText(g[1], { x: x + 0.25, y: y + 0.55, w: 5.45, h: 0.8, fontFace: F_BODY, fontSize: 11.5, color: INK, lineSpacing: 16 });
  });
  footer(s, 3, "03_product");
}

// ---------- P4 证据网络 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "EVIDENCE", "证据网络：11 家公司 · 51 条结构化 Claim");
  statCard(s, 0.75, 2.0, 3.85, 2.0, "51", "结构化 Claim", "覆盖谐波/RV/丝杠/电机全链");
  statCard(s, 4.75, 2.0, 3.85, 2.0, "47", "已验证（公告原文级）", "页码定位 + 内容指纹，双源互证");
  statCard(s, 8.75, 2.0, 3.85, 2.0, "4", "待终验（显式标注）", "不假装验证过——分级即诚信");
  s.addText([
    { text: "绿的谐波 · 双环传动（环动科技）· 步科股份 · 中大力德 · 鸣志电器 · 柯力传感\n", options: { breakLine: true } },
    { text: "五洲新春 · 贝斯特 · 恒立液压 · 国茂股份 · 秦川机床", options: {} },
  ], { x: 0.75, y: 4.35, w: 11.8, h: 0.9, fontFace: F_BODY, fontSize: 13, color: INK, align: "center", lineSpacing: 22 });
  s.addShape("roundRect", { x: 0.75, y: 5.4, w: 11.85, h: 1.25, rectRadius: 0.09, fill: { color: NAVY } });
  s.addText([
    { text: "2026-09-09 终验实证：", options: { bold: true, color: GOLD } },
    { text: "11 条 claim 经巨潮公告原文逐字核对升级（含 SH_003——券商研报把半年报累计数误标为单季，被口径审查捕获并以官方原文纠偏）", options: { color: WHITE } },
  ], { x: 1.05, y: 5.55, w: 11.25, h: 0.95, fontFace: F_BODY, fontSize: 12.5, lineSpacing: 18 });
  footer(s, 4, "04_case_study / claim_bank_filled.json");
}

// ---------- P5 深度案例 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "CASE", "深度案例：一条 Claim 的一生（绿的谐波）");
  const steps = [
    ["① 输入与检出", "「关节模组减重 30%」→ 规则检出限定词缺失（原文「同等出力情况下」被丢）→ 部分成立，置信度 0.3"],
    ["② 门控与归一化", "门控放行 → 14 行参数归一化：4 行可比、10 行明确标记不可比（不可比的不硬算）"],
    ["③ 经济映射", "扭矩密度→渗透率 -10.26%（证据 high）；重量→BOM 成本 -5.47%（弹性经招股书材料成本校准）"],
    ["④ 因果批判", "12 个替代解释、14 条待补反事实：销量里多少是行业 β、多少是公司 α？置信度 0.5→0.32"],
  ];
  steps.forEach((g, i) => {
    const y = 1.95 + i * 1.06;
    s.addShape("roundRect", { x: 0.75, y, w: 7.6, h: 0.92, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
    s.addText(g[0], { x: 0.95, y: y + 0.06, w: 2.1, h: 0.8, fontFace: F_HEAD, fontSize: 13, bold: true, color: NAVY, valign: "middle" });
    s.addText(g[1], { x: 3.1, y: y + 0.06, w: 5.1, h: 0.8, fontFace: F_BODY, fontSize: 10.5, color: INK, valign: "middle", lineSpacing: 14 });
  });
  // 右侧三情景大数字
  s.addShape("roundRect", { x: 8.6, y: 1.95, w: 4.0, h: 4.35, rectRadius: 0.09, fill: { color: NAVY } });
  s.addText("财务三情景 EV", { x: 8.8, y: 2.15, w: 3.6, h: 0.45, fontFace: F_HEAD, fontSize: 15, bold: true, color: ICE, align: "center" });
  [["43.4 亿", "base 基准"], ["69.4 亿", "upside 乐观"], ["15.8 亿", "downside 悲观"]].forEach((v, i) => {
    s.addText(v[0], { x: 8.8, y: 2.7 + i * 1.05, w: 3.6, h: 0.6, fontFace: F_HEAD, fontSize: 28, bold: true, color: GOLD, align: "center" });
    s.addText(v[1], { x: 8.8, y: 3.3 + i * 1.05, w: 3.6, h: 0.35, fontFace: F_BODY, fontSize: 11, color: ICE, align: "center" });
  });
  s.addText("原型情景 · 非投资建议", { x: 8.8, y: 5.85, w: 3.6, h: 0.35, fontFace: F_BODY, fontSize: 10, color: ICE, align: "center", italic: true });
  s.addText("验证强度决定估值强度——这条链路里没有「无条件相信」这个数字。", { x: 0.75, y: 6.5, w: 11.8, h: 0.45, fontFace: F_HEAD, fontSize: 14, bold: true, color: NAVY, align: "center" });
  footer(s, 5, "04.3–4.4 / 10_demo_script");
}

// ---------- P6 通用性 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "GENERALITY", "通用性证明：同一条链路，换一家公司");
  s.addText("不是绿的谐波的专用工具——换一组输入文件，就是另一家公司。", { x: 0.75, y: 1.8, w: 11.8, h: 0.45, fontFace: F_BODY, fontSize: 13.5, color: INK });
  const rows = [
    ["输入", "绿的谐波 fixture", "→", "双环传动 fixture（rv/gear 双产品线）"],
    ["产品线识别", "harmonic / joint", "→", "rv / gear（detect_product_lines 自动识别）"],
    ["映射规则", "默认 ontology", "→", "双环变体（规则级 product_line_scope）"],
    ["三情景 EV", "43.4 / 69.4 / 15.8 亿", "→", "72.7 / 122.9 / 19.0 亿（RV 按环动招股书校准）"],
  ];
  rows.forEach((r, i) => {
    const y = 2.45 + i * 0.92;
    const isEv = i === 3;
    s.addShape("roundRect", { x: 0.75, y, w: 11.85, h: 0.78, rectRadius: 0.06, fill: { color: isEv ? NAVY : LIGHT }, line: { color: ICE, width: 1 } });
    s.addText(r[0], { x: 0.95, y: y + 0.04, w: 2.2, h: 0.7, fontFace: F_HEAD, fontSize: 13, bold: true, color: isEv ? GOLD : NAVY, valign: "middle" });
    s.addText(r[1], { x: 3.2, y: y + 0.04, w: 3.4, h: 0.7, fontFace: F_BODY, fontSize: 11.5, color: isEv ? WHITE : INK, valign: "middle" });
    s.addText(r[2], { x: 6.6, y: y + 0.04, w: 0.5, h: 0.7, fontFace: F_HEAD, fontSize: 14, bold: true, color: isEv ? GOLD : MUTE, valign: "middle", align: "center" });
    s.addText(r[3], { x: 7.1, y: y + 0.04, w: 5.3, h: 0.7, fontFace: F_BODY, fontSize: 11.5, color: isEv ? WHITE : INK, valign: "middle" });
  });
  s.addText("产品线泛化、ontology 变体、规则级作用域全是代码层实现，有 140 项回归测试锁定。", { x: 0.75, y: 6.45, w: 11.8, h: 0.45, fontFace: F_HEAD, fontSize: 13.5, bold: true, color: NAVY, align: "center" });
  footer(s, 6, "04 / tests/test_shuanghuan_chain.py");
}

// ---------- P7 反向 DCF ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "REVERSE DCF", "反向 DCF：诚实的估值观");
  // 左侧对照图
  s.addShape("roundRect", { x: 0.75, y: 1.95, w: 6.2, h: 4.1, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
  s.addText("市价 ↔ 模型三情景（亿元）", { x: 1.0, y: 2.1, w: 5.7, h: 0.4, fontFace: F_HEAD, fontSize: 14, bold: true, color: NAVY, align: "center" });
  const bars = [
    ["市价（2026-09-04）", 512.96, GOLD],
    ["乐观 upside", 58.5, NAVY],
    ["基准 base", 30.8, NAVY],
    ["悲观 downside", 0.9, MUTE],
  ];
  const maxW = 5.3;
  bars.forEach((b, i) => {
    const y = 2.62 + i * 0.82;
    const w = Math.max(0.35, (b[1] / 512.96) * maxW);
    s.addText(b[0], { x: 1.0, y, w: 2.2, h: 0.35, fontFace: F_BODY, fontSize: 10.5, color: INK });
    s.addShape("rect", { x: 1.0, y: y + 0.36, w, h: 0.3, fill: { color: b[2] } });
    s.addText(String(b[1]), { x: 1.05 + w, y: y + 0.3, w: 1.2, h: 0.4, fontFace: F_HEAD, fontSize: 12, bold: true, color: NAVY });
  });
  // 右侧大数字
  s.addShape("roundRect", { x: 7.25, y: 1.95, w: 5.35, h: 4.1, rectRadius: 0.09, fill: { color: NAVY } });
  s.addText("16.7×", { x: 7.45, y: 2.25, w: 4.95, h: 1.1, fontFace: F_HEAD, fontSize: 60, bold: true, color: GOLD, align: "center" });
  s.addText("市价隐含的销量预期 = 可验证 base 假设的 16.7 倍", { x: 7.55, y: 3.4, w: 4.75, h: 0.8, fontFace: F_BODY, fontSize: 14, color: WHITE, align: "center", lineSpacing: 20 });
  s.addText("我们不做目标价——做「隐含预期 ↔ 已验证证据」对照表，\n把赔率判断留给买方。", { x: 7.55, y: 4.4, w: 4.75, h: 0.9, fontFace: F_BODY, fontSize: 12, color: ICE, align: "center", lineSpacing: 18 });
  s.addText("差额 ≈ 市场为「人形机器人量产期权」付的价格；参数按年报/招股书校准后差距反而更大——原假设其实偏乐观。", { x: 0.75, y: 6.35, w: 11.8, h: 0.6, fontFace: F_BODY, fontSize: 12, color: MUTE, align: "center", italic: true });
  footer(s, 7, "05.5 / reverse_dcf()");
}

// ---------- P8 工程可信度 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "ENGINEERING", "工程可信度：可信不是口号，是测试矩阵和延迟曲线");
  statCard(s, 0.75, 2.05, 2.9, 2.1, "140", "回归测试全过", "含 9 项端到端回归");
  statCard(s, 3.8, 2.05, 2.9, 2.1, "0", "提案审校 issue", "跨章锚点数字机器对账");
  statCard(s, 6.85, 2.05, 2.9, 2.1, "4.3ms", "规则链延迟 p50", "p95 5.0ms · N=30 实测");
  statCard(s, 9.9, 2.05, 2.9, 2.1, "91.8%", "判别准确率", "Claude 91.8 / GPT 90.8（98 用例）");
  s.addShape("roundRect", { x: 0.75, y: 4.6, w: 11.85, h: 1.9, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
  s.addText([
    { text: "可信工程的三层含义：\n", options: { bold: true, color: NAVY, fontSize: 14 } },
    { text: "① 每个数字可复算（golden file 回归锁定）；② 每个断言可回溯（证据指纹 + 页码）；③ 每个边界如实标注（降级路径、口径疑点、待验证清单全部写进输出）。\n", options: { color: INK, fontSize: 12.5 } },
    { text: "离线可复现：无 API key 也能跑完整 Demo——评委现场断网也演示得了。", options: { color: MUTE, fontSize: 11.5, italic: true } },
  ], { x: 1.05, y: 4.8, w: 11.3, h: 1.55, fontFace: F_BODY, lineSpacing: 19 });
  footer(s, 8, "06.1 / benchmarks/latency_report.md");
}

// ---------- P9 商业潜力 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "BUSINESS", "商业潜力：市场缺口与定价");
  // 左：漏斗
  s.addShape("roundRect", { x: 0.75, y: 1.95, w: 5.9, h: 4.65, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
  s.addText("TAM / SAM / SOM", { x: 1.0, y: 2.08, w: 5.4, h: 0.4, fontFace: F_HEAD, fontSize: 14, bold: true, color: NAVY, align: "center" });
  const funnel = [
    ["TAM 上限锚", "谐波环节远期空间 71–603 亿（GGII vs 高盛双口径并列）", 5.4],
    ["SAM", "买方 / 卖方 / 产业三类客户可服务市场", 4.2],
    ["SOM", "2–6 亿/年（证据服务订阅）", 3.0],
  ];
  funnel.forEach((f, i) => {
    const y = 2.62 + i * 1.32;
    const x = 0.75 + (5.9 - f[2]) / 2 + 0.0;
    s.addShape("chevron", { x, y, w: f[2], h: 0.78, fill: { color: [NAVY, "3A4A9E", "5B6DB8"][i] } });
    s.addText(f[0], { x, y: y + 0.1, w: f[2], h: 0.4, fontFace: F_HEAD, fontSize: 12, bold: true, color: WHITE, align: "center" });
    s.addText(f[1], { x: 0.95, y: y + 0.85, w: 5.5, h: 0.4, fontFace: F_BODY, fontSize: 9.5, color: MUTE, align: "center" });
  });
  // 右：竞品缺口 + 定价
  s.addText("竞品四大缺口（为什么是我们）", { x: 6.95, y: 1.95, w: 5.6, h: 0.4, fontFace: F_HEAD, fontSize: 14, bold: true, color: NAVY });
  const gaps4 = ["无证据分级传导", "无双账本溯源", "无因果批判层", "无工程口径归一"];
  gaps4.forEach((g, i) => {
    const x = 6.95 + (i % 2) * 2.95, y = 2.45 + Math.floor(i / 2) * 0.85;
    s.addShape("roundRect", { x, y, w: 2.8, h: 0.7, rectRadius: 0.06, fill: { color: WHITE }, line: { color: NAVY, width: 1.25 } });
    s.addText(g, { x, y, w: 2.8, h: 0.7, fontFace: F_HEAD, fontSize: 12, bold: true, color: NAVY, align: "center", valign: "middle" });
  });
  s.addText([
    { text: "定价策略：", options: { bold: true, color: NAVY } },
    { text: "对标金融数据终端与研报服务，按「证据深度」三档分层（基础验证 / 证据链报告 / 定制链路），试点期 5 家付费客户目标。", options: { color: INK } },
  ], { x: 6.95, y: 4.35, w: 5.6, h: 1.0, fontFace: F_BODY, fontSize: 12, lineSpacing: 18 });
  s.addText([
    { text: "落地路径：", options: { bold: true, color: NAVY } },
    { text: "绿的谐波案例报告获客 → 买方研究员工作流嵌入 → API 化输出。", options: { color: INK } },
  ], { x: 6.95, y: 5.4, w: 5.6, h: 0.8, fontFace: F_BODY, fontSize: 12, lineSpacing: 18 });
  footer(s, 9, "05.1 / 05.6 / 05.7");
}

// ---------- P10 路线图 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "ROADMAP", "路线图：验证期 → 放大期 → 规模期");
  s.addShape("rect", { x: 1.2, y: 2.6, w: 10.9, h: 0.06, fill: { color: ICE } });
  const phases = [
    ["0–6 月", "验证期", ["Claim 终验 47/51 已完成（余 4 条待厂商 datasheet）", "5 家付费试点（券商/基金）", "案例报告产品化"]],
    ["6–18 月", "放大期", ["实时检索上线（evidence_retriever）", "专利核验全覆盖", "覆盖扩展至 50 家公司"]],
    ["18–36 月", "规模期", ["平台化 + API 输出", "跨行业 ontology 复用", "证据资产订阅化"]],
  ];
  phases.forEach((ph, i) => {
    const x = 0.85 + i * 4.25;
    s.addShape("ellipse", { x: x + 1.75, y: 2.42, w: 0.42, h: 0.42, fill: { color: i === 0 ? GOLD : NAVY } });
    s.addShape("roundRect", { x, y: 3.05, w: 3.95, h: 3.1, rectRadius: 0.09, fill: { color: LIGHT }, line: { color: ICE, width: 1 } });
    s.addText(ph[0], { x, y: 3.2, w: 3.95, h: 0.4, fontFace: F_BODY, fontSize: 12, bold: true, color: GOLD, align: "center", charSpacing: 2 });
    s.addText(ph[1], { x, y: 3.55, w: 3.95, h: 0.5, fontFace: F_HEAD, fontSize: 19, bold: true, color: NAVY, align: "center" });
    s.addText(ph[2].map(t => ({ text: "· " + t + "\n", options: {} })), { x: x + 0.3, y: 4.15, w: 3.4, h: 1.9, fontFace: F_BODY, fontSize: 11, color: INK, lineSpacing: 17 });
  });
  footer(s, 10, "06_roadmap");
}

// ---------- P11 合规边界 ----------
{
  const s = p.addSlide();
  leftRail(s);
  titleBlock(s, "COMPLIANCE", "合规边界：三条红线写进输出层");
  const rules = [
    ["非投资建议", "所有估值输出常驻「原型情景、非投资建议」标注；悲观情景常驻，对冲卖方一致预期的系统性乐观偏差"],
    ["证据不越级", "券商研报/媒体转述显式降级标注，不与公告原文级证据混用；待验证条目不假装验证过"],
    ["来源全标注", "每个数字带来源与内容指纹；AI 参与部分按大赛要求如实披露"],
  ];
  rules.forEach((r, i) => {
    const y = 2.1 + i * 1.5;
    chip(s, 0.85, y + 0.1, 0.55, ["一", "二", "三"][i], NAVY, WHITE);
    s.addText(r[0], { x: 1.6, y, w: 3.2, h: 0.75, fontFace: F_HEAD, fontSize: 17, bold: true, color: NAVY, valign: "middle" });
    s.addText(r[1], { x: 4.9, y, w: 7.7, h: 0.75, fontFace: F_BODY, fontSize: 12, color: INK, valign: "middle", lineSpacing: 17 });
    if (i < 2) s.addShape("rect", { x: 1.6, y: y + 1.15, w: 10.9, h: 0.02, fill: { color: ICE } });
  });
  footer(s, 11, "08_compliance");
}

// ---------- P12 团队与收尾（深色） ----------
{
  const s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("TEAM & CLOSE", { x: 0.8, y: 0.6, w: 9, h: 0.4, fontFace: F_BODY, fontSize: 13, bold: true, color: GOLD, charSpacing: 2 });
  s.addText("验证派：经济金融 × 工程 × Agent 开发", { x: 0.75, y: 1.0, w: 11.8, h: 0.8, fontFace: F_HEAD, fontSize: 30, bold: true, color: WHITE });
  const team = [
    ["经济金融", "Claim 终验、模型参数复核、估值口径裁定"],
    ["工程实现", "验证链 / 归一化 / 映射 / 批判层全栈代码，140 项回归"],
    ["Agent 设计", "工作流编排、证据账本、合规输出层"],
  ];
  team.forEach((t, i) => {
    const x = 0.8 + i * 4.15;
    s.addShape("roundRect", { x, y: 2.15, w: 3.85, h: 1.7, rectRadius: 0.09, fill: { color: "2A377A" }, line: { color: "3A4A9E", width: 1 } });
    s.addText(t[0], { x: x + 0.25, y: 2.35, w: 3.35, h: 0.5, fontFace: F_HEAD, fontSize: 16, bold: true, color: GOLD });
    s.addText(t[1], { x: x + 0.25, y: 2.9, w: 3.4, h: 0.85, fontFace: F_BODY, fontSize: 11.5, color: ICE, lineSpacing: 16 });
  });
  s.addShape("rect", { x: 5.17, y: 4.5, w: 3, h: 0.03, fill: { color: GOLD } });
  s.addText("把判断权留给人类，把可复算留给机器。", { x: 0.8, y: 4.85, w: 11.7, h: 0.9, fontFace: F_HEAD, fontSize: 30, bold: true, color: WHITE, align: "center" });
  s.addText("Claim2Value · 北大金融 AI 智能体创新大赛 · 谢谢", { x: 0.8, y: 6.1, w: 11.7, h: 0.5, fontFace: F_BODY, fontSize: 14, color: ICE, align: "center" });
}

const OUT = process.argv[2] || "Claim2Value_pitch.pptx";
p.writeFile({ fileName: OUT }).then(() => console.log("written:", OUT));
