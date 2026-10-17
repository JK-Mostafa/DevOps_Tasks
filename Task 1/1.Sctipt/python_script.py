import logging
import re
import sys
from pathlib import Path

# Default Variables
log_file = Path("logs/app.log")
#file_path = Path("users.txt")
global file_path

## Initialize logging
def init_logs(log_file):
    # Create "logs" directory, skip if exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    # Setup basic logging Config
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )

def check_arg():
    if len(sys.argv) < 2:
        logging.error(f"Usage: python {sys.argv[0]} <path_to_file>")
        sys.exit(1)

    global file_path
    file_path = Path(sys.argv[1])
    

def process_file(file_path):
    ## Read the file
    # Check if the file doesn't exists
    
    if not file_path.exists():
        logging.error(f'The file "{file_path.resolve()}" doesn\'t exist!')
        exit(1)

    # If the file exists
    with file_path.open("r", encoding="utf-8") as file_line:
        # Skip first 
        next(file_line)
        for line_number, line in enumerate(file_line, start=2):
            process_line(line, line_number)
        

def process_line(text, line_number):
    # Split user info
    user_info = [part.strip() for part in text.split(",")]

    # Check if userinfo consists of 3 parameters: username, email, UID
    if len(user_info) < 3:
        logging.warning(f"Invalid User Parameters [Line: {line_number}]: '{text.strip()}'")
        return
    elif len(user_info) > 3:
        logging.warning(f"Invalid User Parameters [Line: {line_number}]: '{text.strip()}'")
        return
    else:
        # Check if ID is a number
        try:
            user_id = int(user_info[2])
        except ValueError:
            logging.warning(f"Invalid User Parameters [Line: {line_number}]: '{text.strip()}'")
            return
        #user_name = user_info[0]
        user_email = user_info[1]

        # Check user email
        if check_email(user_email):
            # check if even or odd
            parity = check_parity(user_id)
            logging.info(f"The {user_id} of {user_info[1]} is {parity}")
        else:
            logging.warning(f"Invalid User Parameters [Line: {line_number}]: '{text.strip()}'")

    # print(user_info[0])

def check_parity(number):
    if number % 2 == 0:
        return "Even"
    else:
        return "Odd"

def check_email(email):
    email_check_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(email_check_regex, email):
        return True
    else:
        return False

def main():
    init_logs(log_file)
    check_arg()
    process_file(file_path)


if __name__ == "__main__":
    main()