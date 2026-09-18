import random
import hashlib


secret = "password123"



print("=== Challenge-Response Authentication ===")


challenge = str(random.randint(1000, 9999))
print("Server Challenge:", challenge)


data = challenge + secret
response = hashlib.sha256(data.encode()).hexdigest()

print("Client Response:", response)

expected = hashlib.sha256(
    (challenge + secret).encode()
).hexdigest()


if response == expected:
    print("Authentication Successful!")
else:
    print("Authentication Failed!")




print("\n=== Replay Attack ===")


old_response = response

new_challenge = str(random.randint(1000, 9999))
print("New Server Challenge:", new_challenge)

print("Attacker Sends Old Response:", old_response)


new_expected = hashlib.sha256(
    (new_challenge + secret).encode()
).hexdigest()


if old_response == new_expected:
    print("Replay Attack Successful!")
else:
    print("Replay Attack Blocked!")
