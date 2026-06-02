---
name: find-docs
description: >-
  Retrieve up-to-date documentation, API references, and code examples for developer
  technologies with the Context7 CLI. Use whenever the user asks about a specific
  library, framework, SDK, CLI tool, cloud service, API syntax, configuration option,
  version migration, setup instruction, library-specific debugging issue, or "how do I"
  question involving a named technology such as React, Next.js, Prisma, Express,
  Tailwind, Django, Spring Boot, or similar tools. Always verify current API details
  with Context7 instead of relying on training data unless Context7 is unavailable.
---

# Find Docs

Use Context7 to retrieve current documentation and examples for developer technologies. Prefer current docs over memory for API details, signatures, configuration, migrations, setup, and CLI usage.

## Workflow

1. Identify the library, framework, SDK, CLI tool, or cloud service in the user's request.
2. Remove sensitive or confidential details from the query, including API keys, passwords, credentials, personal data, and proprietary code.
3. Resolve the library ID first:

```bash
npx ctx7@latest library <name> "<specific query>"
```

4. Select the best Context7 library ID from the results.
5. Query the documentation with the selected ID:

```bash
npx ctx7@latest docs /org/project "<specific query>"
```

Use an installed `ctx7` binary only when it is already available or after updating it:

```bash
npm install -g ctx7@latest
ctx7 library <name> "<specific query>"
ctx7 docs /org/project "<specific query>"
```

## Required Lookup Rules

- Always call `ctx7 library` before `ctx7 docs`, unless the user explicitly provides a Context7 library ID in `/org/project` or `/org/project/version` format.
- Always pass a descriptive query argument to `ctx7 library`; use the user's intent to disambiguate similarly named packages.
- Do not run Context7 commands more than 3 times for one user question. If the answer is still incomplete after 3 attempts, use the best result available and state the limitation.
- Prefer `npx ctx7@latest` when the CLI is not known to be installed, because it avoids relying on a stale global installation.
- Do not include sensitive information in Context7 queries.

## Selecting a Library ID

Choose the most relevant match using these signals, in order:

1. Exact or close name match to the requested technology.
2. Description relevance to the user's task.
3. Higher code snippet coverage.
4. High or Medium source reputation.
5. Higher benchmark score.

If multiple strong matches exist, briefly note the ambiguity and proceed with the best match. If no reasonable match exists, state that Context7 did not return a good match and ask for a more specific package, vendor, or library ID.

## Version Handling

If the user requests a specific version, use a version-specific ID from the `ctx7 library` output when available:

```bash
npx ctx7@latest docs /org/project/version "<specific query>"
```

If the exact version is unavailable, use the closest listed version and state the choice. If no suitable version is listed, use the latest indexed ID and state that version-specific docs were not available.

## Query Quality

Use the user's full question when possible. Prefer specific queries such as:

```bash
npx ctx7@latest library react "React useEffect cleanup function with async operations"
npx ctx7@latest docs /facebook/react "React useEffect cleanup function with async operations"
```

Avoid vague one-word queries such as `auth`, `hooks`, or `config`.

## Error Handling

If Context7 fails because of quota errors such as `Monthly quota reached` or `quota exceeded`:

1. Tell the user their Context7 quota is exhausted.
2. Suggest `ctx7 login` for higher limits.
3. If they cannot authenticate, answer from general knowledge only after clearly stating that current docs were not available and the answer may be outdated.

If Context7 fails for network or installation reasons, report the failure, then answer only if useful and clearly mark that the answer was not verified against current docs.
