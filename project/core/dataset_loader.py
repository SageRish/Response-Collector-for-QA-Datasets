import json
import os
from typing import Generator, Tuple, Dict, Any, List

class DatasetLoader:
    def __init__(self):
        self.dataset = None
        self.num_documents = 0
        self.num_questions = 0

    def load(self, file_path: str) -> Tuple[bool, str]:
        """
        Loads and validates the dataset.
        Returns (success, message).
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            file_size = os.path.getsize(file_path)
            
            # Quick check for truncation
            try:
                with open(file_path, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    if f.tell() > 0:
                        f.seek(-1, os.SEEK_END)
                        last_char = f.read(1)
                        # Most JSON files end with } or ] or newline
                        if last_char not in b'}] \n\r\t':
                            return False, f"File appears truncated (ends with byte {last_char}). Please upload again."
            except Exception:
                pass # Ignore check errors, let json.load fail if it must

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "data" not in data:
                return False, "Dataset missing top-level 'data' key."
            
            self.dataset = data
            self.num_documents = len(data["data"])
            self.num_questions = sum(len(doc) for doc in data["data"])
            
            return True, f"Loaded {self.num_documents} documents with {self.num_questions} questions. (Size: {file_size / (1024*1024):.2f} MB)"
        except json.JSONDecodeError as e:
            return False, f"JSON Decode Error: {str(e)}. The file might be corrupted or incomplete."
        except Exception as e:
            return False, f"Error loading dataset: {str(e)}"

    def iter_questions(self) -> Generator[Tuple[int, int, Dict[str, Any]], None, None]:
        """
        Yields (doc_idx, q_idx, question_data) for each question in the dataset.
        """
        if not self.dataset:
            return

        for doc_idx, doc in enumerate(self.dataset["data"]):
            for q_idx, question_entry in enumerate(doc):
                yield doc_idx, q_idx, question_entry

    def get_empty_structure(self) -> List[List[Dict]]:
        """Returns a structure matching the input dataset but empty, to be filled."""
        if not self.dataset:
            return []
        # Create a list of empty lists, one for each document
        return [[] for _ in self.dataset["data"]]
