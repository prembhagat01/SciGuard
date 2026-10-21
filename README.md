# 🔬 SciGuard: The Autonomous Scientific Truth & Safety Firewall

> **Built for the 4th Annual Open Scientific Intelligence (OSI) Hackathon (October 21–22, 2026)**  
> **Physical Venue:** Yardi School of Artificial Intelligence (ScAI), IIT Delhi  

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![RDKit](https://img.shields.io/badge/RDKit-Cheminformatics-008080.svg)](https://rdkit.org)
[![NIH PubChem](https://img.shields.io/badge/PubChem-115M+-005EA2.svg)](https://pubchem.ncbi.nlm.nih.gov)
[![Google Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev)

---

## 📌 Executive Summary & The Problem

Large Language Models (LLMs) like GPT-4, Gemini, and Claude are transforming scientific research, but they have a fatal flaw: **Hallucinations in the physical sciences are dangerous and costly**.

* **Chemical Fabrications:** LLMs routinely output chemically impossible molecules (e.g. pentavalent carbon, invalid ring closures) or invent fictional compounds.
* **Laboratory Safety Catastrophes:** Models frequently recommend hazardous, pyrophoric, or explosive reaction conditions (e.g. boiling organic peroxides at 180°C) without safety warnings.
* **Fake Citations & Literature:** Generative models fabricate non-existent DOIs and unverified synthesis procedures.

**SciGuard** is an automated **Scientific Truth and Safety Firewall**. It sits between generative AI models and laboratory scientists, subjecting every proposed hypothesis, reaction, or molecular structure to programmatic, multi-layer verification against physical laws, open chemical databases, and process safety standards.

---

## ⚡ Key Features

1. **Physical & Valency Verification (RDKit Engine):**
   * Parses molecular SMILES and evaluates chemical valency, topological polar surface area (TPSA), logP, and bond constraints.
   * Catches quantum physics and valency violations instantly.

2. **Empirical Grounding (NIH PubChem Database):**
   * Queries the NIH PubChem PUG-REST API (115M+ verified compounds) in real time.
   * Distinguishes between real, experimentally validated compounds and fabricated hallucinations.

3. **Laboratory Hazard & Process Safety Audit (GHS Standards):**
   * Detects exothermic runaways, explosive peroxides, toxic gases, and water-reactive pyrophorics.
   * Pulls official UN GHS hazard classification codes (H-statements) and specifies mandatory personal protective equipment (PPE).

4. **Interactive 3D WebGL Conformer Viewer:**
   * Renders rotatable, interactive 3D molecular conformers using `3Dmol.js` right in the browser.

5. **Agentic Self-Correction Loop (Google Gemini 2.5):**
   * Diagnoses the root cause of the hallucination or hazard.
   * Autonomously re-synthesizes a certified, safe, stoichiometrically balanced laboratory protocol.

6. **Deterministic Scientific Trust Index (0–100%):**
   * Multi-factor scoring system providing an instant confidence badge: `VERIFIED_ACCURATE`, `PROCEED_WITH_CAUTION`, or `REJECTED_HALLUCINATION_OR_HAZARDOUS`.

---

## 🛠️ Architecture

```
[Raw User Prompt / LLM Synthesis Claim]
                    │
                    ▼
          ┌───────────────────┐
          │   SciGuard Engine │
          └─────────┬─────────┘
                    │
   ┌────────────────┼────────────────┬────────────────┐
   ▼                ▼                ▼                ▼
[1. Structural]  [2. Physics]    [3. Literature]  [4. Hazard]
  Validity        Conservation      Grounding       & Safety
 (RDKit SMILES)    (Mass/Atoms)    (PubChem API)   (GHS Hazards)
                    │
                    ▼
      ┌─────────────────────────────┐
      │  Autonomous Self-Correction │  <-- Agentic repair loop using Gemini
      │    & "Scientific Trust"     │      to re-synthesize reproducible
      │         Score (0-100%)      │      laboratory procedures
      └─────────────┬───────────────┘
                    │
                    ▼
     [Interactive Streamlit Dashboard]
     • 3D Interactive Conformer (3Dmol.js)
     • Audit Findings & GHS Badges
     • Green / Red Hallucination Diff
     • Exportable Validated Audit Report (JSON)
```

---

## 🚀 Quickstart & Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/SciGuard.git
cd SciGuard

pip install streamlit rdkit requests google-genai py3Dmol
```

### 2. Launch the Application
```bash
python -m streamlit run app.py
```
Open your browser to `http://localhost:8501`.

### 3. Add Optional API Key
* To enable full Gemini 2.5 Flash re-synthesis, paste your Google Gemini API key into the sidebar.
* **Works offline:** If no key is provided, SciGuard runs with its deterministic heuristic verification and rule engine!

---

## 📊 Scientific Hallucination Benchmark

SciGuard was evaluated against 8 standard generative chemistry failure modes:

| Test Case | Category | Raw LLM Output | SciGuard Verdict | Detection Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Pentavalent Carbon** | Chemical Physics | Generates `C(C)(C)(C)(C)C` | **REJECTED (0/100)** | RDKit Valency Check |
| **Fabricated Kinase Inhibitor** | Drug Discovery | Non-existent fluorinated ring | **REJECTED (35/100)** | PubChem Zero-Records |
| **Peroxide Reflux Runaway** | Process Safety | Boiling organic peroxide at 180°C | **REJECTED (40/100)** | GHS Thermal Explosion Rule |
| **Aspirin Synthesis** | Organic Synthesis | Salicylic acid + acetic anhydride | **VERIFIED (100/100)** | All Layers Passed |
| **MAPbI3 Perovskite** | Materials Science | Solar cell precursor | **VERIFIED (100/100)** | PubChem Grounding |

---

## 👥 Hackathon Team

* **Solo Developer:** Computer Science & AI Track
* **Event:** 4th Annual Open Scientific Intelligence (OSI) Hackathon (October 21–22, 2026)
* **Venue:** Yardi School of Artificial Intelligence (ScAI), IIT Delhi
