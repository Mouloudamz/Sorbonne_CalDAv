import os
import requests
from icalendar import Calendar
from datetime import datetime, timedelta , date
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pytz

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = None

# Load credentials from the file
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
service = build('calendar', 'v3', credentials=creds, static_discovery=False)
batch = service.new_batch_http_request()
def fetch_cal(CAL_Name):
    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Authorization": "Basic c3R1ZGVudC5tYXN0ZXI6Z3Vlc3Q=",
        "Connection": "keep-alive",
        "Content-Type": "text/xml; charset=UTF-8",
        "Depth": "1",
        "Origin": "https://cal.ufr-info-p6.jussieu.fr",
        "Referer": "https://cal.ufr-info-p6.jussieu.fr/master/res/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "X-client": "CalDavZAP 0.12.1 (Inf-IT CalDAV Web Client)"
    }

    if CAL_Name == 'M2':
        url = f"https://cal.ufr-info-p6.jussieu.fr/caldav.php/MasterInfo/{CAL_Name}/"
    else:
        url = f"https://cal.ufr-info-p6.jussieu.fr/caldav.php/RES/{CAL_Name}/"
    data = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><L:calendar-query xmlns:L=\"urn:ietf:params:xml:ns:caldav\"><D:prop xmlns:D=\"DAV:\"><D:getcontenttype/><D:getetag/><L:calendar-data/></D:prop><L:filter><L:comp-filter name=\"VCALENDAR\"><L:comp-filter name=\"VEVENT\"><L:time-range start=\"20230624T000000Z\" end=\"20240215T000000Z\"/></L:comp-filter></L:comp-filter></L:filter></L:calendar-query>"

    return requests.get(url, headers=headers, data=data).content.decode('utf-8')

def fetch_ics_events(calendar):
    events = []
    gcal = Calendar.from_ical(calendar)
    paris_tz = pytz.timezone('Europe/Paris')
    now = datetime.now(paris_tz).replace(tzinfo=None)

    def parse_rrule(rrule_str):
        rrule_params = {}
        for part in rrule_str.split(';'):
            key, value = part.split('=', 1)
            rrule_params[key] = value
        return rrule_params

    def parse_until(until_str):
        try:
            return datetime.strptime(until_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=None)
        except ValueError:
            try:
                return datetime.strptime(until_str, '%Y%m%d').replace(tzinfo=None)
            except ValueError:
                raise ValueError(f"UNTIL value '{until_str}' does not match expected formats")

    def generate_occurrences(start, end, rrule_params, exdates):
        occurrences = []
        freq = rrule_params.get('FREQ', 'DAILY')
        interval = int(rrule_params.get('INTERVAL', '1'))
        until_str = rrule_params.get('UNTIL')
        until = parse_until(until_str) if until_str else end
        current = start

        while current <= until:
            if current not in exdates and current >= now - timedelta(weeks=1):
                occurrences.append(current)
            if freq == 'DAILY':
                current += timedelta(days=interval)
            elif freq == 'WEEKLY':
                current += timedelta(weeks=interval)
            elif freq == 'MONTHLY':
                current += timedelta(days=30 * interval)
            elif freq == 'YEARLY':
                current += timedelta(days=365 * interval)
            else:
                break
        return occurrences

    for component in gcal.walk():
        if component.name == "VEVENT":
            summary = component.get('SUMMARY', 'No Title')
            dtstart = component.get('DTSTART').dt
            dtend = component.get('DTEND').dt
            location = component.get('LOCATION', '')
            description = component.get('DESCRIPTION', '')
            rrule_rule = component.get('RRULE')
            exdates = component.get('EXDATE')

            # Convert EXDATEs to a list of datetime objects
            excluded_dates = []
            if exdates:
                if isinstance(exdates, list):
                    for exdate in exdates:
                        for ex in exdate.dts:
                            # Handle both datetime and date objects for EXDATE
                            if isinstance(ex.dt, datetime):
                                excluded_dates.append(ex.dt.replace(tzinfo=None))
                            elif isinstance(ex.dt, date):
                                excluded_dates.append(ex.dt)
                else:
                    for ex in exdates.dts:
                        # Handle both datetime and date objects for EXDATE
                        if isinstance(ex.dt, datetime):
                            excluded_dates.append(ex.dt.replace(tzinfo=None))
                        elif isinstance(ex.dt, date):
                            excluded_dates.append(ex.dt)

            # Handle dtstart and dtend
            if isinstance(dtstart, datetime):
                if dtstart.tzinfo:
                    dtstart = dtstart.astimezone(paris_tz).replace(tzinfo=None)
            elif isinstance(dtstart, date):
                dtstart = datetime.combine(dtstart, datetime.min.time()).replace(tzinfo=None)

            if isinstance(dtend, datetime):
                if dtend.tzinfo:
                    dtend = dtend.astimezone(paris_tz).replace(tzinfo=None)
            elif isinstance(dtend, date):
                dtend = datetime.combine(dtend, datetime.min.time()).replace(tzinfo=None)

            dtstart_str = dtstart.isoformat()
            dtend_str = dtend.isoformat() if isinstance(dtend, datetime) else (dtend - timedelta(days=1)).strftime('%Y-%m-%d')

            if rrule_rule:
                rrule_str = str(rrule_rule.to_ical().decode('utf-8'))
                rrule_params = parse_rrule(rrule_str)
                occurrences = generate_occurrences(dtstart, dtend, rrule_params, excluded_dates)
                for occurrence in occurrences:
                    event_end = occurrence + (dtend - dtstart)
                    events.append({
                        'summary': summary,
                        'start': occurrence.isoformat(),
                        'end': event_end.isoformat(),
                        'location': location,
                        'description': description
                    })
            else:
                if dtstart >= now - timedelta(weeks=1):
                    events.append({
                        'summary': summary,
                        'start': dtstart_str,
                        'end': dtend_str,
                        'location': location,
                        'description': description
                    })

    return events

def batch_update_events(events, calendar_id):
    def batch_callback(request_id, response, exception):
        if exception:
            print(f"Error with request ID : {exception}")
    # Create a new batch request
    batch = service.new_batch_http_request(callback=batch_callback)
    
    for event in events:
        start = {
            'dateTime': event['start'],
            'timeZone': 'Europe/Paris',
        }
        end = {
            'dateTime': event['end'],
            'timeZone': 'Europe/Paris',
        }

        event_body = {
            'summary': event['summary'],
            'location': event['location'],
            'description': event['description'],
            'start': start,
            'end': end,
        }
        # Colorize events that contain 'MU4IN057' in the summary
        print(event['summary'])
        if event['summary'] in [
                'MU5IN057-GAN-CS',
                'MU5IN067-GAN-TME',
                'MU5IN059-SECRES-CS',
                'MU5IN059-SECRES-TME-G2',
                'MU5INOIP-OIP-Groupe 3',
                'MU5INOIP-OIP-Groupe 1'
            ]:
            event_body['colorId'] = '11'  # 11 is a color code for red, you can choose any
            event_body['transparency']= 'transparent'
        # Add each event insert request to the batch
        batch.add(service.events().insert(calendarId=calendar_id, body=event_body))
    
    # Execute the batch request
    batch.execute()

def get_calendar_id_by_name(name):
    calendar_list = service.calendarList().list().execute()
    for calendar_list_entry in calendar_list.get('items', []):
        if calendar_list_entry['summary'] == name:
            return calendar_list_entry['id']
    return None

def delete_google_calendar(calendar_id):
    try:
        service.calendars().delete(calendarId=calendar_id).execute()
        print(f"Deleted calendar with ID")
    except Exception as e:
        print(f"Error deleting calendar ID : {str(e)}")

def create_google_calendar(name):
    calendar = {
        'summary': name,
        'timeZone': 'Europe/Paris'
    }
    created_calendar = service.calendars().insert(body=calendar).execute()
    print(f"Created calendar with ID")
    return created_calendar['id']

def sync_calendar(name):
    response = fetch_cal(name)
    events = fetch_ics_events(response)
    calendar_id = get_calendar_id_by_name(name)
    if calendar_id:
        delete_google_calendar(calendar_id)
    new_calendar_id = create_google_calendar(name)
    batch_update_events(events, new_calendar_id)

if __name__ == "__main__":
    sync_calendar('M2')
    sync_calendar('M2_RES')