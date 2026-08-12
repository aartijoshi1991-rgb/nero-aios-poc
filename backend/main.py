from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import json
from groq import Groq

app = FastAPI(title="NERO AIOS POC")

# =========================================================
# GROQ CLIENT
# =========================================================

api_key = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=api_key) if api_key else None


# =========================================================
# DEMO STATE
# One telemetry snapshot stays fixed until "Run AI Analysis"
# is pressed again.
# =========================================================

def create_demo_telemetry():
    return [
        {
            "gpu_id": "GPU-01",
            "vendor": "NVIDIA",
            "utilization_percent": 52,
            "temperature_c": 61,
            "power_watts": 215,
            "memory_used_gb": 14,
            "status": "HEALTHY"
        },
        {
            "gpu_id": "GPU-02",
            "vendor": "NVIDIA",
            "utilization_percent": 96,
            "temperature_c": 88,
            "power_watts": 348,
            "memory_used_gb": 28,
            "status": "CRITICAL"
        },
        {
            "gpu_id": "GPU-03",
            "vendor": "NVIDIA",
            "utilization_percent": 58,
            "temperature_c": 63,
            "power_watts": 225,
            "memory_used_gb": 16,
            "status": "HEALTHY"
        },
        {
            "gpu_id": "GPU-04",
            "vendor": "NVIDIA",
            "utilization_percent": 44,
            "temperature_c": 59,
            "power_watts": 205,
            "memory_used_gb": 12,
            "status": "HEALTHY"
        },
        {
            "gpu_id": "GPU-05",
            "vendor": "NVIDIA",
            "utilization_percent": 67,
            "temperature_c": 68,
            "power_watts": 245,
            "memory_used_gb": 21,
            "status": "HEALTHY"
        },
        {
            "gpu_id": "GPU-06",
            "vendor": "NVIDIA",
            "utilization_percent": 49,
            "temperature_c": 57,
            "power_watts": 198,
            "memory_used_gb": 13,
            "status": "HEALTHY"
        },
        {
            "gpu_id": "GPU-07",
            "vendor": "NVIDIA",
            "utilization_percent": 31,
            "temperature_c": 55,
            "power_watts": 190,
            "memory_used_gb": 10,
            "status": "HEALTHY"
        },
        {
            "gpu_id": "GPU-08",
            "vendor": "NVIDIA",
            "utilization_percent": 62,
            "temperature_c": 65,
            "power_watts": 230,
            "memory_used_gb": 18,
            "status": "HEALTHY"
        }
    ]


telemetry_state = create_demo_telemetry()
analysis_state = None
action_state = None


# =========================================================
# HELPERS
# =========================================================

def get_rack_telemetry():
    return {
        "rack_id": "NERO-RACK-001",
        "telemetry": telemetry_state
    }


def calculate_local_fallback_analysis(telemetry):
    critical = [
        gpu for gpu in telemetry
        if gpu["status"] == "CRITICAL"
    ]

    issues = []

    for gpu in critical:
        issues.append({
            "device": gpu["gpu_id"],
            "severity": "CRITICAL",
            "issue": (
                f'{gpu["gpu_id"]} is operating at '
                f'{gpu["temperature_c"]}°C, '
                f'{gpu["utilization_percent"]}% utilization and '
                f'{gpu["power_watts"]}W power consumption.'
            ),
            "recommendation": (
                f'Rebalance workload from {gpu["gpu_id"]} '
                'to a cooler, underutilized GPU.'
            )
        })

    return {
        "overall_status": "CRITICAL" if critical else "HEALTHY",
        "summary": (
            "Critical GPU infrastructure condition detected. "
            "Immediate workload redistribution is recommended."
            if critical else
            "All GPUs are operating within normal demo ranges."
        ),
        "issues": issues,
        "optimization_opportunities": [
            "Redistribute workloads away from thermally stressed GPUs.",
            "Prefer cooler GPUs with available compute capacity.",
            "Continuously monitor GPU temperature, power and utilization."
        ]
    }


def run_ai_analysis(telemetry):
    global analysis_state

    # If Groq is not configured, use deterministic fallback so the
    # dashboard still works for the demo.
    if client is None:
        analysis_state = calculate_local_fallback_analysis(telemetry)
        return analysis_state

    prompt = f"""
You are NERO AIOS, an AI infrastructure intelligence system.

Analyze this NVIDIA GPU telemetry:

{json.dumps(telemetry, indent=2)}

This is an infrastructure operations demo.

Identify only meaningful infrastructure issues.
Do NOT invent issues for healthy GPUs.

Return ONLY valid JSON using exactly this structure:

{{
  "overall_status": "HEALTHY or WARNING or CRITICAL",
  "summary": "short infrastructure summary",
  "issues": [
    {{
      "device": "GPU-02",
      "severity": "LOW or MEDIUM or HIGH or CRITICAL",
      "issue": "description",
      "recommendation": "recommended action"
    }}
  ],
  "optimization_opportunities": [
    "recommendation 1",
    "recommendation 2"
  ]
}}

If a GPU is healthy, do not put it in issues.

Do not include markdown.
Do not include ```json.
Return only valid JSON.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI infrastructure operations expert. "
                        "Always return valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )

        text = response.choices[0].message.content.strip()
        analysis_state = json.loads(text)
        return analysis_state

    except Exception as exc:
        # Keep the demo usable even if the LLM is temporarily unavailable.
        analysis_state = calculate_local_fallback_analysis(telemetry)
        analysis_state["ai_note"] = (
            "Fallback analysis used because the LLM request failed."
        )
        return analysis_state


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "product": "NERO AIOS",
        "status": "running",
        "message": "NERO AIOS Control Plane is online"
    }


# =========================================================
# RACK
# =========================================================

@app.get("/rack")
def rack():
    critical_count = sum(
        1 for gpu in telemetry_state
        if gpu["status"] == "CRITICAL"
    )

    return {
        "rack_id": "NERO-RACK-001",
        "status": "CRITICAL" if critical_count else "HEALTHY",
        "servers": 2,
        "gpus": 8,
        "critical_gpus": critical_count,
        "network_devices": 1,
        "storage_devices": 1,
        "power_devices": 1,
        "cooling_devices": 1
    }


# =========================================================
# DEVICE INVENTORY
# =========================================================

@app.get("/devices")
def devices():
    result = [
        {
            "id": "SERVER-01",
            "type": "SERVER",
            "vendor": "NERO",
            "status": "HEALTHY"
        },
        {
            "id": "SERVER-02",
            "type": "SERVER",
            "vendor": "NERO",
            "status": "HEALTHY"
        }
    ]

    for gpu in telemetry_state:
        result.append({
            "id": gpu["gpu_id"],
            "type": "GPU",
            "vendor": "NVIDIA",
            "status": gpu["status"]
        })

    result.extend([
        {
            "id": "NETWORK-01",
            "type": "NETWORK",
            "vendor": "NERO",
            "status": "HEALTHY"
        },
        {
            "id": "STORAGE-01",
            "type": "STORAGE",
            "vendor": "NERO",
            "status": "HEALTHY"
        },
        {
            "id": "PDU-01",
            "type": "POWER",
            "vendor": "NERO",
            "status": "HEALTHY"
        },
        {
            "id": "COOLING-01",
            "type": "COOLING",
            "vendor": "NERO",
            "status": "HEALTHY"
        }
    ])

    return {
        "rack_id": "NERO-RACK-001",
        "devices": result
    }


# =========================================================
# TELEMETRY
# =========================================================

@app.get("/telemetry")
def telemetry():
    return get_rack_telemetry()


# =========================================================
# RUN AI ANALYSIS
# =========================================================

@app.post("/analyze")
def analyze_infrastructure():
    global telemetry_state, analysis_state, action_state

    # Start a fresh demo scenario only when the user explicitly
    # presses Run AI Analysis.
    telemetry_state = create_demo_telemetry()
    action_state = None

    analysis = run_ai_analysis(telemetry_state)

    return {
        "rack_id": "NERO-RACK-001",
        "telemetry": telemetry_state,
        "ai_analysis": analysis
    }


# GET is kept for compatibility with your existing URLs.
@app.get("/analyze")
def get_analysis():
    global analysis_state

    if analysis_state is None:
        analysis = run_ai_analysis(telemetry_state)
    else:
        analysis = analysis_state

    return {
        "rack_id": "NERO-RACK-001",
        "telemetry": telemetry_state,
        "ai_analysis": analysis
    }


# =========================================================
# DECISION ENGINE
# Uses THE SAME telemetry snapshot shown on the dashboard.
# =========================================================

def select_best_target_gpu(source_gpu, telemetry):
    candidates = [
        gpu for gpu in telemetry
        if (
            gpu["gpu_id"] != source_gpu
            and gpu["status"] == "HEALTHY"
            and gpu["temperature_c"] < 75
            and gpu["utilization_percent"] < 70
        )
    ]

    if not candidates:
        return None

    def score(gpu):
        temperature_score = 100 - gpu["temperature_c"]
        utilization_score = 100 - gpu["utilization_percent"]
        power_score = 400 - gpu["power_watts"]
        memory_score = 32 - gpu["memory_used_gb"]

        return (
            temperature_score * 0.35
            + utilization_score * 0.35
            + power_score * 0.15
            + memory_score * 0.15
        )

    return max(candidates, key=score)


@app.get("/decision/rebalance")
def rebalance_decision():
    telemetry = telemetry_state

    problem_gpus = [
        gpu for gpu in telemetry
        if (
            gpu["status"] == "CRITICAL"
            or gpu["temperature_c"] >= 80
            or gpu["power_watts"] >= 330
            or gpu["utilization_percent"] >= 90
        )
    ]

    if not problem_gpus:
        return {
            "decision": "NO_ACTION",
            "message": "No GPU currently requires workload redistribution."
        }

    source_gpu = max(
        problem_gpus,
        key=lambda gpu: (
            gpu["temperature_c"],
            gpu["power_watts"],
            gpu["utilization_percent"]
        )
    )

    target_gpu = select_best_target_gpu(
        source_gpu["gpu_id"],
        telemetry
    )

    if target_gpu is None:
        return {
            "decision": "NO_SAFE_TARGET",
            "source_gpu": source_gpu["gpu_id"],
            "message": "No suitable target GPU is currently available."
        }

    return {
        "decision": "WORKLOAD_REBALANCE",
        "source_gpu": source_gpu["gpu_id"],
        "target_gpu": target_gpu["gpu_id"],
        "reason": (
            f'{source_gpu["gpu_id"]} is critically loaded at '
            f'{source_gpu["utilization_percent"]}% utilization, '
            f'{source_gpu["temperature_c"]}°C and '
            f'{source_gpu["power_watts"]}W. '
            f'{target_gpu["gpu_id"]} has available capacity and '
            f'is operating at {target_gpu["temperature_c"]}°C.'
        )
    }


# =========================================================
# ACTION ENGINE
# =========================================================

class RebalanceRequest(BaseModel):
    source_gpu: str
    target_gpu: str


@app.post("/actions/rebalance")
def rebalance_workload(request: RebalanceRequest):
    global telemetry_state, action_state

    source_gpu = request.source_gpu
    target_gpu = request.target_gpu

    if source_gpu == target_gpu:
        return {
            "action": "WORKLOAD_REBALANCE",
            "status": "REJECTED",
            "message": "Source and target GPU cannot be the same."
        }

    source = next(
        (gpu for gpu in telemetry_state
         if gpu["gpu_id"] == source_gpu),
        None
    )

    target = next(
        (gpu for gpu in telemetry_state
         if gpu["gpu_id"] == target_gpu),
        None
    )

    if not source or not target:
        return {
            "action": "WORKLOAD_REBALANCE",
            "status": "REJECTED",
            "message": "Invalid source or target GPU."
        }

    if source["status"] != "CRITICAL":
        return {
            "action": "WORKLOAD_REBALANCE",
            "status": "REJECTED",
            "message": (
                f"{source_gpu} is no longer in a critical state. "
                "Run a new AI analysis."
            )
        }

    # -----------------------------------------------------
    # DEMO SIMULATION
    # Simulate workload movement and show an improvement.
    # -----------------------------------------------------

    moved_utilization = 25

    source["utilization_percent"] = max(
        20,
        source["utilization_percent"] - moved_utilization
    )

    source["temperature_c"] = max(
        62,
        source["temperature_c"] - 16
    )

    source["power_watts"] = max(
        220,
        source["power_watts"] - 70
    )

    source["status"] = "HEALTHY"

    target["utilization_percent"] = min(
        90,
        target["utilization_percent"] + moved_utilization
    )

    target["temperature_c"] = min(
        75,
        target["temperature_c"] + 5
    )

    target["power_watts"] = min(
        320,
        target["power_watts"] + 45
    )

    action_state = {
        "action": "WORKLOAD_REBALANCE",
        "source_gpu": source_gpu,
        "target_gpu": target_gpu,
        "status": "SIMULATED",
        "message": (
            f"Workload redistribution from {source_gpu} "
            f"to {target_gpu} simulated successfully."
        ),
        "result": (
            f"{source_gpu} temperature reduced to "
            f'{source["temperature_c"]}°C and utilization reduced to '
            f'{source["utilization_percent"]}%.'
        )
    }

    return action_state


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return r"""
<!DOCTYPE html>
<html>

<head>
<title>NERO AIOS</title>

<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
}

.header {
    padding: 25px;
    background: #020617;
    border-bottom: 1px solid #334155;
}

.header h1 {
    margin: 0;
    font-size: 28px;
}

.header p {
    color: #94a3b8;
}

.container {
    padding: 25px;
}

.cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 20px;
    margin-bottom: 25px;
}

.card {
    background: #1e293b;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #334155;
}

.card h3 {
    margin-top: 0;
    color: #94a3b8;
}

.value {
    font-size: 28px;
    font-weight: bold;
}

.section {
    background: #1e293b;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 25px;
    border: 1px solid #334155;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #334155;
}

.badge {
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
}

.healthy {
    background: #166534;
}

.warning {
    background: #854d0e;
}

.critical {
    background: #991b1b;
}

.issue {
    padding: 15px;
    margin-bottom: 10px;
    background: #0f172a;
    border-radius: 8px;
}

.recommendation {
    color: #94a3b8;
    margin-top: 8px;
}

.loading {
    color: #94a3b8;
}

button {
    margin-top: 12px;
    padding: 10px 18px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
}

.run-button {
    background: #2563eb;
    color: white;
}

.action-button {
    background: #16a34a;
    color: white;
}

.muted {
    color: #94a3b8;
}

.error {
    color: #fca5a5;
}
</style>

</head>

<body>

<div class="header">
    <h1>⚡ NERO AIOS</h1>
    <p>AI Infrastructure Control Plane</p>
</div>

<div class="container">

<div class="section">

    <h2>🤖 NERO AI CONTROL</h2>

    <p class="muted">
        Run an AI analysis to create a fresh infrastructure snapshot.
        Telemetry remains stable until you run analysis again.
    </p>

    <button class="run-button" onclick="runAIAnalysis()">
        ▶ Run AI Analysis
    </button>

    <span id="lastRun" class="muted"></span>

</div>

<div class="cards">

<div class="card">
    <h3>RACK STATUS</h3>
    <div id="rackStatus" class="value loading">--</div>
</div>

<div class="card">
    <h3>GPU COUNT</h3>
    <div id="gpuCount" class="value">8</div>
</div>

<div class="card">
    <h3>HEALTHY GPUs</h3>
    <div id="healthyCount" class="value">--</div>
</div>

<div class="card">
    <h3>CRITICAL GPUs</h3>
    <div id="criticalCount" class="value">--</div>
</div>

<div class="card">
    <h3>AVERAGE UTILIZATION</h3>
    <div id="avgUtil" class="value">--</div>
</div>

<div class="card">
    <h3>AI STATUS</h3>
    <div id="aiStatus" class="value">--</div>
</div>

</div>

<div class="section">

<h2>GPU TELEMETRY</h2>

<table>
<thead>
<tr>
<th>GPU</th>
<th>Utilization</th>
<th>Temperature</th>
<th>Power</th>
<th>Memory</th>
<th>Status</th>
</tr>
</thead>

<tbody id="gpuTable"></tbody>

</table>

</div>

<div class="section">

<h2>🤖 NERO AI INTELLIGENCE</h2>

<div id="aiSummary" class="loading">
    Press "Run AI Analysis" to start NERO intelligence.
</div>

<div id="issues"></div>

</div>

<div class="section">

<h2>⚡ NERO RECOMMENDED ACTION</h2>

<div id="actionPanel" class="loading">
    No action selected.
</div>

</div>

<div class="section">

<h2>💡 OPTIMIZATION OPPORTUNITIES</h2>

<div id="optimization" class="loading">
    Run AI Analysis first.
</div>

</div>

</div>

<script>

let currentDecision = null;

async function loadTelemetryOnly() {

    try {

        const response = await fetch("/telemetry");
        const data = await response.json();

        renderTelemetry(data.telemetry);

    } catch (error) {

        console.error(error);

    }
}


function renderTelemetry(gpus) {

    const table = document.getElementById("gpuTable");

    table.innerHTML = "";

    let totalUtilization = 0;
    let healthy = 0;
    let critical = 0;

    gpus.forEach(gpu => {

        totalUtilization += gpu.utilization_percent;

        if (gpu.status === "HEALTHY") {
            healthy++;
        }

        if (gpu.status === "CRITICAL") {
            critical++;
        }

        const statusClass = gpu.status.toLowerCase();

        table.innerHTML += `
        <tr>
            <td><strong>${gpu.gpu_id}</strong></td>
            <td>${gpu.utilization_percent}%</td>
            <td>${gpu.temperature_c}°C</td>
            <td>${gpu.power_watts} W</td>
            <td>${gpu.memory_used_gb} GB</td>
            <td>
                <span class="badge ${statusClass}">
                    ${gpu.status}
                </span>
            </td>
        </tr>
        `;
    });

    document.getElementById("healthyCount").innerText = healthy;
    document.getElementById("criticalCount").innerText = critical;

    document.getElementById("avgUtil").innerText =
        Math.round(totalUtilization / gpus.length) + "%";

    document.getElementById("rackStatus").innerText =
        critical > 0 ? "🔴 CRITICAL" : "🟢 HEALTHY";
}


async function runAIAnalysis() {

    const summary =
        document.getElementById("aiSummary");

    const issues =
        document.getElementById("issues");

    const optimization =
        document.getElementById("optimization");

    const actionPanel =
        document.getElementById("actionPanel");

    summary.innerText =
        "NERO is analyzing GPU telemetry...";

    issues.innerHTML = "";
    optimization.innerHTML = "Analyzing...";
    actionPanel.innerHTML = "NERO is evaluating possible actions...";

    try {

        // This is the ONLY place that creates a new demo snapshot.
        const response =
            await fetch("/analyze", {
                method: "POST"
            });

        const data =
            await response.json();

        renderTelemetry(data.telemetry);

        const analysis =
            data.ai_analysis;

        document.getElementById("aiStatus").innerText =
            analysis.overall_status;

        summary.innerText =
            analysis.summary;

        issues.innerHTML = "";

        const criticalIssues =
            analysis.issues.filter(
                issue =>
                    issue.severity === "CRITICAL" ||
                    issue.severity === "HIGH"
            );

        if (criticalIssues.length === 0) {

            issues.innerHTML =
                "<p class='muted'>No critical infrastructure issues detected.</p>";

        } else {

            criticalIssues.forEach(issue => {

                issues.innerHTML += `
                <div class="issue">

                    <strong>🔴 ${issue.device}</strong>

                    <p>
                        <strong>${issue.severity}</strong>
                    </p>

                    <p>
                        ${issue.issue}
                    </p>

                    <div class="recommendation">
                        Recommendation:
                        ${issue.recommendation}
                    </div>

                </div>
                `;

            });
        }

        optimization.innerHTML = "";

        analysis.optimization_opportunities.forEach(item => {

            optimization.innerHTML +=
                `<p>• ${item}</p>`;

        });

        document.getElementById("lastRun").innerText =
            "  • Analysis completed";

        // Now ask the decision engine to use THE SAME snapshot.
        await loadDecision();

    } catch (error) {

        summary.innerHTML =
            `<span class="error">AI analysis failed: ${error}</span>`;

    }
}


async function loadDecision() {

    const actionPanel =
        document.getElementById("actionPanel");

    try {

        const response =
            await fetch("/decision/rebalance");

        const decision =
            await response.json();

        currentDecision = decision;

        if (decision.decision !== "WORKLOAD_REBALANCE") {

            actionPanel.innerHTML = `
                <div class="issue">
                    <strong>✅ NO ACTION REQUIRED</strong>
                    <p>${decision.message}</p>
                </div>
            `;

            return;
        }

        actionPanel.innerHTML = `
            <div class="issue">

                <strong>🔴 CRITICAL CONDITION DETECTED</strong>

                <p>
                    NERO recommends moving workload:
                </p>

                <h2>
                    ${decision.source_gpu}
                    →
                    ${decision.target_gpu}
                </h2>

                <p>
                    ${decision.reason}
                </p>

                <button
                    class="action-button"
                    onclick="executeRecommendedAction()"
                >
                    ⚡ Execute Recommended Action
                </button>

            </div>
        `;

    } catch (error) {

        actionPanel.innerHTML =
            `<div class="error">Decision engine error: ${error}</div>`;

    }
}


async function executeRecommendedAction() {

    const actionPanel =
        document.getElementById("actionPanel");

    if (!currentDecision ||
        currentDecision.decision !== "WORKLOAD_REBALANCE") {

        actionPanel.innerHTML =
            "<p>No executable action is currently available.</p>";

        return;
    }

    actionPanel.innerHTML = `
        <div class="issue">
            <strong>⏳ Executing NERO action...</strong>
            <p>
                ${currentDecision.source_gpu}
                →
                ${currentDecision.target_gpu}
            </p>
        </div>
    `;

    try {

        const response =
            await fetch(
                "/actions/rebalance",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        source_gpu:
                            currentDecision.source_gpu,

                        target_gpu:
                            currentDecision.target_gpu
                    })
                }
            );

        const result =
            await response.json();

        if (result.status === "SIMULATED") {

            actionPanel.innerHTML = `
                <div class="issue">

                    <strong>✅ ACTION EXECUTED</strong>

                    <h2>
                        ${result.source_gpu}
                        →
                        ${result.target_gpu}
                    </h2>

                    <p>
                        ${result.message}
                    </p>

                    <div class="recommendation">
                        ${result.result}
                    </div>

                </div>
            `;

            // Show the post-action state.
            await loadTelemetryOnly();

            document.getElementById("rackStatus").innerText =
                "🟢 HEALTHY";

            document.getElementById("criticalCount").innerText =
                "0";

            document.getElementById("aiStatus").innerText =
                "RESOLVED";

            currentDecision = null;

        } else {

            actionPanel.innerHTML = `
                <div class="issue">
                    <strong>⚠️ ACTION REJECTED</strong>
                    <p>${result.message}</p>
                </div>
            `;
        }

    } catch (error) {

        actionPanel.innerHTML = `
            <div class="issue">
                <strong>❌ ACTION FAILED</strong>
                <p>${error}</p>
            </div>
        `;

    }
}


// Initial screen shows the stable demo telemetry.
// It does NOT automatically call AI analysis.
loadTelemetryOnly();

</script>

</body>
</html>
"""


# =========================================================
# RUN
# =========================================================

# Start with:
# uvicorn main:app --reload
