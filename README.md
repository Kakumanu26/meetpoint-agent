# MeetPoint 🤝📍

An AI agent that turns "we should meet up" into an actual plan — in one conversation.

## `The Problem
Coordinating a meetup means juggling three apps: finding a fair location on maps, creating a calendar event, and messaging everyone. MeetPoint collapses all of it into a single chat.

## What it does?
Give it two or more locations and a time preference. It:
1. Computes a fair geographic midpoint and **snaps it to the nearest real town** so suggestions land on actual high streets, not fields
2. Returns a **Google Maps venue search link** for the meeting area
3. Generates a **pre-filled Google Calendar invite link**
4. Drafts a **ready-to-send WhatsApp message** (wa.me click-to-chat)


## Design decisions
- **URL-scheme integrations** (Maps search URLs, Calendar template links, wa.me) instead of full APIs — keyless, OAuth-free, reproducible by anyone who clones this repo
- **Deterministic Python tools** do the geometry; the LLM only orchestrates and reasons

## Architecture
Single ADK LLM agent + 3 pure-Python tools. No external API keys needed beyond Gemini.

## Setup
```bash
git clone https://github.com/Kakumanu26/meetpoint-agent.git
cd meetpoint-agent
uv venv && source .venv/bin/activate
uv pip install google-adk
echo "GOOGLE_API_KEY=your_key" > .env
adk web
```

## Demo
🎥 [Demo video](https://drive.google.com/file/d/16xP1beSE3gyqe-McI9DIqS8MlS02nZlC/view?usp=sharing)

## Built with
Vibe-coded in **Google Antigravity** for the Kaggle x Google 5-Day AI Agents Intensive capstone - I acted as architect, the agent wrote the code.
