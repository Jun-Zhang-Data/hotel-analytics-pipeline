from __future__ import annotations


def render_home_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hotel Analytics Chat</title>
  <style>
    :root {
      font-family: Inter, system-ui, sans-serif;
      color: #172033;
      background: #f4f6fa;
    }
    body {
      margin: 0;
    }
    main {
      max-width: 920px;
      margin: 48px auto;
      padding: 0 20px;
    }
    .card {
      background: white;
      border: 1px solid #dce2ec;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 10px 30px rgba(31, 45, 61, 0.08);
    }
    h1 {
      margin-top: 0;
    }
    .subtle {
      color: #5d6b82;
      line-height: 1.5;
    }
    .controls {
      display: grid;
      grid-template-columns: 1fr 1fr auto;
      gap: 12px;
      margin: 20px 0;
    }
    select,
    textarea,
    button {
      font: inherit;
    }
    select,
    textarea {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid #c9d2df;
      border-radius: 10px;
      padding: 10px 12px;
      background: white;
    }
    textarea {
      min-height: 110px;
      resize: vertical;
    }
    button {
      border: 0;
      border-radius: 10px;
      padding: 10px 16px;
      cursor: pointer;
      background: #1f5eff;
      color: white;
      font-weight: 600;
    }
    button:disabled {
      opacity: 0.6;
      cursor: wait;
    }
    .examples {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 12px 0 20px;
    }
    .example {
      background: #eef3ff;
      color: #24428f;
      font-weight: 500;
    }
    .answer {
      margin-top: 20px;
      padding: 16px;
      border-radius: 10px;
      background: #f7f9fc;
      min-height: 56px;
      white-space: pre-wrap;
    }
    details {
      margin-top: 16px;
    }
    pre {
      overflow-x: auto;
      background: #111827;
      color: #e5e7eb;
      padding: 14px;
      border-radius: 10px;
    }
    .error {
      color: #a61b1b;
    }
    @media (max-width: 720px) {
      .controls {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
<main>
  <div class="card">
    <h1>Hotel Analytics Chat</h1>
    <p class="subtle">
      Ask a governed analytics question. The app routes the question to an
      approved semantic domain, validates the metric and dimensions, and
      queries only the permitted domain mart.
    </p>

    <div class="controls">
      <label>
        Domain
        <select id="domain">
          <option value="auto">auto</option>
        </select>
      </label>
      <label>
        Parser
        <select id="parser">
          <option value="llm">llm</option>
          <option value="rules">rules</option>
        </select>
      </label>
      <label>
        <input id="details" type="checkbox">
        Show details
      </label>
    </div>

    <div class="examples">
      <button class="example" type="button"
        data-question="Which hotel generated the most revenue in September 2026?">
        Revenue by hotel
      </button>
      <button class="example" type="button"
        data-question="Which source system had the lowest data quality pass rate in September 2026?">
        DQ pass rate
      </button>
    </div>

    <textarea id="question"
      placeholder="Ask a stakeholder question..."></textarea>
    <div style="margin-top: 12px">
      <button id="ask" type="button">Ask</button>
    </div>

    <div id="answer" class="answer">Ready.</div>

    <details id="detailsPanel" hidden>
      <summary>Query details</summary>
      <pre id="detailsOutput"></pre>
    </details>
  </div>
</main>

<script>
const domainSelect = document.getElementById("domain");
const parserSelect = document.getElementById("parser");
const detailsCheckbox = document.getElementById("details");
const questionInput = document.getElementById("question");
const askButton = document.getElementById("ask");
const answerBox = document.getElementById("answer");
const detailsPanel = document.getElementById("detailsPanel");
const detailsOutput = document.getElementById("detailsOutput");

async function loadDomains() {
  const response = await fetch("/domains");
  const payload = await response.json();
  for (const item of payload.domains) {
    const option = document.createElement("option");
    option.value = item.domain;
    option.textContent = item.domain;
    domainSelect.appendChild(option);
  }
}

async function askQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    answerBox.textContent = "Please enter a question.";
    return;
  }

  askButton.disabled = true;
  answerBox.classList.remove("error");
  answerBox.textContent = "Running governed query...";
  detailsPanel.hidden = true;

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        question,
        domain: domainSelect.value,
        parser: parserSelect.value,
        include_details: detailsCheckbox.checked
      })
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Query failed.");
    }

    answerBox.textContent =
      "[" + payload.domain + "] " + payload.answer;

    if (detailsCheckbox.checked) {
      detailsOutput.textContent = JSON.stringify(payload, null, 2);
      detailsPanel.hidden = false;
    }
  } catch (error) {
    answerBox.classList.add("error");
    answerBox.textContent = error.message;
  } finally {
    askButton.disabled = false;
  }
}

document.querySelectorAll(".example").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
  });
});

askButton.addEventListener("click", askQuestion);
questionInput.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") {
    askQuestion();
  }
});

loadDomains().catch((error) => {
  answerBox.classList.add("error");
  answerBox.textContent = "Could not load domains: " + error.message;
});
</script>
</body>
</html>
"""
