import httpx, itertools, threading, json, time, discum, random, re, base64

__CONFIG__ = json.load(open('./config.json'))
__TOKENS__ = open('./tokens.txt', 'r+').read().splitlines()
__EMOTE__ = open('./emojis.txt', 'r+').read().splitlines()
__PROXY__  = itertools.cycle(open('./proxies.txt', 'r+').read().splitlines())

bl = []

class Messager:
    def __init__(self):
        self.tokens = itertools.cycle(__TOKENS__)
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

    def send_message(self, content: str, author_id: str, command: bool=False):
        token = self.get_token(author_id)

        content = re.sub(r'<@[!|\S][0-9]+>', f'<@{base64.b64decode(str(random.choice(__TOKENS__))[:25]).decode("utf-8")}>', content)
        content = re.sub(r'<#[!|\S][0-9]+>', f'<#{__CONFIG__["copy_channel_id"]}>', content)
        #content = re.sub(r':[a-zA-Z]+:', random.choice(__EMOTE__), content)
        
        with httpx.Client(headers={'content-type': 'application/json', 'authorization': token}, timeout=30, proxies=next(__PROXY__) if __CONFIG__['proxyless'] == False else None) as client:
            for _ in range(random.randint(__CONFIG__['min_typing_time'], __CONFIG__['max_typing_time'])):
                r= client.post(f'https://discord.com/api/v9/channels/{__CONFIG__["copy_channel_id"] if not command else __CONFIG__["command_channel"]}/typing')

                if r.status_code == 403:
                    self.allowed.pop(author_id)

                time.sleep(1)
            
            client.post(f"https://discord.com/api/v9/channels/{__CONFIG__['copy_channel_id'] if not command else __CONFIG__['command_channel']}/messages", json={"content": content, "tts": False}).json()
        
class Listerner(threading.Thread):
    def __init__(self):
        self.bot = discum.Client(token=__CONFIG__['main_token'], log=False)
        self.messager = Messager()
        bot = self.bot

        @bot.gateway.command
        def ws(resp):
            if resp.event.ready_supplemental:
                print(f'* Listener started.')

            if resp.event.message:
                m = resp.parsed.auto()

                if 'bot' in str(m):
                    if m['author']['id'] not in bl:
                        print(m['author']['id'])
                        bl.append(m['author']['id'])
                    return

                if __CONFIG__['capture_all'] == True:
                    if str(m['content']).startswith('!') == True or str(m['content']).startswith('.') == True or str(m['content']).startswith('?') == True or str(m['content']).startswith('$') == True or str(m['content']).startswith('pls ') == True or str(m['content']).startswith('s?') == True:
                        self.messager.send_message(m['content'], m['author']['id'], True)
                    else:
                        self.messager.send_message(m['content'], m['author']['id'])
                else:
                    if m['channel_id'] == __CONFIG__['listen_channel_id']:
                        if str(m['content']).startswith('!') == True or str(m['content']).startswith('.') == True or str(m['content']).startswith('?') == True or str(m['content']).startswith('$') == True or str(m['content']).startswith('pls ') == True or str(m['content']).startswith('s?') == True:
                            self.messager.send_message(m['content'], m['author']['id'], True)
                        else:
                            self.messager.send_message(m['content'], m['author']['id'])

        threading.Thread.__init__(self)
    
    def run(self):
        self.bot.gateway.run()

if __name__ == '__main__':
    print(f'* Load {len(__TOKENS__)} tokens.')
    print(f'* Capture all: {__CONFIG__["capture_all"]}')
    print(f'* Proxy: {__PROXY__}.')
    Listerner().start()