#!python3
# vim: set fileencoding=utf-8 :

################################
# discord bot for infra-workshop

## import
import configparser
import regex
import discord
from os.path import dirname, abspath
from datetime import datetime, timedelta, timezone
from requests import get as httpget
from json import loads as json_load
from html import unescape

## static argment
JST = timezone(timedelta(hours=+9), 'JST')
BASE_DIR = dirname(abspath(__file__))

## regex-pattern for discord channel title
title_regexs = [
    r'\p{Han}',r'\p{Katakana}',r'\p{Hiragana}',r'\p{Latin}',
    r'\p{N}',r'\p{So}',r'\p{Pd}',r'-',r'ー',r'（',r'）',
    r'[\u00A2-\u00F7]',r'[\u2100-\u2BD1]',
    r'[\u0391-\u03C9]',r'[\u0401-\u0451]',
    r'[\u2010-\u2312]',r'[\u2500-\u254B]',
    r'[\u25A0-\u266F]',r'[\u3000-\u3049]',
    r'[\uDC00-\uDCFF]',r'[\uFF00-\uFFFF]'
    ]
title_regex = r''
for reg in title_regexs:
    title_regex += reg + r'|'
title_regex = title_regex[0:-1] + r'+'

## read config from .ini
inifile = configparser.ConfigParser()
inifile.read(BASE_DIR + '/config.ini')
calendar_url = inifile.get('calendar',r'url')
calendar_day_line = int(inifile.get('calendar',r'day_line'))
discord_token = inifile.get('discord',r'token')
discord_server_id = inifile.get('discord',r'server_id')

def dprint(var):
    with open(BASE_DIR + '/run.log','a') as f:
        f.write(str(var) + '\n')

################################
# Wordpress

## load today's events from wordpress callender
def get_wp_callender(worpress_url):
    now = datetime.now(JST)
    sdt = now.replace(hour=calendar_day_line, minute=0, second=0, microsecond=0)
    sdt = sdt.strftime('%Y/%m/%dT%H:%MZ')
    edt = (now + timedelta(days=1))
    edt = edt.replace(hour=calendar_day_line-1, minute=59, second=59, microsecond=0)
    edt = edt.strftime('%Y/%m/%dT%H:%MZ')
    API_URI = 'https://' + worpress_url + '/?rest_route=/tribe/events/v1/events'
    url = API_URI + "&start_date=" + sdt + "&end_date=" + edt
    response = httpget(url)
    if response.status_code != 200:
        dprint("error : " + str(response.status_code))
        return
    wss = json_load(response.text)

    ## crop events because time value is ignored by wpapi
    wk = wss['events']
    wss['events'] = []
    for ev in wk:
        if int(ev['start_date_details']['day']) == now.day and int(ev['start_date_details']['hour']) > calendar_day_line:
            wss['events'].append(ev)
        if int(ev['start_date_details']['day']) != now.day and int(ev['start_date_details']['hour']) < calendar_day_line:
            wss['events'].append(ev)

    return wss

################################
# Discord

## discord client object
client = discord.Client()

async def get_events():
    ## regex for remove htmltag
    p = regex.compile(r"<[^>]*?>")
    ret = []

    json_event = get_wp_callender(calendar_url)

    ## parse object for post discord
    for e in json_event["events"]:
        event = {}
        event["title"] = str(e["start_date_details"]["month"]) + str(e["start_date_details"]["day"]) + "-" + e["title"]
        msg = ""
        msg += e["title"] + "\n"
        msg += str(e["start_date_details"]["hour"]) + ":" + str(e["start_date_details"]["minutes"])
        msg += " 〜 "
        msg += str(e["end_date_details"]["hour"]) + ":" + str(e["end_date_details"]["minutes"]) + "\n"
        msg += "----" + "\n"
        description = p.sub("", e["description"])
        msg += unescape(description)
        event["description"] = msg
        if "organizer" in e and len(e["organizer"]) > 0:
            event["actor"] = e["organizer"][0]["organizer"]
        else:
            event["actor"] = ""
        ret.append(event)    
    return ret

## create discord text channel
async def setup_channel(client, title, message, actor):
    server = client.get_server(discord_server_id)
    # check discord member
    members = {}
    mention = None
    for mems in server.members:
        members[mems.mention] = [mems.name,mems.display_name]
    for k in members:   # ignore dupricate
        if members[k][0] == members[k][1]:
            members[k] = [members[k][0]]
    # check spearker
    l = 0
    for k in members:
        for mem in members[k]:
            if (actor in mem or mem in actor) and l < len(mem):
                mention = k
                l = len(mem)
    # parse for discord channel
    title = ("".join(regex.findall(title_regex,title))).lower()
    # check duplicate
    for channel in server.channels:
        if channel.type == discord.ChannelType.text:
            if channel.name == title:
                dprint("already_created")
                return 0
    if not mention is None:
        message = "こちらは " + mention + " さん主催の勉強会チャンネルです。\n" + message
    dprint("Creating Channel...")
    new_chan = await client.create_channel(server, title)
    dprint("Post Description...")
    await client.send_message(new_chan, message)
    message2 = """
■ ご注意!!
音声チャンネルは Study-Group01 です。入室時には意図せずマイクがオンのままになっていないかご確認をお願いします。
http://bit.ly/2HWB9ZL
進行に影響がある場合は一旦 AFK 部屋に移動させて頂く場合がありますのでその際はマイクをミュートにしつつ戻ってきてください。

■ 質問したいとき
頭に "Q. " をつけてコメントしておいてくだされば。あとで主催者が拾います。

■ 匿名で質問したいとき
質問箱 BOT さんに "Q. " の付いた質問を投げるとチャンネルに匿名で投稿し直してくれます。
勉強会中、みんなの前だとちょっと質問しづらいな‥って思ったら質問箱 BOT に "Q." が先頭についたメッセージを送ってください。
http://bit.ly/2rjZyjL
    """
    await client.send_message(new_chan, message)
    # await client.delete_channel_permissions(new_chan, client.connection.user)
    dprint("OK.")

@client.event
async def on_ready():
    dprint('Logged in as : ' + client.user.name)
    # dprint(client.user.id)

    # thread main
    evs = await get_events()
    for ev in evs:
        await setup_channel(client,ev["title"],ev["description"], ev["actor"])        
    # end thread
    await client.close()

def main():
    # execute discord api
    client.run(discord_token)

if __name__ == '__main__':
    main()
