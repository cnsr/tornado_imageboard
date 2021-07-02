from src.board import main
from pymongo.errors import ServerSelectionTimeoutError

if __name__ == '__main__':
    try:
        main()
    except ServerSelectionTimeoutError:
        print("MongoDB service must be running.")

