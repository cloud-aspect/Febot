import re

with open("database/users.json") as fp:
    with open("dest", "w+") as destfp:
        text = fp.read()
        text = re.sub(r'general', r'administrator', text)
        text = re.sub(r'captain', r'moderator', text)
        text = re.sub(r'lieutenant', r'cadet', text)
        text = re.sub(r'corporal', r'peon', text)
        text = re.sub(r'sergeant', r'corporal', text)
        text = re.sub(r'smiley', r'iron', text)
        destfp.write(text)
