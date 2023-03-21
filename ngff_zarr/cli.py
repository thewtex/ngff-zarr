#!/usr/bin/env python

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Convert datasets to and from the OME-Zarr Next Generation File Format.')
    parser.add_argument('input', nargs='+', help='Input image(s)')
    parser.add_argument('output', help='Output image')

    args = parser.parse_args()

if __name__ == '__main__':
    main()
