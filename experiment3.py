import random
import hashlib

# Shared secret known to both client and server
secret = "password123"

# ---------- Challenge-Response Authentication ----------

print("=== Challenge-Response Authentication ===")

# Server generates a random challenge
challenge = str(random.randint(1000, 9999))
print("Server Challenge:", challenge)

# Client creates a response using the challenge and secret
data = challenge + secret
response = hashlib.sha256(data.encode()).hexdigest()

print("Client Response:", response)

# Server creates the expected response
expected = hashlib.sha256(
    (challenge + secret).encode()
).hexdigest()

# Verify the response
if response == expected:
    print("Authentication Successful!")
else:
    print("Authentication Failed!")


# ---------- Replay Attack ----------

print("\n=== Replay Attack ===")

# Attacker stores the old response
old_response = response

# Server generates a new challenge
new_challenge = str(random.randint(1000, 9999))
print("New Server Challenge:", new_challenge)

print("Attacker Sends Old Response:", old_response)

# Server calculates the response for the new challenge
new_expected = hashlib.sha256(
    (new_challenge + secret).encode()
).hexdigest()

# Check the replayed response
if old_response == new_expected:
    print("Replay Attack Successful!")
else:
    print("Replay Attack Blocked!")