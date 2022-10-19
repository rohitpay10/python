from Crypto.Random import get_random_bytes
key = get_random_bytes(32) # 32 bytes * 8 = 256 bits (1 byte = 8 bits)
print(key)