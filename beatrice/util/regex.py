import re

MENTION_STRING = re.compile("^<@!(\d+)>$")
CHANNEL_STRING = re.compile("^<#(\d+)>$")