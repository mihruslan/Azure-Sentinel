import oci
from oci.util import to_dict
import asyncio
import logging
import os
import re
import datetime
from dateutil.parser import parse as parse_date
import azure.functions as func

from .sentinel_connector_async import AzureSentinelConnectorAsync
from .state_manager_async import StateManagerAsync


logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)


WORKSPACE_ID = os.environ['AzureSentinelWorkspaceId']
SHARED_KEY = os.environ['AzureSentinelSharedKey']
TENANCY = os.environ['tenancy']
FILE_SHARE_CONN_STRING = os.environ['AzureWebJobsStorage']
LOG_TYPE = 'OCIAuditLogs'

# if ts of last event is older than now - MAX_PERIOD_MINUTES -> script will get events from now - MAX_PERIOD_MINUTES
MAX_PERIOD_MINUTES = 60 * 24 * 7


LOG_ANALYTICS_URI = os.environ.get('logAnalyticsUri')

if not LOG_ANALYTICS_URI or str(LOG_ANALYTICS_URI).isspace():
    LOG_ANALYTICS_URI = 'https://' + WORKSPACE_ID + '.ods.opinsights.azure.com'

pattern = r'https:\/\/([\w\-]+)\.ods\.opinsights\.azure.([a-zA-Z\.]+)$'
match = re.match(pattern, str(LOG_ANALYTICS_URI))
if not match:
    raise Exception("Invalid Log Analytics Uri.")


def get_config():
    config = {
        "user": os.environ['user'],
        "key_content": parse_key(os.environ['key_content']),
        "pass_phrase": os.environ.get('pass_phrase', ''),
        "fingerprint": os.environ['fingerprint'],
        "tenancy": os.environ['tenancy'],
        "region": os.environ['region']
    }
    return config


async def main(mytimer: func.TimerRequest):
    logging.info('Script started.')
    config = get_config()
    oci.config.validate_config(config)
    client = oci.audit.AuditClient(config)
    sentinel = AzureSentinelConnectorAsync(LOG_ANALYTICS_URI, WORKSPACE_ID, SHARED_KEY, LOG_TYPE, queue_size=10000)
    state_manager = StateManagerAsync(FILE_SHARE_CONN_STRING, share_name='ociauditcheckpoint', file_path='ociauditlasteventdate')

    last_event_date = await state_manager.get()
    max_period = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(minutes=MAX_PERIOD_MINUTES)
    if not last_event_date or parse_date(last_event_date) < max_period:
        start_time = max_period.isoformat()
        logging.info('Last event was too long ago or there is no info about last event timestamp.')
    else:
        start_time = (parse_date(last_event_date) + datetime.timedelta(milliseconds=1)).isoformat()
    logging.info('Starting searching events from {}'.format(start_time))

    end_time = datetime.datetime.utcnow().isoformat()

    res = client.list_events(TENANCY, start_time, end_time)
    for event in res.data:
        event = to_dict(event)
        await sentinel.send(event)
        last_event_date = event['event_time']

    while res.has_next_page:
        res = client.list_events(TENANCY, start_time, end_time, page=res.next_page)
        for event in res.data:
            event = to_dict(event)
            await sentinel.send(event)
            last_event_date = event['event_time']

    await sentinel.flush()

    if last_event_date:
        await state_manager.post(last_event_date)
        logging.info('Last event checkpoint saved - {}'.format(last_event_date))

    logging.info('Program finished. {} events have been sent.'.format(sentinel.successfull_sent_events_number))


def parse_key(key_input):
    try:
        begin_line = re.search(r'-----BEGIN [A-Z ]+-----', key_input).group()
        key_input = key_input.replace(begin_line, '')
        end_line = re.search(r'-----END [A-Z ]+-----', key_input).group()
        key_input = key_input.replace(end_line, '')
        encr_lines = ''
        proc_type_line = re.search(r'Proc-Type: [^ ]+', key_input)
        if proc_type_line:
            proc_type_line = proc_type_line.group()
            dec_info_line = re.search(r'DEK-Info: [^ ]+', key_input).group()
            encr_lines += proc_type_line + '\n'
            encr_lines += dec_info_line + '\n'
            key_input = key_input.replace(proc_type_line, '')
            key_input = key_input.replace(dec_info_line, '')
        body = key_input.strip().replace(' ', '\n')
        res = ''
        res += begin_line + '\n'
        if encr_lines:
            res += encr_lines + '\n'
        res += body + '\n'
        res += end_line
    except Exception:
        raise Exception('Error while reading private key.')
    return res