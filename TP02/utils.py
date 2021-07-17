def encode16(input_string):
    """ Helper function to encode a binary string to a base16 string """

    hex_string = hex(int(input_string, 2))
    return hex_string.split('0x')[1]

def decode16(input_string):
    """ Helper function to decode a base16 string to a binary string"""
    
    bin_string = bin(int(input_string, 16))
    return bin_string.split('0b')[1]