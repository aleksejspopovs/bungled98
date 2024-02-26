import json
import re
import sys

from dataclasses import dataclass
from pathlib import Path

import mutagen

def is_song(filename):
	return filename.lower().endswith(('.mp3', '.wav', '.flac', '.m4a'))

def natural_sort_key(s):
	s = s.lower()
	parts = re.split(r'([0-9]+)', s)
	parts = tuple(
		(0, int(part)) if part.isdigit() else (1, part)
		for part in parts
		if len(part) > 0
	)
	return parts

def flatten_tags(tags):
	match tags:
		case None:
			return None
		case [*parts]:
			return ' / '.join(parts)
		case tag if isinstance(tag, str):
			return tag
		case unknown:
			assert False, f"unexpected tag {unknown!r}"

def scan_song(path):
	file = mutagen.File(path, easy=True)

	return {
		k: v
		for k in ['artist', 'album', 'title', 'tracknumber', 'date']
		if (v := flatten_tags(file.get(k))) is not None
	}

def song_sorting_key(song_meta):
	return song_meta['name']

def scan_music(music_root, meta_root):
	assert music_root.is_dir()
	meta_root.mkdir(exist_ok=True)

	folders = []
	songs = []
	for child in music_root.iterdir():
		if child.is_dir():
			folders.append(child.name)
		elif is_song(child.name):
			songs.append(child.name)

	folders.sort(key=natural_sort_key)

	songs_with_meta = [
		{'name': name, 'tags': scan_song(music_root / name)}
		for name in songs
	]
	songs_with_meta.sort(key=song_sorting_key)

	total_songs = len(songs_with_meta)

	nonempty_folders = []
	for folder in folders:
		folder_songs = scan_music(music_root / folder, meta_root / folder)
		if folder_songs:
			total_songs += folder_songs
			nonempty_folders.append(folder)

	if total_songs > 0:
		meta = {
			'folders': nonempty_folders,
			'songs': songs_with_meta,
			'total': total_songs,
		}
		meta_path = meta_root / 'meta.json'
		with meta_path.open('w') as meta_file:
			json.dump(meta, meta_file)

	return total_songs

def main():
	_, music_root, meta_root = sys.argv

	music_root = Path(music_root)
	meta_root = Path(meta_root)
	
	scan_music(music_root, meta_root)

if __name__ == '__main__':
	main()
