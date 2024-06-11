import threading
import time
from bcc import BPF

class ProcessTracer:
    def __init__(self, output_file):
        self.bpf_program = """
        #include <uapi/linux/ptrace.h>
        #include <linux/sched.h>

        TRACEPOINT_PROBE(sched, sched_process_fork) {
            bpf_trace_printk("C%llu: %s (%d) -> %s (%d)\\n", bpf_ktime_get_ns(), args->parent_comm, args->parent_pid, args->child_comm, args->child_pid);
            return 0;
        }

        TRACEPOINT_PROBE(sched, sched_process_exit) {
            bpf_trace_printk("E%llu: %s (%d)\\n", bpf_ktime_get_ns(), args->comm, args->pid);
            return 0;
        }
        """
        self.b = BPF(text=self.bpf_program)
        self.output_file = output_file
        self.thread = None
        self.running = False

    def trace(self):
        with open(self.output_file, 'w') as f:
            print("Tracing... Output will be written to", self.output_file)
            while self.running:
                try:
                    # Read messages from the BPF ring buffer
                    (task, pid, cpu, flags, ts, msg) = self.b.trace_fields(nonblocking=True)
                    if msg:
                        f.write(f"{ts/1e9:.9f} {msg}\n")
                except KeyboardInterrupt:
                    break

    def start_tracing(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.trace)
            self.thread.start()
            print("Tracing started.")

    def stop_tracing(self):
        if self.running:
            self.running = False
            if self.thread is not None:
                self.thread.join()
            print("Tracing stopped.")

# Functions to start and stop tracing
tracer = ProcessTracer("/home/philipp/pid_trace.txt")

def start():
    tracer.start_tracing()

def stop():
    tracer.stop_tracing()

# Example usage
if __name__ == "__main__":
    start()
    try:
        time.sleep(5)  # Run for a specified duration or perform other tasks
    except KeyboardInterrupt:
        pass
    finally:
        stop()
