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
    """

    def process(self, *args):
        from .. import datamodels

        newargs = []
        for i, arg in enumerate(args):
            if isinstance(arg, datamodels.DataModel):
                filename = "{0}.{1:04d}.{2}".format(
                    self.qualified_name, i, arg.get_fileext())
                arg.save(filename)
                newargs.append(filename)
            else:
                newargs.append(arg)

        cmd_str = self.command.format(*newargs)

        env = dict(os.environ)
        for item in self.env:
            var, sep, val = item.partition('=')
            env[var] = val or None

        # Start the process and wait for it to finish.
        self.log.info('Spawning {0!r}'.format(cmd_str))
        try:
            p = subprocess.Popen(args=[cmd_str],
                                 stdin=None,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 env=env)
            err = p.wait()
        except Exception as e:
            msg = ('Failed with an exception: \n{0}'.format(e))
            self.log.info(msg)

            if self.failure_as_exception:
                raise
        else:
            self.log.info('Done with errorcode {0}'.format(err))

            # Log STDOUT/ERR if we are asked to do so.
            if self.log_stdout:
                self.log.info('STDOUT: {0}'.format(p.stdout.read()))
            if self.log_stderr:
                self.log.info('STDERR: {0}'.format(p.stderr.read()))

            if self.exitcode_as_exception and err != 0:
                raise IOError('{0!r} returned error code {1}'.format(
                    cmd_str, err))
