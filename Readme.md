# Discord Bot for infra-workshop

## How to use
```bash
pip install regex discord
git pull
cd iw_discord_bot
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
pip install -t ./ regex discord
cp config.ini.sample config.ini
# you need inject token and wordpress url for config.ini
zip -r iw_discord_bot.zip ./*
# Let's deploy zip file to AWS_Lambda !
```