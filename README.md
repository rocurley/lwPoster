# lwPoster
### Automatically post Less Wrong meetups

Eventually will post meetup announcements by email, and to Facebook, Discord, and LessWrong itself. Currently in a partially working state; email posting and formatting a text announcement (in plain text and markdown) are working, Facebook support is next in the plan.

Usage: After downloading the repo:
- configure `config.json` and/or `secrets.json` with information for your meetup site, login credentials, target email address for announcements, etc. (see `config_README.md`, `configEXAMPLE.json`, and `secretsEXAMPLE.json`)
- If you have rotating topics, save the topic descriptions and titles in `/meetup/title` and `/meetup/body`. If not, you'll want to use topic `none`.
- Update `boilerplate.md` to be a Markdown (or plain text) copy of your every-week meetup announcement
- run the poster with `python apis.py`. Enter in your topic shortname (possibly `none`), then site shortname (as found in config/secrets), when prompted.
- This should post to your target email and give you a text version you can use to post to unsupported platforms

If you put your site info into the checked-in files like `config.json` and are using it regularly, please check in your updates and send them as a Pull Request.
