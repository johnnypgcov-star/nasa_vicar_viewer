"""Decoder for NASA's compressed Voyager / Viking EDR images (.IMQ / .IBG).

Port of DECOMP.C (Kris Becker, USGS 1988) and VDCOMP.C as shipped on the PDS
CD-ROMs. The file is a sequence of variable-length records (2-byte little-endian
length, data, pad to even): PDS label lines up to END, image histogram, encoding
histogram, engineering summary, (Viking: 1056 line-header records), then one
Huffman-coded first-difference record per image line.
"""
import struct


def _records(raw):
    pos, n = 0, len(raw)
    while pos + 2 <= n:
        length = struct.unpack_from("<H", raw, pos)[0]
        pos += 2
        if length == 0xFFFF or pos + length > n:
            return
        yield raw[pos:pos + length]
        pos += length + (length & 1)


def _sort_freq(freq, nodes, start, count):
    # Stable insertion sort of freq[start:start+count] ascending (mirrors sort_freq).
    for i in range(start + 1, start + count):
        f, nd = freq[i], nodes[i]
        j = i
        while j > start and freq[j - 1] > f:
            freq[j], nodes[j] = freq[j - 1], nodes[j - 1]
            j -= 1
        freq[j], nodes[j] = f, nd


def _huff_tree(hist):
    # Nodes are [dn, right, left]; dn == -1 for internal nodes.
    freq = list(hist[:511]) + [0]
    nodes = [[i + 1, None, None] for i in range(512)]
    _sort_freq(freq, nodes, 0, 512)
    p = 0
    num = 512
    while num and freq[p] == 0:
        p += 1
        num -= 1
    temp = nodes[p]
    while num > 1:
        num -= 1
        temp = [-1, nodes[p], nodes[p + 1]]
        nodes[p + 1] = temp
        freq[p + 1] += freq[p]
        freq[p] = 0
        p += 1
        _sort_freq(freq, nodes, p, num)
    return temp


def _byte_table(root):
    """Precompute, for every tree position and input byte, the decoded dns and end position."""
    internal, stack = [], [root]
    while stack:
        nd = stack.pop()
        if nd[0] == -1:
            internal.append(nd)
            stack.append(nd[1]); stack.append(nd[2])
    index = {id(nd): i for i, nd in enumerate(internal)}
    table = []
    for nd in internal:
        row = []
        for byte in range(256):
            ptr, out, test = nd, [], 0x80
            while test:
                ptr = ptr[2] if byte & test else ptr[1]
                if ptr[0] != -1:
                    out.append(ptr[0])
                    ptr = root
                test >>= 1
            row.append((tuple(out), index[id(ptr)]))
        table.append(row)
    return table, index[id(root)]


def decode(raw):
    """Return (lines, samples, pixel_bytes, label_text)."""
    recs = list(_records(raw))
    label = []
    for r in recs:
        line = r.decode("latin1").rstrip()
        label.append(line)
        if line.strip() == "END":
            break
    text = "\n".join(label)
    val = {}
    for ln in label:
        k, _, v = ln.partition("=")
        v = v.strip()
        if v.isdigit() and k.strip() not in val:
            val[k.strip()] = int(v)
    lines, samples = val.get("LINES", 800), val.get("LINE_SAMPLES", 800)
    # Record pointers in the label are 1-based record numbers.
    enc_start = val["^ENCODING_HISTOGRAM"] - 1
    enc_end = min(v for k, v in val.items() if k.startswith("^") and v - 1 > enc_start) - 1
    enc = b"".join(recs[enc_start:enc_end])
    hist = list(struct.unpack_from("<511i", enc.ljust(511 * 4, b"\0")))
    image = recs[val["^IMAGE"] - 1:]

    table, root_i = _byte_table(_huff_tree(hist))
    out = bytearray()
    for r in image[:lines]:
        if not r:
            break
        odn = r[0]
        row = bytearray([odn])
        state = root_i
        for b in r[1:]:
            dns, state = table[state][b]
            for dn in dns:
                odn = (odn - dn) & 0xFF
                row.append(odn)
            if len(row) >= samples:
                break
        out += bytes(row[:samples]).ljust(samples, b"\0")
    got = len(out) // samples
    return got, samples, bytes(out), text
