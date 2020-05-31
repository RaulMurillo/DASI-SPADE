import spade
import telegramBot
import multiprocessing
import os
import logging
import dialogflow
import json
import datetime
import csv
from pathlib import Path
from google.api_core.exceptions import InvalidArgument
import asyncio
import numpy
import scipy
import tensorflow as tf

if __name__ == "__main__":
    hello = tf.constant("\n\nDASI-project installed succesfully!")
    tf.print(hello)