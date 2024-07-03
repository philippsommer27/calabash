import subprocess
import threading
import os
import logging

class ProcessesCapture:

    bpftrace_script = 'src/experiment/processtrace.bt'

    def __init__(self):
        self.process = None
        self.thread = None
        self.running = False

    def _run_bpftrace(self, output_file):
        if os.path.exists(output_file):
            os.remove(output_file)
        open(output_file, 'w').close()

        command = ['bpftrace', self.bpftrace_script, '-o', output_file]
        self.process = subprocess.Popen(command)
        self.process.wait()

    def start_tracing(self, output_file):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_bpftrace, args=(output_file,))
            self.thread.start()
            logging.info("Tracing started.")
            

    def stop_tracing(self):
        if self.running:
            self.running = False
            if self.process:
                self.process.terminate()
                self.process.wait()
            if self.thread:
                self.thread.join()
            logging.info("Tracing stopped.")

    def load_script(self):
        with open(self.bpftrace_script) as file:
            return file.read()
        
