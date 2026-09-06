from .ProjectController import ProjectController
import os
from .BaseController import BaseController
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnums

class ProcessingController(BaseController):
    def __init__(self,project_id:str):
        super().__init__()
        self.project_id = project_id
        self.project_path=ProjectController().get_or_create_project_path(project_id=project_id)


    def get_file_ext(self,file_id:str):
        file_ext=os.path.splitext(file_id)[-1]
        return file_ext
    def get_file_loader(self,file_id:str):
        file_ext=self.get_file_ext(file_id=file_id)
        file_path=os.path.join(self.project_path,file_id)

        if not os.path.exists(file_path):        # ← ضيف ده
          return None
        if file_ext==ProcessingEnums.TXT.value:
            return TextLoader(file_path)
        elif file_ext==ProcessingEnums.PDF.value:
            return PyMuPDFLoader(file_path)
        else:
            return None

    def get_file_content(self,file_id:str):
        file_loader=self.get_file_loader(file_id=file_id)
        if file_loader is None:
            return None
        else:
            return file_loader.load()

    def process_file(self,file_id:str, chunk_size:int=100,chunk_overlap:int=20):
        file_content=self.get_file_content(file_id=file_id)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                        chunk_overlap=chunk_overlap,
                                                                    length_function=len,
)
        if file_content is None:
            return None
        else:
            file_Texts=[rec.page_content for rec in file_content]
            file_metadata=[rec.metadata for rec in file_content]
            chunks=text_splitter.create_documents(file_Texts,metadatas=file_metadata)
            return chunks
        