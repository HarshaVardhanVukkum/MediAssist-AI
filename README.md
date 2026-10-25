# MediAssist AI — Healthcare Website Project

**Domain:** Healthcare Technology  
**Category:** Website Development  
**Level:** Intermediate  
**Stack:** Python, Flask, SQLite, HTML, CSS, JavaScript  
**AI approach:** Offline rule-based assistant, with optional Ollama local-model integration

## Project overview

MediAssist AI is an educational healthcare website prototype that demonstrates:
- User registration and login with hashed passwords
- Doctor directory using fictional sample doctors
- Appointment creation, listing, duplicate-slot checks, and cancellation
- Patient dashboard
- General health-information chatbot with an offline fallback
- Optional integration with a language model running locally through Ollama
- Admin dashboard with appointment counts, status distribution, and specialty summaries

All doctors, schedules, and appointments are fictional. Do not use this prototype to manage real patient information or deliver clinical care.

## Requirements

- Python 3.10 or newer (Python 3.12 recommended)
- VS Code
- Internet is not required for the basic application after dependencies are installed. The CSS uses a Google Fonts import as a visual enhancement; it falls back to system fonts if offline.
- Optional: Ollama and a compatible local model for generative responses

## Setup on Windows / VS Code

Open the `MediAssist-AI` folder in VS Code. In the VS Code terminal (PowerShell), run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run this for the current terminal only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open http://127.0.0.1:5000 in your browser.

If `py -3.12` is not available, use `python -m venv .venv` with an installed Python version 3.10+.

## Demo administrator login

- Email: `admin@mediassist.local`
- Password: `Admin123!`

This account is created locally on first launch. It is for a local demonstration only. Do not deploy with the default secret key or demo administrator password.

## Optional local AI with Ollama

1. Install Ollama from https://ollama.com/download.
2. Open a terminal and pull a model supported by your computer, for example:

   ```powershell
   ollama pull llama3.2
   ```

3. Start Ollama (the app expects its local API at `http://127.0.0.1:11434`).
4. In PowerShell, set the environment variable before starting Flask:

   ```powershell
   $env:OLLAMA_ENABLED = "true"
   $env:OLLAMA_MODEL = "llama3.2"
   python app.py
   ```

The local model is optional. If it is unavailable, the chatbot falls back to the offline rule-based assistant. Model responses can be inaccurate; the app gives general information only and must not be used for diagnosis or treatment.

## Feature walkthrough

1. Create a patient account from **Get started**.
2. Log in and open **Appointments**.
3. Select a demo doctor, future date, time, and brief non-sensitive reason.
4. Review or cancel your booking.
5. Open **AI Assistant** and try the suggested questions.
6. Log out and sign in with the demo administrator credentials.
7. Review **Admin** analytics. Mark a booked appointment as completed if desired.

## Testing checklist

- [ ] Home page and doctor directory load.
- [ ] Registration succeeds with a new email.
- [ ] Duplicate email registration is rejected.
- [ ] Incorrect login credentials are rejected.
- [ ] A patient can book a future appointment.
- [ ] The same doctor/date/time cannot be booked twice while the first is active.
- [ ] A patient can cancel their own booked appointment.
- [ ] A patient cannot open `/admin`.
- [ ] Admin login displays appointment and user counts.
- [ ] Chatbot answers the appointment and wellness prompts.
- [ ] Empty chatbot message is handled.
- [ ] Emergency-keyword message returns emergency guidance.
- [ ] App works with Ollama disabled.

## Known limitations

- This is a local assignment prototype, not a production healthcare service.
- Demo doctor schedules are descriptive only; the app does not enforce each doctor's published hours.
- No email, SMS, calendar, payment, or real appointment service is connected.
- Basic form/session protections are suitable only for local demonstration; a public deployment needs CSRF protection, secure production configuration, rate limiting, audit controls, privacy review, and security testing.
- The chatbot does not have a verified medical knowledge base and is not a clinical decision-support tool.
- The default Flask development server must not be exposed to the public internet.

## Suggested assignment report

### Title
MediAssist AI: Smart Healthcare Appointment and Patient Support Website

### Problem statement
People can find it inconvenient to keep track of appointments and locate basic healthcare information. This prototype demonstrates how a web application can organise demo bookings and provide a simple general-information assistant in one interface.

### Objectives
- Develop a responsive healthcare website.
- Implement registration, login, and database-backed appointment management.
- Add an AI-style assistant with an offline fallback and optional local LLM.
- Summarise appointment data in an admin dashboard.
- Demonstrate safe handling of sample data and limitations of AI in healthcare.

### Methodology
Requirements analysis → UI design → Flask routes and SQLite schema → chatbot integration → analytics → functional testing.

### AI tools used
- ChatGPT or another coding assistant: project planning, code explanation, debugging support, and test-case generation.
- Optional Ollama local language model: local natural-language responses.
- Offline rule-based assistant: deterministic fallback when a local model is not enabled.

In your final submission, list only the AI tools you actually used and describe your own changes and tests honestly.

### Expected outcome
A locally running website with patient accounts, demo appointment workflows, an assistant page, and a working admin analytics view.

### Future enhancements
- Doctor availability calendar and email reminders
- Secure appointment exports and CSV analytics
- Accessible multilingual interface
- Retrieval-based responses from reviewed public health sources
- Automated test suite and deployment hardening

## Suggested screenshots for submission

1. Home page
2. Register / login
3. Doctor directory
4. Appointment booking form and a saved booking
5. AI assistant responding to a prompt
6. Admin analytics after at least two sample bookings

## GitHub readiness

Before pushing to GitHub:
- Keep `.env`, database files, and personal data out of the repository.
- Change the Flask secret key for any shared environment.
- Never include real patient data.
- Explain the demo admin credentials in the README only if the repository remains a local educational demo.
