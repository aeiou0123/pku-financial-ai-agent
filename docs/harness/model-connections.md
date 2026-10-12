# 模型与套餐连接指南

官方文档核对日期：2026-10-11。共34个选项：25个可填写连接的预设、8个会员或套餐说明、1个自定义入口。区域和套餐分别列出，不等于这些数量的独立厂商。

核对官方配置并以本机模拟服务验证请求形状，没有用真实密钥逐家调用，也没有测试各模型的研究质量。GLM／火山／Step编程套餐的当前工作台适用范围未完成核验，只提供说明。

## 三步连接

1. 页面选择“模型与套餐”，找到你持有的服务。可连接项点击“在侧栏使用这项预设”；或在侧栏“模型连接”直接选择。切换服务会清除旧密钥和旧连接结果。
2. 从该服务官方控制台获取API Key，输入后按Enter。点击“获取模型列表”，选支持文本的模型；服务没有标准列表时，从控制台复制模型ID手填。列表仅代表服务返回的候选，不保证账号对每个模型都有权限。不要复制网页会员登录票据。
3. 点击“测试连接”。它不发送研究材料；通常最多请求256个输出token，OpenAI及MiniMax为思考预留2048个上限，按实际服务计费。HTTP响应与可见正文分别显示；成功也不保证长研究请求成功。随后回到工作区。

协议和地址由预设填写，通常不用自行修改。新账号要核对区域、项目与套餐。当前没有网页登录、AWS Bedrock、Vertex AI或Azure专用鉴权。

## 已登记的配置

| 预设 | 类型／协议 | Base URL | 密钥或使用说明 | 官方来源 |
|---|---|---|---|---|
| DeepSeek API | 按量 API／OpenAI兼容文本 | `https://api.deepseek.com/v1` | 从 DeepSeek 开放平台创建密钥；网页聊天账号不代替 API Key。 | [官方](https://api-docs.deepseek.com/api/list-models/) |
| Kimi 开放平台（国内） | 按量 API／OpenAI兼容文本 | `https://api.moonshot.cn/v1` | 使用开放平台密钥，与 Kimi Code 订阅密钥不同。 | [官方](https://www.kimi.com/code/docs/) |
| Kimi 开放平台（海外） | 按量 API／OpenAI兼容文本 | `https://api.moonshot.ai/v1` | 海外开放平台地址；密钥与账号区域按控制台说明配套。 | [官方](https://www.kimi.com/code/docs/) |
| 千问／百炼（北京） | 按量 API／OpenAI兼容文本 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 填百炼按量密钥；区域须匹配。官方建议生产使用业务空间专属域名，可在地址栏替换。 | [官方](https://help.aliyun.com/zh/model-studio/base-url) |
| 千问／百炼（新加坡） | 按量 API／OpenAI兼容文本 | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | 使用新加坡区域的按量密钥。 | [官方](https://help.aliyun.com/zh/model-studio/base-url) |
| 千问／百炼（美国） | 按量 API／OpenAI兼容文本 | `https://dashscope-us.aliyuncs.com/compatible-mode/v1` | 使用美国区域的按量密钥。 | [官方](https://help.aliyun.com/zh/model-studio/base-url) |
| 智谱 GLM API | 按量 API／OpenAI兼容文本 | `https://open.bigmodel.cn/api/paas/v4` | 使用智谱开放平台密钥。列表接口若不支持，请从控制台复制文本模型 ID。 | [官方](https://docs.bigmodel.cn/cn/best-practice/case/ai-search-engine) |
| Z.AI／GLM（国际） | 按量 API／OpenAI兼容文本 | `https://api.z.ai/api/paas/v4` | 使用 Z.AI 国际开放平台密钥；与国内智谱或 Coding Plan 的入口不同。 | [官方](https://docs.z.ai/api-reference/introduction) |
| 豆包／火山方舟 API | 按量 API／OpenAI兼容文本 | `https://ark.cn-beijing.volces.com/api/v3` | 使用方舟 API Key；模型填账号已开通的模型 ID 或推理接入点 ID。 | [官方](https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh) |
| MiniMax API（国际） | 按量 API／OpenAI兼容文本 | `https://api.minimax.io/v1` | 使用 MiniMax 国际开放平台密钥。选择账号已开通的文本模型。 | [官方](https://platform.minimax.io/docs/api-reference/text-openai-api) |
| MiniMax API（国内） | 按量 API／OpenAI兼容文本 | `https://api.minimax.cn/v1` | 使用国内开放平台密钥；国内外账号和入口按实际控制台配套。 | [官方](https://platform.minimax.cn/docs/api-reference/text-openai-api) |
| 腾讯 TokenHub（广州） | 按量 API／OpenAI兼容文本 | `https://tokenhub.tencentmaas.com/v1` | 使用广州区域 TokenHub API Key；不跨区域或站点混用。 | [官方](https://cloud.tencent.com/document/product/1823/130078) |
| 腾讯 TokenHub（新加坡） | 按量 API／OpenAI兼容文本 | `https://tokenhub-intl.tencentmaas.com/v1` | 中国站文档的新加坡入口；国际站账号如提供不同地址，请选择自定义并填写控制台地址。 | [官方](https://cloud.tencent.com/document/product/1823/130078) |
| 腾讯混元（原平台） | 按量 API／OpenAI兼容文本 | `https://api.hunyuan.cloud.tencent.com/v1` | 官方已提示向 TokenHub 迁移；这个地址供原平台已有服务使用。新账号按控制台的 TokenHub 地址选择自定义。 | [官方](https://cloud.tencent.com/document/product/1729/111007) |
| 百度千帆／文心 API | 按量 API／OpenAI兼容文本 | `https://qianfan.baidubce.com/v2` | 使用千帆 API Key，选择控制台可用的文本模型。 | [官方](https://cloud.baidu.com/doc/qianfan-api/s/3m7of64lb) |
| 阶跃星辰 API | 按量 API／OpenAI兼容文本 | `https://api.stepfun.com/v1` | 使用阶跃开放平台 API Key，模型名称从列表或控制台复制。 | [官方](https://platform.stepfun.com/) |
| 硅基流动（国内） | 按量 API／OpenAI兼容文本 | `https://api.siliconflow.cn/v1` | 聚合模型平台；需保留模型 ID 中的提供者前缀。 | [官方](https://docs.siliconflow.cn/docs/userguide/quickstart) |
| OpenAI | 按量 API／OpenAI兼容文本 | `https://api.openai.com/v1` | 使用 OpenAI Platform 的 API Key；ChatGPT 网页订阅与 API 分开计费。 | [官方](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform) |
| Claude API | 按量 API／Anthropic Messages | `https://api.anthropic.com/v1` | 在 Claude Console 创建 API Key。Max／Team 当前有可领取的月度 API 额度，需按账户规则绑定；不使用网页登录票据。 | [官方](https://platform.claude.com/docs/en/api/overview) |
| Gemini API | 按量 API／OpenAI兼容文本 | `https://generativelanguage.googleapis.com/v1beta/openai` | 在 Google AI Studio 创建 Gemini API Key。这里只使用兼容文本接口，不包含 Google Search 或文件 API。 | [官方](https://ai.google.dev/gemini-api/docs/openai) |
| Grok／xAI API | 按量 API／OpenAI兼容文本 | `https://api.x.ai/v1` | 使用 xAI 开发者 API Key；模型列表不等于账号拥有全部模型权限。 | [官方](https://docs.x.ai/overview) |
| MiniMax M Plan | API 套餐／OpenAI兼容文本 | `https://api.minimax.io/v1` | 在 M Plan 页面创建套餐专用 API Key；与按量密钥的权益不同，按账户返回的模型 ID 选择。 | [官方](https://platform.minimax.io/docs/m-plan/intro) |
| MiniMax M Plan（国内） | API 套餐／OpenAI兼容文本 | `https://api.minimax.cn/v1` | 在国内 M Plan 页面创建套餐专用密钥；与按量密钥的权益不同。 | [官方](https://platform.minimax.cn/docs/m-plan/intro) |
| Kimi Code 订阅 | 编程订阅／OpenAI兼容文本 | `https://api.kimi.com/coding/v1` | 保留已有连接方式。官方定位是开发工具；金融产品集成建议使用 Kimi 开放平台。仅使用本工作台真实客户端标识，不冒充其他工具。 | [官方](https://www.kimi.com/code/docs/) |
| Kimi Code（海外） | 编程订阅／OpenAI兼容文本 | `https://api.kimi.ai/coding/v1` | 使用 Kimi Code 专用密钥；面向开发工具，金融产品集成建议使用开放平台。 | [官方](https://www.kimi.com/code/docs/) |
| 百炼 Coding Plan（说明） | 套餐说明／OpenAI兼容文本 | 说明项，不启用调用 | 官方禁止用于自定义应用后端或非交互批量调用，因此此处只提供说明。金融研究请选择千问／百炼按量 API。 | [官方](https://help.aliyun.com/zh/model-studio/coding-plan) |
| GLM Coding Plan（说明） | 套餐说明／OpenAI兼容文本 | 说明项，不启用调用 | 已收录套餐入口；未取得可读的当前范围原文，未确认本工作台使用范围。可用智谱开放 API 接入。 | [官方](https://docs.bigmodel.cn/cn/coding-plan/overview) |
| 火山 Coding Plan（说明） | 套餐说明／OpenAI兼容文本 | 说明项，不启用调用 | 编程套餐与按量 API 的地址、密钥不同；未完成本工作台使用范围核验，先使用方舟按量 API。 | [官方](https://docs.volcengine.com/docs/ark/integrate-third-party-tools?lang=zh) |
| Step Plan（说明） | 套餐说明／OpenAI兼容文本 | 说明项，不启用调用 | 官网已提供订阅入口；尚未核实套餐端点与本工作台范围，不套用按量密钥。可选阶跃开放 API。 | [官方](https://platform.stepfun.com/) |
| ChatGPT 会员／Codex（说明） | 会员说明／OpenAI兼容文本 | 说明项，不启用调用 | 本工作台未接入 ChatGPT／Codex 登录授权。网页会员不自动变成通用 API Key；金融研究请选择 OpenAI API。 | [官方](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform) |
| Claude Pro／Max／Team（说明） | 会员说明／Anthropic Messages | 说明项，不启用调用 | Max／Team 当前可领取 Console 月度 API 额度，领取后用 Console API Key 选择 Claude API。Pro 等计划的具体权益按账户页核对。网页或 Claude Code 登录未接入。 | [官方](https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-and-team-plans) |
| Google AI Pro／Ultra（说明） | 会员说明／OpenAI兼容文本 | 说明项，不启用调用 | 本工作台使用 AI Studio／Cloud 项目的 Gemini API Key；未接入 Gemini 网页会员登录，项目额度以 API 账单页为准。 | [官方](https://ai.google.dev/gemini-api/docs/billing/) |
| Cursor／GitHub Copilot（说明） | 会员说明／OpenAI兼容文本 | 说明项，不启用调用 | 本工作台未实现这些编辑器的订阅登录或代理调用。不要填写编辑器登录票据；可使用独立开放 API。 | [官方](https://docs.github.com/en/copilot) |

## 地址末尾怎样填

例如OpenAI的以下地址会归一到同一入口：

- `https://api.openai.com` 或末尾带 `/`
- `https://api.openai.com/v1` 或末尾带 `/`
- `https://api.openai.com/v1/chat/completions`
- `https://api.openai.com/v1/completions`（按聊天接口归一，不代表实现旧文本 Completions 协议）

Anthropic可填 `https://api.anthropic.com/v1` 或 `/v1/messages`。Gemini的 `/v1beta/openai`、智谱的 `/api/paas/v4`、百度的 `/v2`和自定义网关路径保留，不额外拼接 `/v1`。页面会显示实际的生成与列表地址。

## 会员与API额度

[ChatGPT与OpenAI API](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform)分开计费。本工作台尚未实现ChatGPT／Codex登录。

[Claude Max／Team](https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-and-team-plans)当前有可领取的Console月度API额度，需要符合资格并绑定组织；领取后依然使用Console创建的API Key。其他计划以官方权益页为准，不能把登录当API密钥。

[百炼Coding Plan](https://help.aliyun.com/zh/model-studio/coding-plan)“订阅前须知”第1项限定编程工具，禁止自定义应用后端、自动化脚本和非交互批量API调用，所以工作台仅列说明项。不要将套餐密钥套进按量地址。

[MiniMax M Plan](https://platform.minimax.cn/docs/m-plan/intro)介绍包括调研、写作以及其他AI工具的API Key接入，本版仅接入文本流程。Kimi Code保留已有配置；[Kimi官方文档](https://www.kimi.com/code/docs/)建议自己的产品使用开放平台。不伪装其他客户端。

## 连不上如何定位

| 提示 | 下一步 |
|---|---|
| 401／403 | 核对密钥所属平台、区域、项目及套餐使用范围；切换服务后重新填对应密钥 |
| 404 | 核对页面显示的实际地址、模型ID和账号是否已开通 |
| 429／额度不足 | 查看账户额度和服务状态，不靠反复测试解决 |
| 无标准模型列表 | 手填控制台中的文本模型ID；获取失败不会自动重试 |
| 有HTTP响应、没有正文 | 不当成可用文本；核对思考预算和模型要求，真实研究另测 |
| 小测试通过、研究失败 | 看分批完成范围；超时、输出上限和重试可在“研究请求与分批设置”调整 |

适配依据：[Gemini客户端标识](https://ai.google.dev/gemini-api/docs/partner-integration)、[OpenAI官方参数定义](https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py)、[MiniMax新输出上限参数](https://platform.minimax.io/docs/api-reference/text-openai-api)。思考文本不作为研究证据；结构化JSON不支持时仅按明确错误回退，不能修补事实。
