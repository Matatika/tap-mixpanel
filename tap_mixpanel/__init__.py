#!/usr/bin/env python3

import sys
import json
import argparse
from datetime import datetime, timedelta, date
import singer
from singer import metadata, utils
from singer.utils import strptime_to_utc, strftime
from tap_mixpanel.client import MixpanelClient
from tap_mixpanel.discover import discover
from tap_mixpanel.sync import sync

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    'project_timezone',
    'date_window_size',
    'attribution_window',
    'start_date',
    'user_agent'
]


def do_discover(client, properties_flag, denest_properties):

    LOGGER.info('Starting discover')
    catalog = discover(client, properties_flag, denest_properties)
    json.dump(catalog.to_dict(), sys.stdout, indent=2)
    LOGGER.info('Finished discover')


@singer.utils.handle_top_exception(LOGGER)
def main():

    parsed_args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)

    start_date = parsed_args.config['start_date']

    #Initialize necessary keys into the dictionary.
    params = parsed_args.config
    if params.get("username") and params.get("password"):
        if params.get("project_id") is None:
            raise Exception("project_id is required for Service User/Password type of authentication")
        params.update({"api_secret":None})
    elif params.get("api_secret"):  
         params.update({"username":None,"password":None,"project_id":None})  
    else:
        raise Exception("No API secret OR Username/Password provided.")
          
    with MixpanelClient(parsed_args.config['api_secret'],
                        parsed_args.config['username'],
                        parsed_args.config['password'],
                        parsed_args.config['project_id'],
                        parsed_args.config['user_agent'],
                        parsed_args.config.get('server')) as client:

        state = {}
        if parsed_args.state:
            state = parsed_args.state

        config = parsed_args.config
        properties_flag = config.get('select_properties_by_default')
        denest_properties_flag = config.get('denest_properties', 'true')


        if parsed_args.discover:
            do_discover(client, properties_flag, denest_properties_flag)
        elif parsed_args.catalog:
            sync(client=client,
                 config=config,
                 catalog=parsed_args.catalog,
                 state=state,
                 start_date=start_date)

if __name__ == '__main__':
    main()
