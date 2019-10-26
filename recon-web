#!/usr/bin/env python3

from recon.core.web import create_app
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1', help="IP address to listen on")
parser.add_argument('--port', default=5000, help="port to bind the web server to")

args = parser.parse_args()

app = create_app()
if __name__ == '__main__':
    app.run(host=args.host, port=args.port)
