import os
import json
import time
import urllib.request
import urllib.error
import streamlit as st
from strands import Agent
from strands.models import BedrockModel

st.set_page_config(page_title="EcoRescue AI", page_icon="🌱", layout="wide")

st.title("🌱 EcoRescue AI")
st.caption("A rapid-response environmental triage agent powered by Strands Decider 2B + Amazon Bedrock.")

DECIDER_URL = os.getenv("DECIDER_URL", "https://da25tnxy06gjk.cloudfront.net").rstrip("/")
DECIDER_API_KEY = os.getenv("DECIDER_API_KEY", "")
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-5-haiku-20241022-v1:0"
)

def decide_priority(report: str):
    if not DECIDER_API_KEY:
        raise RuntimeError("Missing DECIDER_API_KEY. Get a key from the AWS User Group Madurai hackathon kit, then set it in your environment.")
    payload = {
        "state": report,
        "questions": {
            "priority": {
                "type": "choice",
                "instructions": "Which response priority best fits this environmental incident report?",
                "criteria": {
                    "emergency": "Immediate threat to human life, active fire, hazardous chemical spill, or severe immediate danger",
                    "urgent": "Significant ongoing environmental harm that needs prompt action, but no clearly immediate threat to life",
                    "routine": "Low-immediacy issue suitable for normal reporting, monitoring, or scheduled cleanup"
                }
            }
        }
    }
    req = urllib.request.Request(
        f"{DECIDER_URL}/v1/decide",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {DECIDER_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=25) as response:
        result = json.loads(response.read().decode("utf-8"))
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    return result, elapsed_ms

def generate_plan(report: str, priority: str, confidence: float):
    model = BedrockModel(model_id=BEDROCK_MODEL_ID)
    agent = Agent(
        model=model,
        system_prompt=(
            "You are EcoRescue AI, an environmental incident response assistant. "
            "Give a concise, practical response plan based only on the incident description and the supplied priority. "
            "Do not claim to contact authorities or dispatch responders. Never invent facts, locations, or measurements. "
            "For immediate danger, tell the user to keep away and contact local emergency services or the appropriate environmental authority. "
            "Separate immediate safety steps from follow-up actions. State uncertainty when details are missing."
        ),
    )
    prompt = (
        f"Incident report:\n{report}\n\n"
        f"Priority selected by Strands Decider 2B: {priority} "
        f"(reported confidence: {confidence:.2f}).\n\n"
        "Explain briefly why this priority fits, then give 3-5 actionable next steps. "
        "Do not override the priority unless the report contains clear contradictory evidence."
    )
    return str(agent(prompt))

with st.sidebar:
    st.header("Configuration")
    st.write("This prototype uses a community-hosted Decider endpoint and your AWS Bedrock credentials.")
    st.code(f"Bedrock model: {BEDROCK_MODEL_ID}", language="text")
    st.caption("Do not paste API keys into this page or commit them to GitHub.")
    st.markdown("[Decider API setup article](https://builder.aws.com/content/3Ks9uHwd7uxGglJbLXmzB7l6Xed/strands-decider-2b-hosted-16-million-tokens-served-to-100-builders-a-month-and-a-zero-downtime-fix-on-air)")

st.markdown(
    "Describe a pollution, waste, wildlife, water, or public-space incident. "
    "Decider makes the priority choice first; Bedrock then generates a response plan."
)
report = st.text_area(
    "Environmental incident report",
    placeholder="Example: A strong chemical smell is coming from a leaking drum near a public footpath. People are walking nearby.",
    height=130,
)
col1, col2 = st.columns([1, 3])
with col1:
    run = st.button("Assess incident", type="primary", use_container_width=True)
with col2:
    st.caption("Prototype only. For real emergencies, keep away and contact local emergency services.")

if run:
    if len(report.strip()) < 12:
        st.warning("Please enter a little more detail about the incident.")
    else:
        try:
            with st.spinner("Decider 2B is evaluating priority..."):
                raw, latency_ms = decide_priority(report.strip())
            answer = raw.get("answers", {}).get("priority", {})
            priority = answer.get("choice", "routine")
            confidence = float(answer.get("confidence", 0.0))
            if priority not in {"emergency", "urgent", "routine"}:
                priority = "routine"
                confidence = 0.0

            st.subheader("Decision made by Strands Decider 2B")
            metric_cols = st.columns(3)
            metric_cols[0].metric("Selected priority", priority.upper())
            metric_cols[1].metric("Decider confidence", f"{confidence:.0%}")
            metric_cols[2].metric("Decision round trip", f"{latency_ms} ms")
            if confidence < 0.60:
                st.warning("Low confidence: treat this as uncertain and have a person review the incident before acting.")
            elif priority == "emergency":
                st.error("Potential immediate danger. Keep away and contact local emergency services / relevant authorities.")
            elif priority == "urgent":
                st.warning("Prompt human review and action are recommended.")
            else:
                st.info("Suitable for routine reporting, monitoring, or scheduled cleanup, subject to human review.")

            with st.spinner("Amazon Bedrock is generating an action plan..."):
                plan = generate_plan(report.strip(), priority, confidence)
            st.subheader("Bedrock response plan")
            st.write(plan)
            with st.expander("Technical details"):
                st.json({
                    "decision_pattern": "policy",
                    "model": raw.get("model", "model field not returned"),
                    "answers": raw.get("answers", {}),
                    "usage": raw.get("usage", {}),
                    "server_latency_ms": raw.get("latency_ms"),
                    "client_round_trip_ms": latency_ms,
                    "bedrock_model_id": BEDROCK_MODEL_ID,
                })
        except urllib.error.HTTPError as e:
            details = e.read().decode("utf-8", errors="replace")
            st.error(f"Decider API returned HTTP {e.code}. Check the API key/quota and try again. Details: {details[:500]}")
        except Exception as e:
            st.error(f"Could not complete the assessment: {e}")
            st.info("Check that DECIDER_API_KEY is set, AWS credentials work, and your selected Bedrock model is enabled in your AWS Region.")
