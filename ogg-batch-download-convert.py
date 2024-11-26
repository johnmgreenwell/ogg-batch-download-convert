import os
import sys
import requests
import music_tag
from bs4 import BeautifulSoup
from urllib.parse import unquote
from pydub import AudioSegment

def convert_ogg_to_mp3(ogg_path, mp3_path):
    """Convert an ogg file to an mp3 file"""
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(mp3_path, format="mp3")

def download_and_convert_ogg(ogg_url, folder='output'):
    """Download an ogg file given its url,
    convert to mp3, and save it in output directory.
    Duplicates are deliberately skipped.
    Returns output_filname, skip_file
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Remove URL-encoded characters
    filename = unquote(ogg_url.split('/')[-1])

    # Determine the appropriate filename for the downloadable and output
    handle_as_mp3 = False
    local_filename_ogg = os.path.join(folder, filename).split('.ogg', 1)[0] + '.ogg'
    if filename.endswith('.mp3'):
        handle_as_mp3 = True
        with open('output_notes.txt', 'a') as file:
                file.write("Was already mp3: " + local_filename_ogg + '\n')
        local_filename_mp3 = os.path.join(folder, filename).split('.ogg', 1)[0] + '.mp3'
    else:
        local_filename_mp3 = local_filename_ogg.split('.ogg', 1)[0] + '.mp3'

    ogg_file_basename = os.path.basename(local_filename_ogg)
    mp3_file_basename = os.path.basename(local_filename_mp3)

    if os.path.isfile(local_filename_mp3):
        print(f"File {mp3_file_basename} already exists. Skipping...")
        return local_filename_mp3, True
    else:
        print(f"Downloading {ogg_file_basename}...")

        # Download the ogg file
        with requests.get(ogg_url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename_ogg, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Skip encoding if already mp3
        if handle_as_mp3:
            os.rename(local_filename_ogg, local_filename_mp3)
            return local_filename_mp3, False

        print(f"Converting {ogg_file_basename} to {mp3_file_basename}...")

        # Attempt the mp3 encoding, and save a list of failed attempts
        try:
            convert_ogg_to_mp3(local_filename_ogg, local_filename_mp3)
            os.remove(local_filename_ogg)
        except:
            print(f"Conversion failed. Logging entry...")
            with open('output_notes.txt', 'a') as file:
                file.write("Conversion fail: " + local_filename_ogg + '\n')

    return local_filename_mp3, False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # URL of the main page containing links to the individual pages with "File:" links
        main_page_url = sys.argv[1]
    else:
        # URL is needed; quit if not supplied
        sys.exit("Requires one input url from which to download .ogg files for conversion.")

    # Allow for optional output directory name
    output_directory = (sys.argv[2] if (len(sys.argv) > 2) else 'output')
    album_name = (sys.argv[3] if (len(sys.argv) > 3) else None)
    artist_name = (sys.argv[4] if (len(sys.argv) > 4) else None)
    thumbnail_file = (sys.argv[5] if (len(sys.argv) > 5) else None)

    print(f"Target URL: {main_page_url}")
    print(f"Output Directory: {output_directory}")
    print(f"Album Name: {album_name}")
    print(f"Artist Name: {artist_name}")
    print(f"Thumbnail File: {thumbnail_file}")

    # Find all the links that contain "File:" in the href on the target URL page
    response = requests.get(main_page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    file_links = [a['href'] for a in soup.find_all('a', href=True) if "File:" in a['href'] and '.ogg' in a['href']]

    total_links = len(file_links)
    print(f"Total items found: {total_links}.")

    # Loop over each "File:" link to navigate to the subpage and download the actual .ogg file
    for link_index, file_link in enumerate(file_links, start=1):
        print(f"Item {link_index} of {total_links}:")

        # If the link is relative, make it absolute
        if not file_link.startswith("http"):
            file_link = requests.compat.urljoin(main_page_url, file_link)

        # Fetch the subpage containing the .ogg link
        file_page_response = requests.get(file_link)
        file_page_soup = BeautifulSoup(file_page_response.content, 'html.parser')
        
        # Check for <audio> tag with a <source> or <audio> src
        audio_tag = file_page_soup.find('audio')
        ogg_url = None
        if audio_tag:
            source_tag = audio_tag.find('source')
            if source_tag and source_tag.get('src'):
                ogg_url = requests.compat.urljoin(file_link, source_tag['src'])
        
        if not ogg_url:
            # If no <audio> tag found, search for direct .ogg URL in <a> tags or elsewhere
            for a_tag in file_page_soup.find_all('a', href=True):
                if a_tag['href'].endswith('.ogg'):
                    ogg_url = requests.compat.urljoin(file_link, a_tag['href'])
                    break

        # Proceed to download and convert if downloadable ogg file found
        # Add metadata if found or given
        if ogg_url:
            output_file, skip_file = download_and_convert_ogg(ogg_url, output_directory)
            output_file_basename = os.path.basename(output_file)
            if not skip_file:
                try:
                    if os.path.isfile(output_file):
                        file_tag = music_tag.load_file(output_file)
                        file_tag['title'] = os.path.splitext(output_file_basename)[0]
                        if album_name:
                            file_tag['album'] = album_name
                        if artist_name:
                            file_tag['artist'] = artist_name
                        if thumbnail_file:
                            if os.path.isfile(thumbnail_file):
                                with open(thumbnail_file, 'rb') as img:
                                    file_tag['artwork'] = img.read()
                        file_tag.save()
                except:
                    print(f"Could not add metadata to {output_file_basename}.")
                    with open('output_notes.txt', 'a') as file:
                        file.write("Failed to write metadata: " + output_file_basename + '\n')
                print(f"Completed {output_file_basename}.")
        else:
            print(f"No .ogg download link found on page {file_link}")

# EOF
