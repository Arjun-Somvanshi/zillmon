import json
import requests
import os
import telebot
import time

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

class zillmon:
    def read_config(self):
        try:
            with open(os.path.expanduser("~") + os.path.sep + ".config/zillmon/zill.json", "r") as f:
                self.config = json.load(f)
        except Exception as e:
            self.config = {"vald_url": "https://zil-node.lgns.xyz/api", 
                           "remote_url": "https://api.zilliqa.com/",
                           "chat_id": -845793348
                          }
            print(f"Error: {e}")
            print("Loading default config...")

    def rpc_call(self, url, data):
        headers = {"Content-Type": "application/json"}
        data = json.dumps(data)
        r = requests.post(url, data=data, headers=headers)
        return json.loads(r.text)

    def get_blockchain_info(self):
        data = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "GetBlockchainInfo",
                "params": [""]
               }
        self.blockchain_info_vald = self.rpc_call(self.config["vald_url"], data)["result"]
        self.blockchain_info_remote = []
        self.blockchain_info_remote = self.rpc_call(self.config["remote_url"], data)["result"]

    def get_current_ds_block(self):
        data = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "GetDsBlock",
                "params": ["9000"]
               }
        self.current_ds_block_vald = self.rpc_call(self.config["vald_url"], data)["result"]
        self.current_ds_block_remote = self.rpc_call(self.config["remote_url"], data)["result"]

    def alert_BlockNum(self):
        if int(self.blockchain_info_vald["NumDSBlocks"]) < int(self.blockchain_info_remote["NumDSBlocks"]) - 50:
            bot.send_message(self.config["chat_id"], f'''Block Height of Zilliqa Validator is Lagging\n
                              Validator Height: {self.blockchain_info_vald["NumDSBlocks"]}
                              Remote Node Height: {self.blockchain_info_remote["NumDSBlocks"]}
                              ''')
        print(f'''Block Height of Zilliqa Validator is Lagging\n
                          Validator Height: {self.blockchain_info_vald["NumDSBlocks"]}
                          Remote Node Height: {self.blockchain_info_remote["NumDSBlocks"]}
                          ''')

    def alert_DeficitPeers(self):
        if int(self.blockchain_info_vald["NumPeers"]) < int(self.blockchain_info_remote["NumPeers"]) - 10:
            bot.send_message(self.config["chat_id"], f'''Deficit Peers Zilliqa Validator is Lagging\n
                              Validator Peers: {self.blockchain_info_vald["NumPeers"]}
                              Remote Peers: {self.blockchain_info_remote["NumPeers"]}
                              ''')
        print(f'''Deficit Peers Zilliqa Validator is Lagging\n
                          Validator Peers: {self.blockchain_info_vald["NumPeers"]}
                          Remote Node Peers: {self.blockchain_info_remote["NumPeers"]}
                          ''')

    def monitor(self):
        while True:
            self.get_blockchain_info()
            self.alert_BlockNum()
            self.alert_DeficitPeers()
            time.sleep(120)


zill = zillmon()
zill.read_config()
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am Zillmon. 
I am here to monitor you Zilliqa Validator node
""")

@bot.message_handler(commands=['status'])
def send_status(message):
    zill.get_blockchain_info()
    bot.reply_to(message, "Validator Status: \n" + str(zill.blockchain_info_vald))

@bot.message_handler(commands=['rstatus'])
def send_remote_status(message):
    zill.get_blockchain_info()
    bot.reply_to(message, "Remote Node Status: \n" + str(zill.blockchain_info_remote))

def start_monitoring():
    bot.send_message(zill.config["chat_id"], f"Monitoring Validator: {zill.config['vald_url']}")
    zill.monitor()

start_monitoring()
bot.infinity_polling()
