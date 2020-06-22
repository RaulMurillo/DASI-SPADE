.. role:: raw-html-m2r(raw)
   :format: html


DASI-Cheff Bot
==============

Project for DASI subject (UCM, course 2019-2020) consisting on a multi-agent system.

The system is developed with `SPADE platform <https://spade-mas.readthedocs.io/en/latest/readme.html>`_\ , and makes use of a `XMPP server <https://xmpp.org/>`_.

The main purpose is to develop a multi-agent system able to recognize food and ingredients from pictures and sugguest receipes that could be cooked with such ingredients.

Instalation and dependencies
----------------------------

This software uses Python >= 3.6. You can install packages dependencies with ``pip`` as following:

.. code-block:: shell

   pip install -r requirements.txt

Other considerations:


* There is no need to install any XMPP server if agents names are not modified.
* You will need Dialogflow credentials.
* The neural network model can be found at https://drive.google.com/open?id=19PA-QcdE7IBYzLSc-QPdXHSShHL3_G9y.

App execution
-------------


#. Add your ``config.py`` file with the corresponding credentials to ``src`` folder.
#. Execute the script ``src/main.py``.

User's guide
------------

Connect with Telegram Bot
^^^^^^^^^^^^^^^^^^^^^^^^^

Once the application is running, the user can interact with it via Telegram.
There are 2 available options:


#. Accessing link https://t.me/DASIChef_bot
#. Search in the Telegram app for ``DASIChef_bot``.

Bot interaction
^^^^^^^^^^^^^^^

Type ``/start`` for starting a conversation with the bot.\ :raw-html-m2r:`<br>`
To finish the conversation, type ``/exit`` on the main menu.

Authors and credits
-------------------

This project is managed by Raul Murillo (ramuri01@ucm.es) and Ignacio Regueiro (iregueir@ucm.es).   

Source: https://github.com/RaulMurillo/DASI-SPADE.
