def hamming_distance(D1, D2):
    return bin(int(D1, 16) ^ int(D2, 16)).count("1")
count = hamming_distance("38fcb73b109d0f4d1297890237566b6cd51f781d797c65de9f686173c59e6d5c", "4933439b802d44ba77a9b6179bddc84e3a9df36143a4d4b059f6edd7d10f4ee6")
print(count)