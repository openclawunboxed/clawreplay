import sys
print(sys.version)
if sys.version_info < (3, 10):
    raise SystemExit("python 3.10 or newer is recommended")
print("python check passed")
