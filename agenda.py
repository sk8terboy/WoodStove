
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

class Agenda:
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/calendar-python-quickstart.json
    __SCOPES = 'https://www.googleapis.com/auth/calendar'
    __CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), 'client_secret.json')
    __APPLICATION_NAME = 'Google Calendar API Python Quickstart'
    __lastEvent = None
    __credentials = None

    def __init__(self):
        try:
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None

        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'calendar-python-quickstart.json')

        store = Storage(credential_path)
        self.__credentials = store.get()
        if not self.__credentials or self.__credentials.invalid:
            flow = client.flow_from_clientsecrets(self.__CLIENT_SECRET_FILE, self.__SCOPES)
            flow.user_agent = self.__APPLICATION_NAME
            if flags:
                self.__credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                self.__credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)

    def send_alert(self):
        if self.__lastEvent == None:
            http = self.__credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http, cache_discovery=False)

            now = datetime.datetime.utcnow()
                
            # Set new event
            event = {
              'summary': 'S\'occuper du feu',
              'location': '',
              'description': '',
              'start': {
                'dateTime': (now + datetime.timedelta(minutes=20, seconds=20)).isoformat() + 'Z',
                'timeZone': 'Europe/Paris',
              },
              'end': {
                'dateTime': (now + datetime.timedelta(minutes=20, seconds=30)).isoformat() + 'Z',
                'timeZone': 'Europe/Paris',
              },
              'reminders': {
                'useDefault': False,
                'overrides': [
                  {'method': 'popup', 'minutes': 20},
                ],
              },
            }
            self.__lastEvent = service.events().insert(calendarId='primary', body=event).execute()
            print('Event created')
        
    def delete_alert(self):
        if self.__lastEvent != None:
            http = self.__credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http, cache_discovery=False)
            service.events().delete(calendarId='primary', eventId=self.__lastEvent["id"]).execute()
            self.__lastEvent = None
            print('Event deleted')