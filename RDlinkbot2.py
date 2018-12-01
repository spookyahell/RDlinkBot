from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineQueryResultCachedAudio
from telegram.ext import Updater, CallbackQueryHandler, Filters, MessageHandler
import logging
import requests
import json
from os.path import isfile
from sys import exit as sexit


if isfile('RDlink.botdata'):
	f = open('RDlink.botdata')
	lines = f.read().split('\n')
	f.close()
	if len(lines) == 2:
		bottoken, botdata = lines
		botdata = json.loads(botdata)
	else:
		print('ERROR: Not the right amount of lines in the botfile!\nLine 1: Bottoken\nLine 2: Botdata')
		sexit(1)
else:
	print('ERROR: Botfile (RDlink-botdata -> see README.md) non-existant')
	sexit(1)
	

logging.basicConfig(filename='RDLinkBot.log', level=logging.DEBUG)
updater = Updater(token=bottoken)
dispatcher = updater.dispatcher

rdtoken = botdata['rdtoken']
allowed_user_ids = botdata['allowed_user_ids']

headers = {'Authorization': f'Bearer {rdtoken}'}

def onText(bot, update):
	msg = update.message
	id = msg.from_user.id
	if id not in allowed_user_ids:
		msg.reply_text('ERROR! Unauthorized user.')
		return
	message = msg.text
	links = message.split('\n')
	real_links = []
	for link in links:
		if (link.startswith('https://')) or (link.startswith('http://')):
			real_links.append(link)
	output_links = []
	errors = []
	for link in real_links:
		data = {'link': link, 'password':''}
		r = requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/link', data = data, headers = headers)
		linkdata = r.json()
		if 'error' in linkdata:
			error = linkdata['error']
			if error == 'hoster_unsupported':
				r = requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/folder', data = {'link':link}, headers = headers)
				linklist = r.json()
				if linklist[0] != link:
					for link in linklist:
						data = {'link': link, 'password':''}
						r = requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/link', data = data, headers = headers)
						linkdata = r.json()
						if 'error' in linkdata:
							error = linkdata['error']
							errors.append(f'{link} - '+error)
						else:
							output_links.append(linkdata['download'])
				else:
					errors.append(f'{link} - hoster_unsupported')
			else:
				errors.append(f'{link} - '+error)
		else:
			output_links.append(linkdata['download'])
	if len(output_links)>1:
		v, s = ['are','s']
	else:
		v, s = ['is','']
		
	if len(errors)>1:
		ve, se, an = ['are','s','']
	else:
		ve, se, an = ['is',' one of',' an']
		
	if len(errors) == 0:
		msg.reply_text(f'Here {v} your link{s}:\n'+'\n'.join(output_links))
	elif len(output_links) > 0:
		msg.reply_text(f'Here {v} your link{s}:\n'+'\n'.join(output_links)+f'\nand here {ve} the error{se} your links produced:\n'+'\n'.join(errors))
	else:
		msg.reply_text(f'Oops, only{an} error{se}...\n'+'\n'.join(errors))
	
dispatcher.add_handler(MessageHandler(Filters.text, onText))

updater.start_polling()
updater.idle()