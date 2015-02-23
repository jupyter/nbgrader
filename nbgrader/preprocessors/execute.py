from IPython.nbconvert.preprocessors import ExecutePreprocessor
from IPython.nbformat.v4 import output_from_msg
from IPython.kernel.manager import KernelManager

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2


class Execute(ExecutePreprocessor):

    def preprocess(self, nb, resources):
        kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')
        extra_arguments = self.extra_arguments + ["--HistoryManager.hist_file=:memory:"]

        self.km = KernelManager(kernel_name=kernel_name)
        self.km.start_kernel(startup_timeout=60, extra_arguments=extra_arguments)
        self.kc = self.km.client()
        self.kc.start_channels(stdin=False)
        self.kc.wait_for_ready()

        try:
            self.log.info("Executing notebook with kernel: %s" % kernel_name)
            nb, resources = super(ExecutePreprocessor, self).preprocess(nb, resources)
        finally:
            self.kc.stop_channels()
            self.km.shutdown_kernel(now=True)

        return nb, resources

    def run_cell(self, cell):
        msg_id = self.kc.execute(cell.source)
        self.log.debug("Executing cell:\n%s", cell.source)
        # wait for finish, with timeout
        while True:
            try:
                msg = self.kc.shell_channel.get_msg(timeout=self.timeout)
            except Empty:
                self.log.error("Timeout waiting for execute reply")
                self.log.error("Interrupting kernel")
                self.km.interrupt_kernel()
                break

            if msg['parent_header'].get('msg_id') == msg_id:
                break
            else:
                # not our reply
                continue

        outs = []

        while True:
            try:
                msg = self.kc.iopub_channel.get_msg(timeout=self.timeout)
            except Empty:
                self.log.warn("Timeout waiting for IOPub output")
                break
            if msg['parent_header'].get('msg_id') != msg_id:
                # not an output from our execution
                continue

            msg_type = msg['msg_type']
            self.log.debug("output: %s", msg_type)
            content = msg['content']

            # set the prompt number for the input and the output
            if 'execution_count' in content:
                cell['execution_count'] = content['execution_count']

            if msg_type == 'status':
                self.log.debug(content)
                if content['execution_state'] == 'idle':
                    break
                else:
                    continue
            elif msg_type == 'execute_input':
                continue
            elif msg_type == 'clear_output':
                outs = []
                continue

            try:
                out = output_from_msg(msg)
            except ValueError:
                self.log.error("unhandled iopub msg: " + msg_type)
            else:
                outs.append(out)

        return outs
