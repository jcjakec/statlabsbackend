import os
import csv
import requests
from django.core.management.base import BaseCommand
from ...models import *
from django.db import transaction
from collections import defaultdict
import pandas as pd


class Command(BaseCommand):
    help = 'Initial population of the database'

    def handle(self, *args, **kwargs):

        # Environment credentials
        CLIENT_ID = 'zpf3m1fonhiuqtlwge5ud3b50yg19a'
        CLIENT_SECRET = 'jehuqqsox0sbdgaiwvqhpvxp5hp012'


        # Data dumps dictionary to retrieve csv files from
        dumps = {
            'games': 'https://api.igdb.com/v4/dumps/games',
            'external_games': 'https://api.igdb.com/v4/dumps/external_games',
            'covers': 'https://api.igdb.com/v4/dumps/covers',
            'screenshots': 'https://api.igdb.com/v4/dumps/screenshots',
            'genres': 'https://api.igdb.com/v4/dumps/genres',
            'themes': 'https://api.igdb.com/v4/dumps/themes',
            'popularity_primitives': 'https://api.igdb.com/v4/dumps/popularity_primitives',
            'involved_companies': 'https://api.igdb.com/v4/dumps/involved_companies',
            'companies': 'https://api.igdb.com/v4/dumps/companies',
            'aliases': 'https://api.igdb.com/v4/dumps/alternative_names',
        }

        target_dir = './services/games/management/commands/csv'
        os.makedirs(target_dir, exist_ok=True)
        file_paths = {key: os.path.join(target_dir, f'{key}.csv') for key in dumps}


        # OAuth token retrieval for igdb from twitch

        try:
            response = requests.post(
                'https://id.twitch.tv/oauth2/token',
                data={
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'grant_type': 'client_credentials'
                }
            )
            response.raise_for_status()
            TOKEN = response.json()['access_token']

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Failed to get access token: {e}'))
            return
        

        # Headers for IGDB request
        headers = {
            'Client-ID': CLIENT_ID,
            'Authorization': f'Bearer {TOKEN}'
        }


        # Downloading CSV files
        self.stdout.write(self.style.HTTP_INFO('Checking csv files'))
        for key, url in dumps.items():
            file_path = file_paths[key]
            if not os.path.exists(file_path):
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()

                    data_dump = response.json()
                    s3_url = data_dump.get('s3_url')
                    if not s3_url:
                        self.stdout.write(self.style.ERROR(f'No S3 URL found in {key} data dump'))
                        return

                    self.stdout.write(f'Downloading {key}.csv to {file_path}')
                    file_response = requests.get(s3_url, stream=True)
                    file_response.raise_for_status()

                    with open(file_path, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    self.stdout.write(self.style.SUCCESS(f'Successfully downloaded {key}.csv'))

                except requests.RequestException as e:
                    self.stdout.write(self.style.ERROR(f'Failed to fetch or download {key} data dump: {e}'))
                    return
            else:
                self.stdout.write(key+" present")
                

        # Processing downloaded csv files
        self.stdout.write(self.style.SUCCESS('All files present'))
        self.stdout.write(self.style.HTTP_INFO('Processing data:'))

        # Create URL for games
        def construct_url(service, game_id):
            service_urls = {
                steam: 'https://store.steampowered.com/app/{game_id}/',
            }
            return service_urls.get(service, '').format(game_id=game_id)

        # Creating platform models & imperative variables
        self.stdout.write(self.style.HTTP_INFO('Processing platform data'))
        self.stdout.write('- Creating platform objects')
        self.stdout.write('- Initialising variables')
        steam, _ = Platform.objects.get_or_create(name="Steam")
        gog, _ = Platform.objects.get_or_create(name="GOG")
        xbox, _ = Platform.objects.get_or_create(name="Xbox")
        epic_games, _ = Platform.objects.get_or_create(name="Epic Games")
        playstation, _ = Platform.objects.get_or_create(name="Playstation")

        platform_enums = {
            '1': steam,
            '5': gog,
            '11': xbox,
            '26': epic_games,
            '36': playstation,
        }

        supported_platforms = {steam}
        valid_statuses = {'0', '2', '3', '4', '5', '8', ''}
        valid_categories = {'0', '4', '8', '9', '10', '11'}

        unsupported_platform_games = 0
        invalid_games = 0


        # Processing

        # Companies
        file_path = file_paths['involved_companies']
        df = pd.read_csv(file_paths['involved_companies'])
        df = df.drop_duplicates(subset=['game', 'company'])
        df.to_csv(file_path, index=False)
        assert not df.duplicated(subset=['game', 'company']).any(), "Duplicates still exist in the CSV!"


        self.stdout.write(self.style.HTTP_INFO('Processing company data'))
        self.stdout.write('- Creating company objects')
        companies = []
        with open(file_paths['companies'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                companies.append(
                    Company(id=row["id"], name=row["name"])
                )
        # Map for retrieving companies for games - retrieve by fetching company map with game id
        self.stdout.write('- Creating involved company map')
        company_map = defaultdict(list)
        with open(file_paths['involved_companies'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                company_map[row['game']].append(row['company'])
        self.stdout.write('- Appending')     
        Company.objects.bulk_create(companies)
        self.stdout.write(self.style.SUCCESS('Appended '))



        # Tags
        # genres.csv & themes.csv 
        self.stdout.write(self.style.HTTP_INFO('Processing tag data'))
        self.stdout.write('- Genres data')
        tags = []
        genre_map = defaultdict(list)
        theme_map = defaultdict(list)
        with open(file_paths['genres'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tag = Tag(name=row['name'])
                genre_map[row['id']].append(tag)
                tags.append(tag)
        self.stdout.write('- Themes data')
        with open(file_paths['themes'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tag = Tag(name=row['name'])
                theme_map[row['id']].append(tag)
                tags.append(tag)
        self.stdout.write('- Appending')
        Tag.objects.bulk_create(tags)
        self.stdout.write(self.style.SUCCESS('Appended '))

        
        # Misc data 
        self.stdout.write(self.style.HTTP_INFO('Processing miscallaneous game data'))
        self.stdout.write('- Popularity data')
        popularity = {}
        with open(file_paths['popularity_primitives'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                game_id = row['game_id']
                value = float(row['value'])
                popularity[game_id] = round(popularity.get(game_id, 0) + value, 6)  
  
                
        self.stdout.write('- Alias data')
        aliases = {}
        with open(file_paths['aliases'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                aliases.setdefault(row['game'], []).append(row['name'])
        self.stdout.write('- Cover data')
        covers = {}
        with open(file_paths['covers'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                covers[row['game']] = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{row['image_id']}.webp"

        # Platform data 
        self.stdout.write('- Platforms data')
        platforms_map = defaultdict(list)
        with open(file_paths['external_games'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                game_id = row['game']
                if row['category'] in platform_enums:
                    if platform_enums[row['category']]:
                        platforms_map[game_id].append(platform_enums[row['category']])
                    else:
                        pass
        
        

        # Games
        self.stdout.write(self.style.HTTP_INFO('Processing game data'))
        games = []
        game_relations = {}
        total_games = 0

        with open(file_paths['games'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total_games += 1

                if row['category'] not in valid_categories or row['status'] not in valid_statuses:
                    invalid_games += 1
                    continue

                if not any(platform in supported_platforms for platform in platforms_map.get(row['id'], [])):
                    unsupported_platform_games += 1
                    continue


                try:
                    game_data = {
                        'id': row['id'],
                        'name': row['name'],
                        'aliases': aliases.get(row['id'], []),
                        'description': row.get('summary', ''),
                        'cover': covers.get(row['id'], ''),
                        'popularity': popularity.get(row['id'], 0),
                    }

                    game_instance = Game(**game_data)
                    games.append(game_instance)

                    genres = []
                    themes = []

                    for genre in row.get('genres', '').split(','):
                        genres.extend(tag.id for tag in genre_map.get(genre, []))

                    for theme in row.get('themes', '').split(','):
                        themes.extend(tag.id for tag in theme_map.get(theme, []))

                    game_relations[row['id']] = {
                        'companies': company_map.get(row['id'], []),
                        'tags': genres + themes,
                    }
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating game instance for game ID {row['id']}: {e}"))
                    invalid_games += 1

        self.stdout.write('- Created')
        self.stdout.write('- Appending')
        Game.objects.bulk_create(games)
        self.stdout.write(self.style.SUCCESS(f"Appended "))


        self.stdout.write(self.style.HTTP_INFO(f"Processing relationships"))

        self.stdout.write("Game & Company relations")
        valid_game_ids = set(Game.objects.all().values_list('id', flat=True))

        with open(file_paths['involved_companies'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            game_company_relations = []
            for row in reader:
                if int(row['game']) in valid_game_ids:
                    game_company_relations.append(
                        Game.companies.through(game_id=row['game'], company_id=row['company'])
                    )
        self.stdout.write("- Created")
        Game.companies.through.objects.bulk_create(game_company_relations, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"Appended "))



        # Game-Tag Relationships
        self.stdout.write("Game & Tag relations")
        game_tag_relations = []
        for game_id, game_data in game_relations.items():
            for tag_id in game_data['tags']:
                game_tag_relations.append(
                    Game.tags.through(game_id=game_id, tag_id=tag_id)
                )

        self.stdout.write("- Created")
        Game.tags.through.objects.bulk_create(game_tag_relations, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"Appended "))


        file_path = file_paths['external_games']
        df = pd.read_csv(file_paths['external_games'])
        df = df.drop_duplicates(subset=['game', 'category'])
        df.to_csv(file_path, index=False)
        assert not df.duplicated(subset=['game', 'category']).any(), "Duplicates still exist in the CSV!"

        self.stdout.write("Platform Profiles")
        platform_profiles = []
        with open(file_paths['external_games'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if int(row['game']) in valid_game_ids:
                    if row['category'] in platform_enums:
                        platform_profiles.append(
                            GameInstance(game_id=row['game'], platform=platform_enums[row['category']], uid=row['uid'], url=row['url'] if row['url'] else construct_url(platform_enums[row['category']], row['uid']))
                        )
        self.stdout.write("- Created")
        GameInstance.objects.bulk_create(platform_profiles, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"Appended "))



        self.stdout.write(self.style.SUCCESS(f"Completed population"))
        self.stdout.write(f"Processed games: {total_games}")
        self.stdout.write(f"Added: {len(games)}")
        self.stdout.write(f"Invalid: {invalid_games}")
        self.stdout.write(f"Unsupported: {unsupported_platform_games}")