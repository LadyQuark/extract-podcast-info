import json
import os
import requests
from sys import argv, exit
import urllib.parse

def main():

    # If file name provided
    filename = argv[1] if len(argv) == 2 else "podcast_names.txt"

    try:
        podcast_list = get_podcastlist(filename)
    except Exception as e:
        print(e)
        exit(1)

    podcast_feeds = get_feedurls(podcast_list)

    # Serialize dict to JSON formatted string
    json_string = json.dumps(podcast_feeds, indent=4)

    # Write podcast_feed to JSON file
    with open('feeds.json', 'w') as file:
        file.write(json_string)

def get_podcastlist(filename="podcast_names.txt"):
    # Check file ends with `.txt`
    if not filename.endswith(".txt"):
        raise Exception("File name should end in .txt")
    
    # Make path
    try:
        filepath = os.path.join(filename)
    except Exception as e:
        raise Exception(e)

    # Check path exists
    if not os.path.exists(filepath):
        raise Exception(f"Could not find file {filepath}")

    with open(filepath, 'r') as f:
        podcast_list = [line.strip() for line in f.readlines()]

    return podcast_list

def get_feedurls(podcast_list):

    podcast_feeds = {}
    failed = []

    # Iterate through all podcast names
    for name in podcast_list:
    
        # Query for podcast info using iTunes Search API
        url = f'https://itunes.apple.com/search?term={urllib.parse.quote(name)}&media=podcast&entity=podcast'
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            # If request fails, log & move to next podcast name
            print(f"Failed for {name}")
            failed.append(name)
            continue
        
        # Parse response
        try:
            data = response.json()
            
            # Check result count
            count = data['resultCount']
            if count == 0:
                # If no results, log & move to next podcast name
                print(f'{name} has no results')
                failed.append(name)
                continue
            elif count != 1:
                print(f'{name} has more than 1 result')
            
            # Add RSS feed URL to dict `podcast_feeds`
            podcast_feeds[name] = data['results'][0]['feedUrl']

        except (KeyError, TypeError, ValueError, IndexError):
            # If parsing fails, log & move to next podcast name
            print(f"Failed parsing {name}")
            print(data)
            continue

    # Write to JSON file
    # all podcast names that script failed to find RSS feeds for
    if len(failed) > 0:
        with open('failed_feedurl.json', 'w') as file:
            json.dump(failed, file)  
    
    return podcast_feeds



if __name__=="__main__":
    main()