import random
import string

def email():
    """
    Generates a random email address for registration purposes.
    
    Returns:
        str: A randomly generated email address in format: random_string@example.com
    """
    # Generate random string of 12 characters
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    # List of common email domains
    domains = [
        'example.com',
        'test.com',
        'tempmail.com',
        'mailinator.com',
        'temp-mail.org',
        'throwaway.email',
        'guerrillamail.com',
        '10minutemail.com',
        'temp-mail.io',
        'fakeinbox.com',
    ]
    
    domain = random.choice(domains)
    return f"{random_string}@{domain}"
