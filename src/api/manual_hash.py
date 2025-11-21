from argon2 import PasswordHasher
import sys

def hash_password_standalone(password):
    """
    Hashes a given password using Argon2 with the specified parameters.
    """
    # Initialize the PasswordHasher with your specific parameters
    ph = PasswordHasher(
        time_cost=4, 
        memory_cost=102400, 
        parallelism=8, 
        hash_len=32
    )

    # Hash the password
    hashed_password = ph.hash(password)
    
    return hashed_password

if __name__ == "__main__":
    
    # 1. Determine the password source
    if len(sys.argv) < 2:
        # Prompt the user for input if no argument is provided
        password_to_hash = input("What password do you want to hash: ")
        
        # Check if the user entered an empty string
        if not password_to_hash:
            print("Error: No password provided.")
            sys.exit(1)
            
    else:
        # Use the command-line argument
        password_to_hash = sys.argv[1]
    
    # --- Hashing Process ---
    
    print(f"\nHashing password...")
    
    try:
        # Generate the hash
        new_hash = hash_password_standalone(password_to_hash)
        
        # Print the resulting hash (this is what you'll copy/paste into your DB)
        print("\n--- HASH RESULT ---")
        print(new_hash)
        print("-------------------")
        
    except Exception as e:
        print(f"An error occurred during hashing: {e}")