import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root=process.env.PROJECT_ROOT;
const workspaceDir=path.join(root,'work');
const buildDir=path.join(workspaceDir,'slide_build');
const finalPath=path.join(workspaceDir,'slide_output','03_展示稿_复赛草稿.pptx');
const skill='/root/.codex/skills/builtins/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const font='WenQuanYi Micro Hei';
const p=Presentation.create({slideSize:{width:1280,height:720}});
const evaluation=JSON.parse(await fs.readFile(path.join(root,'docs/semifinal/evidence/local_development_20261002/results.json'),'utf8')).summary;
const deployment=JSON.parse(await fs.readFile(path.join(root,'docs/semifinal/evidence/deployment_review_20261002_v3.json'),'utf8'));
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
let s=slide('Claim2Value','版本日期2026-10-02。团队名称、成员和联系信息待负责人在统一信息表补齐。依据附件二，事实与项目说明相同。');
text(s,'机器人产业链声明核查\n与财务情景分析',68,205,1120,180,54,'#102E42',true);
text(s,'北京大学金融AI智能体创新大赛复赛\n2026年10月2日',68,475,1100,105,30);
text(s,'当前演示为本地规则模式　团队资料见统一信息表',68,622,1100,45,23,'#667782');

s=slide('产业叙述中的口径与机制','依据仓库案例GH_001及SH_004，见docs/semifinal/evidence/offline_review_20261002_v3。案例展示风险，不代表行业风险发生率。');
text(s,'减重30%的比较条件',68,185,1120,60,34,'#102E42',true);
text(s,'删掉“同等出力”，比较对象与测试条件就不清楚。\n额定与峰值、归母与扣非也需要各自保留口径。',68,255,1120,120,29);
text(s,'客户覆盖与收入兑现',68,422,1120,65,34,'#102E42',true);
text(s,'客户名单表明覆盖关系。批量订单、价格、销量与利润贡献\n仍需要证据和机制假设。',68,495,1120,120,29);

s=slide('工作流与自研边界','自研实现：src/review_session.py、state_verifier.py、evidence_ledger.py、economic_mapper.py、causal_critic.py、financial_model.py。外部组件Streamlit/openpyxl及资料来源。');
table(s,[['环节','实现内容'],['证据记录与规则','保留输入、出处、指纹和口径提示'],['自定义路径','规则核查与拒答，财务状态skipped'],['固定案例路径','对应公司工程、经济、批判与三情景'],['外部组件','Streamlit、openpyxl与公开资料']],175,360,[330,814]);
text(s,'当前页面没有在线模型或实时检索。规则分数不等于校准概率。',68,585,1135,65,25,'#566A78');

s=slide('当前可操作功能','功能依据app.py、src/review_session.py和本地部署包。当前没有PDF上传、自动原件认证或全行业自动估值。');
table(s,[['功能','当前状态'],['声明与证据输入','已实现，保存本次提交记录'],['公司示例切换','两家公司，固定参数情景'],['出处与报告导出','链接、定位、SHA-256，JSON及Markdown'],['缺证与输入异常','缺证拒答，空声明与错误链接显示错误'],['实时检索与PDF核验','尚未实现']],175,395,[400,744]);
text(s,'人工仍需核原件、页码、公司参数和情景假设。',68,602,1135,55,25,'#566A78');

s=slide('开发库复测命中87/98','来源：docs/semifinal/evidence/local_development_20261002/results.json和report.md。98条派生于19家族，规则开发使用过该库。严格标签准确率87/98，家族等权89.5%，诊断基线总是拒答19/98。');
text(s,'98条扰动来自19个原声明家族，家族等权89.5%',68,150,1140,56,27);
const labels={evidence_absence:'证据缺失',qualifier_removal:'限定词删除',source_downgrade:'来源降级',temporal_shift:'时间错位',unit_swap:'口径偷换',value_tampering:'数值篡改'};
table(s,[['类别','标签命中','比例'],...Object.entries(evaluation.mutations.by_type).map(([k,v])=>[labels[k],`${v.hits}/${v.n}`,`${(v.rate*100).toFixed(1)}%`])],220,330,[544,300,300]);
text(s,'规则曾使用该库开发。这里只报告开发复测，不能称业务准确率。\n总是拒答诊断基线为19/98，不能据此证明优于商业大模型。',68,581,1140,80,24,'#566A78');

s=slide('两家公司固定敏感性情景','EV单位亿元；依据offline_review_20261002_v3/green_demo.json与shuanghuan_demo.json。由enterprise_value_bn乘10换算。历史材料曾存在双重舍入，当前使用原始记录一次舍入。');
text(s,'绿的谐波提示测试条件缺失，双环传动记录客户覆盖。\n示例使用对应公司参数和固定假设。',68,150,1140,96,28);
const values=[['企业价值 亿元','base','upside','downside']];
for(const [stem,label] of [['green_demo','绿的谐波'],['shuanghuan_demo','双环传动']]){
 const r=JSON.parse(await fs.readFile(path.join(root,`docs/semifinal/evidence/offline_review_20261002_v3/${stem}.json`),'utf8'));
 values.push([label,...['base','upside','downside'].map(k=>(r.financial.scenarios[k].enterprise_value_bn*10).toFixed(2))]);
}
table(s,values,290,215,[454,230,230,230]);
text(s,'这些数字是原型情景企业价值，不表示已识别因果效应。\n自定义输入缺少绑定财务参数时不生成估值。',68,559,1140,90,26,'#566A78');

s=slide('同义词修复与剩余失败','来源：local_boundary_probes.json、local_development_20261002/alias_review_comparison.json和failures.json。人工开发探针4/10到6/10，修复题包含其中，不是独立验证。');
text(s,'“扣非净利润”和“扣非后净利润”同义误判已修复。\n归母与扣非继续区分，10条人工开发边界题仍有4条失败。',68,150,1140,100,27);
table(s,[['失败条件','当前现象','人工处理'],['等价单位','172Nm与0.172kNm冲突','做单位转换'],['千分位','1000与1,000冲突','核对数字格式'],['多个型号','其他型号数值掩盖冲突','按型号拆分证据'],['证据背景词','国内背景触发条件提示','核实语义范围']],275,270,[285,559,300]);
text(s,'人工边界题由4/10改善到6/10，属于开发修复。\n既有98题还有11条标签未命中，失败记录全部保留。',68,580,1140,80,24,'#566A78');

s=slide('操作路径与运行成本','来源：deployment_review_20261002_v3.json、local_development_20261002/results.json以及176项pytest实际通过记录。没有真人试用反馈或Windows真机验收。');
text(s,'启动本地页面，选择示例或粘贴证据，查看提示并导出。\n默认无需登录和模型密钥，176项软件回归通过。',68,150,1140,100,28);
table(s,[['实测指标','结果','范围'],['独立首次启动',`${deployment.runs[0].startup_seconds.toFixed(3)}秒`,'含依赖安装'],['再次启动',`${deployment.runs[1].startup_seconds.toFixed(3)}秒`,'跳过pip安装'],['本地核查p50 / p95','0.044 / 0.091ms','各题5次中位数，暖启动'],['外部API费用','0','当前本地路径，算力未计量']],275,280,[430,275,439]);
text(s,'毫秒数不含阅读、浏览器、联网或模型。\nLinux已验收，Windows真机与非开发成员试用待完成。',68,586,1140,80,24,'#566A78');

s=slide('后续验证与团队分工','依据docs/semifinal/execution_plan_20261002.md。工作安排不是已完成成果。正式截止按公告北京时间10月13日00:00，队内目标10月12日18:00。没有真实技术题Sharpe、名单或排名。');
table(s,[['负责方','下一步具体交付'],['西交','四条原件、页码、摘录与状态，Qwen/Kimi辅助定位'],['上交','单公司一年财务样本、字段字典与公告日'],['能下载赛事数据的成员','真实开发折、冻结参数、官方check与复现记录'],['负责人和全队','团队信息、独立标签验证、真人试用和真实录屏']],170,340,[420,724]);
text(s,'按原始来源或时间留出独立测试，补正面与失败案例。\n真实技术题结果仍待完成，模拟检查不作为正式成绩。',68,559,1140,95,26,'#566A78');

await fs.mkdir(buildDir,{recursive:true});await fs.mkdir(path.dirname(finalPath),{recursive:true});
const candidatePath=path.join(buildDir,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidatePath);
const owners=[3,4,5,6,7,8,9];
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath,
 pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...owners.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:owners,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(buildDir,'validation.json')});
console.log(JSON.stringify(result));
