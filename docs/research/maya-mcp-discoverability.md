---
summary: "Evidence-backed plan for Maya MCP search visibility, ecosystem distribution, and adoption measurement."
read_when:
  - When planning Maya MCP SEO, registry publication, marketplace submissions, or launch content.
  - When reviewing discoverability metrics or deciding whether to rename the repository.
---

# Maya MCP discoverability and distribution plan

Research date: 2026-07-13

Scope: Google visibility, GitHub discoverability, MCP ecosystem distribution, Autodesk ecosystem distribution, and measurable adoption for `GimbalGoats/GG_MayaMCP`.

## Implementation status

Completed on 2026-07-13:

- GitHub description, documentation homepage, and 12 focused repository topics
- root Official MCP Registry `server.json`, PyPI ownership marker, validation tests, and release-time OIDC publishing
- generated Autodesk MCP Tool Manifest with drift protection against all 71 live tools
- Autodesk and Anthropic submission-ready documentation
- query-clear README/docs titles, PyPI keywords and homepage, distribution runbook, and `robots.txt` sitemap hint

Still requires publisher action:

- merge and publish a new PyPI/GitHub release before the Official MCP Registry can verify the ownership marker
- complete Autodesk's Publisher Declaration and submit the generated manifest
- accept Anthropic's directory terms and submit the released MCPB
- update the separately managed Gimbal Goats articles and configure Search Console

## Executive recommendation

Run two high-value publication tracks in parallel:

1. **Autodesk certification:** submit Maya MCP to Autodesk's Design & Make Marketplace. Autodesk explicitly accepts MCP servers, certifies them, and is building a path for certified third-party MCPs to become callable from Autodesk Assistant. This is the most relevant audience and strongest trust signal available for a Maya integration. The required artifacts are an MCP Tool Manifest and Publisher Declaration. [Autodesk MCP publisher guide](https://aps.autodesk.com/marketplace/mcp-publisher-guide), [Autodesk marketplace announcement](https://aps.autodesk.com/blog/design-and-make-marketplace-where-your-solutions-meet-industry-agentic-ai-workflows)
2. **Canonical MCP registration:** publish the PyPI-backed server to the Official MCP Registry. That registry is intended as the centralized metadata source for downstream aggregators. PulseMCP and Glama state that they ingest it; GitHub announced an intended automatic path into its MCP Registry, although current automatic inclusion is not documented as complete. [Official MCP Registry overview](https://modelcontextprotocol.io/registry/about), [GitHub MCP Registry launch post](https://github.blog/ai-and-ml/github-copilot/meet-the-github-mcp-registry-the-fastest-way-to-discover-mcp-servers/)

At the same time, submit the existing MCPB to Anthropic's Connectors Directory and fix the inexpensive owned properties: GitHub topics/homepage, links from all three Gimbal Goats articles, and Search Console measurement. Then use qualified directories, awesome lists, and practitioner content as amplification—not as the core strategy.

Do **not** make a repository rename the first move. The claim that an exact-match GitHub repository path materially improves Google rank is unproven. Google says words in domain names are only one of many factors and has an exact-match-domain system specifically to avoid over-crediting them; `GG_MayaMCP` is a URL path, not a domain. [Google ranking systems guide](https://developers.google.com/search/docs/appearance/ranking-systems-guide)

No action can guarantee first place. Google explicitly says there is no technique that automatically ranks a site first. [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)

## Corrections to the supplied diagnosis

### Confirmed

- The repository is young: created 2026-03-17. Current live state is **10 stars and 2 forks**, not 1 star and 0 forks. It has no topics and no homepage URL. [GitHub repository API](https://api.github.com/repos/GimbalGoats/GG_MayaMCP)
- GitHub states that many of its own repository rankings depend on star count. Stars therefore matter for GitHub ecosystem discovery and social proof. [GitHub documentation on stars](https://docs.github.com/en/get-started/exploring-projects-on-github/saving-repositories-with-stars)
- Google confirms that links help it discover pages and that link analysis/PageRank remains part of its core ranking systems. Relevant editorial links and useful directory pages can therefore help discovery and potentially ranking. [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [Google ranking systems guide](https://developers.google.com/search/docs/appearance/ranking-systems-guide)
- The project is already listed on [Glama](https://glama.ai/mcp/servers/GimbalGoats/GG_MayaMCP) and [ConduID](https://conduid.com/servers/gg-mayamcp). The claim that it is in no MCP directories is stale.
- It is **not** in the Official MCP Registry: the official API returned no `io.github.GimbalGoats/*` result on 2026-07-13. [Official Registry API](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.GimbalGoats)
- The PyPI metadata is already solid: `maya-mcp` 0.5.0 has a descriptive summary, relevant keywords, and links to documentation, repository, and issues. [PyPI project](https://pypi.org/project/maya-mcp/), [PyPI JSON API](https://pypi.org/pypi/maya-mcp/json)
- The published docs site already returns a canonical URL, meta description, and `sitemap.xml`. Its current title is generic (`Home - Maya MCP`), and no `robots.txt` is published. A missing `robots.txt` does not block crawling by itself.
- Gimbal Goats has three useful Maya MCP articles. [What Is Maya MCP](https://gimbalgoats.com/blog/what-is-maya-mcp) links to the repository; [Inside Maya MCP](https://gimbalgoats.com/blog/inside-maya-mcp-architecture-examples) and [Debugging a Maya Crash with Maya MCP](https://gimbalgoats.com/blog/debugging-a-maya-crash-with-maya-mcp) currently do not.

### Not established

- Google does not publish repository age, GitHub stars, or forks as direct Google ranking factors. Do not present them as such. They can indirectly create trust, usage, citations, and links, but that is a hypothesis rather than a documented Google signal.
- Google does not document an exact-match GitHub repository name as a strong ranking factor. A rename from `GG_MayaMCP` to `maya-mcp` might improve human clarity, but its SEO benefit is a weak hypothesis and must be weighed against branding, link redirects, release automation, documentation, and registry identifiers.
- Directory quantity is not a valid goal by itself. Google lists low-quality directory links, paid ranking links, automated link creation, and excessive link exchanges as link spam. Prefer relevant, maintained directories with real users. [Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies#link-spam)
- GitHub's public MCP Registry is real but curated. GitHub's 2025 launch article described automatic propagation from the OSS registry in future tense. No current public GitHub submission form or API was found. Publish to the Official MCP Registry first, then verify whether GitHub picked it up. [Live GitHub MCP Registry](https://github.com/mcp), [GitHub launch post](https://github.blog/ai-and-ml/github-copilot/meet-the-github-mcp-registry-the-fastest-way-to-discover-mcp-servers/)

## Current-state audit

### Repository and package

- GitHub name: `GimbalGoats/GG_MayaMCP`
- GitHub description: `MCP server for Autodesk Maya`
- GitHub homepage: unset
- GitHub topics: none
- GitHub adoption: 10 stars, 2 forks
- PyPI package: `maya-mcp` 0.5.0
- Published MCPB: `maya-mcp-0.5.0.mcpb`; 14 release-asset downloads as of 2026-07-13. [GitHub release](https://github.com/GimbalGoats/GG_MayaMCP/releases/tag/v0.5.0)
- Registry metadata: no root `server.json`; no published Official MCP Registry record
- Existing discovery metadata: [`pyproject.toml`](https://github.com/GimbalGoats/GG_MayaMCP/blob/main/pyproject.toml), [`fastmcp.json`](https://github.com/GimbalGoats/GG_MayaMCP/blob/main/fastmcp.json), comprehensive [`README.md`](https://github.com/GimbalGoats/GG_MayaMCP/blob/main/README.md), docs, security and privacy policies

### Owned discovery surfaces

- GitHub Pages docs are crawlable and have a sitemap: `https://gimbalgoats.github.io/GG_MayaMCP/sitemap.xml`.
- The docs homepage title is not query-rich. Change it to a concise, accurate title such as `Maya MCP Server for Autodesk Maya` while keeping `Maya MCP` as the product name.
- Three Gimbal Goats articles establish real production expertise. Two need direct repository and docs links with descriptive anchors.
- A 2026-07-13 search snapshot surfaced Autodesk's official MCP program prominently for generic Maya/Autodesk MCP queries. Autodesk does not currently show a Maya-specific server, but its domain authority changes the competitive landscape: target the accurate long-tail position `open-source local MCP server for Autodesk Maya`, not an implied official Autodesk product. Treat anonymous result snapshots as directional; use Search Console for durable query and position data.
- Rolling GitHub Traffic API snapshot for 2026-06-29 through 2026-07-12:
  - views: 74 total / 25 unique
  - clones: 56 total / 27 unique
  - top referrers: `gimbalgoats.com` 27 views / 6 unique; Google 19 / 6; GitHub 5 / 2; LinkedIn 3 total

These are rolling 14-day figures, not durable trend data. They do show that owned content and Google already send qualified traffic. Preserve snapshots every two weeks because GitHub only exposes recent traffic. [GitHub Traffic API documentation](https://docs.github.com/en/rest/metrics/traffic)

### Ecosystem listings

- Official MCP Registry: absent
- Autodesk Design & Make Marketplace: absent
- GitHub MCP Registry: absent from the live index search observed on 2026-07-13
- Anthropic Connectors Directory: no accepted public listing could be verified; the repo already has the required local MCPB, privacy policy, support path, icon, examples, and submission notes
- Glama: present, currently claimable; do not submit a duplicate
- ConduID and PolicyLayer: present through automated indexing
- PulseMCP, Smithery, LobeHub, MCP Market: no first-party GG listing found in the research snapshot
- Awesome lists: no GG entry found. `wong2/awesome-mcp-servers` currently links PatrickPalmer's Maya MCP only.

## Prioritized action plan

### P0 — do now

#### 1. Autodesk Design & Make Marketplace certification

- Owner: repo maintainer plus Gimbal Goats publisher/admin
- Artifact: `packaging/autodesk/mcp-tool-manifest.json`
- Artifact contents: manifest version, app model, MCP spec version, stdio transport, all 71 tools with plain-language descriptions, resources, prompts, external endpoints, Autodesk APIs used, and AI/LLM providers
- Supporting proof: current privacy policy, security model, installation instructions, MCPB, screenshots/video, tested Maya-version matrix
- Submission: complete Autodesk's Publisher Declaration, then submit through Publisher Corner / `appsubmissions@autodesk.com`
- Acceptance proof: public certified Marketplace listing and publisher access

Autodesk warns against missing tools, undeclared endpoints, sensitive-data instructions in descriptions, and differences between the manifest and actual behavior. Generate or validate the tool list from the same server registration source used by the product; do not hand-maintain 71 entries without a drift check. External endpoints should be empty if none are used, and the declaration should distinguish the local MCP server from whatever cloud model a user's client may call. [Autodesk MCP publisher guide](https://aps.autodesk.com/marketplace/mcp-publisher-guide)

#### 2. Official MCP Registry publication

- Owner: repo maintainer/release owner
- Artifacts:
  - root `server.json`
  - hidden README ownership marker, likely `<!-- mcp-name: io.github.GimbalGoats/maya-mcp -->`
  - published PyPI release containing that marker
  - optional GitHub Actions publisher workflow after the manual first publication succeeds
- Package metadata: `registryType: "pypi"`, identifier `maya-mcp`, released version, stdio transport, repository URL, concise title and description
- Submission:
  1. install `mcp-publisher`
  2. run `mcp-publisher init`
  3. validate the generated file and namespace
  4. publish a PyPI release containing the exact matching README marker
  5. run `mcp-publisher login github`
  6. run `mcp-publisher publish`
- Acceptance proof: exact server returned by `https://registry.modelcontextprotocol.io/v0.1/servers?search=<registry-name>`

The Registry supports PyPI and requires an exact `mcp-name` marker in the package README; a hidden HTML comment is allowed. It remains preview software, so version and schema changes need monitoring. [PyPI package requirements](https://modelcontextprotocol.io/registry/package-types), [publisher quickstart](https://modelcontextprotocol.io/registry/quickstart), [GitHub Actions publishing](https://modelcontextprotocol.io/registry/github-actions)

Use the existing MCPB as a second install option only after the PyPI-backed record works. MCPB registry entries require the release URL and SHA-256. [MCPB Registry requirements](https://modelcontextprotocol.io/registry/package-types#mcpb-packages)

#### 3. Anthropic Connectors Directory submission

- Owner: release owner plus the submitter responsible for ongoing security/support responses
- Artifacts: current release `.mcpb`, public privacy policy, support URL, 512x512 icon, clear reviewer setup, three real use cases, and a disposable Maya test scene or deterministic test steps
- Preflight: confirm every tool has a title plus applicable `readOnlyHint` or `destructiveHint`; rerun MCPB validation and the 71-tool smoke test against the exact submitted bundle
- Path: use the Desktop extension form linked from Anthropic's official [Connectors Directory submission guide](https://claude.com/docs/connectors/building/submission)
- Acceptance proof: reviewed public Desktop Extension listing, install test from the directory, correct version and settings

Anthropic does not list a local PyPI/stdio server directly in its Connectors Directory. The supported local distribution path is MCPB, which this repo already builds and attaches to releases. [Anthropic connectors overview](https://claude.com/docs/connectors/overview)

#### 4. GitHub discoverability metadata

- Owner: GitHub repository admin
- Artifact: repository settings, no code release needed
- Set homepage: `https://gimbalgoats.github.io/GG_MayaMCP/`
- Improve description: `Local, typed MCP server for controlling Autodesk Maya via commandPort`
- Add topics: `maya`, `autodesk-maya`, `mcp`, `mcp-server`, `model-context-protocol`, `3d`, `vfx`, `rigging`, `animation`, `python`, `claude`, `codex`
- Acceptance proof: topics/homepage visible on the repository and repository searchable by those topics

GitHub says topics are intended to help people find projects and are directly searchable. It allows up to 20. [GitHub topics documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)

#### 5. Owned links and Google measurement

- Owner: Gimbal Goats site owner
- Artifacts:
  - one canonical owned product landing page: either a custom-domain front door for the existing docs or a focused `gimbalgoats.com/maya-mcp` page
  - direct repo + docs call-to-action on all three Maya MCP articles
  - descriptive anchor text such as `open-source Maya MCP server for Autodesk Maya`
  - docs homepage title and description update
  - Search Console properties for `gimbalgoats.com` and the GitHub Pages URL prefix if ownership can be verified
- Landing-page content: one-sentence product definition, installation choices, supported clients/Maya versions, evidence-backed differentiators, security boundaries, demo, docs/repo/PyPI calls-to-action, and a short factual comparison section. Avoid copying the current blog article or docs homepage; each page needs a distinct search intent.
- Submission/verification:
  - submit the existing docs sitemap through Search Console
  - inspect the docs homepage and all three articles
  - request indexing after material changes
- Acceptance proof: pages indexed; Search Console query/page data collected; no crawl or canonical errors

Google says it primarily discovers pages through links, uses link context and anchor text to understand them, and accepts sitemap submission through Search Console. [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [Google sitemap guide](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap), [Search Console ownership verification](https://support.google.com/webmasters/answer/9008080)

### P1 — complete within 30–60 days

#### 6. Claim and improve the existing Glama listing

- Owner: repository admin
- Artifact: claimed Glama profile and passing build/inspection
- Path: [current GG listing](https://glama.ai/mcp/servers/GimbalGoats/GG_MayaMCP) → Claim
- Verify: correct PyPI install command, MCPB option, 71 tools, security settings, docs/repo links
- Fix: the listing has tool pages, but its schema summary has shown `No tools`; use the claim/build workflow to get a consistent inspection
- Acceptance proof: verified owner, current version, full capability inspection, searchable categories

Glama also ingests the Official Registry, so registry publication should remain canonical. [Glama methodology](https://glama.ai/mcp/methodology)

#### 7. Publish the local MCPB to Smithery

- Owner: release owner
- Artifact: current release `.mcpb`
- Path: `https://smithery.ai/new` or `smithery mcp publish ./maya-mcp-<version>.mcpb -n <namespace>/maya-mcp`
- Complete Settings → Verification after publishing
- Acceptance proof: live Smithery page, install flow, verified publisher, correct bundle version

Smithery's current model does not import a GitHub repository. Remote publication requires public HTTPS Streamable HTTP; local stdio servers use a prebuilt MCPB. Maya MCP should use the MCPB route unless a separate remote edition is intentionally built. [Smithery publish documentation](https://smithery.ai/docs/build/publish)

#### 8. Downstream directories

- PulseMCP: publish the Official Registry record, wait through its documented ingestion cycle, then contact Pulse only if missing after a week. Pulse also offers manual submission, but its directory API is read-only and it already ingests the official registry; the canonical route avoids duplicate metadata maintenance. [PulseMCP API](https://www.pulsemcp.com/api), [PulseMCP submission page](https://www.pulsemcp.com/submit)
- LobeHub: open [LobeHub MCP Marketplace](https://lobehub.com/mcp), use `Submit MCP`, provide the GitHub URL, and complete human verification. Current acceptance timing/criteria are not publicly documented.
- MCP Market: submit the GitHub URL and contact email at [mcpmarket.com/submit](https://mcpmarket.com/submit). Prefer the free queue unless the paid product exposure has a justified acquisition value. Do not pay for a ranking-passing link; paid links should be `rel="sponsored"` or `nofollow` under Google's policies.
- GitHub MCP Registry: search after Official Registry publication. If absent, use GitHub feedback/support; no separate public submission route was verified.

#### 9. Curated awesome lists

- Owner: maintainer/community owner
- `punkpeye/awesome-mcp-servers`: PR one concise, accurate entry under the relevant 3D/creative category, alphabetized and linked to the repo. Follow its [CONTRIBUTING guide](https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md).
- `wong2/awesome-mcp-servers`: do not open a PR; its README says to use [mcpservers.org/submit](https://mcpservers.org/submit). Submit GG as a distinct Maya MCP implementation with its typed/local/safety differentiators. [Repository instructions](https://github.com/wong2/awesome-mcp-servers)
- `TensorBlock/awesome-mcp-servers`: use the repository's `Add MCP server` issue form or a focused PR with install, transport, auth, client, license, endpoint, and tool metadata. [Repository](https://github.com/TensorBlock/awesome-mcp-servers)

One accepted, maintained list is worth more than many scraped directories. Never imply that another Maya implementation is inferior without a reproducible comparison.

### P2 — compound authority over 60–90 days

#### 10. Publish proof-led content, not generic MCP explainers

- Owner: Gimbal Goats technical author
- Produce one strong artifact per month, each linking to the exact repo/docs page:
  - Maya 2024/2025 commandPort compatibility guide
  - real rig or skin-weight workflow with a downloadable safe sample
  - measured comparison of typed tools vs arbitrary-code approaches
  - Maya MCP setup for Claude Desktop, Codex, Claude Code, and VS Code
  - release walkthrough with short video/GIF and exact version
- Cross-link the three current articles as a series and add a persistent `Get Maya MCP` call-to-action.
- Offer the technical material to Autodesk forums, Maya/rigging communities, TD forums, and relevant newsletters where it answers an existing question. Avoid identical cross-posts and promotional comment drops.

Google says useful, original, up-to-date, people-first content is more influential than mechanical SEO changes. [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)

#### 11. Earn real adoption signals

- Add issue/discussion templates for installation reports, Maya-version compatibility, and workflow examples.
- Ask actual users to star only if the project helped them; never buy or exchange stars.
- Publish tested compatibility and release evidence so other documentation can cite it.
- Invite studios/users to contribute anonymized case studies and integrations.
- Keep releases, changelog, docs, PyPI, MCPB, Official Registry, Autodesk manifest, and directory profiles synchronized.

Stars help GitHub discovery; real usage creates the links, references, examples, and word of mouth that can help broader discovery. Treat stars as an adoption metric, not a Google ranking control.

## 30/60/90-day sequence

### First 30 days

- Add GitHub homepage, description, and topics.
- Add repo/docs calls-to-action to all three Gimbal Goats articles.
- Set up Search Console, submit sitemap, capture baseline queries and pages.
- Create and validate `server.json`; add the PyPI README ownership marker; publish and verify the Official Registry record.
- Generate Autodesk's complete tool manifest, complete the declaration, and submit.
- Validate the release MCPB against Anthropic's current checklist and submit it to the Connectors Directory.
- Claim Glama and correct its current inspection/profile.
- Capture a second GitHub Traffic snapshot after 14 days.

### Days 31–60

- Confirm Official Registry ingestion by PulseMCP; verify GitHub MCP Registry separately.
- Publish and verify the MCPB on Smithery.
- Submit LobeHub and MCP Market free queue.
- Submit to the three curated awesome-list routes.
- Improve docs homepage title/snippet and publish one high-intent compatibility/setup page.
- Add Official Registry publishing automation to the release workflow only after the manual path is proven.
- Respond to Autodesk review feedback and keep manifest/code parity.

### Days 61–90

- Publish two proof-led workflow/case-study assets with video or downloadable samples.
- Distribute them to relevant Autodesk/Maya/TD communities where they directly solve a question.
- Review Search Console by query cluster and landing page; refresh weak titles/snippets and expand the pages already earning impressions.
- Audit every listing for current version, install command, tool count, and link target.
- Compare rolling acquisition/adoption against the baseline; double down on referrers and content that produce installs, clones, or release downloads.
- Revisit repository naming only if user research shows persistent confusion. Do not rename solely on the unproven exact-match SEO theory.

## Query and content clusters

Use natural variants in page titles, headings, body text, examples, and anchors. Do not keyword-stuff.

### Product/discovery

- `Maya MCP server`
- `Autodesk Maya MCP`
- `MCP server for Autodesk Maya`
- `open source Maya MCP`
- Best target page: docs/product homepage with a short proof-led comparison section

### Install/client setup

- `install Maya MCP`
- `Maya MCP Claude Desktop`
- `Maya MCP Codex`
- `Maya MCP Claude Code`
- `Maya MCP VS Code`
- Best target pages: focused client setup pages with copy-paste commands and verification steps

### Production workflows

- `AI Maya rigging tools`
- `AI inspect Maya scene`
- `Maya rig debugging AI`
- `Maya skin weights AI`
- `Maya scene automation MCP`
- Best target pages: real case studies, sample scenes, videos, and tool-call transcripts

### Trust and architecture

- `secure Maya MCP server`
- `local Maya AI tools`
- `Maya MCP commandPort security`
- `typed Maya tools vs code execution`
- Best target pages: architecture and security docs with explicit boundaries

### Compatibility/troubleshooting

- `Maya 2024 MCP commandPort`
- `Maya 2025 MCP server`
- `Maya commandPort empty response`
- `Maya MCP connection error`
- Best target pages: versioned troubleshooting guides derived from tested regressions and releases

### Comparison

- `best Maya MCP server`
- `Maya MCP comparison`
- Best target page: factual matrix using reproducible dimensions—installation, tool coverage, raw-execution defaults, localhost enforcement, supported Maya/client versions, test evidence, update cadence. Avoid unsupported superlatives.

## Measurement and KPIs

Review every two weeks for the first 90 days. Annotate publication and content dates so changes can be correlated with outcomes.

### Visibility

- Search Console impressions, clicks, click-through rate, and average position for each query cluster
- Indexed status for docs homepage and three Gimbal Goats articles
- Top landing pages for non-brand queries
- Goal: establish a four-week baseline first; then target sustained growth rather than one-day rank checks
- Aspirational 90-day outcome: top 10 for `Maya MCP server` and related product query, not a guarantee

### Ecosystem distribution

- Official MCP Registry exact record: live/current
- Autodesk Marketplace: submitted → review → certified/live
- Anthropic Connectors Directory: submitted → reviewed → listed/current
- GitHub MCP Registry: present/absent, checked separately
- Glama: claimed, inspected, current
- Smithery: verified/current MCPB
- PulseMCP, LobeHub, MCP Market: listed/current
- Curated awesome-list acceptances: count and referral traffic

### Acquisition

- GitHub Traffic: views, unique visitors, clones, unique cloners, referrers
- Baseline: 74/25 views and 56/27 clones over the latest 14-day snapshot
- Referrer baselines: Gimbal Goats 27/6; Google 19/6
- Goal after stable four-week baseline: grow Google and qualified ecosystem unique referrals without reducing clone/install intent

### Adoption

- GitHub stars/forks as GitHub/social proof: baseline 10/2
- MCPB release downloads: baseline 14 for v0.5.0
- PyPI installs/downloads, if measured, must use one consistent source and be labeled approximate because PyPI does not publish an official public download counter
- New user issues/discussions, compatibility reports, contributors, and external integrations
- Release-to-release retention: users downloading or reporting success on subsequent versions

### Quality guardrails

- Install smoke tests pass for every documented client route
- Published version consistent across PyPI, GitHub Release, MCPB, Official Registry, Autodesk manifest, and claimed directories
- No listing claims `official Autodesk` unless Autodesk grants that status; use `Autodesk-certified` only after certification and according to its rules
- No paid, exchanged, automated, or low-quality link program

## Risks and controls

- **Official Registry preview changes:** pin the schema used by the current release, validate in CI, monitor release notes, and verify after each publish.
- **Autodesk manifest drift:** generate/validate from the server's real registration metadata; fail CI when names/counts differ.
- **Smithery architecture mismatch:** use MCPB for local stdio. Do not imply a remote endpoint exists.
- **Directory duplication/stale metadata:** make the Official Registry canonical; claim only high-value profiles and audit quarterly.
- **Paid-link risk:** pay only for genuine product distribution, never ranking credit; require sponsored/nofollow treatment where applicable.
- **Unsupported superiority claims:** replace `best` with evidence—tool count, safety defaults, tested clients/Maya versions, real production cases.
- **Search volatility:** use Search Console trends and conversions, not anonymous one-off searches, as the decision source.
- **Rename disruption:** defer; document a separate migration plan if product/user research later justifies it.
- **Security disclosure:** keep raw execution opt-in, localhost boundaries, external endpoints, and AI-provider responsibility explicit everywhere.

## Recommended immediate deliverables

1. `packaging/autodesk/mcp-tool-manifest.json` plus validation against registered tools
2. Root `server.json` plus README `mcp-name` marker
3. Official Registry first publication and API proof
4. Autodesk Publisher Declaration and submission package
5. Anthropic Connectors Directory MCPB submission package
6. GitHub topics/homepage/description update
7. Direct repository links from all three Gimbal Goats posts
8. Search Console ownership + sitemap submission
9. Claimed/correct Glama profile

These deliverables create canonical identity, relevant certification, controlled crawl/index measurement, and real ecosystem distribution. They are higher leverage than a repo rename or mass submission to low-quality directories.
