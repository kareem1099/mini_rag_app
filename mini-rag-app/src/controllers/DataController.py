import re
from .BaseController import BaseController
from fastapi import UploadFile
import os 
from models import ResponseSignal
from .ProjectController import ProjectController
class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.file_max_size = self.app_settings.FILE_MAX_SIZE
        self.file_allowed_extensions = self.app_settings.FILE_ALLOWED_EXTENSIONS

    def validate_uploaded_file(self, file: UploadFile):
        # Validate file extension
        if file.content_type not in self.file_allowed_extensions:
            return False,ResponseSignal.FILE_TYPE_NOT_SUPPORTED   
        # Validate file size
        if file.size > self.file_max_size:
            return False,ResponseSignal.FILE_SIZE_EXCEEDED
        return True,ResponseSignal.FILE_VALIDATED_SUCCESS

    def generate_unique_filepath(self, orig_file_name: str, project_id: str):

        random_key = self.generate_random_string()
        project_path = ProjectController().get_or_create_project_path(project_id=project_id)

        cleaned_file_name = self.get_clean_file_name(
            orig_file_name=orig_file_name
        )

        new_file_path = os.path.join(
            project_path,
            random_key + "_" + cleaned_file_name
        )

        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                random_key + "_" + cleaned_file_name
            )

        return new_file_path, random_key + "_" + cleaned_file_name

    def get_clean_file_name(self, orig_file_name: str):

        # replace spaces with underscore
        cleaned_file_name = orig_file_name.replace(" ", "_")

        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', cleaned_file_name.strip())


        return cleaned_file_name