def bytearray_to_int(b):
    rv = 0;
    for i in b:
        rv = rv * 256 + ord(i)
    return rv

def print_bytearray(data):
    for i in data:
        print(format(ord(i), "02x"), end=' ')
    print()

with open("/Users/ido/Downloads/picture.png", "rb") as f:
    signature = f.read(8)
    print("signature: ", end=' ')
    print_bytearray(signature)
    print()

    idat_count = 0
    while True:
        # read chunk
        chunk_length = bytearray_to_int(f.read(4))
        chunk_type  = f.read(4)
        chunk_data = f.read(chunk_length)
        chunk_crc =  bytearray_to_int(f.read(4))
        if chunk_type == "IHDR":
            print("IHDR :", end=' ')
            print_bytearray(chunk_data)
            print("width %s" % bytearray_to_int(chunk_data[0:4]))
            print("height %s" % bytearray_to_int(chunk_data[4:8]))
            print("bit depth %s" % bytearray_to_int(chunk_data[8]))
            print("color type %s" % bytearray_to_int(chunk_data[9]))
            print("Compression method %s" % bytearray_to_int(chunk_data[10]))
            print("Filter method %s" % bytearray_to_int(chunk_data[11]))
            print("Interlace method	%s" % bytearray_to_int(chunk_data[12]))
            print()
        elif chunk_type == "IDAT":
            idat_count += 1
            print("IDAT",chunk_length, end=' ')
            print_bytearray(chunk_data[0:2])

        elif chunk_type == "iTXt":
            print("iTXt")
            print(chunk_data)
            print()
        elif chunk_type == "IEND":
            break
        else:
            print("chuck %s length %s" % (chunk_type, chunk_length))
    print("idat count %s"% idat_count)