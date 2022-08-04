import json
import os
import re
import requests
from sys import argv, exit
import xmltodict

from feedurls import get_feedurls, get_podcastlist
from transform_for_db import transform_rss_item

def main():

    # with open("feeds.json", "r") as file:
    #     feeds = json.load(file)
    
    # If file name provided
    filename = argv[1] if len(argv) == 2 else "podcast_names.txt"

    try:
        podcast_list = get_podcastlist(filename)
    except Exception as e:
        print(e)
        exit(1)

    feeds = get_feedurls(podcast_list)

    failed = {}

    for name in feeds:

        # Get RSS feed from URL
        url = feeds[name]
        try:
            print(f"Trying to get rss for {name}")
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            # If request fails, log & move to next podcast
            print(f"Unable to fetch RSS for {name}")
            failed[name] = f"Unable to fetch RSS from {url}"
            continue

        # Check response of xml type was received
        if "xml" not in response.headers['content-type']:
            # log & move to next podcast
            print(f"Did not receive valid XML for {name}")
            failed[name] = f"Did not receive valid XML: {response.headers['content-type']}"
            continue

        # Parse xml response as dict
        data_dict = xmltodict.parse(response.content)
        data_dict = data_dict["rss"]["channel"]

        # Create json file for podcast in folder `original_json`
        create_json_file(
            folder="original_json", name=name, source_dict=data_dict, failed=failed
        )
        
        # Extract info about podcast from header tags
        header = {
            'title': data_dict.get("title", name),
            'link': data_dict.get("link"),
            'authors': [data_dict.get("itunes:author", "")]
        }
        if not header['link']:
            print(f"Did not get link to podcast")
            failed[name] = f"Did not get link to podcast"
            continue
        
        # Convert each episode into desired format
        episodes = []
        # Loop through each dict representing episode in list `item`
        for item in data_dict["item"]:
            # Convert into structured dict
            episode = transform_rss_item(item, header)
            if not episode:
                print(f"Failed to transform data for {name}. See failed_episode.json")
                failed[name] = f"Failed to transform data for {name}"
                continue
            # Append to list `episodes`
            episodes.append(episode)
        
        # Create json file for transformed episodes in folder `ki_json`
        create_json_file(
            folder="ki_json", name=name, source_dict=episodes, failed=failed
        )
    
    # Create json file for `failed`
    create_json_file(
        folder="", name="failed", source_dict=failed, failed=failed
    )


def create_json_file(folder, name, source_dict, failed):
    # Convert `data_dict` to JSON formatted string
    json_string = json.dumps(source_dict, indent=4)
    try:
        # Create valid file name
        filename = f"{get_valid_filename(name)}.json"
        # Create folder if does not already exist
        if folder != "" and not os.path.exists(folder):
            os.makedirs(folder)
        # Join folder and filename
        filepath = os.path.join(folder, filename)
    except Exception as e:
        print(e)
        failed[name] = "Could not create valid file name or folder"
        return
    # Write to JSON file
    with open(filepath, 'w') as file:
            file.write(json_string)


def get_valid_filename(name):
    """
    modified from: https://github.com/django/django/blob/main/django/utils/text.py

    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise Exception("Could not derive file name from '%s'" % name)
    return s




if __name__=="__main__":
    main()