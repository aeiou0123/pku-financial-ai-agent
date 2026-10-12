"""Reviewed connection presets; a listed subscription is not an API entitlement."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    base: str
    protocol: str
    docs: str
    note: str
    kind: str = '按量 API'
    model: str = ''

    @property
    def connectable(self):
        return bool(self.base)


# Endpoint sources and review date are also supplied in the offline user guide.
REVIEWED_AT = '2026-10-11'
PRESETS = {
    '自定义': Provider('', 'openai', '', '使用服务商提供的文本接口地址与密钥。', '自定义'),
    'DeepSeek API': Provider('https://api.deepseek.com/v1', 'openai', 'https://api-docs.deepseek.com/api/list-models/', '从 DeepSeek 开放平台创建密钥；网页聊天账号不代替 API Key。'),
    'Kimi 开放平台（国内）': Provider('https://api.moonshot.cn/v1', 'openai', 'https://www.kimi.com/code/docs/', '使用开放平台密钥，与 Kimi Code 订阅密钥不同。'),
    'Kimi 开放平台（海外）': Provider('https://api.moonshot.ai/v1', 'openai', 'https://www.kimi.com/code/docs/', '海外开放平台地址；密钥与账号区域按控制台说明配套。'),
    '千问／百炼（北京）': Provider('https://dashscope.aliyuncs.com/compatible-mode/v1', 'openai', 'https://help.aliyun.com/zh/model-studio/base-url', '填百炼按量密钥；区域须匹配。官方建议生产使用业务空间专属域名，可在地址栏替换。'),
    '千问／百炼（新加坡）': Provider('https://dashscope-intl.aliyuncs.com/compatible-mode/v1', 'openai', 'https://help.aliyun.com/zh/model-studio/base-url', '使用新加坡区域的按量密钥。'),
    '千问／百炼（美国）': Provider('https://dashscope-us.aliyuncs.com/compatible-mode/v1', 'openai', 'https://help.aliyun.com/zh/model-studio/base-url', '使用美国区域的按量密钥。'),
    '智谱 GLM API': Provider('https://open.bigmodel.cn/api/paas/v4', 'openai', 'https://docs.bigmodel.cn/cn/best-practice/case/ai-search-engine', '使用智谱开放平台密钥。列表接口若不支持，请从控制台复制文本模型 ID。'),
    'Z.AI／GLM（国际）': Provider('https://api.z.ai/api/paas/v4', 'openai', 'https://docs.z.ai/api-reference/introduction', '使用 Z.AI 国际开放平台密钥；与国内智谱或 Coding Plan 的入口不同。'),
    '豆包／火山方舟 API': Provider('https://ark.cn-beijing.volces.com/api/v3', 'openai', 'https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh', '使用方舟 API Key；模型填账号已开通的模型 ID 或推理接入点 ID。'),
    'MiniMax API（国际）': Provider('https://api.minimax.io/v1', 'openai', 'https://platform.minimax.io/docs/api-reference/text-openai-api', '使用 MiniMax 国际开放平台密钥。选择账号已开通的文本模型。'),
    'MiniMax API（国内）': Provider('https://api.minimax.cn/v1', 'openai', 'https://platform.minimax.cn/docs/api-reference/text-openai-api', '使用国内开放平台密钥；国内外账号和入口按实际控制台配套。'),
    '腾讯 TokenHub（广州）': Provider('https://tokenhub.tencentmaas.com/v1', 'openai', 'https://cloud.tencent.com/document/product/1823/130078', '使用广州区域 TokenHub API Key；不跨区域或站点混用。'),
    '腾讯 TokenHub（新加坡）': Provider('https://tokenhub-intl.tencentmaas.com/v1', 'openai', 'https://cloud.tencent.com/document/product/1823/130078', '中国站文档的新加坡入口；国际站账号如提供不同地址，请选择自定义并填写控制台地址。'),
    '腾讯混元（原平台）': Provider('https://api.hunyuan.cloud.tencent.com/v1', 'openai', 'https://cloud.tencent.com/document/product/1729/111007', '官方已提示向 TokenHub 迁移；这个地址供原平台已有服务使用。新账号按控制台的 TokenHub 地址选择自定义。'),
    '百度千帆／文心 API': Provider('https://qianfan.baidubce.com/v2', 'openai', 'https://cloud.baidu.com/doc/qianfan-api/s/3m7of64lb', '使用千帆 API Key，选择控制台可用的文本模型。'),
    '阶跃星辰 API': Provider('https://api.stepfun.com/v1', 'openai', 'https://platform.stepfun.com/', '使用阶跃开放平台 API Key，模型名称从列表或控制台复制。'),
    '硅基流动（国内）': Provider('https://api.siliconflow.cn/v1', 'openai', 'https://docs.siliconflow.cn/docs/userguide/quickstart', '聚合模型平台；需保留模型 ID 中的提供者前缀。'),
    'OpenAI': Provider('https://api.openai.com/v1', 'openai', 'https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform', '使用 OpenAI Platform 的 API Key；ChatGPT 网页订阅与 API 分开计费。'),
    'Claude API': Provider('https://api.anthropic.com/v1', 'anthropic', 'https://platform.claude.com/docs/en/api/overview', '在 Claude Console 创建 API Key。Max／Team 当前有可领取的月度 API 额度，需按账户规则绑定；不使用网页登录票据。'),
    'Gemini API': Provider('https://generativelanguage.googleapis.com/v1beta/openai', 'openai', 'https://ai.google.dev/gemini-api/docs/openai', '在 Google AI Studio 创建 Gemini API Key。这里只使用兼容文本接口，不包含 Google Search 或文件 API。'),
    'Grok／xAI API': Provider('https://api.x.ai/v1', 'openai', 'https://docs.x.ai/overview', '使用 xAI 开发者 API Key；模型列表不等于账号拥有全部模型权限。'),
    'MiniMax M Plan': Provider('https://api.minimax.io/v1', 'openai', 'https://platform.minimax.io/docs/m-plan/intro', '在 M Plan 页面创建套餐专用 API Key；与按量密钥的权益不同，按账户返回的模型 ID 选择。', 'API 套餐'),
    'MiniMax M Plan（国内）': Provider('https://api.minimax.cn/v1', 'openai', 'https://platform.minimax.cn/docs/m-plan/intro', '在国内 M Plan 页面创建套餐专用密钥；与按量密钥的权益不同。', 'API 套餐'),
    'Kimi Code 订阅': Provider('https://api.kimi.com/coding/v1', 'openai', 'https://www.kimi.com/code/docs/', '保留已有连接方式。官方定位是开发工具；金融产品集成建议使用 Kimi 开放平台。仅使用本工作台真实客户端标识，不冒充其他工具。', '编程订阅', 'kimi-for-coding'),
    'Kimi Code（海外）': Provider('https://api.kimi.ai/coding/v1', 'openai', 'https://www.kimi.com/code/docs/', '使用 Kimi Code 专用密钥；面向开发工具，金融产品集成建议使用开放平台。', '编程订阅', 'kimi-for-coding'),
    '百炼 Coding Plan（说明）': Provider('', 'openai', 'https://help.aliyun.com/zh/model-studio/coding-plan', '官方禁止用于自定义应用后端或非交互批量调用，因此此处只提供说明。金融研究请选择千问／百炼按量 API。', '套餐说明'),
    'GLM Coding Plan（说明）': Provider('', 'openai', 'https://docs.bigmodel.cn/cn/coding-plan/overview', '已收录套餐入口；本轮未取得可读的当前范围原文，未确认本工作台使用范围。可用智谱开放 API 接入。', '套餐说明'),
    '火山 Coding Plan（说明）': Provider('', 'openai', 'https://docs.volcengine.com/docs/ark/integrate-third-party-tools?lang=zh', '编程套餐与按量 API 的地址、密钥不同；本轮未完成本工作台使用范围核验，先使用方舟按量 API。', '套餐说明'),
    'Step Plan（说明）': Provider('', 'openai', 'https://platform.stepfun.com/', '官网已提供订阅入口；本轮未核实套餐端点与本工作台范围，不套用按量密钥。可选阶跃开放 API。', '套餐说明'),
    'ChatGPT 会员／Codex（说明）': Provider('', 'openai', 'https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform', '本工作台未接入 ChatGPT／Codex 登录授权。网页会员不自动变成通用 API Key；金融研究请选择 OpenAI API。', '会员说明'),
    'Claude Pro／Max／Team（说明）': Provider('', 'anthropic', 'https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-and-team-plans', 'Max／Team 当前可领取 Console 月度 API 额度，领取后用 Console API Key 选择 Claude API。Pro 等计划的具体权益按账户页核对。网页或 Claude Code 登录未接入。', '会员说明'),
    'Google AI Pro／Ultra（说明）': Provider('', 'openai', 'https://ai.google.dev/gemini-api/docs/billing/', '本工作台使用 AI Studio／Cloud 项目的 Gemini API Key；未接入 Gemini 网页会员登录，项目额度以 API 账单页为准。', '会员说明'),
    'Cursor／GitHub Copilot（说明）': Provider('', 'openai', 'https://docs.github.com/en/copilot', '本工作台未实现这些编辑器的订阅登录或代理调用。不要填写编辑器登录票据；可使用独立开放 API。', '会员说明'),
}


def apply_preset(state, name):
    if name == '自定义':
        return
    provider = PRESETS[name]
    state.update(api_base=provider.base, api_protocol=provider.protocol, api_model=provider.model,
                 api_secret='', api_secret_widget='')
    # A credential and a successful probe belong to the old service.
    for key in ('model_catalog','model_catalog_error','api_model_choice','connection_result'):
        state.pop(key, None)


def connection_blocker(name):
    item = PRESETS.get(name)
    return item.note if item and name != '自定义' and not item.connectable else ''


def render_guide():
    import streamlit as st
    st.title('模型与套餐')
    st.write('选择与你的密钥对应的服务。网页会员、编程套餐和开放平台API的调用权限各有范围。')
    st.caption('输入名称可搜索。配置来源核对日期：' + REVIEWED_AT + '；调用前请测试自己的账户。')
    chosen = st.selectbox('查看服务说明', list(PRESETS), key='provider_guide_choice')
    item = PRESETS[chosen]
    st.subheader(chosen)
    st.write(item.note)
    if item.docs:
        st.markdown('[官方文档与账号入口](' + item.docs + ')')
    if item.connectable or chosen == '自定义':
        if item.base:
            st.code(item.base, language=None)
        st.button('在侧栏使用这项预设', on_click=lambda: (apply_preset(st.session_state, st.session_state['provider_guide_choice']), st.session_state.update(api_preset=st.session_state['provider_guide_choice'])))
    st.markdown('**第一次连接**')
    st.write('1. 在侧栏展开“模型连接”，选与你密钥对应的服务；切换服务会清除旧密钥。')
    st.write('2. 从官方控制台创建 API Key，填入后按 Enter。获取模型列表，选择支持文本的模型；不提供列表的服务可手填控制台模型 ID。')
    st.write('3. 点击“测试连接”。成功后回到工作区，先用小样例检查输出。测试不发送研究材料，会产生一次短文本请求，按所选服务计费。')
    with st.expander('术语与常见问题'):
        st.write('测试通常设置256个输出token上限，OpenAI和MiniMax为思考预留2048个；实际消耗与计费由服务商决定。')
        st.write('模型是实际处理文字的程序；服务商决定它在哪里运行、怎样收费。API Key 是调用凭证。地址是服务入口，预设会填写。协议是双方约定的请求格式，通常不用手动改。')
        st.write('401／403：核对密钥平台、区域、权限或套餐范围。404：核对地址和模型 ID。429／额度耗尽：查看账户剩余用量；不要靠反复测试解决。连接成功只证明小请求有响应。')
        st.write('AWS Bedrock、Vertex AI、Azure 等云托管模型的专用鉴权和部署未在此实现；已有 OpenAI／Anthropic 兼容网关可选择自定义。')
