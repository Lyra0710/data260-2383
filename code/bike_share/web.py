"""Browser UI routes for the Capital Bikeshare recommendation agent."""

# ruff: noqa: E501

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from .agent import run_recommendation

DEFAULT_PRICING_URL = "https://capitalbikeshare.com/pricing"

router = APIRouter(prefix="/bike-share", tags=["Capital Bikeshare"])


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Capital Bikeshare Cost Recommendation</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #f5f7fa; color: #172033; margin: 0; }
    main { max-width: 960px; margin: 32px auto; padding: 0 18px 32px; }
    section { background: white; border: 1px solid #dbe2ea; border-radius: 8px; margin-top: 18px; padding: 20px; }
    label { display: block; font-weight: 600; margin-top: 12px; }
    input { box-sizing: border-box; margin-top: 6px; padding: 9px; width: 100%; }
    button { background: #1958a8; border: 0; border-radius: 5px; color: white; cursor: pointer; margin-top: 16px; padding: 10px 16px; }
    button:disabled { background: #71809a; cursor: wait; }
    .metrics { display: flex; flex-wrap: wrap; gap: 12px; }
    .metric { background: #edf3fc; border-radius: 5px; padding: 10px; min-width: 130px; }
    pre { background: #f5f7fa; overflow-wrap: anywhere; padding: 12px; white-space: pre-wrap; }
    #status { color: #4d5b70; }
  </style>
</head>
<body>
  <main>
    <h1>Capital Bikeshare Membership Recommendation</h1>
    <p>Compare one uploaded trip CSV with an official Capital Bikeshare pricing policy.</p>
    <section>
      <form id="recommendation-form">
        <label for="trip-file">Trip CSV</label>
        <input id="trip-file" name="trip_file" type="file" accept=".csv,text/csv" required>
        <label for="pricing-url">Official pricing URL</label>
        <input id="pricing-url" name="pricing_url" type="url" required value="__DEFAULT_PRICING_URL__">
        <button id="run-button" type="submit">Run recommendation</button>
      </form>
      <p id="status">Upload a CSV and run the agent.</p>
    </section>
    <section>
      <h2>Tool-call timeline</h2>
      <ol id="timeline"><li>No run yet.</li></ol>
    </section>
    <section>
      <h2>Cost comparison and decision</h2>
      <pre id="answer">No run yet.</pre>
      <p id="citation"></p>
      <div class="metrics">
        <div class="metric">Steps: <span id="steps">—</span></div>
        <div class="metric">Total time: <span id="time">—</span></div>
        <div class="metric">Stop reason: <span id="stop">—</span></div>
      </div>
    </section>
  </main>
  <script>
    const form = document.getElementById('recommendation-form');
    const button = document.getElementById('run-button');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      button.disabled = true;
      document.getElementById('status').textContent = 'Running the tool-calling agent...';
      try {
        const response = await fetch('/bike-share/run', { method: 'POST', body: new FormData(form) });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'The run failed.');
        const timeline = document.getElementById('timeline');
        timeline.replaceChildren();
        result.timeline.forEach((item) => {
          const entry = document.createElement('li');
          entry.textContent = `${item.step}. ${item.tool} — ${item.observation}`;
          timeline.appendChild(entry);
        });
        document.getElementById('answer').textContent = result.final_answer || 'No final answer was produced.';
        document.getElementById('citation').textContent = `Policy sources: ${result.citation.urls.join(' | ')} | Accessed: ${result.citation.accessed_at}`;
        document.getElementById('steps').textContent = result.step_count;
        document.getElementById('time').textContent = `${result.total_time_ms} ms`;
        document.getElementById('stop').textContent = result.stop_reason;
        document.getElementById('status').textContent = 'Run complete.';
      } catch (error) {
        document.getElementById('status').textContent = error.message;
      } finally {
        button.disabled = false;
      }
    });
  </script>
</body>
</html>""".replace("__DEFAULT_PRICING_URL__", DEFAULT_PRICING_URL)


@router.get("", response_class=HTMLResponse)
def bike_share_page() -> str:
    """Serve the small browser UI."""

    return PAGE


@router.post("/run")
async def bike_share_run(
    trip_file: UploadFile = File(...),
    pricing_url: str = Form(...),
) -> dict:
    """Run the agent for one uploaded CSV and one official policy URL."""

    if not trip_file.filename or not trip_file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file.")
    if not pricing_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Enter an http or https URL.")
    try:
        csv_text = (await trip_file.read()).decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="CSV must be UTF-8 text.",
        ) from error

    result = await run_recommendation(csv_text, pricing_url)
    result["citation"] = {
        "urls": result["policy_sources"] or [pricing_url],
        "accessed_at": datetime.now(timezone.utc).isoformat(),
    }
    return result
