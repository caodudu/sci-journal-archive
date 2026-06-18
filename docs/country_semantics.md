# Country Semantics

Last updated: 2026-06-18

## Current Problem

The current dashboard country field is parsed from `Publisher address` in the Web of Science Core Collection list. This is only a publisher-country signal.

It is not the same as:

- journal owner country
- sponsoring society/institution country
- editorial office country
- journal registration country
- collaborating institution countries
- main author-country distribution

## Example: Signal Transduction and Targeted Therapy

The current local record says:

```text
publisher: SPRINGERNATURE
publisher_country: United Kingdom
publisher_address: CAMPUS, 4 CRINAN ST, LONDON, ENGLAND, N1 9XW
```

This is not enough. The journal is affiliated with / sponsored by West China Hospital, Sichuan University, and its editorial office is in Chengdu, Sichuan, P. R. China. Therefore it should be findable under China as well as under the publisher country.

## Required Model

Add a separate `journal_countries` table:

```text
journal_id
country
role
source
confidence
note
```

Suggested roles:

```text
publisher
owner
sponsor
society
editorial_office
institution
collaborator
inferred
```

The frontend should eventually offer:

- Publisher country filter
- Journal country filter
- Country role filter
- "match any country role" mode

Until this is implemented, frontend labels must say `publisher country`, not just `country`.
