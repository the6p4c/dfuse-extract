#!/usr/bin/env python3

# Based upon the DfuSe file format specification, retrieved from
# http://rc.fdr.hu/UM0391.pdf
# Note: the specification blatantly lies that the DFU Prefix, Target Prefix and
# Image Element structures are big endian. In reality, they are stored in little
# endian.

import argparse
import collections
import json
import struct
import sys

DFUPrefix = collections.namedtuple(
    'DFUPrefix', 'signature version file_size image_count'
)

TargetPrefix = collections.namedtuple(
    'TargetPrefix', 'signature alternate_setting is_target_named target_name image_size element_count'
)

Image = collections.namedtuple('Image', 'alternate_setting target_name elements')
ImageElement = collections.namedtuple('ImageElement', 'address size data')

def c_str_to_str(c_str):
    # From https://stackoverflow.com/a/5076070/3492369
    return c_str.split(b'\0', 1)[0].decode('ascii')

class DfuseFile:
    def __init__(self, f, read_data=True):
        self.read_data = read_data

        dfu_prefix = self.read_dfu_prefix(f)

        self.images = []
        for _ in range(dfu_prefix.image_count):
            image = self.read_image(f)
            self.images.append(image)

    def read_dfu_prefix(self, f):
        DFU_PREFIX_LEN = 11
        DFU_PREFIX_SIGNATURE = bytes('DfuSe', 'ascii')
        DFU_PREFIX_VERSION = 0x01

        dfu_prefix = f.read(DFU_PREFIX_LEN)
        dfu_prefix = DFUPrefix(*struct.unpack('< 5s B I B', dfu_prefix))

        if dfu_prefix.signature != DFU_PREFIX_SIGNATURE:
            print('Error: signature mismatch', file=sys.stderr)
            return

        if dfu_prefix.version != DFU_PREFIX_VERSION:
            print('Error: version mismatch', file=sys.stderr)
            return

        return dfu_prefix

    def read_image(self, f):
        TARGET_PREFIX_LEN = 274

        target_prefix = f.read(TARGET_PREFIX_LEN)
        target_prefix = TargetPrefix(*struct.unpack('< 6s B I 255s I I', target_prefix))

        elements = []
        for _ in range(target_prefix.element_count):
            image_element = self.read_image_element(f)
            elements.append(image_element)

        # boolean value stored in 4 bytes - need to parse it
        has_name = target_prefix.is_target_named != 0

        return Image(
            target_prefix.alternate_setting,
            c_str_to_str(target_prefix.target_name) if has_name else None,
            elements
        )

    def read_image_element(self, f):
        IMAGE_ELEMENT_HEADER_LEN = 8

        image_element_header = f.read(IMAGE_ELEMENT_HEADER_LEN)
        address, size = struct.unpack('< I I', image_element_header)

        if self.read_data:
            data = f.read(size)
        else:
            data = None

            FROM_CURRENT = 1
            f.seek(size, FROM_CURRENT)

        return ImageElement(address, size, data)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'dfuse_file', type=argparse.FileType('rb'),
        help='The DfuSe file to extract'
    )

    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        '--list', action='store_const', dest='action', const='list', default='list',
        help='List the images and image elements in the file.'
    )
    actions.add_argument(
        '--extract', action='store_const', dest='action', const='extract',
        help='Extract each image\'s elements into the current directory. '
            'Each element is saved with the filename '
            '\'image<image index>_element<element index>_0x<address>.bin)\'.'
    )

    parser.add_argument(
        '--save-metadata', type=argparse.FileType('w'),
        dest='metadata_file', metavar='filename',
        help='Save metadata to a JSON file (during list or extract).'
    )

    return parser.parse_args()

def action_list(dfuse_file):
    for image_index, image in enumerate(dfuse_file.images):
        print('Image {} (alternate setting = 0x{:X}{}):'.format(
            image_index,
            image.alternate_setting,
            f', target name \'{image.target_name}\'' if image.target_name else ''
        ))
        for image_element_index, image_element in enumerate(image.elements):
            print('\tElement of 0x{0:X} ({0}) bytes at 0x{1:X}'.format(
                image_element.size, image_element.address
            ))

    print()
    print('Hint: extract with \'--extract\'')

def action_extract(dfuse_file):
    for image_index, image in enumerate(dfuse_file.images):
        for image_element_index, image_element in enumerate(image.elements):
            filename = 'image{}_element{}_0x{:X}.bin'.format(
                image_index, image_element_index, image_element.address
            )

            with open(filename, 'wb') as f:
                f.write(image_element.data)

            print('Extracted image {}, element {} to {}'.format(
                image_index, image_element_index, filename
            ))

def save_metadata(dfuse_file, metadata_file):
    def image_element_metadata(image_element):
        return {
            'address': image_element.address,
            'size': image_element.size
        }

    def image_metadata(image):
        image_metadata = {
            'alternate_setting': image.alternate_setting,
            'elements': [image_element_metadata(x) for x in image.elements]
        }

        if image.target_name:
            image_metadata['target_name'] = image.target_name

        return image_metadata

    metadata = [image_metadata(image) for image in dfuse_file.images]
    json.dump(metadata, metadata_file, sort_keys=True)

def main():
    args = parse_args()

    read_data = args.action == 'extract'
    dfuse_file = DfuseFile(args.dfuse_file, read_data)

    if args.action == 'list':
        action_list(dfuse_file)
    elif args.action == 'extract':
        action_extract(dfuse_file)

    if args.metadata_file:
        save_metadata(dfuse_file, args.metadata_file)

if __name__ == '__main__':
    main()
