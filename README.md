# Soumyajyoti Biswas

```text
role        cloud architect + automation engineer
focus       cloud architecture | automation engineering | reliability systems
building    observable platforms, repeatable workflows, and tools that reduce toil
current     turning real-world operations into safer, testable systems
```

![Cloud Architecture](https://img.shields.io/badge/Cloud-Architecture-1f6feb)
![Automation Engineering](https://img.shields.io/badge/Automation-Engineering-238636)
![Reliability Systems](https://img.shields.io/badge/Reliability-Systems-f78166)
![AWS](https://img.shields.io/badge/AWS-Platform-ff9900)

<p>
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=18&duration=2800&pause=900&color=58A6FF&width=820&lines=Cloud+architecture+with+automation+at+the+center;Reliability+systems+that+make+operations+calmer;Tools%2C+tests%2C+docs%2C+and+guardrails+for+real+workflows" alt="Typing SVG" />
</p>

I design cloud platforms and build the automation that keeps them reliable.

My work sits between architecture and execution: taking operationally messy systems, finding the repeatable shape, and building the tooling, observability, documentation, and safety rails around them.

## Featured Work

### [trade-ops-cli](https://github.com/soumyajyotibiswas/trade-ops-cli)

A terminal broker-operations CLI built around API reliability, dry-run safety, and mocked broker workflows.

What it shows:

- Broker API orchestration for 5paisa and Kotak Neo.
- Dry-run mode for order placement and cancellation safety.
- Offline unit tests that mock live broker calls.
- Session-cache hardening, SSL/CA handling, atomic JSON writes, and structured logging.
- Expiry/date logic with NSE holiday-aware tests.
- GitHub Actions CI, Ruff, compile checks, and dependency lockfiles.

Why the broker split exists:

- 5paisa is used for quote-heavy workflows because its quote API has been dependable for this use case.
- Kotak Neo is used for trade execution because API trades are zero brokerage in this setup.

## What I Build

| Area                   | Shape of the work                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------- |
| Cloud architecture     | AWS infrastructure, secure networking, CDN/WAF patterns, repeatable deployment workflows    |
| Automation engineering | Scripts, CLIs, pipelines, and API integrations that remove toil and reduce decision fatigue |
| Reliability systems    | Observability, incident reduction, dashboard hygiene, alert quality, operational guardrails |
| Platform tooling       | Background workers, data snapshots, session handling, retries, safer failure modes          |
| Engineering quality    | Tests, linting, docs, runbooks, small refactors, and production-minded defaults             |

## Engineering Taste

- Prefer boring infrastructure and sharp automation.
- Make failure modes visible before they become incidents.
- Document the path someone will need during a bad day.
- Build tools that reduce decision fatigue.
- Treat tests, logs, and runbooks as production features.

## Current Focus

- Publishing polished, safe portfolio projects from real-world engineering work.
- Improving automation around cloud platforms, APIs, background workers, and reliability workflows.
- Turning one-off scripts into maintainable tools with tests, docs, and clear operating boundaries.

## Toolbox

```text
Cloud         AWS, EC2, Lambda, CloudFront, WAF, CloudWatch
Infra         Terraform, GitHub Actions, Pipenv
Automation    Python, Bash, PowerShell, TypeScript
Data/API      pandas, requests, httpx, JSON workflows, broker/service APIs
Quality       unittest, Ruff, static analysis, operational documentation
```

## Connect

- [LinkedIn](https://in.linkedin.com/in/soumyajyotibiswas)
- [Dev.to](https://dev.to/soumyajyotibiswas)
