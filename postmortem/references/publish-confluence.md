# Publishing to Confluence

**WHEN TO READ**: Phase 8, after the user has approved the draft.

## Title convention

```
Postmortem: <short incident title> (YYYY-MM-DD)
```

Date-suffixed so the space sorts chronologically and a recurrence is visible at a glance in the page
list — which is most of the reason for keeping them together.

## Publish from the file

The document is already on disk from Phase 4. Publish it with `-f`. **Never inline it into a heredoc**
— that serialises the whole document into a Bash argument, which puts a second full copy into the main
session's context for no benefit.

These invocations are verified against the installed `confluence` CLI. If one fails, run
`confluence <cmd> --help`; do not improvise a flag.

```bash
confluence create "Postmortem: <title> (<YYYY-MM-DD>)" <SPACEKEY> \
  --file postmortem-<YYYY-MM-DD>-<slug>.md --format markdown
```

To nest it under a parent page (most spaces have a "Postmortems" index), use the **`create-child`
subcommand**. There is no `--parent` flag on `create`:

```bash
confluence create-child "Postmortem: <title> (<YYYY-MM-DD>)" <PARENT_PAGE_ID> \
  --file postmortem-<YYYY-MM-DD>-<slug>.md --format markdown
```

Note the second argument differs: `create` takes a **space key**, `create-child` takes a **parent page
id**. Find a parent id with `confluence find "<parent title>"`.

## Unknown space key

Ask the user. They will usually paste a URL:

```
https://<site>.atlassian.net/wiki/spaces/ENG/overview
                                        ^^^ space key
```

If they do not know, `confluence spaces` lists what the token can see. Do not guess a space — a
postmortem published to the wrong space is worse than one not published, because nobody finds it and
everybody assumes it exists.

## After publishing

1. **Link the ticket back.** If an incident Jira ticket exists, comment the page URL onto it — the
   ticket is where people look first.

   ```bash
   jira issue comment add <INCIDENT-KEY> "Postmortem published: <confluence-url>"
   ```

2. **Link the action items.** Each action-item ticket from Phase 7 should carry the postmortem URL in
   its description, so an engineer picking it up months later knows why it exists. An action item
   without that context is the one that gets closed as "no longer relevant".

3. **Offer to post the link back to the Slack thread.** Ask first — never post to a channel unprompted.

   ```bash
   slack-cli send -c <CHANNEL> \
     -m "Postmortem published: <confluence-url>" \
     --thread <THREAD_TS>
   ```

   This closes the loop for everyone who lived through the incident, and it is how the next person
   searching Slack for the same symptom finds the document.

## Failure handling

If `confluence create` fails, **the document is not at risk** — it is already on disk from Phase 4.
Report the file path and the error, and let the user retry or publish by hand. The publish step is
cheap to repeat; the document cost three fan-outs and a fact-check pass.

The same holds if `confluence` is not installed at all: the run still produces the document, and
Phase 0 will already have warned that publishing is unavailable.
