# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import threading
from typing import List


def run_process(args):
    """
    Runs the go process and redirect the input/output in the console.
    """
    process = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def forward_output(src, dest):
        for line in src:
            dest.write(line)
            dest.flush()

    threading.Thread(target=forward_output, args=(process.stdout, sys.stdout)).start()
    threading.Thread(target=forward_output, args=(process.stderr, sys.stderr)).start()

    return process


def run_go(argv: List[str]) -> None:
    httdbg_tracer_filename = "httpdbg-tracer.go"
    try:
        if argv[0] != "run":
            print("only the 'go run' command is supported.")
        else:
            args: List[str] = argv.copy()

            args.insert(0, "go")

            # we inject the "tracer" in the Go program during the execution of the "go run" command
            tracer = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "hooks",
                httdbg_tracer_filename,
            )
            os.symlink(
                tracer, httdbg_tracer_filename
            )  # the file must be in the same directory as the other files

            i = 2
            while i < len(args):
                if args[i].endswith(".go") and os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), args[i]
                ):
                    i += 1
                else:
                    break
            args.insert(i, httdbg_tracer_filename)

            process = run_process(args)

            process.wait()
    except SystemExit:
        pass
    finally:
        if os.path.exists(httdbg_tracer_filename):
            os.remove(httdbg_tracer_filename)
