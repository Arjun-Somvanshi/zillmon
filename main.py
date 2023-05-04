#!/bin/python3

import json
import requests
import os
import telebot
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [zillmon]: %(message)s')

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
            logging.warning("User Config is missing: %s", str(e))
            logging.info("Loading default config...")

    def rpc_call(self, url, data, counter=0):
        headers = {"Content-Type": "application/json"}
        data = json.dumps(data)
        try:
            r = requests.post(url, data=data, headers=headers)
            return json.loads(r.text)
        except Exception as e:
            print(f"There was an issue with the rpc call, check if {url} is up")
            print(e)
            if counter < 4:
                time.sleep((counter + 1)*2)
                return self.rpc_call(url, data, counter + 1)
            else:
                print("Retried 5 times... Error Occured in RPC call")
                self.error_url = url
                return {"result": "RPC Failure"}

    def get_blockchain_info(self):
        data = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "GetBlockchainInfo",
                "params": [""]
               }
        self.blockchain_info_vald = self.rpc_call(self.config["vald_url"], data)["result"]
        self.blockchain_info_remote = self.rpc_call(self.config["remote_url"], data)["result"]
        if self.blockchain_info_vald != "RPC Failure" and self.blockchain_info_remote != "RPC Failure":
            return True
        else:
            return False

    def alert_BlockNum(self):
        if int(self.blockchain_info_vald["NumDSBlocks"]) < int(self.blockchain_info_remote["NumDSBlocks"]) - 50:
            bot.send_message(self.config["chat_id"], f'''Block Height of Zilliqa Validator is Lagging\n
                              Validator Height: {self.blockchain_info_vald["NumDSBlocks"]}
                              Remote Node Height: {self.blockchain_info_remote["NumDSBlocks"]}
                              ''')
        logging.error(f'''Block Height of Zilliqa Validator is Lagging''')
        logging.error(f''' Validator Height: {self.blockchain_info_vald["NumDSBlocks"]} Remote Node Height: {self.blockchain_info_remote["NumDSBlocks"]}''')

    def alert_DeficitPeers(self):
        if int(self.blockchain_info_vald["NumPeers"]) < int(self.blockchain_info_remote["NumPeers"]) - 10:
            bot.send_message(self.config["chat_id"], f'''Deficit Peers Zilliqa Validator is Lagging\n
                              Validator Peers: {self.blockchain_info_vald["NumPeers"]}
                              Remote Peers: {self.blockchain_info_remote["NumPeers"]}
                              ''')
        logging.error(f'''Deficit Peers for Zilliqa Validator''')
        logging.error(f'''Validator Peers: {self.blockchain_info_vald["NumPeers"]} Remote Node Peers: {self.blockchain_info_remote["NumPeers"]}''')

    def monitor(self):
        while True:
            if self.get_blockchain_info():
                self.alert_BlockNum()
                self.alert_DeficitPeers()
            else:
                print("One monitor cycle has failed due to RPC Error")
                bot.send_message(self.config["chat_id"], f'RPC Error the following url is down: {self.error_url}')
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
    #bot.send_message(zill.config["chat_id"], f"Monitoring Validator: {zill.config['vald_url']}")
    zill.monitor()

monitorThread = threading.Thread(target=start_monitoring)
monitorThread.start()
bot.infinity_polling()
