@echo off
chcp 65001 >nul
echo =========================================
echo Claim2Value Research Environment Setup
echo =========================================
echo.

set REPO_DIR=%~dp0research_materials\github_repos
set PAPER_DIR=%~dp0research_materials\papers

if not exist "%REPO_DIR%" mkdir "%REPO_DIR%"
if not exist "%PAPER_DIR%" mkdir "%PAPER_DIR%"

cd /d "%REPO_DIR%"

echo [1/2] Cloning reference GitHub repositories...

if not exist "anthropic-financial-services" git clone https://github.com/anthropics/financial-services.git anthropic-financial-services
if not exist "modelforge" git clone https://github.com/Whatsonyourmind/modelforge.git modelforge
if not exist "Due-diligence-engine" git clone https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git Due-diligence-engine
if not exist "rd-agent" git clone https://github.com/microsoft/rd-agent.git rd-agent
if not exist "academic-commercialization-agent" git clone https://github.com/shuxiachai/academic-commercialization-agent.git academic-commercialization-agent
if not exist "PatentAgent" git clone https://github.com/iStoryOfSpring/PatentAgent.git PatentAgent
if not exist "disruptiq" git clone https://github.com/Sakshi3027/disruptiq.git disruptiq
if not exist "Meridian" git clone https://github.com/YoussefMadkour/Meridian.git Meridian
if not exist "Sanjaya-AI" git clone https://github.com/Swayam8115/Sanjaya-AI.git Sanjaya-AI
if not exist "SupplyChainCortex" git clone https://github.com/JiuTian-dev/SupplyChainCortex.git SupplyChainCortex
if not exist "TradingAgents" git clone https://github.com/tauricresearch/tradingagents.git TradingAgents
if not exist "FinRobot" git clone https://github.com/AI4Finance-Foundation/FinRobot.git FinRobot

cd /d "%PAPER_DIR%"

echo.
echo [2/2] Downloading arXiv papers...

curl -L --retry 5 --connect-timeout 20 -o 2507.19090_debate.pdf https://arxiv.org/pdf/2507.19090
curl -L --retry 5 --connect-timeout 20 -o 2508.03092_verifiable.pdf https://arxiv.org/pdf/2508.03092
curl -L --retry 5 --connect-timeout 20 -o 2505.22993_vegraph.pdf https://arxiv.org/pdf/2505.22993
curl -L --retry 5 --connect-timeout 20 -o 2607.25069_checkthat.pdf https://arxiv.org/pdf/2607.25069
curl -L --retry 5 --connect-timeout 20 -o 2503.07937_corroborating.pdf https://arxiv.org/pdf/2503.07937
curl -L --retry 5 --connect-timeout 20 -o 2602.02569_adversarial.pdf https://arxiv.org/pdf/2602.02569
curl -L --retry 5 --connect-timeout 20 -o 2403.16632_supply_chain_risk.pdf https://arxiv.org/pdf/2403.16632
curl -L --retry 5 --connect-timeout 20 -o 2505.16120_llm_agents_industry.pdf https://arxiv.org/pdf/2505.16120
curl -L --retry 5 --connect-timeout 20 -o 2412.20138_tradingagents.pdf https://arxiv.org/pdf/2412.20138
curl -L --retry 5 --connect-timeout 20 -o 2405.14767_finrobot.pdf https://arxiv.org/pdf/2405.14767
curl -L --retry 5 --connect-timeout 20 -o 2505.15155_rdagent_quant.pdf https://arxiv.org/pdf/2505.15155
curl -L --retry 5 --connect-timeout 20 -o 2508.03860_local_survey.pdf https://arxiv.org/pdf/2508.03860

cd /d "%~dp0"

echo.
echo =========================================
echo Setup complete!
echo Papers: %PAPER_DIR%
echo Repos:  %REPO_DIR%
echo =========================================
pause
