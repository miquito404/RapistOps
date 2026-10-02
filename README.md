# RapistOps
A public-source accountability intelligence system designed to make sexual violence harder to hide.

RapistOps connects publicly available reports, records, evidence, people, cases, and institutions so information that might otherwise disappear can be found, connected, and tracked.

## Purpose
RapistOps is being developed to organize information about sexual violence across publicly available and otherwise lawfully accessible sources.

The system is designed to preserve the distinction between:
- A report being made
- An investigation occurring
- A person being charged
- A case being dismissed
- An acquittal
- A conviction
- Other documented outcomes

A lack of conviction does not mean a report or record never existed. RapistOps is intended to preserve those distinctions rather than reducing every case to a simple convicted/not-convicted classification.

## Core Question 
How can we preserve, connect, and analyze fragmented information about sexual violence so that survivors are not dependent on a single institutional outcome for their experiences to remain visible, traceable, and accountable?

## Engineering Question 
How can a software system transform fragmented, heterogeneous, and changing records into a traceable network of evidence, entities, relationships, and outcomes without collapsing uncertainty or documented claims into unsupported conclusions?

## Overlapping Question 
How can we engineer an accountability system that preserves survivors' documented experiences, connects fragmented records, and makes the resulting evidence and institutional history traceable over time?

## Core Capabilities
The long-term system is intended to support:
- Public-source data collection
- Evidence and record preservation
- Source provenance
- People and entity records
- Case and event records
- Institutional records
- Relationship mapping
- Status and case-history tracking
- Temporal change tracking
- Search and analysis
- APIs
- Web-based access
- Automated source monitoring

## Volume 1
Volume 1 focuses on building the first complete working version of the core system.

The initial pipeline is:
1. Public Source
2. Import
3. Preserve
4. Structure
5. Connect
6. Store
7. Search
8. Display

Volume 1 will establish the foundation needed for the larger RapistOps system without attempting to implement the entire long-term vision at once.

## Technology
Initial technology stack:
- Python 3.12
- PostgreSQL
- FastAPI
- Pydantic
- httpx
- BeautifulSoup
- pytest
- Docker
- Git
- React
- TypeScript

Additional technologies may be introduced when the project's requirements justify them.

## Development
RapistOps is being developed incrementally.

For PostgreSQL setup and connection configuration, see the
[local development database guide](docs/local_database.md).

The project follows a roadmap-driven approach:
1. Define the complete system in the Master Roadmap.
2. Define the bounded Volume 1 scope.
3. Build and test one phase at a time.
4. Expand only when the requirements call for it.

## Status
**Version:** 0.1.0
**Development status:** Early development

## Project Structure
RapistOps/
    src/
    tests/
    data/
    docs/
    notes/
    README.md
    .gitignore
    pyproject.toml

## Scope & Principles
RapistOps is intended to work with publicly available or otherwise lawfully accessible information.

The system should preserve source provenance, distinguish documented facts from allegations or claims, and avoid presenting unverified information as established fact.

Information should be represented with enough context to understand where it came from, what it documents, and what its recorded status is.

## License
See LICENSE.

## Safety & Privacy
RapistOps is intended for lawful public-source research, documentation, and accountability work.

The project is designed around the following principles:
- Use publicly available or otherwise lawfully accessible information.
- Preserve source provenance and context.
- Clearly distinguish allegations, reports, claims, investigations, charges, and adjudicated outcomes.
- Do not present unverified claims as established facts.
- Collect only information necessary for the system's documented purpose.
- Avoid exposing unnecessary sensitive personal information.
- Use the least precise geographic information necessary for a given purpose.
- Do not use RapistOps to facilitate harassment, threats, stalking, doxxing, or retaliation.
- Build appropriate access controls, auditing, and abuse-prevention measures as the system develops.
- Respect applicable laws, regulations, source terms, and access restrictions.

Safety and privacy requirements are part of the system architecture and will evolve alongside the project.