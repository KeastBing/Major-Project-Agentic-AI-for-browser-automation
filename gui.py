# gui.py
import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import threading
import asyncio
import sys
import logging
from types import SimpleNamespace

# Import your async function (must be importable)
from main import run_automation  # noqa: E402

# Retro color palette
BG_COLOR = "#282828"
FG_COLOR = "#00FF00"
INPUT_BG = "#101010"
OUTPUT_BG = "#000000"
BUTTON_BG = "#004400"
BUTTON_FG = "#00FF00"
BUTTON_ACTIVE_BG = "#007700"
FONT_FAMILY = "Courier New"
FONT_SIZE = 13

class StreamToWidget:
    """
    File-like object to replace sys.stdout/sys.stderr.
    write() will be marshalled back to the GUI thread using root.after.
    """
    def __init__(self, write_func, flush_func=None):
        self.write_func = write_func
        self.flush_func = flush_func or (lambda: None)
        self._buffer = ""
        self._lock = threading.Lock()

    def write(self, msg):
        # buffer partial lines until newline to avoid many updates
        if not msg:
            return
        with self._lock:
            self._buffer += msg
            if "\n" in self._buffer:
                lines = self._buffer.splitlines(True)
                for line in lines:
                    if line.endswith("\n"):
                        self.write_func(line.rstrip("\n"))
                    else:
                        # incomplete line; keep in buffer
                        self._buffer = line
                        break
                else:
                    self._buffer = ""
    def flush(self):
        with self._lock:
            if self._buffer:
                self.write_func(self._buffer)
                self._buffer = ""
        self.flush_func()

    def isatty(self):
        return False

class GuiLoggingHandler(logging.Handler):
    """A logging handler that forwards logs to a GUI write function."""
    def __init__(self, write_func):
        super().__init__()
        self.write_func = write_func

    def emit(self, record):
        try:
            msg = self.format(record)
            self.write_func(msg)
        except Exception:
            pass

class App:
    def __init__(self, root):
        self.root = root
        root.title("AI Browser Automation - Retro")
        root.geometry("900x650")
        root.configure(bg=BG_COLOR)

        # Fonts
        self.custom_font = font.Font(family=FONT_FAMILY, size=FONT_SIZE)

        # Input frame
        input_frame = tk.Frame(root, bg=BG_COLOR, padx=12, pady=8)
        input_frame.pack(fill=tk.X)

        self.label = tk.Label(input_frame, text="Enter your task:", fg=FG_COLOR, bg=BG_COLOR, font=self.custom_font)
        self.label.pack(anchor="w")

        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=6,
            font=self.custom_font,
            bg=INPUT_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=6)

        # Buttons frame
        btn_frame = tk.Frame(root, bg=BG_COLOR)
        btn_frame.pack(fill=tk.X, padx=12)

        self.run_button = tk.Button(
            btn_frame, text="Run",
            bg=BUTTON_BG, fg=BUTTON_FG,
            activebackground=BUTTON_ACTIVE_BG,
            activeforeground=BUTTON_FG,
            font=self.custom_font, relief="flat",
            command=self.run_task, cursor="hand2"
        )
        self.run_button.pack(side=tk.LEFT, pady=8, ipadx=12, ipady=6)

        self.stop_button = tk.Button(
            btn_frame, text="Stop",
            bg="#550000", fg="#FFFFFF",
            activebackground="#770000",
            font=self.custom_font, relief="flat",
            command=self.stop_task, cursor="hand2", state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(8,0), pady=8, ipadx=10, ipady=6)

        # Output frame
        output_frame = tk.Frame(root, bg=BG_COLOR, padx=12, pady=8)
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output_label = tk.Label(output_frame, text="Output / Logs:", fg=FG_COLOR, bg=BG_COLOR, font=self.custom_font)
        self.output_label.pack(anchor="w")

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=15,
            font=self.custom_font,
            bg=OUTPUT_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            wrap=tk.WORD
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=6)

        # Bind Ctrl+Q to quit
        root.bind('<Control-q>', lambda e: root.destroy())

        # Keep original std streams for restore
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        self._orig_logging_handlers = None
        self._logging_handler = None

    def append_log(self, message: str):
        """Thread-safe append to log. Called from background threads."""
        def _append():
            self.output_text.insert(tk.END, str(message) + "\n")
            self.output_text.see(tk.END)
        self.root.after(0, _append)

    def _install_stream_capture(self):
        """Replace sys.stdout/sys.stderr and attach logging handler."""
        # write function used by the replacements
        def write_fn(msg):
            # keep it simple: preserve newlines
            self.append_log(msg)

        # Replace stdout and stderr
        self._stream_wrapper = StreamToWidget(write_fn)
        sys.stdout = self._stream_wrapper
        sys.stderr = self._stream_wrapper

        # Install logging handler
        logger = logging.getLogger()
        # Save existing handlers so we can restore them later
        self._orig_logging_handlers = logger.handlers[:]
        # Create and add our handler (format minimally)
        self._logging_handler = GuiLoggingHandler(write_fn)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S")
        self._logging_handler.setFormatter(formatter)
        logger.handlers = [self._logging_handler]
        logger.setLevel(logging.DEBUG)  # show everything; change if noisy

    def _restore_streams(self):
        """Restore sys.stdout/sys.stderr and logging handlers."""
        try:
            sys.stdout = self._orig_stdout
            sys.stderr = self._orig_stderr
        except Exception:
            pass

        if self._orig_logging_handlers is not None:
            logger = logging.getLogger()
            logger.handlers = self._orig_logging_handlers
            self._orig_logging_handlers = None
        self._logging_handler = None

    def run_task(self):
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("Input needed", "Please enter a task before running.")
            return

        # Disable UI controls
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.input_text.config(state=tk.DISABLED)
        self.append_log("Starting task...")

        # Start background thread (daemon so app exits cleanly)
        t = threading.Thread(target=self._thread_worker, args=(user_input,), daemon=True)
        t.start()

    def stop_task(self):
        """Attempt to stop the background automation by flipping the flag in main module."""
        try:
            import main as main_module
            if hasattr(main_module, "in_use"):
                main_module.in_use = False
                self.append_log("Requested stop (main.in_use=False). Automation should stop shortly.")
            else:
                self.append_log("Unable to find 'in_use' in main module.")
        except Exception as e:
            self.append_log(f"Error while requesting stop: {e}")

    def _thread_worker(self, prompt: str):
        """
        Runs in a background thread. Create a new event loop for this thread and run the coroutine.
        We also redirect stdout/stderr and logging while the task runs.
        """
        try:
            # Each thread must have its own event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Install stream capture
            self._install_stream_capture()
            self.append_log("[GUI] Console capture installed. sys.stdout and sys.stderr forwarded here.")

            async def runner():
                # define log callback that marshals logs back to GUI thread
                def log_cb(message: str):
                    # prefer appending directly (these are from your code's log_callback)
                    self.append_log(message)

                try:
                    res = await run_automation(prompt, log_callback=log_cb)
                    return res
                except Exception as ex:
                    # ensure exceptions get printed to captured stdout/stderr and show up in GUI
                    print(f"[Task Exception] {ex}", file=sys.stderr)
                    raise

            result = loop.run_until_complete(runner())

            # Show completion message on GUI thread
            def on_done():
                self.append_log("\n--- Task Finished ---")
                if result is not None:
                    self.append_log(str(result))
                # restore streams
                self._restore_streams()
                self.append_log("[GUI] Console capture stopped. Restored stdout/stderr.")
                self.run_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.input_text.config(state=tk.NORMAL)
            self.root.after(0, on_done)

        except Exception as ex:
            def on_error(ex=ex):
                try:
                    self.append_log(f"\nError in background task: {ex}")
                finally:
                    self._restore_streams()
                    self.append_log("[GUI] Console capture stopped (due to error). Restored stdout/stderr.")
                    self.run_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    self.input_text.config(state=tk.NORMAL)

            self.root.after(0, on_error)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
