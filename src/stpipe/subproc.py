import os
import subprocess

from .step import Step


class SystemCall(Step):
    """
    Execute a system call in the shell.
    """

    spec = """
    # SystemCall is a step to run external processes as Steps.

    # The command can pass along arguments that were passed to the step.
    # To refer to positional arguments, use {0}, {1}, {2}, etc.
    # To refer to keyword arguments, use {keyword}.
    command = string() # The command to execute

    env = string_list(default=list()) # Environment variables to define

    log_stdout = boolean(default=True) # Do we want to log STDOUT?

    log_stderr = boolean(default=True) # Do we want to log STDERR?

    exitcode_as_exception = boolean(default=True) # Should a non-zero exit code be converted into an exception?

    failure_as_exception = boolean(default=True) # If subprocess fails to run at all, should that be an exception?
    """  # noqa: E501

    def process(self, *args):
        from .. import datamodels

        newargs = []
        for i, arg in enumerate(args):
            if isinstance(arg, datamodels.DataModel):
                filename = f"{self.qualified_name}.{i:04d}.{arg.getfileext()}"
                arg.save(filename)
                newargs.append(filename)
            else:
                newargs.append(arg)

        cmd_str = self.command.format(*newargs)

        env = dict(os.environ)
        for item in self.env:
            var, sep, val = item.partition("=")
            env[var] = val or None

        # Start the process and wait for it to finish.
        self.log.info(f"Spawning {cmd_str!r}")
        try:
            p = subprocess.Popen(
                args=[cmd_str],
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                env=env,
            )
            err = p.wait()
        except Exception as e:
            msg = f"Failed with an exception: \n{e}"
            self.log.info(msg)

            if self.failure_as_exception:
                raise
        else:
            self.log.info(f"Done with errorcode {err}")

            # Log STDOUT/ERR if we are asked to do so.
            if self.log_stdout:
                self.log.info(f"STDOUT: {p.stdout.read()}")
            if self.log_stderr:
                self.log.info(f"STDERR: {p.stderr.read()}")

            if self.exitcode_as_exception and err != 0:
                raise OSError(f"{cmd_str!r} returned error code {err}")
