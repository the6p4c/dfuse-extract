# dfuse-extract
Extract DfuSe images (.dfu) into plain binary files.

DfuSe is the format of DFU firmware images used by ST, and most commonly on their STM32 line of microcontrollers.

## Usage
### List images and image elements
`$ dfuse-extract.py dfuse_file` or `$ dfuse-extract.py dfuse_file --list`

### Extract images and image elements
`$ dfuse-extract.py dfuse_file --extract`

Image elements will be saved into the current directory with the name `image<image index>_element<element index>_0x<address>.bin`.

### Extract images with all elements written to a single bin file
`$ dfuse-extract.py dfuse_file --extract-single`

Image elements will be saved into the current directory with the name `image<image index>_0x<address>.bin`.
