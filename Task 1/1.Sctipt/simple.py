import re
import sys

if len(sys.argv) < 2:
  print(f"Usage: python {sys.argv[0]} <path_to_file>")
  sys.exit(1)

file_path = sys.argv[1]
print(f"The passed path is: {file_path}")

#file_path = "users.txt"
email_check_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

with open(file_path, "r", encoding="utf-8") as file:
    next(file) # Skip first line
    for line_number, line in enumerate(file, start=2): # loop over the rest of the file
        #print(line)
        user_info = [part.strip() for part in line.split(",")]
        #print(user_info)
        
        # Check if line have 3 parameters
        if len(user_info) <3:
            print(f"Invalid parameters [Line {line_number}]: '{line.strip()}'")
            continue

        user_name = user_info[0]
        user_email = user_info[1]
        user_uid = user_info[2]
        
        # Check email
        if not re.match(email_check_regex, user_email):
            print(f"Invalid parameters [Line {line_number}]: '{line.strip()}'")
            continue

        # Check if UID is even or odd
        if int(user_uid) % 2 == 0:
            parity = "Even"
        else:
            parity = "Odd"

        print(f"The {user_uid} of {user_email} is {parity}.")









