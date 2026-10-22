# Event social posting

Both the Django process and Celery worker must run the current application image
with the same posting configuration. Restart/recreate both after environment or
image changes; changing the web container alone does not update workers.

- Set `POST_TO_DISCORD=True` and a nonempty `DISCORD_WEBHOOK_URL` on workers.
  The flag alone is insufficient. The global webhook is required even when a
  group has a webhook. Missing configuration returns a skipped task result;
  missing Discord webhook configuration also emits a warning.
- Set `POST_TO_LINKEDIN=True`, `LINKEDIN_ORGANIZATION_URN`, and LinkedIn
  credentials on workers. Stored IntegrationCredential tokens take precedence
  over environment tokens.
- Inspect worker results/logs for `web.post_event_to_discord` and
  `web.post_event_to_linkedin`. Check skipped results and HTTP errors as well
  as failed tasks. HTTP 400 can indicate an invalid webhook payload; 401/403/404
  can indicate credentials, webhook access, or a deleted webhook.
- LinkedIn hashtags were added in commit `361b1b2`. Ensure workers include that
  commit. New posts append `#spokanetech` and normalized event tags independently
  of AI output, reserving space within the post limit. Existing published posts
  are not updated by deploying this change.
- Scraped tags are saved in the same transaction as the event; announcement
  tasks are dispatched after commit. Tags added later are not retroactively
  appended to a published post.

The notifier now bounds Discord announcement/reminder content and embed fields
when site promotion is either enabled or disabled. Both notifiers fall back to
local event text if AI generation raises a network error.

A source review cannot establish the reason for a specific production failure
without worker logs, task results, and the deployed image version. Check those
before retrying individual missed events to avoid duplicate posts. There is no
automatic backfill on deployment.
