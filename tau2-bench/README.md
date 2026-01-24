# $\tau^2$-Bench: Evaluating Conversational Agents in a Dual-Control Environment

[![python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![arXiv](http://img.shields.io/badge/cs.AI-arXiv%3A2506.07982-B31B1B.svg?logo=arxiv&logoColor=red)](https://arxiv.org/abs/2506.07982)
[![blog](https://img.shields.io/badge/blog-tau2--bench-green)](https://sierra.ai/blog/benchmarking-agents-in-collaborative-real-world-scenarios)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/sierra.svg?style=social&label=Follow%20%40SierraPlatform)](https://x.com/SierraPlatform/status/1932464265207889974)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/posts/sierra_last-year-we-introduced-%F0%9D%9C%8F-bench-a-benchmark-activity-7338229693898231809-F8L4?utm_source=share&utm_medium=member_desktop&rcm=ACoAAAdc8goBmhEsiEo1_t_XSJbAnY4_zMfAWcE)
[![Leaderboard](https://img.shields.io/badge/🏆_Live_Leaderboard-taubench.com-brightgreen?style=flat)](https://taubench.com)

<div align="center">
<img src="figs/overview.png" width="95%" alt="System Overview"><br>
<em>Figure 1: τ²-bench allows users to interact with the agent and the environment</em>
</div>

<div align="center">
<img src="figs/traj.png" width="95%" alt="Trajectory"><br>
<em>Figure 2: Trajectory of a conversation between an agent and a user</em>
</div>

## 🆕 What's New

### 🤖 Reinforcement Learning Support (New!)
τ²-bench now supports RL training with a Gymnasium-compatible interface:

- **🏋️ Train RL Agents**: Use the gym interface to train agents with popular RL frameworks. 
- **🎮 Play as Agent or User**: Interactive mode lets you control either the agent or the user in conversations
- **📊 Train/Test Splits**: To help support experiments around training Agents and evaluating them, all domains include standardized task splits for proper train/test evaluation.

> **⚠️ IMPORTANT FOR BACKWARD COMPATIBILITY**: If you are just evaluating an agent (not training), you **MUST** use the `base` task split to evaluate on the complete task set that matches the original τ²-bench structure. This ensures your results are comparable to previous evaluations and maintains consistency with the established benchmark. (If you don't specify a task split, it will default to `base`.)
- **🔧 Gymnasium Compatible**: Standard gym interface works with existing RL tools and libraries

[**→ See Gym Documentation**](src/tau2/gym/README.md) | [**→ Try CLI Play Mode**](#interactive-play-mode)

### 🏆 Live Leaderboard (v0.2.0)
The τ²-bench leaderboard is now live at **[taubench.com](https://taubench.com)**! 

- **📊 Interactive Rankings**: Compare model performance across all domains
- **📱 Mobile-Friendly**: View results on any device  
- **🔍 Detailed Analysis**: Explore trajectories and conversation flows
- **📥 Easy Submission**: Submit your results directly through the interface

[**→ Visit the Leaderboard**](https://taubench.com) | [**→ Submit Your Results**](#leaderboard-submission)

## Overview

$\tau^2$-bench implements a simulation framework for evaluating customer service agents across various domains.

**$\tau^2$-bench is the new iteration of the original $\tau$-bench**, featuring code fixes and an additional telecom domain.

Each domain specifies:
- a policy that the agent must follow
- a set of tools that the agent can use
- a set of tasks to evaluate the agent's performance
- Optionally: A set of tools that the user simulator can use

Domains are:
- `mock`
- `airline`
- `retail`
- `telecom`

All the information that an agent developer needs to build an agent for a domain can be accessed through the domain's API docs. See [View domain documentation](#view-domain-documentation) for more details.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sierra-research/tau2-bench
cd tau2-bench
```

2. Create a new environment (optional)

$\tau^2$-bench requires Python 3.10 or higher. You may create and activate a new environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install tau2

```bash
pip install -e .
```

This will enable you to run the `tau2` command.

**Note:** If you use `pip install .` (without `-e`), you'll need to set the `TAU2_DATA_DIR` environment variable to point to your data directory:

```bash
export TAU2_DATA_DIR=/path/to/your/tau2-bench/data
```

**Check your data directory setup:**

After installation, you can verify that your data directory is correctly configured by running:

```bash
tau2 check-data
```

This command will check if the data directory exists and print instructions if it is missing.

To remove all the generated files and the virtual environment, run:
```bash
make clean
```

## Quick Start

### Setup LLM API keys

We use [LiteLLM](https://github.com/BerriAI/litellm) to manage LLM APIs, so you can use any LLM provider supported by LiteLLM.

To provide your API keys, copy `.env.example` as `.env` and edit it to include your API keys.

### OpenRouter로 5개 모델 평가하기 (한국어 가이드)

이 섹션은 OpenRouter를 통해 아래 5개 모델을 `tau2 run`으로 평가하고, 엑셀 리포트를 생성하는 실무용 절차를 설명합니다.

#### 평가 의도(무엇을 측정하나)

τ²-bench는 “정답 텍스트 한 줄”을 맞히는 벤치마크가 아니라, **고객센터 시나리오에서 에이전트가 정책을 지키며 도구를 사용해 상태(DB)를 올바르게 바꾸고, 사용자에게 필요한 정보를 전달하는지**를 측정합니다. 오케스트레이터가 Agent ↔ UserSimulator ↔ Environment(툴/DB)를 중재하며 여러 턴의 대화를 시뮬레이션합니다(README 하단 Orchestration Sequence Diagram 참고).

#### 평가 카테고리(도메인)

- **Retail**: 주문 조회/반품/교환/주소·결제 변경 등 전자상거래 고객센터 업무
- **Airline**: 항공 예약/변경/좌석/마일리지 등 여행 고객센터 업무
- **Telecom**: 요금제/장애/청구/개통 등 통신 고객센터 업무

#### 평가 지표(스코어)와 산식

- **Success(성공/실패)**: 한 trial의 최종 성공 여부. τ²-bench 코드 기준으로 **`reward == 1.0(±1e-6)`이면 성공**입니다(`src/tau2/metrics/agent_metrics.py:is_successful`).
- **Reward (0~1)**: `reward_info.reward`로 기록됩니다. 실전적으로는 성공이면 1.0, 아니면 0.0에 가깝게 나오는 경우가 많습니다(도메인별 체크가 모두 충족되어야 1.0).
- **Pass^k (k=1..n)**: 같은 Task를 `n`번(trials) 실행했을 때, **그 중 k개를 동시에 성공할 확률 기반**으로 계산합니다.
  - 산식(코드): \( \mathrm{Pass}^k = \binom{c}{k} / \binom{n}{k} \)  (n=총 시행 수, c=성공 횟수)
  - 집계: Task별 Pass^k를 평균내어 도메인 점수로 보고, 도메인 점수들을 평균(매크로 평균)해 전체 요약을 만듭니다.

#### OpenRouter 설정

OpenRouter는 LiteLLM provider로 호출됩니다.

- **모델 표기 규칙**: `openrouter/<provider>/<model>` 형태
- **API 키 설정(둘 중 하나)**:
  - 환경변수: `export OPENROUTER_API_KEY="..."`  
  - 또는 `.env` 파일에 `OPENROUTER_API_KEY=...` 추가(키는 절대 커밋하지 마세요)

#### 평가 대상 모델(요청하신 5개)

- `openrouter/meta-llama/llama-3.3-70b-instruct`
- `openrouter/mistralai/mistral-small-3.2-24b-instruct`
- `openrouter/qwen/qwen3-32b`
- `openrouter/qwen/qwen3-14b`
- `openrouter/qwen/qwen3-next-80b-a3b-instruct`

#### Quick 평가 CLI(연결/포맷/리포트 확인용)

아래는 “정말 빠르게” API 연동/툴콜/리포트 생성 파이프라인만 확인하는 예시입니다.

```bash
export OPENROUTER_API_KEY="YOUR_KEY"

tau2 run \
  --domain retail \
  --agent-llm openrouter/qwen/qwen3-32b \
  --user-llm openrouter/qwen/qwen3-32b \
  --num-trials 1 \
  --num-tasks 1 \
  --max-concurrency 3 \
  --log-level ERROR

python3 generate_excel_report.py
```

#### Full 평가 CLI(Leaderboard 방식에 준하는 실행)

Leaderboard 제출 규칙과 동일하게 하려면 **도메인 3개(retail/airline/telecom)를 모두**, 그리고 **같은 agent/user LLM 설정을 일관되게** 사용해야 합니다(README의 “Consistent model configuration” 참고).

```bash
export OPENROUTER_API_KEY="YOUR_KEY"

tau2 run --domain retail  --agent-llm openrouter/qwen/qwen3-32b --user-llm openrouter/qwen/qwen3-32b --num-trials 4 --task-split base --save-to qwen3-32b_retail
tau2 run --domain airline --agent-llm openrouter/qwen/qwen3-32b --user-llm openrouter/qwen/qwen3-32b --num-trials 4 --task-split base --save-to qwen3-32b_airline
tau2 run --domain telecom --agent-llm openrouter/qwen/qwen3-32b --user-llm openrouter/qwen/qwen3-32b --num-trials 4 --task-split base --save-to qwen3-32b_telecom
```

#### 5개 모델 자동 실행 스크립트

레포 루트의 `run_evaluation.sh`는 위 5개 모델 × 3개 도메인을 순차 실행하고, 실행 후 `generate_excel_report.py`로 리포트를 갱신합니다.

```bash
export OPENROUTER_API_KEY="YOUR_KEY"
./run_evaluation.sh
```

#### 엑셀 리포트(`generate_excel_report.py`) 구성(요약)

리포트는 사람이 바로 읽을 수 있게 **3개 시트만 노출**합니다.

- **요약**: 모델 랭킹 + 모델×도메인 Pass^k 매트릭스
- **런**: Run 단위(요청/GT/툴/최종응답/결과/근거). 원본 JSON/툴응답은 숨김 컬럼을 펼쳐 확인
- **턴**: 턴 단위 원문(디버깅용). ToolCalls/ToolResult는 기본 숨김

#### OpenRouter에서 실제로 겪을 수 있는 이슈(운영 팁)

- **HTTP 503 (No instances available)**: 해당 시점에 provider 쪽 가용 인스턴스가 부족한 상황입니다. 모델 성능 문제가 아니라 **호스팅 수용량 이슈**일 가능성이 큽니다.
  - 대응: 재시도, `--max-concurrency` 감소, 시간대 변경
- **HTTP 422 (요청 포맷 거부)**: 특정 provider 조합에서 tool calling 스키마 검증이 엄격해 요청이 차단될 수 있습니다.
  - 대응: LiteLLM/tau2 최신화, provider/route 변경(가능한 경우), 재시도
- **LiteLLM cost mapping 경고**: 일부 모델은 비용 테이블에 매핑이 없어서 cost 계산이 0이거나 경고가 날 수 있습니다. 평가 자체(성공/실패, Pass^k)와는 별개지만 로그 노이즈가 될 수 있습니다.

### Run agent evaluation

To run a test evaluation on only 5 tasks with 1 trial per task, run:

```bash
tau2 run \ 
--domain airline \
--agent-llm gpt-4.1 \
--user-llm gpt-4.1 \
--num-trials 1 \
--num-tasks 5
```

Results will be saved in `data/tau2/simulations/`.

> **💡 Tip**: For full agent evaluation that matches the original τ²-bench methodology, remove `--num-tasks` and use `--task-split base` to evaluate on the complete task set.

## Command Line Interface

The `tau2` command provides a unified interface for all functionality:

### Running Benchmark 
```bash
tau2 run \
  --domain <domain> \
  --agent-llm <llm_name> \
  --user-llm <llm_name> \
  --num-trials <trial_count> \
  --task-ids <task_ids> \
  --max-concurrency <concurrent_sims> \
  ...
```

### Interactive Play Mode
```bash
tau2 play
```
Experience τ²-bench from either perspective! The play mode allows you to:
- **Play as Agent**: Manually control the agent's responses and tool calls
- **Play as User**: Control the user while an LLM agent handles requests (available in domains with user tools like telecom)
- **Understand tasks** by walking through scenarios step-by-step
- **Test strategies** before implementing them in code
- **Choose task splits** to practice on training data or test on held-out tasks

This is perfect for:
- Getting familiar with domain policies and tools from both perspectives
- Debugging task scenarios and conversation flows
- Developing intuition for agent strategies
- Testing user behavior and agent responses
- Training yourself before training your model!

See the [Gym Documentation](src/tau2/gym/README.md) for more details on using the gymnasium interface programmatically, including the `AgentGymEnv` (play as agent) and `UserGymEnv` (play as user).

### Viewing Results
```bash
tau2 view
```
This tool allows you to:
- Browse simulation files (in `data/tau2/simulations/`)
- View agent performance metrics
- View a particular simulation
- View task details

### View domain documentation
```bash
tau2 domain <domain>
```
Visit http://127.0.0.1:8004/redoc to see the domain policy and API documentation.

![domain_viewer1](figs/domain_viewer.png)

### Check data configuration
```bash
tau2 check-data
```
This command checks if your data directory is properly configured and all required files are present.

## Leaderboard Submission

To submit your agent results to the τ²-bench leaderboard, you need to prepare a valid submission package that meets specific requirements.

### Requirements for Valid Submissions

Your trajectory runs must follow these constraints:

1. **Complete domain coverage**: Include results for all three domains:
   - `retail`
   - `airline` 
   - `telecom`

2. **Consistent model configuration**: All trajectory files must use:
   - The same agent LLM with identical arguments across all domains
   - The same user simulator LLM with identical arguments across all domains

3. **One result per domain**: Each domain should appear exactly once in your submission

4. **All tasks completed**: Run evaluation on all tasks within each domain (don't use `--task-ids` or `--num-tasks` filters)

> **📝 Note**: For consistency with the original τ²-bench evaluation methodology, use the `base` task split when evaluating your agent to ensure you're testing on the complete, standard task set.

### Preparing Your Submission

#### Step 1: Run Evaluations
First, run your agent evaluation on all domains with consistent settings:

```bash
# Example: Run complete evaluation for all domains
tau2 run --domain retail --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-trials 4 --save-to my_model_retail
tau2 run --domain airline --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-trials 4 --save-to my_model_airline  
tau2 run --domain telecom --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-trials 4 --save-to my_model_telecom
```

**Important**: Use identical `--agent-llm`, `--user-llm`, and their arguments across all runs.

#### Step 2: Prepare Submission Package
Use the submission preparation tool to create your leaderboard submission:

```bash
tau2 submit prepare data/tau2/simulations/my_model_*.json --output ./my_submission
```

This command will:
- Verify all trajectory files are valid
- Check that submission requirements are met
- Compute performance metrics (Pass^k rates)
- Prompt for required metadata (model name, organization, contact email)
- Create a structured submission directory with:
  - `submission.json`: Metadata and metrics
  - `trajectories/`: Your trajectory files

#### Step 3: Validate Your Submission
Before submitting, validate your submission package:

```bash
tau2 submit validate ./my_submission
```

This will verify:
- All required files are present
- Trajectory files are valid
- Domain coverage is complete
- Model configurations are consistent

### Additional Options

#### Skip Verification (if needed)
```bash
tau2 submit prepare data/tau2/simulations/my_model_*.json --output ./my_submission --no-verify
```

#### Verify Individual Trajectory Files
```bash
tau2 submit verify-trajs data/tau2/simulations/my_model_*.json
```

### Submitting to the Leaderboard

Once your submission package is prepared and validated:

1. Review the generated `submission.json` file
2. Follow the submission guidelines in [web/leaderboard/public/submissions/README.md](web/leaderboard/public/submissions/README.md) to create a Pull Request
3. Keep your `trajectories/` directory for reference

The leaderboard will display your model's Pass^k success rates (k=1,2,3,4) across all domains.

## Experiments

### Experimental Code Directory

The `@experiments/` directory contains experimental features and research code that extends beyond the core tau2 benchmark. This directory is designed for community contributions of innovative approaches, prototypes, and new features that are not part of the core evaluation framework.

- **Purpose**: Research code and experimental features
- **Location**: `src/experiments/`
- **Usage**: Each experimental component has its own README with documentation
- **Status**: Experimental code is provided as-is and may not be fully tested or supported

For more details, see the [experiments README](src/experiments/README.md).

### Running Ablation Studies (No User, or Agent with Oracle Plan)
`telecom` domain enables running ablation studies.

1. Running an LLM in `no-user` mode. In this mode, the LLM is given all the tools and the information upfront.
Just choose `llm_agent_solo` as the agent and `dummy_user` as the user.

```bash
tau2 run \
  --domain telecom \
  --agent llm_agent_solo \
  --agent-llm gpt-4.1 \
  --user dummy_user \
  ...
```

2. Running an LLM in `oracle-plan` mode. In this mode, the LLM is given an oracle plan ahead of time alleviating the need for action planning.
Just choose `llm_agent_gt` as the agent.

```bash
tau2 run \
  --domain telecom \
  --agent llm_agent_gt \
  --agent-llm gpt-4.1 \
  --user-llm gpt-4.1 \
  ...
```

### Running Telecom Domain with Workflow Policy
To test the impact of policy format, we provide an additional "workflow" policy for the telecom domain.
To run using this policy, use the `telecom-workflow` domain.

```bash
tau2 run \
  --domain telecom-workflow \
  --agent-llm gpt-4.1 \
  --user-llm gpt-4.1 \
  ...
```

## Domains

For all the details see the domains [README](src/tau2/domains/README.md).

### Basics

- Code is located in `src/tau2/domains/`
- Data is located in `data/tau2/domains/`
- Each domain has its own configuration and task definitions

#### View domain-specific policy and API docs:
Run the following command to see the domain policy and API documentation.
```bash
tau2 env <domain>
```

Then visit http://127.0.0.1:8004/redoc

### Environment CLI (beta)

An interactive command-line interface for directly querying and testing domain environments. Features:
- Interactive query interface with domain-specific tools
- Support for multiple domains (airline, mock, etc.)
- Session management with history

To use:
```bash
make env-cli
```

Available commands:
- `:q` - quit the program
- `:d` - change domain
- `:n` - start new session (clears history)

Example usage:
```bash
$ make env-cli

Welcome to the Environment CLI!
Connected to airline domain.

Query (:n new session, :d change domain, :q quit)> What flights are available from SF to LA tomorrow?
Assistant: Let me check the flight availability for you...
[Flight details will appear here]
```

The Environment CLI is useful for:
- Testing domain tools and queries
- Debugging environment responses
- Exploring available domain functionality
- Quick domain interaction without starting the full server stack


## Run tests
To run the test suite use the command

```sh
make test
```

## Config

To configure the framework, see the [config](src/tau2/config.py) file.

### LLM Calls caching
LLM call caching is disabled by default.

To enable LLM calls caching:
    - Make sure `redis` is running.
    - Update the redis config in `config.py` if necessary.
    - Set `LLM_CACHE_ENABLED` to `True` in `config.py`


## Evaluate Your Own Agent
For local or remote agent evaluation, see our [agent developer guide](src/tau2/agent/README.md).

## Contributing

We welcome contributions to τ²-bench! Whether you're fixing bugs, adding new features, creating new domains, or contributing experimental research code, please see our [Contributing Guide](CONTRIBUTING.md) for detailed guidelines on:

- **Opening issues** before starting work
- **Branch naming conventions** and development workflow  
- **Code quality standards** and testing requirements
- **Pull request guidelines** for clean, reviewable contributions
- **Domain and experimental contributions** specific guidelines

For experimental features and research code, check out the [`@experiments/`](src/experiments/) directory.

## Orchestration Sequence Diagram

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant A as Agent
    participant U as UserSimulator
    participant E as Environment

    Note over O: Initialize(task)
    rect rgb(100, 150, 150)
        O->>A: get_init_state_info(message_history)
        A->>O: agent_state_info
        O->>U: get_init_state_info(message_history)
        U->>O: user_state_info
        O->>E: set_state(initialization_data, initialization_actions, message_history)
    end
    Note over O: Start simulation
    loop Pass messages between Agent, User, and Environment

        alt Agent/Env to User
            rect rgb(200, 150, 150)
            O->>U: generate_next_message(msg, user_state_info)
            U-->>O: (user_msg, user_state_info)
            end
            Note over O: Check if user_msg is STOP
        else User/Env to Agent
            rect rgb(100, 200, 100)
            O->>A: generate_next_message(msg, agent_state_info)
            A-->>O: (assistant_msg, agent_state_info)
            Note over O: Check if too many errors
            end
        else User/Agent to Environment
            rect rgb(150, 150, 200)
            O->>E: get_response(tool_call)
            E-->>O: tool_message
            end
        end
        Note over O: Check if max turns reached.
    end
    Note over O: Return simulation run
```

## Citation

```bibtex
@misc{barres2025tau2,
      title={$\tau^2$-Bench: Evaluating Conversational Agents in a Dual-Control Environment}, 
      author={Victor Barres and Honghua Dong and Soham Ray and Xujie Si and Karthik Narasimhan},
      year={2025},
      eprint={2506.07982},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2506.07982}, 
}
```
