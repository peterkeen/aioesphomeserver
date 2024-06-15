from colored import Fore, Style

LOG_LEVEL_COLORS = [
    "",           # NONE
    "\033[1;31m", # ERROR (bold red)
    "\033[0;33m", # WARNING (yellow)
    "\033[0;32m", # INFO (green)
    "\033[0;35m", # CONFIG (magenta)
    "\033[0;36m", # DEBUG (cyan)
    "\033[0;37m", # VERBOSE (gray)
    "\033[0;38m", # VERY_VERBOSE (white)
]

LOG_LEVEL_LETTERS = [
    "",    # NONE
    "E",   # ERROR
    "W",   # WARNING
    "I",   # INFO
    "C",   # CONFIG
    "D",   # DEBUG
    "V",   # VERBOSE
    "VV",  # VERY_VERBOSE
]

LOG_RESET = "\033[0m"

def format_log(level, tag, line_number, message):
    color = LOG_LEVEL_COLORS[level]
    letter = LOG_LEVEL_LETTERS[level]
        
    return f"{color}[{letter}][{tag}:{line_number}]: {message}{LOG_RESET}"
    
