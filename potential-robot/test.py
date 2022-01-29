import os
import dotenv

dotenv.load_dotenv()
print(os.environ['TESTVAR'])