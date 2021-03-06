'''
Inspired by https://github.com/twitchdev/chatbot-python-sample
'''

import sys
import os
import irc.bot
import irc.schedule
import yaml

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print(f'Connecting to {server} on port {port}...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, token)], username, username)

        # Load static commands
        with open("commands.yaml", "r") as stream:
            try:
                self.commands = yaml.load(stream)
            except yaml.YANLError as exc:
                print(exc)

        self.reactor.scheduler.execute_every(300, self.say_bot)        

    def say_bot(self):
        self.connection.privmsg(self.channel, "I'm a bot! RavingHelmet created me. I know a few !commands")

    def on_welcome(self, c, e):
        print(f'Joining {self.channel}')

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    def on_pubmsg(self, c, e):

        # If a chat message starts with an exclamation point, try to run it as a command
        if e.arguments[0][:1] == '!':
            cmd = e.arguments[0].split(' ')[0][1:]
            print(f'Received command: {cmd}')
            self.do_command(e, cmd)
        return

    def do_command(self, e, cmd):
        c = self.connection

        if cmd == "commands":
            cmdlist = ', '.join(["!"+k for k in self.commands])
            c.privmsg(self.channel, f"I know {cmdlist}")
        elif cmd in self.commands:
            c.privmsg(self.channel, self.commands[cmd])

        # The command was not recognized
        else:
            c.privmsg(self.channel, f"I don't know !{cmd} yet")


def main():
    if len(sys.argv) != 3:
        print("Usage: twitchbot <username> <client id> <token> <channel>")
        sys.exit(1)

    username  = sys.argv[1]
    channel   = sys.argv[2]
    token     = os.environ["IRC_OAUTH"]

    bot = TwitchBot(username, 0, token, channel)
    bot.start()

if __name__ == "__main__":
    main()