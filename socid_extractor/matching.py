"""
    Accounts matching
"""

import io
import requests

from imagehash import phash, whash, dhash, colorhash, average_hash
from Levenshtein import ratio
from PIL import Image


def get_image_content(link):
    """
        Download image and convert to PIL Image format
    """
    response = requests.get(link, timeout=10)
    if response.content and 'image' in response.headers.get('content-type', ''):
        return Image.open(io.BytesIO(response.content))
    return None


def get_strings_similarity(str1, str2):
    """
        Levenstein strings distance
    """
    return round(ratio(str1, str2), 2)


def get_images_similarity(image1, image2):
    """
        Best image hash similarity from several hashes
    """
    ratios = []
    for hash_func in [phash, whash, colorhash, average_hash, dhash]:
        score = get_strings_similarity(
            str(hash_func(image1)),
            str(hash_func(image2)),
        )
        ratios.append((score, str(hash_func).split()[1]))

    best_result = sorted(ratios, key=lambda x: x[0])
    return best_result[-1]


def get_similarity(str1, str2):
    """
        General similarity function
    """
    if 'https' in str1 and 'https' in str2:
        return get_images_similarity(
            get_image_content(str1),
            get_image_content(str2),
        )

    return get_strings_similarity(str1, str2), 'levenshtein distance'


def get_similarity_description(score, sim_type, field):
    """
        Pretty-printed info about extracted accounts values similarity
    """
    percent_score = score * 100
    return (f'Similarity of field "{field}" values'
            f'\n ┣╸{percent_score}%\n ┗╸{sim_type} check')
