# dfuse-extract
Extract DfuSe images (.dfu) into plain binary files.

## Usage
### List images and image elements
`$ dfuse-extract.py dfuse_file` or `$ dfuse-extract.py dfuse_file --list`

### Extract images and image elements
`$ dfuse-extract.py dfuse_file --extract`

Image elements will be saved into the current directory with the name `image<image index>_element<element index>_0x<address>.bin`.
