# Discord Bot for infra-workshop

## How to use

```bash
git pull
cd iw_discord_bot
python -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp config.ini.sample config.ini
# you need inject token and wordpress url for config.ini
python3 iw_discord_bot.py
# this program is run once.
# need run everyday ? let write cron !
```

or

```bash
git pull
cd iw_discord_bot
python -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp config.ini.sample config.ini
# you need inject token and wordpress url for config.ini
zip -r iw_discord_bot.zip ./*
# Let's deploy zip file to AWS_Lambda !
```
