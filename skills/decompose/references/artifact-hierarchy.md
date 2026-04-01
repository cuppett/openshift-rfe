# Red Hat Artifact Hierarchy for RFE Planning

This reference covers **Level 4 and above** — the strategic artifact types relevant when decomposing RFEs into planned work. Execution-level types (Epic, Story, Task) are out of scope here, but their project routing is noted for completeness.

Sources: Red Hat Jira issue hierarchy standards, HCM project routing guide, OCP strategy project conventions, and ccjira artifact guide.

---

## Level 5: Outcome

- **What it is:** A specific, incremental, measurable business result. Connects roadmap deliverables to corporate strategy.
- **Scope:** Spans multiple Releases; may take longer than a year. May cross multiple product/engineering areas.
- **Who it's for:** Internal — Red Hat business/strategy stakeholders. Describes human behavior changes and business results, not deliverables.
- **Completion:** Knowing whether delivered changes created desired business results (observed/measured).
- **When to create:** Rarely from RFE triage. Only if a cluster of RFEs reveals an unmeasured business outcome with no existing parent Outcome. Confirm with PM leadership first.

**Outcome project routing:**

| Domain | Project |
|---|---|
| HCM (Hybrid Cloud Management) | `HCMSTRAT` |
| OCP/cross-cluster management | `XCMSTRAT` |
| Engineering-driven strategic work | `SDSTRAT` |
| Customer & roadmap planning | `CRCPLAN` or `FRSTAT` |

---

## Level 4: Initiative vs. Feature

This is the primary decision point when decomposing RFEs.

### Feature

- **What it is:** A capability or well-defined set of functionality that delivers business value **to customers**.
- **Scope:** Fits within a Release. Scoped to a single product/engineering area. Can span multiple teams.
- **Who it's for:** External — customers gain new/improved ability to do something in the product.
- **Owned by:** Lead Product Manager.
- **Completion:** All dependent Epics delivered in a Release. Customers can now do something more/better/differently.
- **When to create from an RFE:** The RFE describes a customer-facing capability gap — something the product is missing that customers want to use directly.

### Initiative

- **What it is:** A large product/portfolio goal — typically architectural or improvement-focused work.
- **Scope:** ~6 months or a single Release. Scoped to a single product/engineering area.
- **Who it's for:** Internal — creates the **ability for Red Hat associates** to do something more/better/differently (e.g., enables engineering to ship faster, improves reliability, restructures internals).
- **Owned by:** Engineering Management, PM, or Change Leader.
- **Completion:** All dependent Epics closed. Red Hat associates can now do something they couldn't before.
- **When to create from an RFE:** The RFE implies significant architectural or infrastructure work that isn't directly a customer-facing feature — e.g., migrating a subsystem, establishing a new internal framework, enabling a platform capability that other features depend on.

---

## Feature vs. Initiative Decision Guide

| Signal | Feature | Initiative |
|--------|---------|------------|
| Customers directly interact with the delivered capability | Yes | No |
| Work is architectural / infrastructure / internal tooling | No | Yes |
| Described as "support for X" or "ability to do Y" in the product | Yes | Sometimes |
| Described as "refactor", "migrate", "redesign", "enable", "framework" | No | Yes |
| Outcome: customers can do something new | Yes | No |
| Outcome: Red Hat engineers can do something new/better | No | Yes |
| Would be customer-visible in release notes | Yes | Rarely |

**When in doubt:** If the RFE was filed by a customer describing something they want to do with the product, it is almost always a Feature. If the work is primarily internal scaffolding that enables future features, it is an Initiative.

---

## Project Routing

Routing depends on **which product domain** the artifact belongs to, not just the artifact type.

### OCP Platform (not managed-service-specific)

For tools that are part of OCP itself and ship with every OCP release — oc-mirror, OLM, installer, oc CLI, etc. — use OCPSTRAT for Features and Initiatives.

| Artifact type | Project |
|---|---|
| Feature | `OCPSTRAT` |
| Initiative | `OCPSTRAT` |
| Outcome | `XCMSTRAT` or `SDSTRAT` |
| Epic (execution) | `CLID` (oc-mirror), or component-specific team project |

**Signal:** The existing Features for oc-mirror are in OCPSTRAT (OCPSTRAT-2699, OCPSTRAT-2680, OCPSTRAT-1808, etc.). oc-mirror engineering execution lands in CLID. If existing Features for a tool are in OCPSTRAT, new Features for the same tool go there too.

### Cross-Cutting Container/Cluster Management

For strategic work that spans managed-service offerings or the broader cluster-management domain (not specific to OCP-native tools or a single managed service).

| Artifact type | Project |
|---|---|
| Feature | `XCMSTRAT` |
| Initiative | `XCMSTRAT` |
| Outcome | `XCMSTRAT` or `HCMSTRAT` |
| Epic (execution) | `OCM` (primary), `SREP`, `RHCLOUD` |

### ROSA (Red Hat OpenShift Service on AWS)

| Artifact type | Project |
|---|---|
| Feature | `ROSA` |
| Initiative | `ROSA` |
| Risk | `ROSA` |

### ARO (Azure Red Hat OpenShift)

| Artifact type | Project |
|---|---|
| Feature | `ARO` |
| Initiative | `ARO` |
| Epic (execution) | `ARO` (handles both strategic and execution) |

### GCP HCP

| Artifact type | Project |
|---|---|
| Feature | `GCP` |
| Initiative | `GCP` |

### Hybrid Cloud Console / CRC

| Artifact type | Project |
|---|---|
| Feature | `CRCPLAN` |
| Initiative | `CRCPLAN` |
| Epic (execution) | `RHCLOUD` |

### HCM Platform Engineering

| Artifact type | Project |
|---|---|
| Initiative | `HCMPE` |
| Risk | `HCMPE` |

### HCM Business Outcomes

| Artifact type | Project |
|---|---|
| Outcome | `HCMSTRAT` |

### Never create Features, Initiatives, or Outcomes in execution projects

Execution projects (OCM, SREP, OHSS, OCMUI, RHCLOUD, CLID, etc.) are for Epics and below only.

---

## How to Determine the Right Project

1. **Look at existing linked Features in the source issue.** If the RFE already links to OCPSTRAT Features, new Features for the same capability belong in OCPSTRAT.
2. **Is this tool/component OCP-native (ships with OCP itself)?** → OCPSTRAT
3. **Is this specific to ROSA / ARO / GCP?** → Use that product's project.
4. **Is this cross-cutting across managed services or the cluster-management domain?** → XCMSTRAT
5. **Is this a business outcome spanning multiple releases?** → HCMSTRAT (HCM) or XCMSTRAT (OCP/cross-cloud)
6. **When in doubt:** Ask the user which project to use. Do not guess for Features and Initiatives — wrong project placement is hard to fix.

---

## Lifecycle Statuses

### Feature
`New` → `Refinement` → `Backlog` → `In Progress` → `Closed`

- **New:** Need identified; stakeholders and high-level use cases documented.
- **Refinement:** Actively scoped; MVP described, risks/dependencies outlined, Epics produced.
- **Backlog:** In scope but not yet committed.
- **In Progress:** Developing, testing, documenting.
- **Closed:** All underlying work developed, tested, and released.

### Initiative
`New` → `Refinement` → `In Progress` → `Review` → `Closed`

- **New:** Need identified; stakeholders and success criteria documented.
- **Refinement:** Actively scoped; MVP described, risks/dependencies outlined, Epics produced.
- **In Progress:** Actively developing, testing, documenting.
- **Review:** Stakeholder review; confirming success criteria met.
- **Closed:** Success criteria met (fully, partially, or not); all Epics closed.

### Outcome
`New` → `Refinement` → `In Progress` → `Review` → `Closed`

---

## Supported Clients Matrix — Context

The Feature template includes a Supported Clients matrix. Fill it based on the product domain:

- **OCP-native features** (oc-mirror, OLM, installer, etc.): ROSA CLI, OCM CLI, OCM UI, Terraform, CAPI are all **N/A** — these are standalone OCP tools, not managed service interfaces.
- **ROSA/managed service features**: Fill in each row as Yes/No/N/A based on whether the feature is accessible through that interface.
- **FedRAMP**: Always answer explicitly — air-gapped and FedRAMP customers are disproportionately affected by OCP-level features.
- **Already supported in OCP?**: If yes, note which version. This tracks whether the feature is a v2 regression vs. net-new.
