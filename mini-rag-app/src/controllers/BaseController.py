import os
import random
import string
from helpers.config import get_settings


class BaseController:
    def __init__(self):
        self.app_settings = get_settings()                          # 1
        self.base_dir = os.path.dirname(os.path.dirname(__file__))  # 2
        self.files_dir = os.path.join(self.base_dir, "assets/files")

    def generate_random_string(self, length: int = 12):             # 3
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    