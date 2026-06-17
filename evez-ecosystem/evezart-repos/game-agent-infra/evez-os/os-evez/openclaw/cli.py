"""openclaw.cli — Command-line interface for OpenClaw."""
import argparse, sys
from .tools import ToolRunner


def main():
    p = argparse.ArgumentParser(prog="openclaw")
    sub = p.add_subparsers(dest="cmd")
    read_p = sub.add_parser("read")
    read_p.add_argument("path")
    write_p = sub.add_parser("write")
    write_p.add_argument("path")
    write_p.add_argument("content")
    shell_p = sub.add_parser("shell")
    shell_p.add_argument("cmd")
    args = p.parse_args()
    runner = ToolRunner()
    if args.cmd == "read":
        print(runner.read_file(args.path))
    elif args.cmd == "write":
        runner.write_file(args.path, args.content)
        print("written")
    elif args.cmd == "shell":
        print(runner.run_shell(args.cmd))
    else:
        p.print_help()


if __name__ == "__main__":
    main()
