# Stavya Datta personal website

The site is deployed from `main` to [stavyadatta.com](https://stavyadatta.com/).

## LinkedIn activity sync

`data/linkedin_posts.json` contains the public posts shown in the Latest news section. The scheduled workflow runs every two days and uses LinkedIn's authorised Posts API; it filters out non-public visibility values and does not scrape a browser session.

To enable automatic updates, add these repository secrets in GitHub:

- `LINKEDIN_ACCESS_TOKEN`: an OAuth token with LinkedIn's `r_member_social` permission.
- `LINKEDIN_MEMBER_URN`: the authenticated member URN, such as `urn:li:person:...`.

The workflow can also be started manually from the Actions tab. Without both secrets, the workflow is intentionally skipped and the checked-in feed remains available.

## Local checks

```bash
python3 -m unittest discover -s tests -v
python3 -m http.server 8000
```
