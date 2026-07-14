# Financial Advisor Multi-Agent System

A modular, multi-agent financial planning and advisory system built using the **Google Agent Development Kit (ADK)** and the **Vertex AI Agent Platform**. 

The system leverages specialized sub-agents orchestrated by a coordinator to provide users with tailored math, guidance, and education on budgeting, debt management, home affordability, investments, and retirement planning.

---

## 🏗️ Architecture & Specialist Agents

The system uses a coordinator-specialist pattern. All user inquiries are routed by a central **Coordinator Agent** which executes safety checks and dispatches requests to the appropriate specialist:

*   **Home Buying Advisor:** Property tax, insurance, mortgage math, and affordability guidelines.
*   **Retirement Planner:** Timeline planning, IRA/401(k) comparisons, and compound growth education.
*   **Investment Advisor:** Corporate finance statements, individual stock risks, and low-cost index funds.
*   **Budgeting Expert:** Income allocation and cashflow guidance.
*   **Debt Advisor:** Debt reduction strategies.
*   **Windfall Advisor:** Guidance on managing sudden financial gains.

---

## 🛠️ Environment Variables

Create a local `.env` file in the root of the project to set up your environment:

```env
# Gemini API Key for local testing and playground runs
GEMINI_API_KEY="your_gemini_api_key"

# Google Cloud project details (used for local test mocks and deployment metadata)
GOOGLE_CLOUD_PROJECT="rm-fde-training-sandbox-122462"
GOOGLE_CLOUD_LOCATION="us-east1"

# Allowed CORS origins for the FastAPI server (comma-separated)
ALLOW_ORIGINS="*"
```

---

## 🚀 Local Development & Testing

This project uses `uv` for python package and environment management.

### 1. Installation
Install the project dependencies and sync the virtual environment:
```bash
uv sync
```

### 2. Run the Local Test Suite
Execute the unit and integration tests (validating the FastAPI server and routing endpoints):
```bash
uv run pytest tests/unit tests/integration
```

### 3. Run Agent Evaluations
Evaluate agent performance across 13 diverse financial scenarios using the local evaluation script:
```bash
uv run python run_evals.py
```

### 4. Interactive Playground
Test the agents interactively in your terminal using the CLI playground:
```bash
agents-cli playground
```

---

## ☁️ Deployment to Google Cloud (GCP)

Follow these steps to deploy the agent as an **Agent Engine / Reasoning Engine** service in Google Cloud.

### Prerequisites

1. **Install the Google Cloud SDK CLI (`gcloud`):**
   If you are on macOS:
   ```bash
   brew install --cask google-cloud-sdk
   ```
   Or download it from [Google Cloud CLI Docs](https://cloud.google.com/sdk/docs/install).

2. **Authenticate with your Google Cloud Account:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Configure your target GCP project:**
   ```bash
   gcloud config set project rm-fde-training-sandbox-122462
   ```

4. **Enable Required APIs:**
   ```bash
   gcloud services enable cloudbuild.googleapis.com \
                          secretmanager.googleapis.com \
                          aiplatform.googleapis.com
   ```

5. **Store your API Key in Secret Manager:**
   ```bash
   echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
   ```

### Deploy Command

Trigger the deployment using the `agents-cli` deploy tool. This will package your agent, set up the Cloud Run service, and link the Secret Manager secret for runtime execution:

```bash
agents-cli deploy \
  --project=rm-fde-training-sandbox-122462 \
  --region=us-east1 \
  --secrets="GEMINI_API_KEY=GEMINI_API_KEY"
```

Once deployment completes, the output will provide the API endpoint URIs for invoking your agent via HTTP or Vertex AI Console Playground.