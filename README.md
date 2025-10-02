# Open Wind Instrument Design

This is the official repository of the  OpenWInD toolbox, a tool for modelization
of wind musical instruments, using one-dimensional Finite Elements Methods.
Our webpage is [here](https://openwind.inria.fr/).

## Installation

In your python [environment](https://docs.python.org/3/library/venv.html) :

```sh
pip install openwind
```

If you want to install from source, instructions can be found [here](https://files.inria.fr/openwind/docs/quickstart.html#install-from-source)

## Documentation

You can read the official documentation [here](https://files.inria.fr/openwind/docs).

## Previous versions

If you are interested in early development versions, you can download them from  [our previous repository](https://gitlab.inria.fr/openwind/release/-/releases)

## Website

Our website is [here](https://openwind.inria.fr/).

## About

This toolbox stems from the work of several [contributors](https://openwind.inria.fr/contributions/), mainly from [Inria](https://www.inria.fr/).

Feel free to contact the team at [openwind-contact@inria.fr](mailto:openwind-contact@inria.fr)!

#### Note about participating to the project

If you want to get involved and help us developing the openwind toolbox, you will have to create an account on [gitlab.inria.fr](https://gitlab.inria.fr/)

At the moment, following [INRIA's policy](https://gitlab.inria.fr/siteadmin/doc/-/wikis/home#gitlab-accounts), you have to request this access through our team. In order to create your account, we need you to send us your Name, Surname and email address [here](mailto:openwind-contact@inria.fr). We promise we won't use it for anything else than granting you an access as developer to our project.

---

# OpenWInD Bb Clarinet Studio (local build)

This repository now ships a FastAPI microservice and React 18 client that wrap the OpenWInD
numerical engine for Bb clarinet design. The stack is tailored for Windows 11 one-shot setup via
PowerShell.

## Server (FastAPI)

* Location: `server/openwind_service`
* Entrypoint: `uvicorn openwind_service.main:app --host 127.0.0.1 --port 8001 --reload`
* Key endpoints (`/api/v1` prefix):
  * `GET /health` – service heartbeat.
  * `GET /presets/bb_clarinet` – default geometry and constraints.
  * `POST /recommend` – heuristic starter layout generator.
  * `POST /simulate` – impedance and intonation prediction.
  * `POST /optimize` & `GET /optimize/stream` – asynchronous geometry optimisation with SSE progress.
  * `POST /export/{json|csv|dxf|step}` – export utilities (STEP requires CadQuery).

The adapter layer sanitises inputs, feeds OpenWInD, and guards against numerical errors.
Exports are written under `exports/` and served read-only via `/exports`.

## Client (React + Vite)

* Location: `ui/`
* Start: `npm install` (or `pnpm install`) then `npm run dev`
* Pages:
  * **Home** – quick start and API status.
  * **Geometry Builder** – bore / tone-hole editing with validation and live persistence.
  * **Simulation** – impedance & intonation charts with debounced runs.
  * **Optimization** – SSE driven progress, objective tuning, convergence plots.
  * **Results** – exports and optimisation history.
  * **Settings** – persistent tuning & environment configuration.

The UI respects 44px touch targets, keyboard focus styles, dark-mode, and exposes accessible switch controls.

## Full-stack dependency install

You can install every Python and Node dependency from the repository root:

```powershell
python -m venv .\.venv
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt

npm install
```

The root `package.json` delegates to the `ui` workspace, so commands such as
`npm run build`, `npm run preview`, or `npm run dev` automatically execute in
the React project. Use `npm run check` to run a build followed by a preview
sanity check (`vite preview --help`).

## PowerShell one-shot setup

Run `./setup_and_run.ps1` from a Windows PowerShell prompt. The script:

1. Verifies Python 3.11 and Node.js 20+ availability.
2. Creates `.venv`, installs FastAPI dependencies, and installs OpenWInD editable.
3. Installs UI dependencies (`pnpm` preferred when available).
4. Launches Uvicorn on `http://127.0.0.1:8001` and Vite dev server on `http://127.0.0.1:5173`.
5. Opens the browser pointing at the studio.

Troubleshooting hints are in the script and below:

* CadQuery STEP export will return HTTP 501 when no wheel is available; install from https://cadquery.readthedocs.io/.
* SciPy may require the Microsoft C++ redistributable on Windows; install from Microsoft if builds fail.
* Allow both ports through Windows Defender firewall the first time the servers start.

## Smoke test

1. `./setup_and_run.ps1`
2. In the UI: load the preset, tweak bore diameter, observe auto-simulate.
3. Run optimisation for ~30 iterations and watch the SSE log fill.
4. Export JSON and DXF to `exports/`.

