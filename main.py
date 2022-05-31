import httpx, itertools, threading, json, time, discum, random, re, base64

__config__ = json.load(open('./config.json', encoding='utf8', errors='ignore'))
__tokens__ = open('./tokens.txt', 'r+').read().splitlines()
__emotes__ = open('./emojis.txt', 'r+', encoding='utf8', errors='ignore').read().splitlines()
__proxy__  = itertools.cycle(open('./proxies.txt', 'r+').read().splitlines())
__channels__  = open('./forward_channels.txt', 'r+').read().splitlines()
__bad_word__  = open('./blacklist.txt', 'r+').read().splitlines()
__good_word__  = itertools.cycle(open('./insultes.txt', 'r+').read().splitlines())

bl = []

class Messager:
    def __init__(self):
        self.tokens = itertools.cycle(__tokens__)
        self.allowed = {}

    def allow_token(self, user_id: str):
        self.allowed[user_id] = next(self.tokens)
        print(f'> Allowed user {user_id}')
        return self.allowed[user_id]
    
    def get_token(self, user_id: str):
        try:
            return self.allowed[user_id]
        except:
            return self.allow_token(user_id)

    def send_message(self, content: str, author_id: str, channel_id: str, m: dict):
        if channel_id not in bl:
            token = self.get_token(author_id)

            # replace all owo words by *
            for word in content.split(' '):
                if word in __bad_word__:
                    content = content.lower().replace(word, '**'+next(__good_word__) + '**')

            # mentions
            content = re.sub(r'<[!|\S][0-9]+>', "", content)

            # math all discord emoji [need to match :emoji: to, btw lazy]
            content = re.sub(r'<:[^>]+>', random.choice(__emotes__), content)
            content = re.sub(r'<:[a-zA-Z]+:[0-9]+> ', random.choice(__emotes__), content)
            
            # reply to messages with ping ex:
            """
            foo123: hello
            bar1337: @foo123, hi
            """
            if __config__['ping_reply']:
                if m['type'] == 'reply':
                    mention = m['referenced_message']['author']['id']
                    try:
                        token_id = base64.b64decode(str(self.allowed[mention])[:25].encode("utf-8")).decode('utf-8')
                        print('reply', token_id)
                        content = f'<@{token_id}>, {content}'
                    except Exception as e:
                        print(e) 
                        pass

                #print(content)
            
            with httpx.Client(headers={'content-type': 'application/json', 'authorization': token}, timeout=30, proxies='http://'+next(__proxy__) if __config__['proxyless'] == False else None) as client:
                for _ in range(random.randint(__config__['min_typing_time'], __config__['max_typing_time'])):
                    r= client.post(f'https://discord.com/api/v9/channels/{channel_id}/typing')

                    if r.status_code == 403:
                        self.allowed.pop(author_id)

                    time.sleep(1)
                
                r = client.post(f"https://discord.com/api/v9/channels/{channel_id}/messages", json={"content": content, "tts": False}).json()

                print(f'[{channel_id}] {r}')

                # banned :( ?
                if 'Missing Access' in str(r):
                    bl.append(channel_id)

class Listerner(threading.Thread):
    def __init__(self):
        self.bot = discum.Client(token=__config__['main_token'], log=False)
        self.messager = Messager()
        bot = self.bot
        
        @bot.gateway.command
        def ws(resp):
            if resp.event.ready_supplemental:
                print(f'* Listener started.')
                bot.gateway.subscribeToGuildEvents(False)

            if resp.event.message:
                m = resp.parsed.auto()

                if 'bot' in str(m):
                    if m['author']['id'] not in bl:
                        print(m['author']['id'])
                        bl.append(m['author']['id'])
                    return
                
                if m['author']['id'] in bl:
                    return

                if m['channel_id'] in __channels__:
                    for chan in __channels__:
                        if chan != m['channel_id']:
                            threading.Thread(target=self.messager.send_message, args=[m['content'], m['author']['id'], chan, m]).start()

        threading.Thread.__init__(self)
    
    def run(self):
        self.bot.gateway.run()

if __name__ == '__main__':
    print(f'* Load {len(__tokens__)} tokens.')
    print(f'* Proxy: {__proxy__}.')

    for token in __tokens__:
        bl.append(base64.b64decode(token[:25].encode("utf-8")).decode('utf-8'))

    Listerner().start()