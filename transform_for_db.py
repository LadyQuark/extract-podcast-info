from datetime import datetime
from dateutil.parser import parse
import json

DEFAULT_VALUES = {
    'permission': "Global",
    'mediaType': "audio",
    'tags': "podcast",
    'type': "ki",
    'transcript': "",
    'createdBy': None,
    'updated': "",
    'isDeleted': False,
}

def standard_date(pub_date):
    if pub_date:
        try:
            date = parse(pub_date)
            # date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
            pub_date = date.strftime("%Y-%m-%d")
        except ValueError:
            return None
    
    return pub_date

def standard_duration(audio_length):
    if audio_length:
        try:
            time = datetime.strptime(audio_length, "%H:%M:%S")
        except ValueError:
            try:
                time = datetime.strptime(audio_length, "%M:%S")
            except ValueError:
                return None

        audio_length = time.strftime("%H:%M:%S")
    
    return audio_length
    

def timestamp_ms():
    utc_time = datetime.utcnow()
    return int(utc_time.timestamp() * 1000)


def transform_rss_item(episode, header):
    try:
        db_item = {
            'title': episode.get('title'), 
            'thumbnail': episode.get('itunes:image').get('@href') if episode.get('itunes:image') else None, 
            'description': episode.get('description'), 
            'permission': DEFAULT_VALUES['permission'], 
            'authors': [episode.get('itunes:author')] if episode.get('itunes:author') else header['authors'], 
            'mediaType': DEFAULT_VALUES['mediaType'], 
            'tags': DEFAULT_VALUES['tags'], 
            'type': DEFAULT_VALUES['type'], 
            'metadata': {
                'audio_length': standard_duration(episode.get('itunes:duration')),
                'audio_file': episode.get('enclosure').get('@url') if episode.get('enclosure') else None,
                'podcast_title': header['title'],
                'url': episode.get('link', header['link']),
                'transcript': episode.get('podcast:transcript', DEFAULT_VALUES['transcript']),
                }, 
            'created': {
                '$date': {
                    '$numberLong': str(timestamp_ms())
                    }
                }, 
            'createdBy': DEFAULT_VALUES['createdBy'],
            'updated': DEFAULT_VALUES['updated'],
            'isDeleted': DEFAULT_VALUES['isDeleted'],
            'original': [episode], 
            'publishedDate': standard_date(episode.get('pubDate'))
        }
    except (KeyError, TypeError) as e:
        print(e)
        # Convert `episode` dict to JSON formatted string
        json_string = json.dumps(episode, indent=4)
        # Write to JSON file
        with open('failed_episode.json', 'w') as file:
            file.write(json_string)
        raise Exception("Key Error / Type Error")

    return db_item