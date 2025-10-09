import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import asyncio
import threading
from main import run_automation

# Retro color palette
BG_COLOR = "#282828"        # dark grey background
FG_COLOR = "#00FF00"        # bright green text (classic terminal)
INPUT_BG = "#101010"        # darker input box bg
OUTPUT_BG = "#000000"       # pure black output bg
BUTTON_BG = "#004400"       # dark green button
BUTTON_FG = "#00FF00"       # bright green text on button
BUTTON_ACTIVE_BG = "#007700"  # brighter green on hover
FONT_FAMILY = "Courier New"
FONT_SIZE = 14

class App:
    def __init__(self, root):
        self.root = root
        root.title("AI Browser Automation - Retro")
        root.geometry("900x650")
        root.configure(bg=BG_COLOR)

        # Fonts
        self.custom_font = font.Font(family=FONT_FAMILY, size=FONT_SIZE)

        # Input frame
        input_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=10)
        input_frame.pack(fill=tk.X)

        self.label = tk.Label(input_frame, text="Enter your task:", fg=FG_COLOR, bg=BG_COLOR, font=self.custom_font)
        self.label.pack(anchor="w")

        self.input_text = scrolledtext.ScrolledText(input_frame, height=6, font=self.custom_font, bg=INPUT_BG, fg=FG_COLOR, insertbackground=FG_COLOR)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=10)

        # Run button
        self.run_button = tk.Button(root, text="Run", bg=BUTTON_BG, fg=BUTTON_FG, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG,
                                    font=self.custom_font, relief="flat", command=self.run_task, cursor="hand2")
        self.run_button.pack(pady=10, ipadx=15, ipady=5)

        # Output frame
        output_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=10)
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output_label = tk.Label(output_frame, text="Output / Logs:", fg=FG_COLOR, bg=BG_COLOR, font=self.custom_font)
        self.output_label.pack(anchor="w")

        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, font=self.custom_font, bg=OUTPUT_BG, fg=FG_COLOR, insertbackground=FG_COLOR)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=10)

        # Bind Ctrl+Q to quit
        root.bind('<Control-q>', lambda e: root.destroy())

    def run_task(self):
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("Input needed", "Please enter a task before running.")
            return

        self.run_button.config(state=tk.DISABLED)
        self.output_text.insert(tk.END, "Starting task...\n")

        threading.Thread(target=self.async_runner, args=(user_input,), daemon=True).start()

    def async_runner(self, prompt):
        asyncio.run(self.async_run(prompt))

    async def async_run(self, prompt):
        try:
            def log(message):
                self.root.after(0, self.output_text.insert, tk.END, str(message) + "\n")
                self.root.after(0, self.output_text.see, tk.END)

            result = await run_automation(prompt, log_callback=log)
            self.root.after(0, self.output_text.insert, tk.END, f"\n--- Task Finished ---\n{result}\n")
        except Exception as ex:
            self.root.after(0, self.output_text.insert, tk.END, f"\nError: {ex}\n")
        finally:
            self.root.after(0, self.run_button.config, {"state": tk.NORMAL})

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
