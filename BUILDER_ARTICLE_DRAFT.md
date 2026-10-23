# EcoRescue AI: Giving environmental reports a fast first decision with Strands Decider 2B

Environmental incidents arrive in many forms: a leaking container, a polluted stream, illegal dumping, or a growing pile of waste near a public space. Before writing a response, an agent needs to make a small but meaningful decision: what level of attention should this report receive?

EcoRescue AI is a hackathon prototype that combines Strands Decider 2B with Amazon Bedrock through Strands Agents. Its goal is to demonstrate a hybrid agent architecture in which a compact decision model classifies the report and a generative model turns that classification into a clear action plan.

## The decision handed to Decider 2B

The app sends the incident report as the state and asks one typed choice question: should the report be classified as `emergency`, `urgent`, or `routine`? The criteria describe immediate danger, significant ongoing environmental harm, and lower-immediacy reports. Decider returns a choice and confidence instead of generating a paragraph.

The app displays the selected priority, confidence, and measured client round-trip time. If confidence is below the prototype's 0.60 threshold, it explicitly asks for human review rather than treating the prediction as certain. The threshold is a demonstration setting, not a validated safety standard.

## Why use a decision model and a generative model together?

A language model is useful for explaining a situation and drafting practical next steps. But a repeated classification can be separated into a narrow, typed decision. EcoRescue AI uses Decider for that choice, then passes the selected priority and original report to a Strands agent backed by Amazon Bedrock. Bedrock generates a concise response plan and is instructed not to claim that it has contacted anyone or invented missing facts.

This separation makes the decision inspectable: the category and confidence are shown independently from the generated explanation. It also makes the reusable decision recipe easy to adapt to other triage workflows.

## Reusable pattern

The repository includes `DECISION_PATTERN.md`, which documents the typed question, option criteria, API wiring, confidence handling, and integration steps. Another builder can replace the environmental categories with support queues, maintenance severity levels, or other policy labels while retaining the same pattern.

## What this prototype does not do

EcoRescue AI does not verify reports, contact emergency services, or dispatch responders. The confidence threshold is not a calibrated operational safety policy. Real deployments would need validated data, careful evaluation across languages and incident types, human oversight, privacy controls, and integration with authorized local agencies.

## Try it

The public repository includes the Streamlit app, requirements, setup instructions, demo script, and reusable decision pattern. To reproduce the demo, configure a Decider API key and AWS credentials with access to a Bedrock model, install the requirements, and run `streamlit run app.py`.

**Tags:** #strands-decider-2b #policy
