import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root=process.env.PROJECT_ROOT;
const workspaceDir=path.join(root,'work');
const buildDir=path.join(workspaceDir,'slide_final_build_20261009');
const finalPath=path.join(workspaceDir,'materials_final_20261009','03_展示稿_复赛草稿.pptx');
const skill='/root/.codex/skills/builtins/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const font='WenQuanYi Micro Hei';
const p=Presentation.create({slideSize:{width:1280,height:720}});
const evaluation=JSON.parse(await fs.readFile(path.join(root,'docs/semifinal/evidence/local_development_20261003/results.json'),'utf8')).summary;
const deployment=JSON.parse(await fs.readFile(path.join(root,'docs/semifinal/evidence/deployment_review_20261003.json'),'utf8'));
function text(slide,value,x,y,w,h,size=28,color='#18232D',bold=false){
 const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value;shape.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return shape;
}
function slide(title,notes){
 const s=p.slides.add();s.background.fill='#FFFFFF';text(s,title,68,48,1144,88,44,'#102E42',true);
 text(s,String(p.slides.items.length),1180,673,40,30,16,'#667782');
 s.speakerNotes.textFrame.setText(notes);return s;
}
function table(s,values,y=190,height=340,widths=[380,300,464]){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:68,top:y,width:1144,height,columnWidths:widths,values});
 t.borders.assign({style:'solid',fill:'#D9E0E5',width:1});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#E5EDF2':r%2?'#FFFFFF':'#F5F7F8';
  cell.text.style={typeface:font,fontSize:24,color:'#18232D',bold:r===0};
 }
 return t;
}
let s=slide('Claim2Value','版本日期2026-10-09。团队名称、成员和联系信息待负责人在统一信息表补齐。依据附件二，事实与项目说明相同。');
text(s,'机器人产业链声明核查\n与财务情景分析',68,205,1120,180,54,'#102E42',true);
text(s,'北京大学金融AI智能体创新大赛复赛\n2026年10月9日',68,475,1100,105,30);
text(s,'当前演示为本地规则模式　团队资料见统一信息表',68,622,1100,45,23,'#667782');

s=slide('产业叙述中的口径与机制','依据仓库案例GH_001及SH_004，见docs/semifinal/evidence/offline_review_20261003。案例展示风险，不代表行业风险发生率。');
text(s,'减重30%的比较条件',68,185,1120,60,34,'#102E42',true);
text(s,'删掉“同等出力”，比较对象与测试条件就不清楚。\n额定与峰值、归母与扣非也需要各自保留口径。',68,255,1120,120,29);
text(s,'客户覆盖与收入兑现',68,422,1120,65,34,'#102E42',true);
text(s,'客户名单表明覆盖关系。批量订单、价格、销量与利润贡献\n仍需要证据和机制假设。',68,495,1120,120,29);

s=slide('工作流与自研边界','自研实现：src/review_session.py、state_verifier.py、evidence_ledger.py、economic_mapper.py、causal_critic.py、financial_model.py。外部组件Streamlit/openpyxl及资料来源。');
table(s,[['环节','实现内容'],['证据记录与规则','保留输入、出处、指纹和口径提示'],['自定义路径','规则核查与拒答，财务状态skipped'],['固定案例路径','对应公司工程、经济、批判与三情景'],['外部组件','Streamlit、openpyxl与公开资料']],175,360,[330,814]);
text(s,'当前页面没有在线模型或实时检索。规则分数不等于校准概率。',68,585,1135,65,25,'#566A78');

s=slide('当前可操作功能','功能依据app.py、src/review_session.py和本地部署包。当前没有PDF上传、自动原件认证或全行业自动估值。');
table(s,[['功能','当前状态'],['声明与证据输入','已实现，保存本次提交记录'],['公司示例切换','两家公司，固定参数情景'],['报告与批量核查','JSON、Markdown、CSV逐条处理与指纹'],['缺证与输入异常','缺证拒答，空声明与错误链接显示错误'],['实时检索与PDF核验','尚未实现']],175,395,[400,744]);
text(s,'人工仍需核原件、页码、公司参数和情景假设。',68,602,1135,55,25,'#566A78');

s=slide('开发库复测命中87/98','来源：docs/semifinal/evidence/local_development_20261003/results.json和report.md。98条派生于19家族，规则开发使用过该库。严格标签准确率87/98，家族等权89.5%，诊断基线总是拒答19/98。');
text(s,'98条扰动来自19个原声明家族，家族等权89.5%',68,150,1140,56,27);
const labels={evidence_absence:'证据缺失',qualifier_removal:'限定词删除',source_downgrade:'来源降级',temporal_shift:'时间错位',unit_swap:'口径偷换',value_tampering:'数值篡改'};
table(s,[['类别','标签命中','比例'],...Object.entries(evaluation.mutations.by_type).map(([k,v])=>[labels[k],`${v.hits}/${v.n}`,`${(v.rate*100).toFixed(1)}%`])],220,330,[544,300,300]);
text(s,'规则曾使用该库开发。这里只报告开发复测，不能称业务准确率。\n总是拒答诊断基线为19/98，不能据此证明优于商业大模型。',68,581,1140,80,24,'#566A78');

s=slide('两家公司固定敏感性情景','EV单位亿元；依据offline_review_20261003/green_demo.json与shuanghuan_demo.json。由enterprise_value_bn乘10换算。历史材料曾存在双重舍入，当前使用原始记录一次舍入。');
text(s,'绿的谐波提示测试条件缺失，双环传动记录客户覆盖。\n示例使用对应公司参数和固定假设。',68,150,1140,96,28);
const values=[['企业价值 亿元','base','upside','downside']];
for(const [stem,label] of [['green_demo','绿的谐波'],['shuanghuan_demo','双环传动']]){
 const r=JSON.parse(await fs.readFile(path.join(root,`docs/semifinal/evidence/offline_review_20261003/${stem}.json`),'utf8'));
 values.push([label,...['base','upside','downside'].map(k=>(r.financial.scenarios[k].enterprise_value_bn*10).toFixed(2))]);
}
table(s,values,290,215,[454,230,230,230]);
text(s,'这些数字是原型情景企业价值，不表示已识别因果效应。\n自定义输入缺少绑定财务参数时不生成估值。',68,559,1140,90,26,'#566A78');

s=slide('数量与型号边界修复','来源：local_boundary_probes.json、local_development_20261002/alias_review_comparison.json（历史同义词对照）与local_development_20261003/results.json及failures.json（当前边界结果）。当前10条开发探针全命中，修复题包含其中，不是独立验证。');
text(s,'“扣非净利润”和“扣非后净利润”同义误判已修复。\n归母与扣非继续区分，当前10条开发边界题全部命中。',68,150,1140,100,27);
table(s,[['已修复边界','当前处理','人工核对'],['注册等价单位','Nm/kNm、g/kg、人民币换算','未知单位'],['合法千分位','只转换三位分组','错误格式'],['明确X型号标记','保留该型号全部分段','无标记表格'],['特定公司背景句','不当作指标限定条件','其他语义范围']],275,270,[285,559,300]);
text(s,'10/10属于修复用开发题，不能称独立验证提升。\n既有98题还有11条标签未命中，失败记录全部保留。',68,580,1140,80,24,'#566A78');

s=slide('操作路径与运行成本','来源：deployment_review_20261003.json、local_development_20261003/results.json以及250项pytest实际通过记录。没有真人试用反馈或Windows真机验收。');
text(s,'启动本地页面，选择示例或粘贴证据，查看提示并导出。\n默认无需登录和模型密钥，250项软件回归通过。',68,150,1140,100,28);
table(s,[['实测指标','结果','范围'],['独立首次启动',`${deployment.runs[0].startup_seconds.toFixed(3)}秒`,'含依赖安装'],['再次启动',`${deployment.runs[1].startup_seconds.toFixed(3)}秒`,'跳过pip安装'],['本地核查p50 / p95',`${evaluation.runtime.p50_case_median_ms.toFixed(3)} / ${evaluation.runtime.p95_case_median_ms.toFixed(3)}ms`,'各题5次中位数，暖启动'],['外部API费用','0','当前本地路径，算力未计量']],275,280,[430,275,439]);
text(s,'毫秒数不含阅读、浏览器、联网或模型。\nLinux已验收，Windows真机与非开发成员试用待完成。',68,586,1140,80,24,'#566A78');

s=slide('参数复核与剩余证据','官方来源：https://www.finemotion.com.cn/home/Index/product?id=34；https://precision.nabtesco.com/tw/products/detail/RV-E；https://www.leaderdrive.com/product/4.html。获取2026-10-02，记录2026-10-03。页版本日期未明，未认证历史原件。完整修改前后见primary_source_review_20261003/review.json。截止按公告北京时间10月13日00:00。');
table(s,[['复核项目','结论与使用条件'],['SHPR-20E与RV-20E','167 Nm、4.7 kg（15 rpm）\n推算密度35.53 Nm/kg'],['LHS旧版与官网现版','未混版计算，移除错误峰值130 Nm'],['同业结构比较','谐波与RV分开，未知或混合结构拒绝量化'],['仍需取得的证据','历史原件、真实财务样本、独立标签及真人试用']],170,340,[420,724]);
text(s,'网页历史版本未认证，四条急件状态未升级。\n技术题三件套与运行视频已补齐。\n团队资料、签名与真人试用仍需成员完成。',68,559,1140,95,26,'#566A78');

s=slide('技术题结果与本轮比较','来源：首轮官方不可变运行记录与work/refinement_20261009/selection_lock.json。开发期最低Sharpe决定是否替换。2020年已被检验，测试收益未公开。');
text(s,'首轮三件套完成并通过官方校验。\n1212个交易日，每日20家公司等权持仓。',68,150,1140,96,28);
table(s,[['扣费Sharpe','原版本','10月9日最好候选'],['2016—2017开发期','−0.102','−0.338'],['2018—2019开发期','0.789','0.840'],['2020年首轮检验','−0.091','未再次评测']],290,230,[464,340,340]);
text(s,'12个候选均未达到替换标准，保留原名单。\n测试期收益与比赛排名未知，开发比较不代表泛化。',68,575,1140,86,25,'#566A78');

await fs.mkdir(buildDir,{recursive:true});await fs.mkdir(path.dirname(finalPath),{recursive:true});
const candidatePath=path.join(buildDir,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidatePath);
const owners=[3,4,5,6,7,8,9,10];
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath,
 pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...owners.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:owners,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(buildDir,'validation.json')});
console.log(JSON.stringify(result));

