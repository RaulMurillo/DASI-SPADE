# DASI-SPADE
Project for DASI subject (UCM, course 2019-2020) consisting on a multi-agent system.

The system is developed with [SPADE platform](https://spade-mas.readthedocs.io/en/latest/readme.html), and makes use of a [XMPP server](https://xmpp.org/).

The main purpose is to develop a multi-agent system able to recognize food and ingredients from pictures and sugguest receipes that could be cooked with such ingredients.

## Instalation and dependencies

This software uses Python >= 3.6. You can install packages dependencies with `pip` as following:
```shell
pip install -r requirements.txt
```

Other considerations:
* There is no need to install any XMPP server if agents names are not modified.
* You will need Dialogflow credentials.
* The neural network model can be found at https://drive.google.com/open?id=19PA-QcdE7IBYzLSc-QPdXHSShHL3_G9y.

## App execution
1. Add your `config.py` file with the corresponding credentials to `src` folder.
2. Execute the script `src/main.py`.

## User's guide

### Connect with Telegram Bot
Once the application is running, the user can interact with it via Telegram.
There are 2 available options:
1. Accessing link https://t.me/DASIChef_bot
2. Search in the Telegram app for `DASIChef_bot`.

### Bot interaction
Type `/start` for starting a conversation with the bot.  
To finish the conversation, type `/exit` on the main menu.


## Authors and credits

This project is managed by Raul Murillo (ramuri01@ucm.es) and Ignacio Regueiro.
