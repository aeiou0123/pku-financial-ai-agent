import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root=process.env.PROJECT_ROOT;
const workspaceDir=path.join(root,'work');
const buildDir=path.join(workspaceDir,'technical_report_build_20261003');
const finalPath=path.join(workspaceDir,'technical_delivery_20261003','07_技术题','技术题报告.pptx');
const skill='/root/.codex/skills/builtins/presentations';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const data=JSON.parse(await fs.readFile(path.join(workspaceDir,'technical_report_data_20261003.json'),'utf8'));
const font='WenQuanYi Micro Hei';
const p=Presentation.create({slideSize:{width:1280,height:720}});
const n=(v,d=3)=>Number(v).toFixed(d);
const pct=v=>(100*v).toFixed(2)+'%';
const foldLabel=f=>f.id==='2020'?'2020留出':f.id==='A'?'2016—2017开发':'2018—2019开发';
function text(s,v,x,y,w,h,size=28,color='#18232D',bold=false){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=v;q.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return q;
}
function slide(title,notes){
 const s=p.slides.add();s.background.fill='#FFFFFF';text(s,title,68,45,1144,86,46,'#102E42',true);
 text(s,String(p.slides.items.length),1180,673,40,30,18,'#667782');
 s.speakerNotes.textFrame.setText(notes);return s;
}
function table(s,values,y=185,height=350,widths){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:68,top:y,width:1144,height,columnWidths:widths,values});
 t.borders.assign({style:'solid',fill:'#D9E0E5',width:1});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#E5EDF2':r%2?'#FFFFFF':'#F5F7F8';
  cell.text.style={typeface:font,fontSize:24,color:'#18232D',bold:r===0};
 }
 return t;
}
const common='来源：真实官方实验plan.json、selection_lock.json、holdout_summary.json及final/receipt.json。2026-10-03。官方数据与tools.py SHA-256均已核对。';
let s=slide('股票收益预测与等权组合',common+' 项目Claim2Value。身份信息以统一信息表为准。');
text(s,'Claim2Value\n统一技术题报告',68,220,1100,165,58,'#102E42',true);
text(s,'每日截面秩变换与 Ridge 收益预测\n固定参数、2020单次留出与可复现持仓',68,425,1100,115,31);
text(s,'2026年10月3日　测试期收益与比赛排名尚未公开',68,605,1100,50,25,'#566A78');

s=slide('官方数据与获取核验',common+' 核验记录train_acquisition_20261003.json、test_acquisition_20261003.json。训练SHA256 '+data.data_sha256.train+'；测试SHA256 '+data.data_sha256.test);
table(s,[['数据','实际范围与数量'],['训练集','2000-01-04至2020-12-31\n2,035,600行，5,089日'],['测试集','2021-01-04至2025-12-31\n484,800行，1,212日'],['每日结构','400家公司、100个匿名因子\n训练集含收益，测试集不含收益'],['质量检查','官方指纹、字段类型、每日完整公司集\n日期与公司唯一，asof_date早于收益日期']],170,380,[270,874]);
text(s,'训练文件经云端分段后逐字节还原，完整指纹与原件一致。',68,585,1144,60,27,'#566A78');

s=slide('截面秩变换与线性预测',common+' 自研competition/baseline.py。公式中n为训练样本数，rank为当日400公司中位秩。匿名因子不强行映射经济含义。');
text(s,'当日每个因子在400家公司间取平均秩，\n按固定公式映射，常数因子变成零。',68,175,1144,100,31);
text(s,'x = √12 × [(rank − 0.5) / 400 − 0.5]',68,298,1144,65,34,'#102E42',true);
text(s,'训练标签为同日收益减去当日400公司平均收益。\n累计 XᵀX 与 Xᵀy 后求解 Ridge 系数。',68,407,1144,110,31);
text(s,'β = (XᵀX / n + αI)⁻¹ Xᵀy / n',68,550,1144,65,34,'#102E42',true);

s=slide('时间划分与预先登记的选择规则',common+' 在产生结果之前创建plan.json。开发完成后selection_lock.json锁定所有模型、名单、账户和对照的receipt指纹。选择规则：'+data.selection_rule);
table(s,[['阶段','模型训练截止','预测与比较区间'],['开发折A','2015-12-31','2016—2017'],['开发折B','2017-12-31','2018—2019'],['一次留出','2019-12-31','2020'],['最终模型','2020-12-31','2021—2025']],170,285,[300,360,484]);
text(s,'α：0.00001、0.001、0.1　持有奖励：0、0.0004、0.0008\n先最大化两折较低扣费Sharpe，再比较均值，最后取较小参数。',68,488,1144,118,26);

s=slide('九组开发结果与冻结参数',common+' 两折为分别结算的独立账户，Sharpe均调用原官方tools.py。没有将独立账户的Sharpe拼成连续全期Sharpe。');
table(s,[['α','持有奖励','开发折A','开发折B','两折较低值'],...data.candidates.map(c=>[String(c.alpha),n(c.hold_bonus,4),n(c.fold_sharpes[0]),n(c.fold_sharpes[1]),n(Math.min(...c.fold_sharpes))])],158,445,[205,210,243,243,243]);
text(s,`锁定 α=${data.selected.alpha}，持有奖励=${n(data.selected.hold_bonus,4)}。第一折仍为负值。`,68,625,1144,42,25,'#566A78');

s=slide('冻结策略与固定20公司对照',common+' 固定对照为C0001—C0020，每天等权，按官方费用记账。毛Sharpe来自同一持仓的daily_gross_returns，扣费Sharpe来自daily_net_returns。');
table(s,[['比较区间','策略扣费Sharpe','固定20扣费Sharpe','策略毛Sharpe'],...data.fold_comparisons.map(r=>[foldLabel(r.fold),n(r.strategy.net_sharpe),n(r.fixed20.net_sharpe),n(r.strategy.gross_sharpe_same_holdings)])],185,280,[330,290,294,230]);
text(s,'对照只提供可复核的起点，不能代表市场指数或最优策略。\n开发期差异明显，单年留出结果不能证明多年稳定收益。',68,525,1144,112,29,'#566A78');

s=slide('2020留出账户月末净值',common+' '+data.chart.sample_note+' 数据来自holdout/2020_a00_b00/accounting.json与controls/2020/accounting.json。月末取最后交易日实际净值，起点1；最终点包含期末卖出费用。可编辑图表的点值保留6位小数，指标表及原始账户保持完整精度。');
const plotValues=values=>values.map(v=>Number(v.toFixed(6)));
const chart=s.charts.add('line',{position:{left:68,top:170,width:1144,height:420},categories:data.chart.categories.map((v,i)=>i===0?v:`${i}月`),series:[{name:'冻结策略',values:plotValues(data.chart.strategy_nav),line:{style:'solid',fill:'#146C94',width:3}},{name:'固定20公司',values:plotValues(data.chart.fixed20_nav),line:{style:'solid',fill:'#C47C31',width:3}}],lineOptions:{smooth:false},hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{typeface:font,fontSize:24}},xAxis:{textStyle:{typeface:font,fontSize:24}},yAxis:{numberFormatCode:'0.00',textStyle:{typeface:font,fontSize:24},majorGridlines:{style:'solid',fill:'#E2E8F0',width:1}}});
applyPresentationChartFont(chart,{fontFamily:font});
text(s,'仅展示公开训练集内的2020留出账户。测试期收益尚未公开。',68,620,1144,48,26,'#566A78');

const held=data.fold_comparisons.find(r=>r.fold.id==='2020');
s=slide('2020留出指标',common+' 年化按252交易日；波动率用样本标准差ddof=1；最大回撤包括初始净值1。全部计算与官方逐日账户核对，2020未参与参数选择。');
table(s,[['指标','冻结策略','固定20公司'],['扣费年化Sharpe',n(held.strategy.net_sharpe),n(held.fixed20.net_sharpe)],['期末净值，起点1',n(held.strategy.final_nav,4),n(held.fixed20.final_nav,4)],['净值年化收益，252日',pct(held.strategy.net_annualized_return_252),pct(held.fixed20.net_annualized_return_252)],['收益年化波动，252日',pct(held.strategy.net_annualized_volatility_252),pct(held.fixed20.net_annualized_volatility_252)],['最大回撤',pct(held.strategy.max_drawdown_including_initial_nav),pct(held.fixed20.max_drawdown_including_initial_nav)]],175,360,[450,347,347]);
text(s,`验证区间共${held.strategy.days}日。只做一次2020留出，不据此改参数。`,68,586,1144,58,27,'#566A78');

s=slide('选股规则、换手与官方费用',common+' 费用BUY_FEE=0.00015，SELL_FEE=0.00065，调用官方80次二分费用结算。名单替换比例与绝对NAV单位费用分别记录。');
text(s,'当日分数为预测相对收益加此前持仓奖励。\n取前20家公司并等权，分数相同时按股票编号确定。',68,166,1144,105,30);
table(s,[['项目','实际设置或实测'],['买入 / 卖出费率','1.5 bp / 6.5 bp，含期末清仓'],['2020日均名单替换比例',pct(held.turnover.mean_constituent_replacement_fraction_excluding_first_day)],['2020累计费用，净值单位',n(held.turnover.absolute_nav_units_total_fees,6)]],305,245,[525,619]);
text(s,'名单保留仍须调回等权，会产生再平衡费用。\n累计费用随账户净值变化，不能当作换手率。',68,585,1144,78,26,'#566A78');

s=slide('实测运行时间与环境',common+' runtime文件记录每个真实阶段的墙钟时间与Linux子进程峰值RSS。排除依赖安装与资料阅读；finalize包括全量训练、两次预测和封装。货币算力成本未计量。');
table(s,[['阶段','墙钟时间 秒','峰值RSS MiB'],...data.runtime.map(r=>[r.phase,n(r.elapsed_seconds,2),n(r.maximum_child_rss_kib_linux/1024,1)])],175,280,[460,350,334]);
text(s,`三阶段合计 ${n(data.runtime_total_seconds,2)} 秒\nPython ${data.environment.python}，NumPy ${data.environment.numpy}\npandas ${data.environment.pandas}，PyArrow ${data.environment.pyarrow}`,68,494,1144,136,28);
text(s,'建模不调用商业大模型API。算力货币成本未计量。',68,639,1144,34,24,'#566A78');

s=slide('测试名单与解压复现',common+' 官方check与两次预测摘要见final/receipt.json、prediction/run_summary.json、reproduction/run_summary.json。名单SHA256 '+data.final.files_sha256['submission.csv']);
text(s,`官方 check：${data.final.official_check.status}\n${data.final.official_check.days}个交易日，每日20家公司，共${data.final.official_check.rows.toLocaleString()}行。\n同环境两次预测的完整CSV指纹一致。`,68,167,1144,160,31);
text(s,'解压 code.zip 后安装固定依赖：\npython -m pip install -r competition/requirements.txt',68,370,1144,100,26);
text(s,'运行：python reproduce.py --data <官方数据目录>\n　　　　　 --out <不存在的新目录>',68,500,1144,95,26);
text(s,'复现命令检查原名单指纹。Windows与跨系统一致性未实测。',68,630,1144,40,25,'#566A78');

s=slide('验证范围与局限',common+' 没有测试期收益、测试Sharpe、队伍有效数N或排名r，不计算技术题加分。2020验证已使用，后续新方法必须披露。');
text(s,'匿名因子的经济含义未认证，模型只利用统计关系。\n线性模型可能遗漏非线性与时变关系。',68,170,1144,106,30);
text(s,'开发折A与2020策略扣费Sharpe均为负。\n高持有奖励使2020名单几乎固定，择股适应性有限。',68,322,1144,106,30);
text(s,'2021—2025收益尚未公开，无法报告测试Sharpe或加分。\n后续修改方法时必须披露2020已被查看。',68,474,1144,112,30);

s=slide('自研部分与交付证据',common+' AI使用声明：'+data.ai_tools+' 完整指纹和运行证据随私人交付包提供。公共仓库不含官方Parquet或账号凭据。');
text(s,'自研：每日截面秩、Ridge拟合、带持有奖励选股，\n开发参数冻结、证据指纹与单次留出约束。',68,170,1144,112,30);
text(s,'外部：赛事数据与官方记账工具，\nNumPy、pandas、PyArrow，以及报告生成组件。',68,326,1144,112,30);
text(s,'AI协助：ChatGPT Work / Codex 编写与审查代码和报告。\n本次建模未调用Qwen或Kimi。后台模型标识未由程序记录。',68,478,1144,112,28);

if(p.slides.items.length!==13)throw new Error('Unexpected slide count');
await fs.mkdir(buildDir,{recursive:true});await fs.mkdir(path.dirname(finalPath),{recursive:true});
const candidatePath=path.join(buildDir,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidatePath);
const owners=[2,4,5,6,8,9,10];
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath,explicitTotalSlideCount:13,
 pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...owners.flatMap(i=>['--require-native-table-slide',String(i)])],
 requiredNativeTableOwnerSlides:owners,requiredNativeChartOwnerSlides:[7],materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(buildDir,'validation.json')});
console.log(JSON.stringify(result));
