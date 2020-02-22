# schedule-bot
### A discord chatbot for scheduling enrichment classes
#### Why?
I made this for fun and as a personal challenge, and also just because *why not?* I had a lot of fun and learned a lot along the way. 
### Features
- Viewing your current class

![Using the class command](https://totallynotavir.us/i/32fu2xpo.png)

- Picking a class with an interactive reaction menu (identifying details blurred)

![Picking a class with the list command](https://totallynotavir.us/i/k876ni93.png)

- Allowing your classes to be shared with your friends

![Enabling sharing with the sharing command](https://totallynotavir.us/i/s5wl3icx.png)

![Checking the class of a friend with sharing enable](https://totallynotavir.us/i/5zpppgm5.png)

- Automatically sign up for classes as soon as they're available

![Enabling automatic signup](https://totallynotavir.us/i/2z5o3igb.png)

![Being automatically signed up](https://totallynotavir.us/i/1kj7w829.png)

- Check how much time you've spent on the school math site this school year

![Checking IXL math stats](https://totallynotavir.us/i/al8bt350.png)

- Frustrationless sign up process: checks if login is valid before allowing signup
- Thorough and easy to manage logging system

### Internals
- Written in Python 3 with [discord.py](https://discordpy.readthedocs.io/)
- Fully asynchronous
- 1300+ lines of code
- Intelligent configuration system using environment variables enables easy configuration of and switch between development and production modes
- Runs a web server so that I know it is online

### File breakdown
- `main.py`: Set up logging, start bot, tasks, and web server, handle messages
- `cmds.py`: Where most commands are handled. Interfaces between discord and code
- `admin.py`: Admin commands (for testing)
- `config.py`: Interfaces for environment variables and enables access to discord client across files
- `ixl.py`: API binding for math site
- `schedule.py`: API binding for scheduling site
- `menu.py`: Reaction menus
- `storage.py`: Database (local JSON file) interface
- `tasks.py`: Recurring task (auto signup) runner
- `web.py`: Very simple web server
- `utils.py`: Utilies: message and data processing, etc.


Made by [Scoder12](https://scoder.ml)
