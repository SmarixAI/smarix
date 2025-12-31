# Compatibility shim to preserve existing imports like `from utils.file_utils import FileUtils`
# Delegates implementation to backend/utils/DataCollection/file_utils.py
from .DataCollection.file_utils import *

