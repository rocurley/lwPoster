# lwPoster
### Automatically post Less Wrong meetups

Eventually will post meetup announcements by email, and to Facebook, Discord, and LessWrong itself. Currently in a partially working state; email posting and formatting a text announcement (in plain text and markdown) are working, Facebook support is next in the plan.

Text-formatted announcement/description is also placed in description.txt and plaindescription.txt,
if copying from the shell is annoying.

### Usage
After downloading the repo:
- configure `config.json` and/or `secrets.json` with information for your meetup site, login credentials, target email address for announcements, etc. (see `config_README.md`, `configEXAMPLE.json`, and `secretsEXAMPLE.json`)
- If you have rotating topics, save the topic descriptions and titles in `/meetup/title` and `/meetup/body`. If not, you'll want to use topic `none`.
- Update `boilerplate.md` to be a Markdown (or plain text) copy of your every-week meetup announcement
- run the poster with `python apis.py`. Enter in your topic shortname (possibly `none`), then site shortname (as found in config/secrets), when prompted.
- This should post to your target email and give you a text version you can use to post to unsupported platforms

If you put your site info into the checked-in files like `config.json` and are using it regularly, please check in your updates and send them as a Pull Request.

## Lack of Configurability
If this hardcodes something you need to change, add a comment on [the PR for 'youcan'tcreateissuesonforks'](https://github.com/jkopczyn/lwPoster/pull/8) ...because you can't create issues on forks. (Maybe I should break this loose of the antecedent, but most of the code is still his work.) Fixing that kind of thing is my highest priority for maintaining this.

### Fixing it yourself
If you don't want to wait, here's the preferred method of adding a configuration option: Add the current default value as an entry in `config.json`, and check that in. Add your customized version in `secrets.json`. Modify the code to load those values from the config object; this ensures that secrets take precedence over general config and that it's available everywhere the value gets used. Preferably make the helpers follow the style of existing helpers, but that's just to make the code cleaner, not mandatory. If it's complicated, add some tests. When you've run it in the wild and confirmed it worked as expected, open a PR.
