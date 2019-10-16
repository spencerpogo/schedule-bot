# schedule-bot
Discord bot to automatically schedule enrichment classes. 

I made this project as hobby project for a new site that was introduced into my school for enrichment classes, as I use discord a lot. 

## Features
- Database that stores logins
- `class` command: See your next class, with configurable date
- `list` command: Select a class with a reaction menu
- Sharing: if enabled, you can see what classes your friends are signed up for
- Automatic signup: Automatically be signed up for a certain class as soon as it's available

### File structure
- `main.py` Starts bot, website, tasks, and logging
- `cmds.py` Code to run individual commands
- `config.py` Configuration of bot (prefix, gets environment variables)
- `menu.py` Code for reaction menus
- `schedule.py` Interacts with enrichment website's API
- `storage.py` Interacts with the database
- `tasks.py` Code for recurring task(s) (auto signup)
- `utils.py` Miscellaneous utilities (functions to resolve members, parse courses)
- `admin.py` Admin commands (for testing)
- `web.py` Website (to keep bot alive)

Made by [Scoder12](https://scoder12.ml)
